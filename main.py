"""
FourMeme Monitor - Main Entry Point
Real-time BSC chain monitoring for FourMeme platform
"""

import asyncio
import signal
import sys
import logging
import os
from pathlib import Path

# 设置环境变量以支持 UTF-8 输出
if sys.platform == 'win32':
    # 设置控制台代码页为 UTF-8
    os.system('chcp 65001 > nul 2>&1')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from config.trading_config import TradingConfig
from src.core.ws_manager import WSConnectionManager
from src.core.listener import FourMemeListener
from src.core.processor import DataProcessor
from src.core.coordinator import TradingCoordinator
from src.utils.helpers import setup_logging
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

logger = logging.getLogger(__name__)


class FourMemeMonitor:
    """Main monitor application"""

    def __init__(self):
        self.config = Config
        self.ws_manager: WSConnectionManager = None
        self.listener: FourMemeListener = None
        self.processor: DataProcessor = None
        self.coordinator: TradingCoordinator = None
        self.running = False

    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing FourMeme Monitor...")

        # Setup WebSocket manager
        self.ws_manager = WSConnectionManager(
            ws_url=self.config.BSC_WSS_URL,
            max_retry_delay=self.config.MAX_RETRY_DELAY
        )

        # Connect to BSC
        connected = await self.ws_manager.connect()
        if not connected:
            logger.error("Failed to connect to BSC WebSocket")
            return False

        # Initialize processor
        self.processor = DataProcessor(output_dir=self.config.OUTPUT_DIR)

        # Initialize listener
        w3 = self.ws_manager.get_web3()
        contract_config = self.config.get_contract_config()
        self.listener = FourMemeListener(w3, contract_config, self.ws_manager)

        # Initialize trading coordinator (if enabled)
        if TradingConfig.ENABLE_TRADING or TradingConfig.ENABLE_BACKTEST:
            self.coordinator = TradingCoordinator(w3)
            logger.info(f"Trading coordinator initialized (Trading: {TradingConfig.ENABLE_TRADING})")

        # Register event handlers
        self.listener.register_handler('TokenCreate', self.processor.process_event)
        self.listener.register_handler('TokenPurchase', self.processor.process_event)
        self.listener.register_handler('TokenSale', self.processor.process_event)
        self.listener.register_handler('TradeStop', self.processor.process_event)
        self.listener.register_handler('LiquidityAdded', self.processor.process_event)

        # Register trading handlers if enabled
        if self.coordinator:
            self.listener.register_handler('TokenCreate', self.coordinator.on_token_create)
            self.listener.register_handler('TokenPurchase', self.coordinator.on_token_purchase)
            self.listener.register_handler('TokenSale', self.coordinator.on_token_sale)
            logger.info("Trading event handlers registered")

        logger.info("✅ All components initialized")
        return True

    async def start(self):
        """Start monitoring"""
        if not await self.initialize():
            logger.error("Initialization failed")
            return

        self.running = True

        logger.info("="*60)
        logger.info("🎯 FourMeme Monitor Started")
        logger.info(f"Contract: {self.config.FOURMEME_CONTRACT}")
        logger.info(f"Output: {self.config.OUTPUT_DIR}")
        logger.info(f"WebSocket: {self.config.BSC_WSS_URL[:50]}...")
        logger.info("="*60)
        print("\n⏳ Waiting for events... (Press Ctrl+C to stop)\n")

        # Run monitoring tasks
        tasks = [
            self.listener.subscribe_to_events(),
            self.ws_manager.monitor_heartbeat(self._heartbeat_callback),
            self._stats_reporter()
        ]

        # 如果有交易协调器，增加周期性持仓检查任务
        if self.coordinator:
            tasks.append(self.coordinator.position_tracker.run_periodic_check())

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def _heartbeat_callback(self, block_number: int):
        """Heartbeat callback"""
        logger.debug(f"💓 Heartbeat - Block: {block_number}")

    async def _stats_reporter(self):
        """Periodically report statistics"""
        counter = 0
        while self.running:
            # 如果有活跃持仓，每 60 秒报一次；否则每 300 秒报一次
            has_positions = False
            if self.coordinator:
                stats = self.coordinator.get_stats()
                has_positions = stats['positions']['active_positions'] > 0

            wait_time = 60 if has_positions else 300
            await asyncio.sleep(wait_time)

            if self.listener and self.processor:
                listener_stats = self.listener.get_stats()
                processor_stats = self.processor.get_stats()

                logger.info("="*60)
                logger.info("📊 Statistics Report")
                logger.info(f"  Events processed: {listener_stats['events_processed']}")
                logger.info(f"  Last block: {listener_stats['last_block_processed']}")
                logger.info(f"  Events saved: {processor_stats['total_events']}")

                # Trading stats if enabled
                if self.coordinator:
                    trading_stats = self.coordinator.get_stats()
                    pos_stats = trading_stats['positions']

                    logger.info(f"  Trading enabled: {trading_stats['trading_enabled']}")
                    logger.info(f"  Active positions: {pos_stats['active_positions']}")
                    logger.info(f"  Daily trades: {trading_stats['risk']['daily_trades']}/{trading_stats['risk']['daily_trades_limit']}")

                    # 收益概览
                    pnl_color = Fore.GREEN if pos_stats['total_pnl'] >= 0 else Fore.RED
                    logger.info(f"  Profit Summary:")
                    logger.info(f"    - Total PnL: {pnl_color}{pos_stats['total_pnl']:.6f} BNB{Style.RESET_ALL}")
                    logger.info(f"    - Realized: {pos_stats['total_realized_pnl']:.6f} BNB")
                    logger.info(f"    - Unrealized: {pos_stats['total_unrealized_pnl']:.6f} BNB")
                    logger.info(f"    - Fees & Gas: {pos_stats['total_fees_paid']:.6f} BNB")
                    logger.info(f"    - Total Invested: {pos_stats['total_invested']:.4f} BNB")

                    if has_positions:
                        logger.info(f"  Position Details:")
                        for addr, pos in pos_stats['positions'].items():
                            p_color = Fore.GREEN if pos['pnl_pct'] >= 0 else Fore.RED
                            logger.info(f"    - {addr[:10]}...: {pos['status']} | {p_color}PnL: {pos['pnl_pct']:+.2f}%{Style.RESET_ALL} | Hold: {pos['hold_time_seconds']:.0f}s")


                logger.info("="*60)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down...")
        self.running = False

        # 如果有交易协调器，强制清仓
        if self.coordinator:
            await self.coordinator.position_tracker.close_all()
            self.coordinator.position_tracker.print_final_summary()

        # Print data processor stats
        if self.processor:
            self.processor.print_stats()

        # Close connections
        if self.ws_manager:
            await self.ws_manager.disconnect()

        logger.info("✅ Shutdown complete")


def main_sync():
    """Main entry point wrapper to handle keyboard interrupt correctly"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 捕捉到 Ctrl+C 后不做任何事，让 shutdown 流程自然跑完
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging(
        log_level=Config.LOG_LEVEL,
        log_file=Config.LOG_FILE
    )

    # 移除信号处理器，防止它直接 sys.exit() 导致 shutdown 跑不完
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)

    # Start monitor
    monitor = FourMemeMonitor()
    await monitor.start()


if __name__ == '__main__':
    main_sync()
