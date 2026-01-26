"""
训练集生成器 - 从历史数据生成训练样本
"""

import json
import logging
from typing import Dict, List, Optional, Generator
from pathlib import Path
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """从历史数据构建训练集"""

    def __init__(self, lifecycle_dir: str = "data/training"):
        self.lifecycle_dir = Path(lifecycle_dir)
        self.samples: List[Dict] = []

    def load_lifecycle_files(self, file_pattern: str = "lifecycle_*.jsonl") -> int:
        """
        加载生命周期数据文件

        Args:
            file_pattern: 文件匹配模式

        Returns:
            加载的代币数量
        """
        loaded_tokens = 0
        lifecycle_files = list(self.lifecycle_dir.glob(file_pattern))

        logger.info(f"Found {len(lifecycle_files)} lifecycle files")

        for filepath in lifecycle_files:
            with filepath.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        lifecycle = json.loads(line.strip())
                        # 生成样本
                        samples = self._generate_samples_from_lifecycle(lifecycle)
                        self.samples.extend(samples)
                        loaded_tokens += 1
                    except Exception as e:
                        logger.error(f"Error loading lifecycle: {e}")
                        import traceback
                        traceback.print_exc()

        logger.info(f"Loaded {loaded_tokens} tokens, generated {len(self.samples)} samples")
        return loaded_tokens

    def _normalize_lifecycle(self, lifecycle: Dict) -> Dict:
        """标准化生命周期数据格式 (适配新数据源)"""
        # 如果是新格式 (包含 created_at 且没有 buys/sells)
        if 'created_at' in lifecycle and 'buys' not in lifecycle:
            norm = lifecycle.copy()
            norm['create_timestamp'] = lifecycle['created_at']

            # 初始化 buys/sells
            norm['buys'] = []
            norm['sells'] = []

            # 缩放 supply 和 launch_fee 到 Wei (以匹配旧代码的除法逻辑)
            # 假设新数据是 readable 格式 (如 10亿, 0.01)
            norm['total_supply'] = float(lifecycle.get('total_supply', 0)) * 1e18
            norm['launch_fee'] = float(lifecycle.get('launch_fee', 0)) * 1e18

            # 处理 purchases -> buys
            for p in lifecycle.get('purchases', []):
                new_p = p.copy()
                # 关键: 计算价格
                # price = ether_amount / token_amount
                new_p['bnb_amount'] = p['ether_amount']
                if p['token_amount'] > 0:
                    new_p['price'] = p['ether_amount'] / p['token_amount']
                else:
                    new_p['price'] = 0
                norm['buys'].append(new_p)

            # 处理 sales -> sells
            for s in lifecycle.get('sales', []):
                new_s = s.copy()
                new_s['bnb_amount'] = s['ether_amount']
                if s['token_amount'] > 0:
                    new_s['price'] = s['ether_amount'] / s['token_amount']
                else:
                    new_s['price'] = 0
                norm['sells'].append(new_s)

            return norm

        return lifecycle

    def _generate_samples_from_lifecycle(self, lifecycle: Dict,
                                          sample_intervals: List[int] = None) -> List[Dict]:
        """
        从单个代币生命周期生成多个训练样本

        Args:
            lifecycle: 代币生命周期数据
            sample_intervals: 采样时间点 (相对launch时间的秒数)
                             默认: 多个时间点以获取更多样本

        Returns:
            训练样本列表
        """
        # 标准化数据格式 (适配新旧数据)
        lifecycle = self._normalize_lifecycle(lifecycle)

        if sample_intervals is None:
            # 增加更多采样点: 15s, 30s, 45s, 60s, 90s, 120s, 180s, 240s, 300s
            sample_intervals = [15, 30, 45, 60, 90, 120, 180, 240, 300]

        samples = []
        create_time = lifecycle['create_timestamp']

        # 恢复 set
        lifecycle['unique_buyers'] = set(lifecycle.get('unique_buyers', []))
        lifecycle['unique_sellers'] = set(lifecycle.get('unique_sellers', []))

        for interval in sample_intervals:
            sample_time = create_time + interval

            # 检查是否有足够的历史数据
            past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
            if not past_buys or len(past_buys) < 3:  # 至少3笔交易
                continue

            # 为每个采样点生成多个未来窗口的样本
            future_windows = [60, 120, 300, 600]  # 1分钟, 2分钟, 5分钟, 10分钟

            for future_window in future_windows:
                future_end_time = sample_time + future_window
                future_trades = [t for t in lifecycle['buys'] + lifecycle['sells']
                               if sample_time < t['timestamp'] <= future_end_time]

                if not future_trades:
                    continue  # 没有未来数据

                # 生成样本
                sample = self._create_sample_with_window(
                    lifecycle, sample_time, future_window
                )
                if sample:
                    samples.append(sample)

        return samples

    def _create_sample_with_window(self, lifecycle: Dict, sample_time: int, future_window: int) -> Optional[Dict]:
        """创建单个训练样本 (带未来窗口信息)"""

        # 只使用 sample_time 之前的数据
        past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
        past_sells = [s for s in lifecycle['sells'] if s['timestamp'] <= sample_time]

        if not past_buys:
            return None

        # 计算特征
        features = self._extract_features(lifecycle, past_buys, past_sells, sample_time)

        # 添加未来窗口作为特征 (帮助模型理解预测时间范围)
        features['future_window'] = future_window

        # 计算标签
        label = self._calculate_label_with_window(lifecycle, sample_time, future_window)

        if label is None:
            return None

        return {
            'features': features,
            'label': label,
            'meta': {
                'token_address': lifecycle['token_address'],
                'symbol': lifecycle['symbol'],
                'sample_time': sample_time,
                'sample_interval': sample_time - lifecycle['create_timestamp'],
                'future_window': future_window,
            }
        }

    def _extract_features(self, lifecycle: Dict,
                          past_buys: List[Dict],
                          past_sells: List[Dict],
                          sample_time: int) -> Dict:
        """提取特征 (增强版)"""

        time_since_launch = sample_time - lifecycle['create_timestamp']

        # 基本信息
        total_supply = lifecycle['total_supply'] / 1e18
        launch_fee = lifecycle['launch_fee'] / 1e18
        liquidity_ratio = (launch_fee * 1e18) / lifecycle['total_supply'] if lifecycle['total_supply'] > 0 else 0

        # 交易统计
        total_buys = len(past_buys)
        total_sells = len(past_sells)
        unique_buyers = len(set(b['account'] for b in past_buys))
        unique_sellers = len(set(s['account'] for s in past_sells))

        total_buy_volume = sum(b['bnb_amount'] for b in past_buys)
        total_sell_volume = sum(s['bnb_amount'] for s in past_sells)

        # 价格统计
        current_price = past_buys[-1]['price'] if past_buys else 0
        first_price = past_buys[0]['price'] if past_buys else 0
        price_change_pct = ((current_price - first_price) / first_price * 100) if first_price > 0 else 0

        all_prices = [b['price'] for b in past_buys] + [s['price'] for s in past_sells]
        max_price = max(all_prices) if all_prices else 0
        min_price = min(all_prices) if all_prices else 0

        # 时间窗口成交量 (多个窗口)
        def calc_window_volume(window_seconds):
            cutoff = sample_time - window_seconds
            return sum(b['bnb_amount'] for b in past_buys if b['timestamp'] >= cutoff)

        volume_10s = calc_window_volume(10)
        volume_30s = calc_window_volume(30)
        volume_1min = calc_window_volume(60)
        volume_2min = calc_window_volume(120)
        volume_5min = calc_window_volume(300)

        # 动量指标
        buy_pressure = total_buy_volume / (total_buy_volume + total_sell_volume) if (total_buy_volume + total_sell_volume) > 0 else 0.5
        avg_buy_size = total_buy_volume / total_buys if total_buys > 0 else 0
        avg_sell_size = total_sell_volume / total_sells if total_sells > 0 else 0
        trade_frequency = (total_buys + total_sells) / (time_since_launch / 60) if time_since_launch > 0 else 0

        # 价格动量 (最近vs最初)
        recent_window = 30  # 最近30秒
        recent_buys = [b for b in past_buys if b['timestamp'] >= sample_time - recent_window]
        recent_avg_price = sum(b['price'] for b in recent_buys) / len(recent_buys) if recent_buys else current_price
        price_momentum = ((recent_avg_price - first_price) / first_price * 100) if first_price > 0 else 0

        # 持有者集中度
        buyer_concentration = unique_buyers / total_buys if total_buys > 0 else 0  # 越低越集中
        seller_concentration = unique_sellers / total_sells if total_sells > 0 else 1

        # 新增: 交易量变化率
        volume_acceleration = (volume_1min - volume_2min) / volume_2min if volume_2min > 0 else 0

        # ========== 新增: 持币地址分析 ==========
        # 计算每个地址的持币量 (买入 - 卖出)
        address_balances = {}
        for buy in past_buys:
            addr = buy['account']
            address_balances[addr] = address_balances.get(addr, 0) + buy['token_amount']

        for sell in past_sells:
            addr = sell['account']
            address_balances[addr] = address_balances.get(addr, 0) - sell['token_amount']

        # 过滤掉余额为0或负数的地址
        holder_balances = {addr: balance for addr, balance in address_balances.items() if balance > 0}

        # 持币地址数量
        holder_count = len(holder_balances)

        # 持币集中度 (前5大地址占比)
        if holder_balances:
            sorted_balances = sorted(holder_balances.values(), reverse=True)
            total_held = sum(sorted_balances)
            top5_balances = sum(sorted_balances[:5]) if len(sorted_balances) >= 5 else sum(sorted_balances)
            holder_concentration_top5 = top5_balances / total_held if total_held > 0 else 0

            # 最大持币者占比
            max_holder_ratio = sorted_balances[0] / total_held if total_held > 0 else 0

            # 平均持币量
            avg_holding = total_held / holder_count if holder_count > 0 else 0
        else:
            holder_concentration_top5 = 0
            max_holder_ratio = 0
            avg_holding = 0

        # ========== 创建者地址分析 ==========
        creator = lifecycle.get('creator', '')

        # 创建者是否参与交易
        creator_is_buyer = creator in [b['account'] for b in past_buys]
        creator_is_seller = creator in [s['account'] for s in past_sells]

        # 创建者交易量
        creator_buy_volume = sum(b['bnb_amount'] for b in past_buys if b['account'] == creator)
        creator_sell_volume = sum(s['bnb_amount'] for s in past_sells if s['account'] == creator)

        # 创建者持币比例
        creator_balance = address_balances.get(creator, 0)
        creator_holding_ratio = creator_balance / total_supply if total_supply > 0 else 0

        # ========== 大户分析 ==========
        # 定义大户: 单笔买入 > 平均买入量的3倍
        if avg_buy_size > 0:
            whale_threshold = avg_buy_size * 3
            whale_buys = [b for b in past_buys if b['bnb_amount'] > whale_threshold]
            whale_count = len(set(b['account'] for b in whale_buys))
            whale_buy_volume = sum(b['bnb_amount'] for b in whale_buys)
            whale_volume_ratio = whale_buy_volume / total_buy_volume if total_buy_volume > 0 else 0
        else:
            whale_count = 0
            whale_volume_ratio = 0

        # ========== 交易行为分析 ==========
        # 重复买家比例 (买过多次的人)
        buyer_trade_counts = {}
        for buy in past_buys:
            addr = buy['account']
            buyer_trade_counts[addr] = buyer_trade_counts.get(addr, 0) + 1

        repeat_buyers = sum(1 for count in buyer_trade_counts.values() if count > 1)
        repeat_buyer_ratio = repeat_buyers / unique_buyers if unique_buyers > 0 else 0

        # 卖出/买入地址重叠率 (既买又卖的地址)
        buyers_set = set(b['account'] for b in past_buys)
        sellers_set = set(s['account'] for s in past_sells)
        overlap_addresses = buyers_set & sellers_set
        address_overlap_ratio = len(overlap_addresses) / len(buyers_set) if buyers_set else 0

        # ========== 新增: 早期活动分析 (30秒内) ==========
        create_time = lifecycle['create_timestamp']
        early_window = 30  # 前30秒

        early_buys = [b for b in past_buys if b['timestamp'] - create_time <= early_window]
        early_buy_count = len(early_buys)
        early_buy_volume = sum(b['bnb_amount'] for b in early_buys)
        early_unique_buyers = len(set(b['account'] for b in early_buys))

        # 早期活跃度占比
        early_activity_ratio = early_buy_count / total_buys if total_buys > 0 else 0
        early_volume_ratio = early_buy_volume / total_buy_volume if total_buy_volume > 0 else 0

        # ========== 新增: 突发买入检测 ==========
        # 检测是否在某个时间窗口内有大量买入
        burst_detected = False
        max_burst_volume = 0
        burst_window = 10  # 10秒窗口

        if len(past_buys) >= 3:
            for i in range(len(past_buys)):
                window_start = past_buys[i]['timestamp']
                window_buys = [b for b in past_buys if window_start <= b['timestamp'] < window_start + burst_window]
                window_volume = sum(b['bnb_amount'] for b in window_buys)

                if window_volume > max_burst_volume:
                    max_burst_volume = window_volume

                # 判断是否为爆发: 10秒内成交量 > 总成交量的30%
                if window_volume > total_buy_volume * 0.3:
                    burst_detected = True

        burst_intensity = max_burst_volume / total_buy_volume if total_buy_volume > 0 else 0

        # ========== 新增: 相似名字热度分析 (需要全局数据) ==========
        # 提取名字前缀 (前3-4个字符)
        token_name = lifecycle.get('name', '')
        token_symbol = lifecycle.get('symbol', '')

        # 简化: 使用名字长度和符号长度的组合作为"相似度"的简单代理
        # 真正的相似度分析需要访问其他代币数据,这里先用简化版本
        name_prefix_length = min(4, len(token_name))
        symbol_prefix_length = min(3, len(token_symbol))

        # TODO: 如果要实现真正的相似名字检测,需要:
        # 1. 在collector中维护一个全局的名字索引
        # 2. 计算当前代币名字与最近代币的相似度
        # 3. 统计相似名字代币的数量和表现

        # ========== 新增: 交易时间分布 ==========
        # 计算交易的时间间隔方差 (判断是机器人还是自然交易)
        if len(past_buys) >= 3:
            buy_intervals = []
            for i in range(1, len(past_buys)):
                interval = past_buys[i]['timestamp'] - past_buys[i-1]['timestamp']
                buy_intervals.append(interval)

            avg_interval = sum(buy_intervals) / len(buy_intervals)
            interval_variance = sum((x - avg_interval) ** 2 for x in buy_intervals) / len(buy_intervals)
            interval_std = interval_variance ** 0.5

            # 归一化标准差 (越小越规律,可能是机器人)
            interval_regularity = interval_std / avg_interval if avg_interval > 0 else 0
        else:
            interval_regularity = 0

        # ========== 新增: 价格稳定性 ==========
        # 价格波动系数 (标准差/均值)
        if all_prices:
            avg_price = sum(all_prices) / len(all_prices)
            price_variance = sum((p - avg_price) ** 2 for p in all_prices) / len(all_prices)
            price_volatility = (price_variance ** 0.5) / avg_price if avg_price > 0 else 0
        else:
            price_volatility = 0

        # ========== 新增: 买单规模分布 ==========
        # 小额买单比例 (< 平均买单的50%)
        if avg_buy_size > 0:
            small_buy_threshold = avg_buy_size * 0.5
            small_buys = [b for b in past_buys if b['bnb_amount'] < small_buy_threshold]
            small_buy_ratio = len(small_buys) / len(past_buys)

            # 大额买单比例 (> 平均买单的200%)
            large_buy_threshold = avg_buy_size * 2
            large_buys = [b for b in past_buys if b['bnb_amount'] > large_buy_threshold]
            large_buy_ratio = len(large_buys) / len(past_buys)
        else:
            small_buy_ratio = 0
            large_buy_ratio = 0

        return {
            # 基本信息
            'total_supply': total_supply,
            'launch_fee': launch_fee,
            'liquidity_ratio': liquidity_ratio,
            'name_length': len(lifecycle['name']),
            'symbol_length': len(lifecycle['symbol']),

            # 时间
            'time_since_launch': time_since_launch,

            # 交易数据
            'total_buys': total_buys,
            'total_sells': total_sells,
            'unique_buyers': unique_buyers,
            'unique_sellers': unique_sellers,
            'total_buy_volume': total_buy_volume,
            'total_sell_volume': total_sell_volume,

            # 时间窗口成交量
            'volume_10s': volume_10s,
            'volume_30s': volume_30s,
            'volume_1min': volume_1min,
            'volume_2min': volume_2min,
            'volume_5min': volume_5min,

            # 价格
            'current_price': current_price,
            'first_price': first_price,
            'price_change_pct': price_change_pct,
            'max_price': max_price,
            'min_price': min_price,
            'price_momentum': price_momentum,

            # 指标
            'buy_pressure': buy_pressure,
            'avg_buy_size': avg_buy_size,
            'avg_sell_size': avg_sell_size,
            'trade_frequency': trade_frequency,
            'buyer_concentration': buyer_concentration,
            'seller_concentration': seller_concentration,
            'volume_acceleration': volume_acceleration,

            # 持币地址分析
            'holder_count': holder_count,
            'holder_concentration_top5': holder_concentration_top5,
            'max_holder_ratio': max_holder_ratio,
            'avg_holding': avg_holding,

            # 创建者分析
            'creator_is_buyer': 1 if creator_is_buyer else 0,
            'creator_is_seller': 1 if creator_is_seller else 0,
            'creator_buy_volume': creator_buy_volume,
            'creator_sell_volume': creator_sell_volume,
            'creator_holding_ratio': creator_holding_ratio,

            # 大户分析
            'whale_count': whale_count,
            'whale_volume_ratio': whale_volume_ratio,

            # 交易行为
            'repeat_buyer_ratio': repeat_buyer_ratio,
            'address_overlap_ratio': address_overlap_ratio,

            # 早期活动分析
            'early_buy_count': early_buy_count,
            'early_buy_volume': early_buy_volume,
            'early_unique_buyers': early_unique_buyers,
            'early_activity_ratio': early_activity_ratio,
            'early_volume_ratio': early_volume_ratio,

            # 突发买入检测
            'burst_detected': 1 if burst_detected else 0,
            'burst_intensity': burst_intensity,
            'max_burst_volume': max_burst_volume,

            # 交易规律性
            'interval_regularity': interval_regularity,

            # 价格稳定性
            'price_volatility': price_volatility,

            # 买单规模分布
            'small_buy_ratio': small_buy_ratio,
            'large_buy_ratio': large_buy_ratio,
        }

    def _calculate_label_with_window(self, lifecycle: Dict, sample_time: int, future_window: int) -> Optional[Dict]:
        """计算标签 (带窗口信息)"""

        # 当前价格
        past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
        if not past_buys:
            return None

        current_price = past_buys[-1]['price']

        # 未来价格
        future_end_time = sample_time + future_window
        future_prices = [
            p['price'] for p in (lifecycle['buys'] + lifecycle['sells'])
            if sample_time < p['timestamp'] <= future_end_time
        ]

        if not future_prices:
            return None

        max_future_price = max(future_prices)
        min_future_price = min(future_prices)
        final_price = future_prices[-1]

        # 计算收益率
        if current_price > 0:
            max_return = ((max_future_price - current_price) / current_price) * 100
            min_return = ((min_future_price - current_price) / current_price) * 100
            final_return = ((final_price - current_price) / current_price) * 100
        else:
            max_return = 0
            min_return = 0
            final_return = 0

        # --- 新增: 严格的 "Moon" 标签逻辑 (先止损后止盈检测) ---
        # 按照时间顺序遍历交易，模拟真实持仓体验
        is_moon_200 = 0
        is_moon_300 = 0

        # 重新获取带时间戳的交易列表并排序
        future_trades = [
            p for p in (lifecycle['buys'] + lifecycle['sells'])
            if sample_time < p['timestamp'] <= future_end_time
        ]
        future_trades.sort(key=lambda x: x['timestamp'])

        hit_stop_loss = False

        for trade in future_trades:
            p = trade['price']
            if current_price <= 0:
                continue

            ret = ((p - current_price) / current_price) * 100

            # 优先检查止损 (-50%)
            if ret <= -50:
                hit_stop_loss = True
                break # 爆仓离场

            # 检查止盈目标
            if ret >= 200:
                is_moon_200 = 1
            if ret >= 300:
                is_moon_300 = 1

        # 根据未来窗口调整盈利阈值
        # 短期窗口(1分钟): 10%算盈利
        # 长期窗口(10分钟): 30%算盈利
        if future_window <= 60:
            profit_threshold = 10
        elif future_window <= 300:
            profit_threshold = 20
        else:
            profit_threshold = 30

        # 分类标签
        return {
            'max_return_pct': max_return,
            'min_return_pct': min_return,
            'final_return_pct': final_return,

            # 二分类 (旧版)
            'is_profitable': 1 if max_return > profit_threshold else 0,

            # 二分类 (新版 - 策略专用)
            'is_moon_200': is_moon_200,
            'is_moon_300': is_moon_300,

            # 多分类 (基于最大收益)
            'return_class': self._classify_return(max_return),

            # 风险标签
            'is_risky': 1 if min_return < -20 else 0,  # 回撤超过20%

            # 元信息
            'profit_threshold': profit_threshold,
        }

    def _classify_return(self, return_pct: float) -> int:
        """
        将收益率分类

        返回:
            0: 亏损 (< 0%)
            1: 小赚 (0-50%)
            2: 中赚 (50-100%)
            3: 大赚 (100-300%)
            4: 暴赚 (>300%)
        """
        if return_pct < 0:
            return 0
        elif return_pct < 50:
            return 1
        elif return_pct < 100:
            return 2
        elif return_pct < 300:
            return 3
        else:
            return 4

    def split_dataset(self, train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1):
        """
        划分数据集

        Returns:
            train_samples, val_samples, test_samples
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例之和必须为1"

        # 打乱样本
        random.shuffle(self.samples)

        total = len(self.samples)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train = self.samples[:train_end]
        val = self.samples[train_end:val_end]
        test = self.samples[val_end:]

        logger.info(f"Dataset split: train={len(train)}, val={len(val)}, test={len(test)}")

        return train, val, test

    def save_dataset(self, output_dir: str = "data/datasets"):
        """保存数据集"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 划分数据集
        train, val, test = self.split_dataset()

        # 保存
        def save_split(samples, name):
            filepath = output_path / f"{name}_{timestamp}.jsonl"
            with filepath.open('w', encoding='utf-8') as f:
                for sample in samples:
                    json.dump(sample, f, ensure_ascii=False)
                    f.write('\n')
            logger.info(f"Saved {len(samples)} samples to {filepath}")

        save_split(train, 'train')
        save_split(val, 'val')
        save_split(test, 'test')

        # 保存元数据
        meta_file = output_path / f"metadata_{timestamp}.json"
        metadata = {
            'timestamp': timestamp,
            'total_samples': len(self.samples),
            'train_samples': len(train),
            'val_samples': len(val),
            'test_samples': len(test),
            'feature_names': list(self.samples[0]['features'].keys()) if self.samples else [],
            'label_names': list(self.samples[0]['label'].keys()) if self.samples else [],
        }

        with meta_file.open('w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset saved to {output_dir}")

    def get_stats(self) -> Dict:
        """获取数据集统计"""
        if not self.samples:
            return {'total_samples': 0}

        # 统计标签分布
        return_classes = [s['label']['return_class'] for s in self.samples]
        class_counts = {i: return_classes.count(i) for i in range(5)}

        profitable_count = sum(1 for s in self.samples if s['label']['is_profitable'])

        return {
            'total_samples': len(self.samples),
            'profitable_samples': profitable_count,
            'profitable_ratio': profitable_count / len(self.samples),
            'return_class_distribution': class_counts,
        }
