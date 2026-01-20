"""
Risk Manager
风险控制管理器
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class RiskManager:
    """风控管理器"""

    def __init__(self):
        self.max_daily_trades = TradingConfig.MAX_DAILY_TRADES
        self.max_daily_investment = TradingConfig.MAX_DAILY_INVESTMENT_BNB
        self.max_concurrent_positions = TradingConfig.MAX_CONCURRENT_POSITIONS

        # 每日统计 (每天重置)
        self.daily_trades = 0
        self.daily_investment = 0.0
        self.last_reset_date = datetime.now().date()

        # 当前持仓
        self.active_positions: List[str] = []

        logger.info(f"RiskManager initialized: max_trades={self.max_daily_trades}, "
                   f"max_investment={self.max_daily_investment} BNB, "
                   f"max_positions={self.max_concurrent_positions}")

    def _reset_daily_if_needed(self):
        """检查是否需要重置每日统计"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            logger.info(f"Resetting daily stats (new day: {today})")
            self.daily_trades = 0
            self.daily_investment = 0.0
            self.last_reset_date = today

    def can_buy(self, amount_bnb: float) -> tuple[bool, str]:
        """
        检查是否可以买入

        Args:
            amount_bnb: 计划买入金额 (BNB)

        Returns:
            (can_buy, reason)
        """
        self._reset_daily_if_needed()

        # 检查今日交易次数
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"

        # 检查今日投入
        if self.daily_investment + amount_bnb > self.max_daily_investment:
            return False, f"Daily investment limit: {self.daily_investment + amount_bnb:.4f}/{self.max_daily_investment} BNB"

        # 检查持仓数量
        if len(self.active_positions) >= self.max_concurrent_positions:
            return False, f"Max concurrent positions: {len(self.active_positions)}/{self.max_concurrent_positions}"

        return True, "OK"

    def record_buy(self, token_address: str, amount_bnb: float):
        """记录买入"""
        self._reset_daily_if_needed()

        self.daily_trades += 1
        self.daily_investment += amount_bnb
        self.active_positions.append(token_address)

        logger.info(f"Buy recorded: {token_address[:10]}... | "
                   f"Daily: {self.daily_trades}/{self.max_daily_trades} trades, "
                   f"{self.daily_investment:.4f}/{self.max_daily_investment} BNB | "
                   f"Positions: {len(self.active_positions)}/{self.max_concurrent_positions}")

    def record_sell(self, token_address: str, is_complete: bool = True):
        """记录卖出"""
        if is_complete and token_address in self.active_positions:
            self.active_positions.remove(token_address)
            logger.info(f"Position closed: {token_address[:10]}... | "
                       f"Remaining positions: {len(self.active_positions)}")

    def get_stats(self) -> Dict:
        """获取风控统计"""
        self._reset_daily_if_needed()

        return {
            'daily_trades': self.daily_trades,
            'daily_trades_limit': self.max_daily_trades,
            'daily_investment_bnb': self.daily_investment,
            'daily_investment_limit_bnb': self.max_daily_investment,
            'active_positions': len(self.active_positions),
            'max_positions': self.max_concurrent_positions,
            'last_reset_date': str(self.last_reset_date)
        }
