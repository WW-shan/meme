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
    GAS_MULTIPLIER = float(os.getenv('GAS_MULTIPLIER', '1.2')) # 默认上浮 20%
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
    MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '100'))
    MAX_DAILY_INVESTMENT_BNB = float(os.getenv('MAX_DAILY_INVESTMENT_BNB', '0.5'))
    MAX_CONCURRENT_POSITIONS = int(os.getenv('MAX_CONCURRENT_POSITIONS', '3'))

    # ========== 过滤条件 ==========
    FILTER_KEYWORDS_BLACKLIST = os.getenv('FILTER_KEYWORDS_BLACKLIST', 'scam,rug,test,dev,burn,locked,free,airdrop').split(',')
    FILTER_MIN_INITIAL_LIQUIDITY = float(os.getenv('FILTER_MIN_INITIAL_LIQUIDITY', '0.01'))

    # ========== 热度追踪 ==========
    FILTER_ENABLE_TREND_TRACKING = os.getenv('FILTER_ENABLE_TREND_TRACKING', 'true').lower() == 'true'
    FILTER_TREND_WINDOW_MINUTES = int(os.getenv('FILTER_TREND_WINDOW_MINUTES', '5'))
    FILTER_TREND_THRESHOLD = int(os.getenv('FILTER_TREND_THRESHOLD', '3'))
    FILTER_TREND_PREFIX_LENGTH = int(os.getenv('FILTER_TREND_PREFIX_LENGTH', '4'))
    FILTER_CLUSTER_BUY_AMOUNT_BNB = float(os.getenv('FILTER_CLUSTER_BUY_AMOUNT_BNB', '0.015'))

    # ========== 地址过滤 ==========
    FILTER_ENABLE_ADDRESS_CHECK = os.getenv('FILTER_ENABLE_ADDRESS_CHECK', 'true').lower() == 'true'
    FILTER_MAX_TOKENS_PER_CREATOR_24H = int(os.getenv('FILTER_MAX_TOKENS_PER_CREATOR_24H', '5'))
    FILTER_MIN_CREATOR_TX_COUNT = int(os.getenv('FILTER_MIN_CREATOR_TX_COUNT', '10'))
    FILTER_MIN_CREATOR_BALANCE_BNB = float(os.getenv('FILTER_MIN_CREATOR_BALANCE_BNB', '0.01'))

    # ========== 代币基本信息过滤 ==========
    FILTER_MIN_NAME_LENGTH = int(os.getenv('FILTER_MIN_NAME_LENGTH', '2'))
    FILTER_MAX_NAME_LENGTH = int(os.getenv('FILTER_MAX_NAME_LENGTH', '30'))
    FILTER_MIN_SYMBOL_LENGTH = int(os.getenv('FILTER_MIN_SYMBOL_LENGTH', '2'))
    FILTER_MAX_SYMBOL_LENGTH = int(os.getenv('FILTER_MAX_SYMBOL_LENGTH', '10'))

    # ========== 代币供应量检查 ==========
    FILTER_MIN_TOTAL_SUPPLY = float(os.getenv('FILTER_MIN_TOTAL_SUPPLY', '1000000'))  # 100万
    FILTER_MAX_TOTAL_SUPPLY = float(os.getenv('FILTER_MAX_TOTAL_SUPPLY', '1000000000000'))  # 1万亿

    # ========== 流动性比例检查 ==========
    FILTER_MIN_LIQUIDITY_RATIO = float(os.getenv('FILTER_MIN_LIQUIDITY_RATIO', '0.00001'))  # launch_fee / total_supply

    # ========== 创建者发币间隔检查 ==========
    FILTER_MIN_CREATOR_TOKEN_INTERVAL_MINUTES = int(os.getenv('FILTER_MIN_CREATOR_TOKEN_INTERVAL_MINUTES', '30'))

    @classmethod
    def validate(cls) -> bool:
        """验证配置"""
        if cls.ENABLE_TRADING and not cls.PRIVATE_KEY:
            raise ValueError("ENABLE_TRADING=true requires PRIVATE_KEY to be set")

        if cls.FILTER_CLUSTER_BUY_AMOUNT_BNB <= 0:
            raise ValueError("FILTER_CLUSTER_BUY_AMOUNT_BNB must be positive")

        return True
