"""
FourMeme Event Listener
Monitors and processes FourMeme platform events on BSC
"""

import asyncio
import logging
from typing import Dict, Set, Callable, Any, List
from web3 import AsyncWeb3
from web3.contract import AsyncContract
from eth_utils import event_abi_to_log_topic
import json

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

        if not self.contract_abi:
            # Use minimal ABI for common events if full ABI not available
            self.contract_abi = self._get_minimal_abi()

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(self.contract_address),
            abi=self.contract_abi
        )

    def _get_minimal_abi(self) -> List[Dict]:
        """
        Minimal ABI with common FourMeme-like events
        Based on typical bonding curve platforms
        """
        return [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "token", "type": "address"},
                    {"indexed": True, "name": "creator", "type": "address"},
                    {"indexed": False, "name": "name", "type": "string"},
                    {"indexed": False, "name": "symbol", "type": "string"},
                    {"indexed": False, "name": "initialLiquidity", "type": "uint256"},
                ],
                "name": "TokenLaunched",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "token", "type": "address"},
                    {"indexed": False, "name": "progress", "type": "uint256"},
                    {"indexed": False, "name": "currentMarketCap", "type": "uint256"},
                ],
                "name": "BondingProgress",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "token", "type": "address"},
                    {"indexed": False, "name": "finalMarketCap", "type": "uint256"},
                    {"indexed": False, "name": "dexPair", "type": "address"},
                ],
                "name": "TokenGraduated",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "user", "type": "address"},
                    {"indexed": True, "name": "token", "type": "address"},
                    {"indexed": False, "name": "bnbAmount", "type": "uint256"},
                    {"indexed": False, "name": "tokenAmount", "type": "uint256"},
                ],
                "name": "TokenPurchase",
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
        tx_hash = event_data.get('transactionHash', '').hex()

        # Deduplicate
        if self._is_duplicate(tx_hash):
            logger.debug(f"Skipping duplicate event: {tx_hash}")
            return

        # Call all registered handlers
        handlers = self.event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                await handler(event_name, event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")

        self.events_processed += 1

    async def subscribe_to_events(self):
        """Subscribe to contract events via WebSocket"""
        if not self.contract:
            self._load_contract()

        logger.info(f"🎯 Subscribing to FourMeme events at {self.contract_address}")

        # Get current block to start from
        current_block = await self.w3.eth.block_number
        self.last_block_processed = current_block

        # Subscribe to all events
        event_filter = await self.w3.eth.filter({
            'address': self.contract_address,
            'fromBlock': 'latest'
        })

        logger.info(f"✅ Event subscription active (starting from block {current_block})")

        # Poll for new events
        while True:
            try:
                new_events = await event_filter.get_new_entries()

                for event_log in new_events:
                    await self._parse_and_process_event(event_log)

                # Small delay to avoid hammering the node
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error polling events: {e}")
                await asyncio.sleep(5)

    async def _parse_and_process_event(self, event_log: Dict):
        """Parse raw event log and process"""
        try:
            # Get block info for timestamp
            block = await self.w3.eth.get_block(event_log['blockNumber'])

            # Try to decode with contract ABI
            decoded_events = self.contract.events

            for event_name in ['TokenLaunched', 'BondingProgress', 'TokenGraduated', 'TokenPurchase']:
                try:
                    event = getattr(decoded_events, event_name, None)
                    if event:
                        processed_log = event().process_log(event_log)

                        # Add metadata
                        processed_log['event_name'] = event_name
                        processed_log['timestamp'] = block['timestamp']

                        await self._process_event(event_name, processed_log)
                        return
                except Exception:
                    continue

            # If no event matched, log raw event
            logger.debug(f"Unknown event in block {event_log['blockNumber']}: {event_log}")

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
