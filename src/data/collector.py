"""
数据收集器 - 整合事件数据并生成训练样本
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataCollector:
    """收集和整合交易数据用于训练"""

    def __init__(self, output_dir: str = "data/training"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存: token_address -> 完整生命周期数据
        self.token_lifecycle: Dict[str, Dict] = {}

        # 统计
        self.tokens_tracked = 0
        self.samples_generated = 0

    def on_token_create(self, event_data: Dict):
        """处理TokenCreate事件"""
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            if not token_address:
                return

            # 初始化代币生命周期数据
            self.token_lifecycle[token_address] = {
                # 基本信息
                'token_address': token_address,
                'creator': args.get('creator', ''),
                'name': args.get('name', ''),
                'symbol': args.get('symbol', ''),
                'total_supply': float(args.get('totalSupply', 0)),
                'launch_fee': float(args.get('launchFee', 0)),
                'launch_time': args.get('launchTime', 0),
                'create_timestamp': event_data.get('timestamp', 0),
                'create_block': event_data.get('blockNumber', 0),

                # 交易数据
                'buys': [],  # [{timestamp, account, token_amount, bnb_amount, price}]
                'sells': [],

                # 价格历史
                'price_history': [],  # [{timestamp, price, type: buy/sell}]

                # 聚合统计
                'total_buy_volume_bnb': 0.0,
                'total_sell_volume_bnb': 0.0,
                'total_buy_count': 0,
                'total_sell_count': 0,
                'unique_buyers': set(),
                'unique_sellers': set(),

                # 时间窗口统计 (1min, 5min, 15min, 30min, 1h)
                'volume_1min': 0.0,
                'volume_5min': 0.0,
                'volume_15min': 0.0,
                'volume_30min': 0.0,
                'volume_1h': 0.0,

                # 价格指标
                'price_max': 0.0,
                'price_min': float('inf'),
                'price_current': 0.0,
                'price_first': 0.0,

                # 毕业状态
                'graduated': False,
                'graduate_time': None,

                # 更新时间
                'last_update': event_data.get('timestamp', 0),
            }

            self.tokens_tracked += 1
            logger.debug(f"Tracking new token: {args.get('symbol', 'Unknown')} ({token_address[:10]}...)")

        except Exception as e:
            logger.error(f"Error in on_token_create: {e}")

    def on_token_purchase(self, event_data: Dict):
        """处理TokenPurchase事件"""
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            if token_address not in self.token_lifecycle:
                return

            lifecycle = self.token_lifecycle[token_address]
            timestamp = event_data.get('timestamp', 0)

            # 提取交易数据
            account = args.get('account', '')
            token_amount = float(args.get('amount', 0))
            bnb_amount = float(args.get('cost', 0))

            if token_amount > 0:
                price = (bnb_amount / 1e18) / (token_amount / 1e18)

                # 记录买入
                lifecycle['buys'].append({
                    'timestamp': timestamp,
                    'account': account,
                    'token_amount': token_amount / 1e18,
                    'bnb_amount': bnb_amount / 1e18,
                    'price': price
                })

                # 更新价格历史
                lifecycle['price_history'].append({
                    'timestamp': timestamp,
                    'price': price,
                    'type': 'buy'
                })

                # 更新统计
                lifecycle['total_buy_volume_bnb'] += bnb_amount / 1e18
                lifecycle['total_buy_count'] += 1
                lifecycle['unique_buyers'].add(account)

                # 更新价格指标
                lifecycle['price_current'] = price
                lifecycle['price_max'] = max(lifecycle['price_max'], price)
                lifecycle['price_min'] = min(lifecycle['price_min'], price)
                if lifecycle['price_first'] == 0:
                    lifecycle['price_first'] = price

                lifecycle['last_update'] = timestamp

                # 更新时间窗口统计
                self._update_time_window_stats(lifecycle, timestamp, bnb_amount / 1e18)

        except Exception as e:
            logger.error(f"Error in on_token_purchase: {e}")

    def on_token_sale(self, event_data: Dict):
        """处理TokenSale事件"""
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            if token_address not in self.token_lifecycle:
                return

            lifecycle = self.token_lifecycle[token_address]
            timestamp = event_data.get('timestamp', 0)

            # 提取交易数据
            account = args.get('account', '')
            token_amount = float(args.get('amount', 0))
            bnb_amount = float(args.get('cost', 0))

            if token_amount > 0:
                price = (bnb_amount / 1e18) / (token_amount / 1e18)

                # 记录卖出
                lifecycle['sells'].append({
                    'timestamp': timestamp,
                    'account': account,
                    'token_amount': token_amount / 1e18,
                    'bnb_amount': bnb_amount / 1e18,
                    'price': price
                })

                # 更新价格历史
                lifecycle['price_history'].append({
                    'timestamp': timestamp,
                    'price': price,
                    'type': 'sell'
                })

                # 更新统计
                lifecycle['total_sell_volume_bnb'] += bnb_amount / 1e18
                lifecycle['total_sell_count'] += 1
                lifecycle['unique_sellers'].add(account)

                # 更新价格指标
                lifecycle['price_current'] = price
                lifecycle['price_max'] = max(lifecycle['price_max'], price)
                lifecycle['price_min'] = min(lifecycle['price_min'], price)

                lifecycle['last_update'] = timestamp

                # 更新时间窗口统计
                self._update_time_window_stats(lifecycle, timestamp, bnb_amount / 1e18)

        except Exception as e:
            logger.error(f"Error in on_token_sale: {e}")

    def on_trade_stop(self, event_data: Dict):
        """处理TradeStop事件 (代币毕业)"""
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            if token_address not in self.token_lifecycle:
                return

            lifecycle = self.token_lifecycle[token_address]
            lifecycle['graduated'] = True
            lifecycle['graduate_time'] = event_data.get('timestamp', 0)

            logger.info(f"Token graduated: {lifecycle['symbol']} ({token_address[:10]}...)")

        except Exception as e:
            logger.error(f"Error in on_trade_stop: {e}")

    def _update_time_window_stats(self, lifecycle: Dict, current_time: int, volume: float):
        """更新时间窗口统计"""
        # 清理过期的交易记录并计算窗口成交量
        windows = {
            'volume_1min': 60,
            'volume_5min': 300,
            'volume_15min': 900,
            'volume_30min': 1800,
            'volume_1h': 3600
        }

        for window_key, seconds in windows.items():
            cutoff_time = current_time - seconds

            # 计算窗口内的买入成交量
            window_volume = sum(
                buy['bnb_amount'] for buy in lifecycle['buys']
                if buy['timestamp'] >= cutoff_time
            )

            lifecycle[window_key] = window_volume

    def generate_training_sample(self, token_address: str,
                                  sample_time: int,
                                  future_window_seconds: int = 300) -> Optional[Dict]:
        """
        生成训练样本

        Args:
            token_address: 代币地址
            sample_time: 采样时间点 (用于计算特征)
            future_window_seconds: 未来窗口 (用于计算标签) 默认5分钟

        Returns:
            训练样本 {features: {...}, label: {...}}
        """
        if token_address not in self.token_lifecycle:
            return None

        lifecycle = self.token_lifecycle[token_address]

        # 只使用 sample_time 之前的数据计算特征
        past_buys = [b for b in lifecycle['buys'] if b['timestamp'] <= sample_time]
        past_sells = [s for s in lifecycle['sells'] if s['timestamp'] <= sample_time]

        if not past_buys:
            return None  # 没有历史数据

        # 计算未来收益 (标签)
        future_end_time = sample_time + future_window_seconds
        future_prices = [p['price'] for p in lifecycle['price_history']
                        if sample_time < p['timestamp'] <= future_end_time]

        current_price = past_buys[-1]['price']  # 当前价格

        if future_prices:
            max_future_price = max(future_prices)
            min_future_price = min(future_prices)
            max_return = ((max_future_price - current_price) / current_price) * 100
            min_return = ((min_future_price - current_price) / current_price) * 100
        else:
            # 未来没有价格数据,可能代币没交易了
            max_return = 0
            min_return = 0

        # 计算特征
        features = self._extract_features(lifecycle, past_buys, past_sells, sample_time)

        # 标签
        label = {
            'max_return_pct': max_return,
            'min_return_pct': min_return,
            'profitable': max_return > 10,  # 10%以上算盈利
            'high_return': max_return > 50,  # 50%以上算高收益
            'stop_loss': min_return < -30,  # -30%以下算需要止损
        }

        return {
            'features': features,
            'label': label,
            'meta': {
                'token_address': token_address,
                'symbol': lifecycle['symbol'],
                'sample_time': sample_time,
                'current_price': current_price,
            }
        }

    def _extract_features(self, lifecycle: Dict,
                          past_buys: List[Dict],
                          past_sells: List[Dict],
                          sample_time: int,
                          future_window: int = 300) -> Dict:
        """提取特征 (增强版 - 与 DatasetBuilder 保持一致)"""

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
            'future_window': future_window,
        }

    def save_lifecycle_data(self):
        """保存所有代币生命周期数据"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.output_dir / f"lifecycle_{timestamp}.jsonl"

            saved_count = 0
            with output_file.open('w', encoding='utf-8') as f:
                for token_address, lifecycle in self.token_lifecycle.items():
                    # 转换 set 为 list 以便JSON序列化
                    lifecycle_copy = lifecycle.copy()
                    lifecycle_copy['unique_buyers'] = list(lifecycle['unique_buyers'])
                    lifecycle_copy['unique_sellers'] = list(lifecycle['unique_sellers'])

                    json.dump(lifecycle_copy, f, ensure_ascii=False)
                    f.write('\n')
                    saved_count += 1

            logger.info(f"Saved {saved_count} token lifecycles to {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error saving lifecycle data: {e}")
            return None

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'tokens_tracked': self.tokens_tracked,
            'tokens_in_memory': len(self.token_lifecycle),
            'samples_generated': self.samples_generated,
        }
