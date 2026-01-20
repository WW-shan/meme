"""
FourMeme Event Listener
Monitors and processes FourMeme platform events on BSC
"""

import asyncio
import logging
import time
from typing import Dict, Set, Callable, Any, List, Optional
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from eth_utils import event_abi_to_log_topic
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FourMemeListener:
    """Real-time event listener for FourMeme platform"""

    def __init__(self, w3: AsyncWeb3, config: Dict[str, Any]):
        self.w3 = w3
        self.config = config
        self.contract_address = config.get('contract_address')
        self.contract_abi = config.get('contract_abi', [])
        self.contract: Optional[AsyncContract] = None

        # Event deduplication cache (last 1000 tx hashes)
        self.seen_txs: Set[str] = set()
        self.max_cache_size = 1000

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}

        # Statistics
        self.events_processed = 0
        self.last_block_processed = 0

    def _load_contract(self):
        """Load contract instance"""
        if not self.contract_address:
            raise ValueError("Contract address not configured")

        # Use provided ABI or fall back to minimal ABI
        if not self.contract_abi or len(self.contract_abi) == 0:
            logger.warning("No ABI provided, using minimal ABI")
            self.contract_abi = self._get_minimal_abi()
        else:
            logger.info(f"Loaded contract ABI with {len(self.contract_abi)} entries")

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )

    def _get_minimal_abi(self) -> List[Dict]:
        """
        Minimal ABI with FourMeme TokenManager events
        Official events from TokenManager.lite.abi
        """
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "creator", "type": "address"},
                    {"indexed": False, "name": "token", "type": "address"},
                    {"indexed": False, "name": "requestId", "type": "uint256"},
                    {"indexed": False, "name": "name", "type": "string"},
                    {"indexed": False, "name": "symbol", "type": "string"},
                    {"indexed": False, "name": "totalSupply", "type": "uint256"},
                    {"indexed": False, "name": "launchTime", "type": "uint256"},
                    {"indexed": False, "name": "launchFee", "type": "uint256"},
                ],
                "name": "TokenCreate",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "token", "type": "address"},
                    {"indexed": False, "name": "account", "type": "address"},
                    {"indexed": False, "name": "tokenAmount", "type": "uint256"},
                    {"indexed": False, "name": "etherAmount", "type": "uint256"},
                    {"indexed": False, "name": "fee", "type": "uint256"},
                ],
                "name": "TokenPurchase",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "origin", "type": "uint256"},
                ],
                "name": "TokenPurchase2",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "token", "type": "address"},
                    {"indexed": False, "name": "account", "type": "address"},
                    {"indexed": False, "name": "tokenAmount", "type": "uint256"},
                    {"indexed": False, "name": "etherAmount", "type": "uint256"},
                    {"indexed": False, "name": "fee", "type": "uint256"},
                ],
                "name": "TokenSale",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "origin", "type": "uint256"},
                ],
                "name": "TokenSale2",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": False, "name": "token", "type": "address"},
                ],
                "name": "TradeStop",
                "type": "event"
            },
        ]

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def _is_duplicate(self, tx_hash: str) -> bool:
        """Check if transaction has been processed"""
        if tx_hash in self.seen_txs:
            return True

        self.seen_txs.add(tx_hash)

        # LRU cache cleanup
        if len(self.seen_txs) > self.max_cache_size:
            # Remove oldest 100 entries
            oldest = list(self.seen_txs)[:100]
            for old_tx in oldest:
                self.seen_txs.discard(old_tx)

        return False

    async def _process_event(self, event_name: str, event_data: Dict):
        """Process a single event and call registered handlers"""
        try:
            tx_hash = event_data.get('transactionHash', b'')
            if isinstance(tx_hash, bytes):
                tx_hash = tx_hash.hex()
            log_index = event_data.get('logIndex', 0)

            # Use tx_hash + log_index for deduplication (one tx can have multiple events)
            dedup_key = f"{tx_hash}_{log_index}"

            if self._is_duplicate(dedup_key):
                logger.debug(f"Skipping duplicate event: {dedup_key}")
                return

            # Call all registered handlers
            handlers = self.event_handlers.get(event_name, [])
            for handler in handlers:
                try:
                    await handler(event_name, event_data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {e}")
                    import traceback
                    traceback.print_exc()

            self.events_processed += 1
        except Exception as e:
            logger.error(f"❌ ERROR in _process_event for {event_name}: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise so we can see it in the outer handler

    async def subscribe_to_events(self):
        """Subscribe to contract events via WebSocket"""
        if not self.contract:
            self._load_contract()

        logger.info(f"🎯 Subscribing to FourMeme events at {self.contract_address}")

        # Get current block to start from
        current_block = await self.w3.eth.block_number
        self.last_block_processed = current_block

        logger.info(f"✅ Event subscription active (starting from block {current_block})")

        # Poll for new blocks and events
        while True:
            try:
                # Get latest block number
                latest_block = await self.w3.eth.block_number

                # Process new blocks
                if latest_block > self.last_block_processed:
                    # Start with small batch to avoid rate limits
                    # Will process 10 blocks at a time
                    to_block = min(latest_block, self.last_block_processed + 10)

                    await self._process_block_range(
                        self.last_block_processed + 1,
                        to_block
                    )
                    self.last_block_processed = to_block

                # Wait before next check (poll every 1 second for faster catchup)
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error polling events: {e}")
                await asyncio.sleep(5)

    async def _process_block_range(self, from_block: int, to_block: int, retry_count: int = 0):
        """Process events in a block range with exponential backoff"""
        try:
            # For single block, use the block number directly
            if from_block == to_block:
                from_block = to_block = from_block

            # Get logs for this block range
            logs = await self.w3.eth.get_logs({
                'address': self.contract_address,
                'fromBlock': from_block,
                'toBlock': to_block
            })

            if logs:
                logger.info(f"Found {len(logs)} events in blocks {from_block}-{to_block}")

                # Process all events in parallel (without fetching blocks)
                tasks = [self._parse_and_process_event(log, None) for log in logs]
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            error_msg = str(e).lower()

            # Handle rate limit errors
            if 'invalid block range' in error_msg or 'eth_getlogs is limited' in error_msg or 'limit exceeded' in error_msg:
                # If range is already 1 block, just skip with warning
                if to_block - from_block <= 0:
                    logger.warning(f"Skipping single block {from_block} due to rate limit")
                    return

                # Split range in half and retry
                mid = (from_block + to_block) // 2
                logger.warning(f"Rate limit hit for blocks {from_block}-{to_block}, splitting into {from_block}-{mid} and {mid+1}-{to_block}")

                # Exponential backoff delay
                delay = min(2 ** retry_count, 10)  # Max 10 seconds
                await asyncio.sleep(delay)

                # Process first half
                await self._process_block_range(from_block, mid, retry_count + 1)

                # Small delay between halves
                await asyncio.sleep(0.5)

                # Process second half
                await self._process_block_range(mid + 1, to_block, retry_count + 1)
            else:
                logger.error(f"Error processing blocks {from_block}-{to_block}: {e}")

    async def _parse_and_process_event(self, event_log: Dict, block: Optional[Dict] = None):
        """Parse raw event log and process"""
        try:
            # Use current timestamp (faster than fetching block)
            timestamp = int(time.time())

            # Try to decode with contract ABI
            decoded_events = self.contract.events

            # FourMeme TokenManager2 events - 监控所有事件
            event_names = ['TokenCreate', 'TokenPurchase', 'TokenPurchase2', 'TokenSale', 'TokenSale2', 'TradeStop', 'LiquidityAdded']
            for event_name in event_names:
                try:
                    event = getattr(decoded_events, event_name, None)
                    if not event:
                        continue

                    processed_log = event().process_log(event_log)

                    # Convert to regular dict if needed
                    if not isinstance(processed_log, dict):
                        processed_log = dict(processed_log)

                    processed_log['event_name'] = event_name
                    processed_log['timestamp'] = timestamp

                except Exception as e:
                    # Log decoding errors for debugging
                    logger.debug(f"Failed to decode as {event_name}: {str(e)[:100]}")
                    continue
                
                # Decode succeeded - process the event
                await self._process_event(event_name, processed_log)
                return

            # If no event matched, check if it's a buy/sell event we're skipping
            topic0 = event_log['topics'][0].hex() if event_log.get('topics') else 'no-topic'

            # Skip logging for buy/sell events (we're intentionally not monitoring them)
            buy_sell_topics = [
                '7db52723a3b2cdd6164364b3b766e65e540d7be48ffa89582956d8eaebe62942',  # TokenPurchase
                '48063b1239b68b5d50123408787a6df1f644d9160f0e5f702fefddb9a855954d',  # TokenPurchase2
                '0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19',  # TokenSale
                '741ffc4605df23259462547defeab4f6e755bdc5fbb6d0820727d6d3400c7e0d',  # TokenSale2
            ]

            if topic0 not in buy_sell_topics:
                tx_hash = event_log.get('transactionHash', b'').hex()
                logger.warning(f"⚠️  Unrecognized event - Block: {event_log['blockNumber']}, Tx: {tx_hash[:10]}..., Topic: {topic0}")

        except Exception as e:
            logger.error(f"Error parsing event: {e}")

    async def poll_historical_events(self, from_block: int, to_block: int = None):
        """Poll historical events (useful for testing)"""
        if not self.contract:
            self._load_contract()

        if to_block is None:
            to_block = await self.w3.eth.block_number

        logger.info(f"Polling historical events from block {from_block} to {to_block}")

        # Get all events in range
        event_filter = await self.w3.eth.filter({
            'address': self.contract_address,
            'fromBlock': from_block,
            'toBlock': to_block
        })

        events = await event_filter.get_all_entries()
        logger.info(f"Found {len(events)} events in range")

        for event_log in events:
            await self._parse_and_process_event(event_log)

    def get_stats(self) -> Dict:
        """Get listener statistics"""
        return {
            'events_processed': self.events_processed,
            'last_block_processed': self.last_block_processed,
            'cache_size': len(self.seen_txs),
            'handlers_registered': sum(len(h) for h in self.event_handlers.values())
        }
