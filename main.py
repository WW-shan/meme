"""
FourMeme Monitor - Main Entry Point
Real-time BSC chain monitoring for FourMeme platform
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import Config
from src.core.ws_manager import WSConnectionManager
from src.core.listener import FourMemeListener
from src.core.processor import DataProcessor
from src.utils.helpers import setup_logging

logger = logging.getLogger(__name__)


class FourMemeMonitor:
    """Main monitor application"""

    def __init__(self):
        self.config = Config
        self.ws_manager: WSConnectionManager = None
        self.listener: FourMemeListener = None
        self.processor: DataProcessor = None
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
        self.listener = FourMemeListener(w3, contract_config)

        # Register event handlers - 只监控发行和毕业事件
        self.listener.register_handler('TokenCreate', self.processor.process_event)
        self.listener.register_handler('TradeStop', self.processor.process_event)
        self.listener.register_handler('LiquidityAdded', self.processor.process_event)

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
        try:
            await asyncio.gather(
                self.listener.subscribe_to_events(),
                self.ws_manager.monitor_heartbeat(self._heartbeat_callback),
                self._stats_reporter()
            )
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
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes

            if self.listener and self.processor:
                listener_stats = self.listener.get_stats()
                processor_stats = self.processor.get_stats()

                logger.info("="*60)
                logger.info("📊 Statistics Report")
                logger.info(f"  Events processed: {listener_stats['events_processed']}")
                logger.info(f"  Last block: {listener_stats['last_block_processed']}")
                logger.info(f"  Events saved: {processor_stats['total_events']}")
                logger.info("="*60)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down...")

        self.running = False

        # Print final stats
        if self.processor:
            self.processor.print_stats()

        # Close connections
        if self.ws_manager:
            await self.ws_manager.disconnect()

        logger.info("✅ Shutdown complete")


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n⚠️  Received interrupt signal, stopping...")
    sys.exit(0)


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging(
        log_level=Config.LOG_LEVEL,
        log_file=Config.LOG_FILE
    )

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start monitor
    monitor = FourMemeMonitor()
    await monitor.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
