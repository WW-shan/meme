"""
Trading Configuration
加载和管理交易相关配置参数
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class TradingConfig:
    """交易配置"""

    # ========== 钱包配置 ==========
    PRIVATE_KEY = os.getenv('PRIVATE_KEY', '')

    # ========== 交易开关 ==========
    ENABLE_TRADING = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
    ENABLE_BACKTEST = os.getenv('ENABLE_BACKTEST', 'false').lower() == 'true'

    # ========== 买入策略 ==========
    BUY_AMOUNT_BNB = float(os.getenv('BUY_AMOUNT_BNB', '0.05'))
    BUY_GAS_PRICE_GWEI = int(os.getenv('BUY_GAS_PRICE_GWEI', '20'))
    BUY_SLIPPAGE_PERCENT = int(os.getenv('BUY_SLIPPAGE_PERCENT', '15'))

    # ========== 卖出策略 (第一阶段) ==========
    TAKE_PROFIT_PERCENT = int(os.getenv('TAKE_PROFIT_PERCENT', '200'))
    TAKE_PROFIT_SELL_PERCENT = int(os.getenv('TAKE_PROFIT_SELL_PERCENT', '90'))
    STOP_LOSS_PERCENT = int(os.getenv('STOP_LOSS_PERCENT', '-50'))
    MAX_HOLD_TIME_SECONDS = int(os.getenv('MAX_HOLD_TIME_SECONDS', '300'))

    # ========== 卖出策略 (第二阶段 - 底仓) ==========
    KEEP_POSITION_FOR_MOONSHOT = os.getenv('KEEP_POSITION_FOR_MOONSHOT', 'true').lower() == 'true'
    MOONSHOT_PROFIT_PERCENT = int(os.getenv('MOONSHOT_PROFIT_PERCENT', '500'))
    MOONSHOT_STOP_LOSS_PERCENT = int(os.getenv('MOONSHOT_STOP_LOSS_PERCENT', '-30'))
    MOONSHOT_MAX_HOLD_HOURS = int(os.getenv('MOONSHOT_MAX_HOLD_HOURS', '24'))

    # ========== 风控参数 ==========
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '10'))
    MAX_DAILY_INVESTMENT_BNB = float(os.getenv('MAX_DAILY_INVESTMENT_BNB', '0.5'))
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))

    # ========== 过滤条件 ==========
    FILTER_KEYWORDS_BLACKLIST = os.getenv('FILTER_KEYWORDS_BLACKLIST', 'scam,rug,test').split(',')
    FILTER_MIN_INITIAL_LIQUIDITY = float(os.getenv('FILTER_MIN_INITIAL_LIQUIDITY', '0.01'))

    @classmethod
    def validate(cls) -> bool:
        """验证配置"""
        if cls.ENABLE_TRADING and not cls.PRIVATE_KEY:
            raise ValueError("ENABLE_TRADING=true requires PRIVATE_KEY to be set")

        if cls.BUY_AMOUNT_BNB <= 0:
            raise ValueError("BUY_AMOUNT_BNB must be positive")

        return True
