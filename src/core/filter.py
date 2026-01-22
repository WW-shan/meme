"""
Trade Filter
决定是否对新币执行买入
"""

import logging
from typing import Dict
from collections import defaultdict
from datetime import datetime, timedelta
from web3 import AsyncWeb3
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class TradeFilter:
    """交易过滤器"""

    def __init__(self, w3: AsyncWeb3 = None):
        self.blacklist_keywords = [k.strip().lower() for k in TradingConfig.FILTER_KEYWORDS_BLACKLIST]
        self.min_liquidity = TradingConfig.FILTER_MIN_INITIAL_LIQUIDITY
        self.w3 = w3

        # 创建者地址追踪: {creator_address: [(timestamp, token_address)]}
        self.creator_history: Dict[str, list] = defaultdict(list)
        self.creator_blacklist: set = set()

        # 地址检查参数
        self.max_tokens_per_creator_24h = TradingConfig.FILTER_MAX_TOKENS_PER_CREATOR_24H
        self.min_creator_tx_count = TradingConfig.FILTER_MIN_CREATOR_TX_COUNT
        self.min_creator_balance_bnb = TradingConfig.FILTER_MIN_CREATOR_BALANCE_BNB
        self.enable_address_check = TradingConfig.FILTER_ENABLE_ADDRESS_CHECK

        # 代币基本信息过滤
        self.min_name_length = TradingConfig.FILTER_MIN_NAME_LENGTH
        self.max_name_length = TradingConfig.FILTER_MAX_NAME_LENGTH
        self.min_symbol_length = TradingConfig.FILTER_MIN_SYMBOL_LENGTH
        self.max_symbol_length = TradingConfig.FILTER_MAX_SYMBOL_LENGTH

        # 供应量检查
        self.min_total_supply = TradingConfig.FILTER_MIN_TOTAL_SUPPLY
        self.max_total_supply = TradingConfig.FILTER_MAX_TOTAL_SUPPLY

        # 流动性比例检查
        self.min_liquidity_ratio = TradingConfig.FILTER_MIN_LIQUIDITY_RATIO

        # 创建者发币间隔检查
        self.min_creator_token_interval_minutes = TradingConfig.FILTER_MIN_CREATOR_TOKEN_INTERVAL_MINUTES

        logger.info(f"TradeFilter initialized: blacklist={self.blacklist_keywords}, "
                   f"min_liquidity={self.min_liquidity} BNB, address_check={self.enable_address_check}")

    async def should_buy(self, token_info: Dict) -> tuple[bool, str]:
        """
        判断是否应该买入此代币

        Args:
            token_info: 代币信息 (TokenCreate事件数据)

        Returns:
            (should_buy, reason)
        """
        # 1. 检查代币名称长度
        name = token_info.get('token_name', '')
        symbol = token_info.get('token_symbol', '')

        if len(name) < self.min_name_length or len(name) > self.max_name_length:
            return False, f"Invalid name length: {len(name)} (allowed: {self.min_name_length}-{self.max_name_length})"

        if len(symbol) < self.min_symbol_length or len(symbol) > self.max_symbol_length:
            return False, f"Invalid symbol length: {len(symbol)} (allowed: {self.min_symbol_length}-{self.max_symbol_length})"

        # 2. 检查黑名单关键词
        name_lower = name.lower()
        symbol_lower = symbol.lower()

        for keyword in self.blacklist_keywords:
            if keyword in name_lower or keyword in symbol_lower:
                return False, f"Blacklisted keyword: {keyword}"

        # 3. 检查代币供应量
        total_supply = token_info.get('total_supply', 0)
        if total_supply < self.min_total_supply:
            return False, f"Supply too low: {total_supply:,.0f} < {self.min_total_supply:,.0f}"

        if total_supply > self.max_total_supply:
            return False, f"Supply too high: {total_supply:,.0f} > {self.max_total_supply:,.0f}"

        # 4. 检查初始流动性
        launch_fee = token_info.get('launch_fee', 0)
        if launch_fee < self.min_liquidity:
            return False, f"Low liquidity: {launch_fee:.4f} BNB < {self.min_liquidity} BNB"

        # 5. 检查流动性/供应量比例
        if total_supply > 0:
            # launch_fee 是 BNB, total_supply 是原始值 (未除以1e18)
            # 需要统一单位: 将 launch_fee 转回 wei 或将 total_supply 转为实际数量
            liquidity_ratio = (launch_fee * 1e18) / total_supply
            if liquidity_ratio < self.min_liquidity_ratio:
                return False, f"Low liquidity ratio: {liquidity_ratio:.8f} < {self.min_liquidity_ratio:.8f}"

        # 6. 检查创建者地址 (如果启用)
        if self.enable_address_check:
            creator = token_info.get('creator', '')
            token_address = token_info.get('token_address', '')

            # 检查是否在黑名单
            if creator in self.creator_blacklist:
                return False, f"Creator blacklisted: {creator[:10]}..."

            # 记录创建者历史
            self._record_creator(creator, token_address)

            # 检查发币间隔
            if self._is_rapid_creator(creator):
                self.creator_blacklist.add(creator)
                return False, f"Rapid token creation: interval < {self.min_creator_token_interval_minutes}m"

            # 检查批量发币
            if self._is_batch_creator(creator):
                self.creator_blacklist.add(creator)
                return False, f"Batch creator: {len(self.creator_history[creator])} tokens in 24h"

            # 检查钱包声誉 (需要RPC调用,可能较慢)
            if self.w3:
                is_suspicious, reason = await self._check_wallet_reputation(creator)
                if is_suspicious:
                    self.creator_blacklist.add(creator)
                    return False, reason

        return True, "Passed all filters"

    def _record_creator(self, creator: str, token_address: str):
        """记录创建者发币历史"""
        now = datetime.now()
        cutoff = now - timedelta(hours=24)

        # 清理24小时前的记录
        self.creator_history[creator] = [
            (ts, addr) for ts, addr in self.creator_history[creator]
            if ts >= cutoff
        ]

        # 添加新记录
        self.creator_history[creator].append((now, token_address))

    def _is_batch_creator(self, creator: str) -> bool:
        """判断是否是批量发币者"""
        return len(self.creator_history[creator]) > self.max_tokens_per_creator_24h

    def _is_rapid_creator(self, creator: str) -> bool:
        """判断是否是快速发币者 (短时间内连续发币)"""
        history = self.creator_history[creator]
        if len(history) < 2:
            return False

        # 检查最近两次发币的时间间隔
        latest_time = history[-1][0]
        previous_time = history[-2][0]
        interval = (latest_time - previous_time).total_seconds() / 60  # 转换为分钟

        return interval < self.min_creator_token_interval_minutes

    async def _check_wallet_reputation(self, address: str) -> tuple[bool, str]:
        """
        检查钱包声誉

        Returns:
            (is_suspicious, reason)
        """
        try:
            # 检查交易数量
            tx_count = await self.w3.eth.get_transaction_count(address)
            if tx_count < self.min_creator_tx_count:
                return True, f"New wallet: {tx_count} txs"

            # 检查余额
            balance_wei = await self.w3.eth.get_balance(address)
            balance_bnb = float(balance_wei) / 1e18
            if balance_bnb < self.min_creator_balance_bnb:
                return True, f"Low balance: {balance_bnb:.4f} BNB"

            return False, "Wallet OK"

        except Exception as e:
            logger.warning(f"Wallet check failed for {address[:10]}...: {e}")
            # 如果RPC失败,不拒绝 (避免误杀)
            return False, "Check skipped"

    def get_stats(self) -> Dict:
        """获取过滤器统计"""
        return {
            'blacklist_keywords': self.blacklist_keywords,
            'min_liquidity': self.min_liquidity,
            'address_check_enabled': self.enable_address_check,
            'tracked_creators': len(self.creator_history),
            'blacklisted_creators': len(self.creator_blacklist)
        }
