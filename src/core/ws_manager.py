"""
WebSocket Connection Manager for BSC
Handles WebSocket connection, reconnection, and heartbeat monitoring
"""

import asyncio
import logging
from typing import Optional, Callable
from web3 import AsyncWeb3
from web3.providers import WebSocketProvider
import time

logger = logging.getLogger(__name__)


class WSConnectionManager:
    """Manages WebSocket connection to BSC node with auto-reconnection"""

    def __init__(self, ws_url: str, max_retry_delay: int = 60):
        self.ws_url = ws_url
        self.max_retry_delay = max_retry_delay
        self.w3: Optional[AsyncWeb3] = None
        self.provider: Optional[WebSocketProvider] = None
        self.is_connected = False
        self.retry_count = 0
        self.last_block_time = time.time()

    async def connect(self) -> bool:
        """Establish WebSocket connection to BSC node"""
        try:
            logger.info(f"Connecting to BSC WebSocket: {self.ws_url[:50]}...")

            # Create WebSocket provider
            self.provider = WebSocketProvider(
                self.ws_url,
                websocket_kwargs={
                    'ping_interval': 20,
                    'ping_timeout': 10,
                    'close_timeout': 10,
                    'max_size': 2**25,  # 32MB
                }
            )

            # Connect the provider
            await self.provider.connect()

            # Create Web3 instance
            self.w3 = AsyncWeb3(self.provider)

            # Test connection
            block_number = await self.w3.eth.block_number
            logger.debug(f"Current block: {block_number}")

            self.is_connected = True
            self.retry_count = 0
            logger.info("✅ Successfully connected to BSC WebSocket")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Gracefully close WebSocket connection"""
        if self.provider:
            try:
                await self.provider.disconnect()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

        self.is_connected = False
        self.w3 = None
        self.provider = None

    async def reconnect(self) -> bool:
        """Reconnect with exponential backoff"""
        self.retry_count += 1

        # Calculate delay: 1s -> 2s -> 4s -> 8s -> ... -> 60s max
        delay = min(2 ** (self.retry_count - 1), self.max_retry_delay)

        logger.warning(f"🔄 Attempting reconnection #{self.retry_count} in {delay}s...")
        await asyncio.sleep(delay)

        await self.disconnect()
        return await self.connect()

    async def ensure_connection(self) -> bool:
        """Ensure connection is active, reconnect if needed"""
        if not self.is_connected or not self.w3:
            return await self.reconnect()

        try:
            # Test connection with a simple call
            await self.w3.eth.block_number
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            self.is_connected = False
            return await self.reconnect()

    async def monitor_heartbeat(self, callback: Optional[Callable] = None):
        """Monitor connection health and new blocks"""
        while True:
            try:
                if not await self.ensure_connection():
                    await asyncio.sleep(5)
                    continue

                current_block = await self.w3.eth.block_number
                current_time = time.time()

                # Check if we're receiving new blocks
                time_since_last = current_time - self.last_block_time
                if time_since_last > 300:  # 5 minutes
                    logger.warning(f"⚠️  No new blocks for {int(time_since_last)}s - possible node issue")

                self.last_block_time = current_time

                if callback:
                    await callback(current_block)

                # Check every 60 seconds
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(10)

    def get_web3(self) -> AsyncWeb3:
        """Get Web3 instance"""
        if not self.w3 or not self.is_connected:
            raise ConnectionError("WebSocket not connected")
        return self.w3
