"""
Trading Coordinator
交易协调器 - 整合所有交易模块,处理完整的交易流程
"""

import logging
import asyncio
from typing import Dict, Optional
from web3 import AsyncWeb3

from src.core.filter import TradeFilter
from src.core.trader import TradeExecutor
from src.core.position import PositionTracker
from src.core.risk import RiskManager
from config.trading_config import TradingConfig

logger = logging.getLogger(__name__)


class TradingCoordinator:
    """交易协调器 - 连接监控系统和交易系统"""

    def __init__(self, w3: AsyncWeb3):
        """
        Args:
            w3: Web3异步实例
        """
        self.w3 = w3

        # 初始化所有模块
        self.filter = TradeFilter()
        self.trader = TradeExecutor(w3)
        self.risk_manager = RiskManager()
        self.position_tracker = PositionTracker(self.trader, self.risk_manager)

        self.enabled = TradingConfig.ENABLE_TRADING

        logger.info(f"TradingCoordinator initialized | Trading: {self.enabled}")

    async def on_token_create(self, event_name: str, event_data: Dict):
        """
        处理TokenCreate事件 - 主交易入口

        Args:
            event_name: 事件名称
            event_data: 事件数据
        """
        try:
            # 提取代币信息
            args = event_data.get('args', {})
            token_info = {
                'token_address': args.get('token', ''),
                'token_name': args.get('name', ''),
                'token_symbol': args.get('symbol', ''),
                'creator': args.get('creator', ''),
                'total_supply': float(args.get('totalSupply', 0)) / 1e18,
                'launch_fee': float(args.get('launchFee', 0)) / 1e18,
                'launch_time': args.get('launchTime', 0),
            }

            token_address = token_info['token_address']
            logger.info(f"New token detected: {token_info['token_symbol']} ({token_address[:10]}...)")

            # 1. 过滤检查
            should_buy, filter_reason = self.filter.should_buy(token_info)
            if not should_buy:
                logger.info(f"Skipped: {filter_reason}")
                return

            # 2. 风控检查
            can_buy, risk_reason = self.risk_manager.can_buy(TradingConfig.BUY_AMOUNT_BNB)
            if not can_buy:
                logger.warning(f"Risk check failed: {risk_reason}")
                return

            # 3. 执行买入 (异步,不阻塞监控)
            asyncio.create_task(self._execute_buy(token_info))

        except Exception as e:
            logger.error(f"Error in on_token_create: {e}")
            import traceback
            traceback.print_exc()

    async def _execute_buy(self, token_info: Dict):
        """
        执行买入流程

        Args:
            token_info: 代币信息
        """
        token_address = token_info['token_address']
        buy_amount = TradingConfig.BUY_AMOUNT_BNB

        try:
            logger.info(f"Attempting to buy {token_info['token_symbol']} for {buy_amount} BNB")

            # 执行买入
            tx_hash = await self.trader.buy_token(token_address)

            if tx_hash:
                # 记录买入成功
                self.risk_manager.record_buy(token_address, buy_amount)

                # 计算买入价格 (简化: 使用launch_fee估算)
                # 实际应该等待交易确认后获取精确的买入数量
                estimated_price = buy_amount / (token_info['total_supply'] * 0.8)  # 粗略估算

                # 添加到持仓追踪
                await self.position_tracker.add_position(
                    token_address=token_address,
                    tx_hash=tx_hash,
                    entry_price=estimated_price,
                    token_amount=token_info['total_supply'] * 0.8,  # 估算
                    bnb_invested=buy_amount
                )

                logger.info(f"Buy successful: {tx_hash}")
            else:
                logger.warning(f"Buy failed for {token_address}")

        except Exception as e:
            logger.error(f"Error executing buy for {token_address}: {e}")
            import traceback
            traceback.print_exc()

    async def on_token_purchase(self, event_name: str, event_data: Dict):
        """
        处理TokenPurchase事件 - 更新价格

        Args:
            event_name: 事件名称
            event_data: 事件数据
        """
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')
            token_amount = float(args.get('tokenAmount', 0)) / 1e18
            ether_amount = float(args.get('etherAmount', 0)) / 1e18

            if token_amount > 0:
                # 计算隐含价格 (BNB per token)
                price = ether_amount / token_amount

                # 通知持仓追踪器价格更新
                await self.position_tracker.on_price_update(token_address, price)

        except Exception as e:
            logger.error(f"Error in on_token_purchase: {e}")

    async def on_token_sale(self, event_name: str, event_data: Dict):
        """
        处理TokenSale事件 - 更新价格

        Args:
            event_name: 事件名称
            event_data: 事件数据
        """
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')
            token_amount = float(args.get('tokenAmount', 0)) / 1e18
            ether_amount = float(args.get('etherAmount', 0)) / 1e18

            if token_amount > 0:
                # 计算隐含价格 (BNB per token)
                price = ether_amount / token_amount

                # 通知持仓追踪器价格更新
                await self.position_tracker.on_price_update(token_address, price)

        except Exception as e:
            logger.error(f"Error in on_token_sale: {e}")

    def get_stats(self) -> Dict:
        """获取交易统计"""
        return {
            'trading_enabled': self.enabled,
            'filter': self.filter.get_stats(),
            'risk': self.risk_manager.get_stats(),
            'positions': self.position_tracker.get_stats()
        }
