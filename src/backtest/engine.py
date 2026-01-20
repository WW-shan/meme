"""
Backtest Engine
回测引擎 - 使用历史数据验证交易策略
"""

import logging
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from src.core.filter import TradeFilter
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class BacktestEngine:
    """回测引擎"""

    def __init__(self):
        self.filter = TradeFilter()

        # 策略参数
        self.buy_amount_bnb = TradingConfig.BUY_AMOUNT_BNB
        self.take_profit_pct = TradingConfig.TAKE_PROFIT_PERCENT
        self.take_profit_sell_pct = TradingConfig.TAKE_PROFIT_SELL_PERCENT
        self.stop_loss_pct = TradingConfig.STOP_LOSS_PERCENT
        self.max_hold_time = TradingConfig.MAX_HOLD_TIME_SECONDS

        self.keep_moonshot = TradingConfig.KEEP_POSITION_FOR_MOONSHOT
        self.moonshot_profit_pct = TradingConfig.MOONSHOT_PROFIT_PERCENT
        self.moonshot_stop_loss_pct = TradingConfig.MOONSHOT_STOP_LOSS_PERCENT
        self.moonshot_max_hold_hours = TradingConfig.MOONSHOT_MAX_HOLD_HOURS

        # 风控参数
        self.max_daily_trades = TradingConfig.MAX_DAILY_TRADES
        self.max_daily_investment = TradingConfig.MAX_DAILY_INVESTMENT_BNB
        self.max_concurrent_positions = TradingConfig.MAX_CONCURRENT_POSITIONS

        # 回测状态
        self.positions: Dict[str, Dict] = {}
        self.closed_positions: List[Dict] = []
        self.daily_trades = 0
        self.daily_investment = 0.0

        # 价格缓存: {token_address: latest_price}
        self.latest_prices: Dict[str, float] = {}

        logger.info("BacktestEngine initialized")

    def load_events(self, data_file: str) -> List[Dict]:
        """
        加载历史事件数据

        Args:
            data_file: JSONL文件路径

        Returns:
            事件列表
        """
        events = []
        data_path = Path(data_file)

        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")

        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line: {e}")

        logger.info(f"Loaded {len(events)} events from {data_file}")
        return events

    async def run_backtest(self, data_file: str) -> Dict:
        """
        运行回测

        Args:
            data_file: 历史数据文件路径

        Returns:
            回测结果统计
        """
        events = self.load_events(data_file)

        logger.info(f"Starting backtest with {len(events)} events")

        for i, event in enumerate(events):
            event_type = event.get('event_type', '')

            if event_type == 'launch':
                await self._process_launch_event(event)
            elif event_type in ['buy', 'sell']:
                await self._process_trade_event(event)

            # 定期检查时间止损
            if i % 100 == 0:
                await self._check_time_stops(event.get('timestamp', 0))

        # 最后关闭所有剩余持仓
        await self._close_all_positions()

        # 生成统计报告
        stats = self._generate_stats()

        logger.info("Backtest completed")
        return stats

    async def _process_launch_event(self, event: Dict):
        """处理代币发行事件"""
        token_info = {
            'token_address': event.get('token_address', ''),
            'token_name': event.get('token_name', ''),
            'token_symbol': event.get('token_symbol', ''),
            'creator': event.get('creator', ''),
            'total_supply': event.get('total_supply', 0),
            'launch_fee': event.get('launch_fee', 0),
            'launch_time': event.get('timestamp', 0),
        }

        # 过滤检查
        should_buy, reason = self.filter.should_buy(token_info)
        if not should_buy:
            return

        # 风控检查
        if self.daily_trades >= self.max_daily_trades:
            return
        if self.daily_investment + self.buy_amount_bnb > self.max_daily_investment:
            return
        if len(self.positions) >= self.max_concurrent_positions:
            return

        # 模拟买入
        token_address = token_info['token_address']

        # 估算买入价格 (使用初始流动性估算)
        estimated_price = self.buy_amount_bnb / (token_info['total_supply'] * 0.8) if token_info['total_supply'] > 0 else 0

        position = {
            'token_address': token_address,
            'token_symbol': token_info['token_symbol'],
            'entry_price': estimated_price,
            'entry_time': token_info['launch_time'],
            'total_amount': token_info['total_supply'] * 0.8,
            'remaining_amount': token_info['total_supply'] * 0.8,
            'bnb_invested': self.buy_amount_bnb,
            'status': 'holding',
            'peak_price': estimated_price,
        }

        self.positions[token_address] = position
        self.daily_trades += 1
        self.daily_investment += self.buy_amount_bnb

        logger.debug(f"Simulated buy: {token_info['token_symbol']} @ {estimated_price:.10f} BNB")

    async def _process_trade_event(self, event: Dict):
        """处理交易事件 (buy/sell)"""
        token_address = event.get('token_address', '')
        token_amount = event.get('token_amount', 0)
        ether_amount = event.get('ether_amount', 0)
        timestamp = event.get('timestamp', 0)

        if token_amount <= 0:
            return

        # 计算价格
        price = ether_amount / token_amount
        self.latest_prices[token_address] = price

        # 检查是否有此代币的持仓
        if token_address not in self.positions:
            return

        position = self.positions[token_address]

        # 检查止盈止损
        if position['status'] == 'holding':
            await self._check_initial_position(token_address, price, timestamp)
        elif position['status'] == 'partial_sold':
            await self._check_moonshot_position(token_address, price, timestamp)

    async def _check_initial_position(self, token_address: str, current_price: float, timestamp: int):
        """检查初始持仓止盈止损"""
        position = self.positions[token_address]
        entry_price = position['entry_price']

        if entry_price <= 0:
            return

        pnl_pct = (current_price - entry_price) / entry_price * 100

        # 止盈
        if pnl_pct >= self.take_profit_pct:
            await self._sell_partial(token_address, self.take_profit_sell_pct / 100, current_price, timestamp, 'take_profit')
            return

        # 止损
        if pnl_pct <= self.stop_loss_pct:
            await self._sell_all(token_address, current_price, timestamp, 'stop_loss')
            return

    async def _check_moonshot_position(self, token_address: str, current_price: float, timestamp: int):
        """检查底仓止盈止损"""
        position = self.positions[token_address]

        # 更新峰值
        if current_price > position['peak_price']:
            position['peak_price'] = current_price

        entry_price = position['entry_price']
        if entry_price <= 0:
            return

        entry_pnl_pct = (current_price - entry_price) / entry_price * 100

        # 底仓止盈
        if entry_pnl_pct >= self.moonshot_profit_pct:
            await self._sell_all(token_address, current_price, timestamp, 'moonshot_profit')
            return

        # 峰值回撤止损
        drawdown_pct = (current_price - position['peak_price']) / position['peak_price'] * 100
        if drawdown_pct <= self.moonshot_stop_loss_pct:
            await self._sell_all(token_address, current_price, timestamp, 'moonshot_drawdown')
            return

    async def _check_time_stops(self, current_time: int):
        """检查时间止损"""
        for token_address in list(self.positions.keys()):
            position = self.positions[token_address]
            hold_time = current_time - position['entry_time']

            if position['status'] == 'holding' and hold_time > self.max_hold_time:
                price = self.latest_prices.get(token_address, position['entry_price'])
                await self._sell_all(token_address, price, current_time, 'time_stop')
            elif position['status'] == 'partial_sold' and hold_time > self.moonshot_max_hold_hours * 3600:
                price = self.latest_prices.get(token_address, position['entry_price'])
                await self._sell_all(token_address, price, current_time, 'moonshot_time_stop')

    async def _sell_partial(self, token_address: str, sell_ratio: float, price: float, timestamp: int, reason: str):
        """部分卖出"""
        position = self.positions[token_address]

        sell_amount = position['remaining_amount'] * sell_ratio
        bnb_received = sell_amount * price

        position['remaining_amount'] -= sell_amount
        position['status'] = 'partial_sold'
        position['peak_price'] = price
        position['first_sell'] = {
            'price': price,
            'bnb_received': bnb_received,
            'timestamp': timestamp,
            'reason': reason
        }

        logger.debug(f"Partial sell: {position['token_symbol']} | {sell_ratio*100:.0f}% @ {price:.10f} BNB | Reason: {reason}")

    async def _sell_all(self, token_address: str, price: float, timestamp: int, reason: str):
        """全部卖出"""
        position = self.positions[token_address]

        sell_amount = position['remaining_amount']
        bnb_received = sell_amount * price

        # 计算总收益
        total_bnb_received = bnb_received
        if 'first_sell' in position:
            total_bnb_received += position['first_sell']['bnb_received']

        pnl_bnb = total_bnb_received - position['bnb_invested']
        pnl_pct = (pnl_bnb / position['bnb_invested']) * 100 if position['bnb_invested'] > 0 else 0

        # 记录关闭的持仓
        closed_position = {
            **position,
            'exit_price': price,
            'exit_time': timestamp,
            'exit_reason': reason,
            'total_bnb_received': total_bnb_received,
            'pnl_bnb': pnl_bnb,
            'pnl_pct': pnl_pct,
            'hold_duration': timestamp - position['entry_time']
        }

        self.closed_positions.append(closed_position)
        del self.positions[token_address]

        logger.debug(f"Position closed: {position['token_symbol']} | PnL: {pnl_pct:+.1f}% ({pnl_bnb:+.4f} BNB) | Reason: {reason}")

    async def _close_all_positions(self):
        """关闭所有剩余持仓"""
        for token_address in list(self.positions.keys()):
            price = self.latest_prices.get(token_address, self.positions[token_address]['entry_price'])
            await self._sell_all(token_address, price, 0, 'backtest_end')

    def _generate_stats(self) -> Dict:
        """生成统计报告"""
        if not self.closed_positions:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl_bnb': 0,
                'total_pnl_pct': 0,
                'avg_pnl_bnb': 0,
                'avg_pnl_pct': 0,
                'max_win_bnb': 0,
                'max_loss_bnb': 0,
            }

        total_trades = len(self.closed_positions)
        winning_trades = [p for p in self.closed_positions if p['pnl_bnb'] > 0]
        losing_trades = [p for p in self.closed_positions if p['pnl_bnb'] <= 0]

        total_pnl_bnb = sum(p['pnl_bnb'] for p in self.closed_positions)
        total_invested = sum(p['bnb_invested'] for p in self.closed_positions)
        total_pnl_pct = (total_pnl_bnb / total_invested * 100) if total_invested > 0 else 0

        avg_pnl_bnb = total_pnl_bnb / total_trades
        avg_pnl_pct = sum(p['pnl_pct'] for p in self.closed_positions) / total_trades

        max_win_bnb = max((p['pnl_bnb'] for p in winning_trades), default=0)
        max_loss_bnb = min((p['pnl_bnb'] for p in losing_trades), default=0)

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            'total_invested_bnb': total_invested,
            'total_pnl_bnb': total_pnl_bnb,
            'total_pnl_pct': total_pnl_pct,
            'avg_pnl_bnb': avg_pnl_bnb,
            'avg_pnl_pct': avg_pnl_pct,
            'max_win_bnb': max_win_bnb,
            'max_loss_bnb': max_loss_bnb,
            'avg_win_bnb': sum(p['pnl_bnb'] for p in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss_bnb': sum(p['pnl_bnb'] for p in losing_trades) / len(losing_trades) if losing_trades else 0,
        }

    def get_closed_positions(self) -> List[Dict]:
        """获取所有已关闭持仓"""
        return self.closed_positions
