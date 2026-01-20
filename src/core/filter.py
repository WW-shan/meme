"""
Trade Filter
决定是否对新币执行买入
"""

import logging
from typing import Dict
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class TradeFilter:
    """交易过滤器"""

    def __init__(self):
        self.blacklist_keywords = [k.strip().lower() for k in TradingConfig.FILTER_KEYWORDS_BLACKLIST]
        self.min_liquidity = TradingConfig.FILTER_MIN_INITIAL_LIQUIDITY

        logger.info(f"TradeFilter initialized: blacklist={self.blacklist_keywords}, min_liquidity={self.min_liquidity} BNB")

    def should_buy(self, token_info: Dict) -> tuple[bool, str]:
        """
        判断是否应该买入此代币

        Args:
            token_info: 代币信息 (TokenCreate事件数据)

        Returns:
            (should_buy, reason)
        """
        # 检查黑名单关键词
        name = token_info.get('token_name', '').lower()
        symbol = token_info.get('token_symbol', '').lower()

        for keyword in self.blacklist_keywords:
            if keyword in name or keyword in symbol:
                return False, f"Blacklisted keyword: {keyword}"

        # 检查初始流动性
        launch_fee = token_info.get('launch_fee', 0)
        if launch_fee < self.min_liquidity:
            return False, f"Low liquidity: {launch_fee:.4f} BNB < {self.min_liquidity} BNB"

        return True, "Passed all filters"

    def get_stats(self) -> Dict:
        """获取过滤器统计"""
        return {
            'blacklist_keywords': self.blacklist_keywords,
            'min_liquidity': self.min_liquidity
        }
