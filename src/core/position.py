"""
Position Tracker
持仓追踪器 - 追踪每笔交易,监控价格变化,触发止盈止损
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Optional
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class PositionTracker:
    """持仓追踪器"""

    def __init__(self, trader, risk_manager):
        """
        Args:
            trader: TradeExecutor实例
            risk_manager: RiskManager实例
        """
        self.trader = trader
        self.risk_manager = risk_manager

        # 持仓字典: {token_address: position_data}
        self.positions: Dict[str, Dict] = {}

        # 策略参数
        self.take_profit_pct = TradingConfig.TAKE_PROFIT_PERCENT
        self.take_profit_sell_pct = TradingConfig.TAKE_PROFIT_SELL_PERCENT
        self.stop_loss_pct = TradingConfig.STOP_LOSS_PERCENT
        self.max_hold_time = TradingConfig.MAX_HOLD_TIME_SECONDS

        self.keep_moonshot = TradingConfig.KEEP_POSITION_FOR_MOONSHOT
        self.moonshot_profit_pct = TradingConfig.MOONSHOT_PROFIT_PERCENT
        self.moonshot_stop_loss_pct = TradingConfig.MOONSHOT_STOP_LOSS_PERCENT
        self.moonshot_max_hold_hours = TradingConfig.MOONSHOT_MAX_HOLD_HOURS

        # 交易记录目录
        self.trades_dir = Path('data/trades')
        self.trades_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"PositionTracker initialized | "
                   f"TP:{self.take_profit_pct}% SL:{self.stop_loss_pct}% | "
                   f"Moonshot: {self.keep_moonshot}")

    async def add_position(self, token_address: str, tx_hash: str, entry_price: float,
                          token_amount: float, bnb_invested: float):
        """
        添加新持仓

        Args:
            token_address: 代币地址
            tx_hash: 买入交易哈希
            entry_price: 买入价格 (BNB per token)
            token_amount: 代币数量
            bnb_invested: 投入BNB数量
        """
        position = {
            'token_address': token_address,
            'entry_price': entry_price,
            'total_amount': token_amount,
            'remaining_amount': token_amount,
            'bnb_invested': bnb_invested,
            'buy_time': time.time(),
            'buy_tx_hash': tx_hash,
            'status': 'holding',  # holding/partial_sold/closed
            'first_sell_price': None,
            'peak_price': entry_price,
        }

        self.positions[token_address] = position

        # 保存到文件
        self._save_position(position)

        logger.info(f"Position added: {token_address[:10]}... | "
                   f"Amount: {token_amount:,.2f} | Price: {entry_price:.10f} BNB | "
                   f"Invested: {bnb_invested:.4f} BNB")

    async def on_price_update(self, token_address: str, current_price: float):
        """
        价格更新时检查止盈止损

        Args:
            token_address: 代币地址
            current_price: 当前价格 (BNB per token)
        """
        if token_address not in self.positions:
            return

        position = self.positions[token_address]

        # 根据状态选择检查函数
        if position['status'] == 'holding':
            await self._check_initial_position(token_address, current_price)
        elif position['status'] == 'partial_sold' and self.keep_moonshot:
            await self._check_moonshot_position(token_address, current_price)

    async def _check_initial_position(self, token_address: str, current_price: float):
        """检查初始持仓 (未卖出阶段)"""
        position = self.positions[token_address]
        entry_price = position['entry_price']
        pnl_pct = (current_price - entry_price) / entry_price * 100

        # 止盈: 达到目标收益
        if pnl_pct >= self.take_profit_pct:
            logger.info(f"Take profit triggered: {token_address[:10]}... | "
                       f"PnL: +{pnl_pct:.1f}% (target: +{self.take_profit_pct}%)")
            await self._sell_partial(token_address, self.take_profit_sell_pct / 100, current_price)
            return

        # 止损: 达到最大亏损
        if pnl_pct <= self.stop_loss_pct:
            logger.info(f"Stop loss triggered: {token_address[:10]}... | "
                       f"PnL: {pnl_pct:.1f}% (limit: {self.stop_loss_pct}%)")
            await self._sell_all(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        if hold_time > self.max_hold_time:
            logger.info(f"Time stop triggered: {token_address[:10]}... | "
                       f"Held: {hold_time:.0f}s (max: {self.max_hold_time}s) | PnL: {pnl_pct:+.1f}%")
            await self._sell_all(token_address, current_price)
            return

    async def _check_moonshot_position(self, token_address: str, current_price: float):
        """检查底仓 (已部分卖出阶段)"""
        position = self.positions[token_address]

        # 更新峰值价格
        if current_price > position['peak_price']:
            position['peak_price'] = current_price

        # 相对买入价的收益
        entry_pnl_pct = (current_price - position['entry_price']) / position['entry_price'] * 100

        # 底仓止盈: 5倍收益
        if entry_pnl_pct >= self.moonshot_profit_pct:
            logger.info(f"Moonshot profit: {token_address[:10]}... | "
                       f"PnL: +{entry_pnl_pct:.1f}% (target: +{self.moonshot_profit_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 峰值回撤止损
        drawdown_pct = (current_price - position['peak_price']) / position['peak_price'] * 100
        if drawdown_pct <= self.moonshot_stop_loss_pct:
            logger.info(f"Moonshot drawdown stop: {token_address[:10]}... | "
                       f"Drawdown: {drawdown_pct:.1f}% (limit: {self.moonshot_stop_loss_pct}%)")
            await self._sell_remaining(token_address, current_price)
            return

        # 时间止损
        hold_time = time.time() - position['buy_time']
        max_hold_seconds = self.moonshot_max_hold_hours * 3600
        if hold_time > max_hold_seconds:
            logger.info(f"Moonshot time stop: {token_address[:10]}... | "
                       f"Held: {hold_time/3600:.1f}h (max: {self.moonshot_max_hold_hours}h)")
            await self._sell_remaining(token_address, current_price)
            return

    async def _sell_partial(self, token_address: str, sell_ratio: float, price: float):
        """部分卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'] * sell_ratio)

        # 执行卖出
        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            position['remaining_amount'] -= sell_amount
            position['status'] = 'partial_sold'
            position['first_sell_price'] = price
            position['peak_price'] = price

            self._save_position(position)

            logger.info(f"Partial sell executed: {sell_amount/1e18:,.2f} tokens | "
                       f"Remaining: {position['remaining_amount']/1e18:,.2f}")

    async def _sell_all(self, token_address: str, price: float):
        """全部卖出"""
        position = self.positions[token_address]
        sell_amount = int(position['remaining_amount'])

        tx_hash = await self.trader.sell_token(token_address, sell_amount)

        if tx_hash:
            position['status'] = 'closed'
            position['remaining_amount'] = 0

            self._save_position(position)
            self.risk_manager.record_sell(token_address, is_complete=True)

            # 移除持仓
            del self.positions[token_address]

            logger.info(f"Position closed: {token_address[:10]}...")

    async def _sell_remaining(self, token_address: str, price: float):
        """卖出剩余底仓"""
        await self._sell_all(token_address, price)

    def _save_position(self, position: Dict):
        """保存持仓到文件"""
        filename = self.trades_dir / f"{position['token_address']}.json"
        with open(filename, 'w') as f:
            json.dump({
                **position,
                'updated_at': time.time()
            }, f, indent=2)

    def get_stats(self) -> Dict:
        """获取持仓统计"""
        return {
            'active_positions': len(self.positions),
            'positions': {addr: {
                'status': pos['status'],
                'entry_price': pos['entry_price'],
                'remaining_amount': pos['remaining_amount'],
                'hold_time_seconds': time.time() - pos['buy_time']
            } for addr, pos in self.positions.items()}
        }
