"""
Trading Coordinator
交易协调器 - 整合所有交易模块,处理完整的交易流程
"""

import logging
import asyncio
from typing import Dict, Optional, List
from web3 import AsyncWeb3

from src.core.filter import TradeFilter
from src.core.trader import TradeExecutor
from src.core.position import PositionTracker
from src.core.risk import RiskManager
from src.core.trend_tracker import TrendTracker
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
        self.filter = TradeFilter(w3)
        self.trader = TradeExecutor(w3)
        self.risk_manager = RiskManager()
        self.position_tracker = PositionTracker(self.trader, self.risk_manager)

        # 初始化热度追踪 (如果启用)
        self.trend_tracker = None
        if TradingConfig.FILTER_ENABLE_TREND_TRACKING:
            self.trend_tracker = TrendTracker(
                window_minutes=TradingConfig.FILTER_TREND_WINDOW_MINUTES,
                threshold=TradingConfig.FILTER_TREND_THRESHOLD,
                prefix_length=TradingConfig.FILTER_TREND_PREFIX_LENGTH
            )

        self.enabled = TradingConfig.ENABLE_TRADING

        logger.info(f"TradingCoordinator initialized | Trading: {self.enabled} | TrendTracking: {self.trend_tracker is not None}")

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
            token_symbol = token_info['token_symbol']

            # 1. 基础过滤检查 (先过滤掉明显不合格的代币)
            should_buy, filter_reason = await self.filter.should_buy(token_info)
            if not should_buy:
                mode_prefix = "🧪 [BACKTEST]" if TradingConfig.ENABLE_BACKTEST else "💰 [LIVE]"
                logger.info(f"{mode_prefix} ❌ Token filtered: {token_symbol} | Reason: {filter_reason}")
                return

            # 2. 热度检测 (只买热门聚类)
            if self.trend_tracker:
                is_hot, cluster_tokens = self.trend_tracker.add_token(token_address, token_symbol)

                if is_hot and cluster_tokens:
                    # 热门聚类 - 批量买入所有代币
                    await self._handle_hot_cluster(cluster_tokens, token_info)
                    return  # 批量处理完成
                else:
                    # 未触发热度 - 不买入
                    mode_prefix = "🧪 [BACKTEST]" if TradingConfig.ENABLE_BACKTEST else "💰 [LIVE]"
                    logger.info(f"{mode_prefix} ⏸️ Token passed filters but no trend: {token_symbol} | Skipped")
                    return
            else:
                # 未启用热度追踪 - 不买入
                mode_prefix = "🧪 [BACKTEST]" if TradingConfig.ENABLE_BACKTEST else "💰 [LIVE]"
                logger.info(f"{mode_prefix} ⏸️ Trend tracking disabled: {token_symbol} | Skipped")

        except Exception as e:
            logger.error(f"Error in on_token_create: {e}")
            import traceback
            traceback.print_exc()

    async def _handle_hot_cluster(self, cluster_tokens: List[str], latest_token_info: Dict):
        """
        处理热门聚类 - 批量买入所有代币

        Args:
            cluster_tokens: 聚类中的所有代币地址
            latest_token_info: 最新代币的信息 (用于日志)
        """
        cluster_buy_amount = TradingConfig.FILTER_CLUSTER_BUY_AMOUNT_BNB
        mode_prefix = "🧪 [BACKTEST]" if TradingConfig.ENABLE_BACKTEST else "💰 [LIVE]"

        logger.info(f"{mode_prefix} 🔥 HOT CLUSTER BUY | {len(cluster_tokens)} tokens | "
                   f"{cluster_buy_amount} BNB each | Latest: {latest_token_info['token_symbol']}")

        # 批量买入聚类中的所有代币
        for token_addr in cluster_tokens:
            # 风控检查
            can_buy, risk_reason = self.risk_manager.can_buy(cluster_buy_amount)
            if not can_buy:
                logger.warning(f"⚠️ Cluster buy skipped for {token_addr[:10]}...: {risk_reason}")
                continue

            # 异步买入 (不等待完成)
            asyncio.create_task(self._execute_buy_by_address(token_addr, cluster_buy_amount))

    async def _execute_buy_by_address(self, token_address: str, buy_amount: float):
        """
        通过地址执行买入 (用于聚类批量买入)

        Args:
            token_address: 代币地址
            buy_amount: 买入金额 (BNB)
        """
        try:
            logger.info(f"Cluster buy: {token_address[:10]}... for {buy_amount} BNB")

            # 执行买入 - 传入买入金额
            tx_hash = await self.trader.buy_token(token_address, buy_amount)

            if tx_hash:
                # 记录买入成功
                self.risk_manager.record_buy(token_address, buy_amount)

                # 添加到持仓追踪 - 初始设为 0，等待第一笔成交事件填充真实价格和数量
                await self.position_tracker.add_position(
                    token_address=token_address,
                    tx_hash=tx_hash,
                    entry_price=0,
                    token_amount=0,
                    bnb_invested=buy_amount
                )

                logger.info(f"Cluster buy executed: {tx_hash} | Waiting for on-chain confirmation...")
            else:
                logger.warning(f"Cluster buy failed for {token_address[:10]}...")

        except Exception as e:
            logger.error(f"Error in cluster buy for {token_address[:10]}...: {e}")

    async def _execute_buy(self, token_info: Dict, buy_amount: float):
        """
        执行买入流程

        Args:
            token_info: 代币信息
            buy_amount: 买入金额 (BNB)
        """
        token_address = token_info['token_address']

        try:
            logger.info(f"Attempting to buy {token_info['token_symbol']} for {buy_amount} BNB")

            # 执行买入 - 传入买入金额
            tx_hash = await self.trader.buy_token(token_address, buy_amount)

            if tx_hash:
                # 记录买入成功
                self.risk_manager.record_buy(token_address, buy_amount)

                # 添加到持仓追踪 - 初始设为 0，等待第一笔成交事件填充真实价格和数量
                await self.position_tracker.add_position(
                    token_address=token_address,
                    tx_hash=tx_hash,
                    entry_price=0,
                    token_amount=0,
                    bnb_invested=buy_amount
                )

                logger.info(f"Buy executed: {tx_hash} | Waiting for on-chain confirmation to initialize position...")
            else:
                logger.warning(f"Buy failed for {token_address}")

        except Exception as e:
            logger.error(f"Error executing buy for {token_address}: {e}")
            import traceback
            traceback.print_exc()

    async def on_token_purchase(self, event_name: str, event_data: Dict):
        """
        处理TokenPurchase事件 - 更新价格
        """
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            # 兼容多种参数名: amount/tokenAmount, cost/etherAmount
            token_amount_raw = args.get('amount') or args.get('tokenAmount') or 0
            ether_amount_raw = args.get('cost') or args.get('etherAmount') or 0

            token_amount = float(token_amount_raw) / 1e18
            ether_amount = float(ether_amount_raw) / 1e18

            if token_amount > 0:
                # 计算隐含价格 (BNB per token)
                price = ether_amount / token_amount

                # 检查是否需要初始化持仓 (针对我们刚刚买入的情况)
                position = self.position_tracker.positions.get(token_address)
                if position and position['entry_price'] == 0:
                    # 使用第一笔成交事件的价格初始化持仓
                    position['entry_price'] = price
                    # 提取手续费 (BNB)
                    fee = float(args.get('fee', 0)) / 1e18

                    # 重要修复：不能直接用 event 里的 token_amount_raw (那是别人的成交量)
                    my_token_amount = position['bnb_invested'] / price
                    token_amount_wei = int(my_token_amount * 1e18)

                    # 初始化持仓数据，加入手续费
                    await self.position_tracker.add_position(
                        token_address=token_address,
                        tx_hash=position['buy_tx_hash'],
                        entry_price=price,
                        token_amount=token_amount_wei,
                        bnb_invested=position['bnb_invested'],
                        buy_fee=fee
                    )

                    logger.info(f"✨ Position Initialized: {token_address[:10]}... | "
                               f"Price: {price:.10f} | Calculated Amount: {my_token_amount:,.2f} tokens | Fee: {fee:.6f} BNB")
                else:
                    # 通知持仓追踪器价格更新
                    await self.position_tracker.on_price_update(token_address, price)

        except Exception as e:
            logger.error(f"Error in on_token_purchase: {e}")

    async def on_token_sale(self, event_name: str, event_data: Dict):
        """
        处理TokenSale事件 - 更新价格
        """
        try:
            args = event_data.get('args', {})
            token_address = args.get('token', '')

            # 兼容多种参数名: amount/tokenAmount, cost/etherAmount
            token_amount_raw = args.get('amount') or args.get('tokenAmount') or 0
            ether_amount_raw = args.get('cost') or args.get('etherAmount') or 0

            token_amount = float(token_amount_raw) / 1e18
            ether_amount = float(ether_amount_raw) / 1e18

            if token_amount > 0:
                # 计算隐含价格 (BNB per token)
                price = ether_amount / token_amount
                # 通知持仓追踪器价格更新 (Sale 事件不用于初始化，因为买入之后才有卖出)
                await self.position_tracker.on_price_update(token_address, price)

        except Exception as e:
            logger.error(f"Error in on_token_sale: {e}")

    def get_stats(self) -> Dict:
        """获取交易统计"""
        stats = {
            'trading_enabled': self.enabled,
            'filter': self.filter.get_stats(),
            'risk': self.risk_manager.get_stats(),
            'positions': self.position_tracker.get_stats()
        }

        if self.trend_tracker:
            stats['trend_tracker'] = self.trend_tracker.get_stats()

        return stats
