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
                          sample_time: int) -> Dict:
        """提取特征"""

        # 时间特征
        time_since_launch = sample_time - lifecycle['create_timestamp']

        # 基本信息特征
        total_supply = lifecycle['total_supply'] / 1e18
        launch_fee = lifecycle['launch_fee'] / 1e18
        liquidity_ratio = (launch_fee * 1e18) / lifecycle['total_supply'] if lifecycle['total_supply'] > 0 else 0

        # 交易特征
        total_buys = len(past_buys)
        total_sells = len(past_sells)
        unique_buyers = len(set(b['account'] for b in past_buys))
        unique_sellers = len(set(s['account'] for s in past_sells))

        total_buy_volume = sum(b['bnb_amount'] for b in past_buys)
        total_sell_volume = sum(s['bnb_amount'] for s in past_sells)

        # 价格特征
        current_price = past_buys[-1]['price'] if past_buys else 0
        first_price = past_buys[0]['price'] if past_buys else 0
        price_change_pct = ((current_price - first_price) / first_price * 100) if first_price > 0 else 0

        all_prices = [b['price'] for b in past_buys] + [s['price'] for s in past_sells]
        max_price = max(all_prices) if all_prices else 0
        min_price = min(all_prices) if all_prices else 0

        # 时间窗口特征 (1min, 5min)
        def calc_window_volume(window_seconds):
            cutoff = sample_time - window_seconds
            return sum(b['bnb_amount'] for b in past_buys if b['timestamp'] >= cutoff)

        volume_1min = calc_window_volume(60)
        volume_5min = calc_window_volume(300)

        # 买卖压力
        buy_pressure = total_buy_volume / (total_buy_volume + total_sell_volume) if (total_buy_volume + total_sell_volume) > 0 else 0.5

        # 平均交易规模
        avg_buy_size = total_buy_volume / total_buys if total_buys > 0 else 0
        avg_sell_size = total_sell_volume / total_sells if total_sells > 0 else 0

        # 交易频率 (每分钟交易次数)
        trade_frequency = (total_buys + total_sells) / (time_since_launch / 60) if time_since_launch > 0 else 0

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
            'volume_1min': volume_1min,
            'volume_5min': volume_5min,

            # 价格
            'current_price': current_price,
            'first_price': first_price,
            'price_change_pct': price_change_pct,
            'max_price': max_price,
            'min_price': min_price,

            # 指标
            'buy_pressure': buy_pressure,
            'avg_buy_size': avg_buy_size,
            'avg_sell_size': avg_sell_size,
            'trade_frequency': trade_frequency,
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
