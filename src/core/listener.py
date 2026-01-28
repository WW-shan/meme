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
from config.config import Config

logger = logging.getLogger(__name__)


class FourMemeListener:
    """Real-time event listener for FourMeme platform"""

    def __init__(self, w3: AsyncWeb3, config: Dict[str, Any], ws_manager: Any = None):
        self.w3 = w3
        self.config = config
        self.ws_manager = ws_manager
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

        # Ensure Checksum Address
        try:
            self.contract_address = self.w3.to_checksum_address(self.contract_address)
        except:
            pass

        # Load ABI from config and combine with internal version to ensure
        # all possible event signatures are covered
        external_abi = self.config.get('contract_abi', [])
        internal_abi = self._get_minimal_abi()

        # Combine ABIs (filter duplicates by name)
        combined_abi = internal_abi.copy()
        existing_names = {item.get('name') for item in internal_abi if item.get('type') == 'event'}

        for item in external_abi:
            if item.get('type') == 'event' and item.get('name') not in existing_names:
                combined_abi.append(item)
            elif item.get('type') == 'function':
                combined_abi.append(item)

        self.contract_abi = combined_abi
        logger.info(f"Loaded combined ABI with {len(self.contract_abi)} entries")

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

        # Check historical scan settings
        scan_historical = self.config.get('scan_historical', Config.SCAN_HISTORICAL)
        historical_blocks = self.config.get('historical_blocks', Config.HISTORICAL_BLOCKS)

        if scan_historical:
            start_block = max(0, current_block - historical_blocks)
            logger.info(f"📜 Scanning historical blocks {start_block} to {current_block} ({historical_blocks} blocks)...")
            # Use _process_block_range directly as it handles chunking and retries
            await self._process_block_range(start_block, current_block)
            logger.info("✅ Historical scan complete")

        self.last_block_processed = current_block

        logger.info(f"✅ Event subscription active (starting from block {current_block})")

        # Poll for new blocks and events
        while True:
            try:
                # Get latest block number
                latest_block = await self.w3.eth.block_number

                # Process new blocks
                if latest_block > self.last_block_processed:
                    logger.debug(f"Processing blocks {self.last_block_processed+1} to {latest_block}")

                    # 检查落后块数，如果落后太多（超过 100 块），考虑直接跳过或分片抓取
                    if latest_block - self.last_block_processed > 100:
                         logger.warning(f"⚠️ Listener lagging behind! Current: {latest_block}, Last: {self.last_block_processed}. Catching up...")

                    # 每次抓取最多 20 个块，提高实时性
                    to_block = min(latest_block, self.last_block_processed + 20)

                    await self._process_block_range(
                        self.last_block_processed + 1,
                        to_block
                    )
                    self.last_block_processed = to_block

                    # 如果还是落后，不进入 sleep，继续 catchup
                    if self.last_block_processed < latest_block:
                        continue

                # Wait before next check
                await asyncio.sleep(0.5) # 缩短到 0.5 秒，提高响应速度

            except Exception as e:
                logger.error(f"Error polling events: {e}")

                # Try to ensure connection if ws_manager is available
                if self.ws_manager:
                    try:
                        await self.ws_manager.ensure_connection()
                        # Update w3 reference in case it changed
                        self.w3 = self.ws_manager.get_web3()
                        self._load_contract() # Re-load contract with new w3
                    except Exception as conn_err:
                        logger.error(f"Failed to reconnect: {conn_err}")

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
                logger.debug(f"Found {len(logs)} events in blocks {from_block}-{to_block}")

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
            # 记录事件被发现的时间
            discovery_time = int(time.time())

            # Try to decode with contract ABI
            decoded_events = self.contract.events

            # FourMeme TokenManager2 events - 监控所有事件
            event_names = ['TokenCreate', 'TokenPurchase', 'TokenPurchaseV1', 'TokenPurchase2', 'TokenSale', 'TokenSaleV1', 'TokenSale2', 'TradeStop', 'LiquidityAdded']
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
                    # 优先使用 discovery_time，确保时序逻辑一致
                    processed_log['timestamp'] = discovery_time
                    processed_log['blockNumber'] = event_log.get('blockNumber')
                    processed_log['transactionHash'] = event_log.get('transactionHash')

                except Exception as e:
                    # Log decoding errors for debugging
                    logger.debug(f"Failed to decode as {event_name}: {str(e)[:100]}")
                    continue
                
                # Decode succeeded - process the event
                await self._process_event(event_name, processed_log)
                return

            # If no event matched, check if it's a known event type we are logging
            topic0 = event_log['topics'][0].hex() if event_log.get('topics') else 'no-topic'

            # Known topics for FourMeme
            known_topics = {
                'a78d55aeb92a87db782edde05df51f62cd9c43f9c4ee844147e54d963cd30d37a': 'TokenPurchase',
                'c18aa71171b358b706fe33dd345299685ba21a5316c66ffa9e319268b033c44b0': 'TokenSale',
                '7db52723a3b2cdd6164364b3b766e65e540d7be48ffa89582956d8eaebe62942': 'TokenPurchase (Alt)',
                '48063b1239b68b5d50123408787a6df1f644d9160f0e5f702fefddb9a855954d': 'TokenPurchase2',
                '0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19': 'TokenSale (Alt)',
                '741ffc4605df23259462547defeab4f6e755bdc5fbb6d0820727d6d3400c7e0d': 'TokenSale2',
            }

            if topic0 in known_topics:
                event_name_raw = known_topics[topic0]

                # Determine normalized event name
                if 'Purchase' in event_name_raw:
                    normalized_name = 'TokenPurchase'
                else:
                    normalized_name = 'TokenSale'

                # Manual Decoding
                try:
                    data = event_log.get('data', b'')
                    topics = event_log.get('topics', [])
                    if isinstance(data, str):
                        data = bytes.fromhex(data.replace('0x', ''))

                    token_address = None
                    account_address = None
                    amount = 0
                    cost = 0
                    price = 0

                    # Scenario 1: Unindexed (Token/Account in Data) - Matches TokenSale (Alt)
                    # Word 0: Token
                    # Word 1: Account
                    # Word 2: Price
                    # Word 3: Amount
                    # Word 4: Cost
                    if len(topics) == 1 and len(data) >= 160:
                        token_hex = data[12:32].hex()
                        account_hex = data[44:64].hex()
                        token_address = self.w3.to_checksum_address('0x' + token_hex)
                        account_address = self.w3.to_checksum_address('0x' + account_hex)

                        # price = int.from_bytes(data[64:96], 'big')
                        amount = int.from_bytes(data[96:128], 'big')
                        cost = int.from_bytes(data[128:160], 'big')

                    # Scenario 2: Indexed (Token/Account in Topics) - Matches TokenPurchase2?
                    # Topic 1: Token
                    # Topic 2: Account
                    # Data: Price, Amount, Cost...
                    elif len(topics) >= 3 and len(data) >= 96:
                        token_address = self.w3.to_checksum_address('0x' + topics[1].hex()[24:])
                        account_address = self.w3.to_checksum_address('0x' + topics[2].hex()[24:])

                        # Assuming Data: Price, Amount, Cost
                        # Word 0: Price
                        # Word 1: Amount
                        # Word 2: Cost
                        amount = int.from_bytes(data[32:64], 'big')
                        cost = int.from_bytes(data[64:96], 'big')

                    # Scenario 3: Partial Indexed (Token in Topic, Account in Data?)
                    # Some variants might have Token indexed but Account not.
                    elif len(topics) == 2 and len(data) >= 128:
                        token_address = self.w3.to_checksum_address('0x' + topics[1].hex()[24:])
                        account_hex = data[12:32].hex() # Account at Word 0
                        account_address = self.w3.to_checksum_address('0x' + account_hex)

                        # Data: Account, Price, Amount, Cost
                        amount = int.from_bytes(data[64:96], 'big')
                        cost = int.from_bytes(data[96:128], 'big')

                    # Scenario 4: Lightweight Event (Topics: 1, Data: 32)
                    # Likely just "origin" or similar signal event, insufficient for trade stats.
                    elif len(topics) == 1 and len(data) == 32:
                         logger.debug(f"Skipping lightweight signal event {event_name_raw} (Data: 32 bytes)")
                         return

                    if token_address and account_address:
                        if amount > 0:
                            price = cost / amount

                        processed_log = {
                            'event_name': normalized_name,
                            'args': {
                                'token': token_address,
                                'account': account_address,
                                'amount': amount,
                                'cost': cost,
                                'price': price
                            },
                            'transactionHash': event_log.get('transactionHash'),
                            'blockNumber': event_log.get('blockNumber'),
                            'timestamp': discovery_time
                        }

                        logger.debug(f"✅ Manually decoded {event_name_raw} -> {normalized_name}: {processed_log['args']['token'][:10]}...")
                        await self._process_event(normalized_name, processed_log)
                        return
                    else:
                        # Log specific failure reason for debugging
                        logger.debug(f"Manual decode skip: topics={len(topics)}, data_len={len(data)}")

                except Exception as decode_err:
                    logger.error(f"Manual decode failed: {decode_err}")

                tx_hash = event_log.get('transactionHash', b'').hex()
                logger.error(f"❌ Failed to decode KNOWN event {event_name_raw} - Topic match found but ABI mismatch? Tx: {tx_hash[:10]}... Topics: {len(event_log.get('topics', []))} Data: {len(event_log.get('data', b''))}")
            else:
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

        # Use _process_block_range to handle large ranges and rate limits safely
        await self._process_block_range(from_block, to_block)

        logger.info(f"Finished polling historical events")

    def get_stats(self) -> Dict:
        """Get listener statistics"""
        return {
            'events_processed': self.events_processed,
            'last_block_processed': self.last_block_processed,
            'cache_size': len(self.seen_txs),
            'handlers_registered': sum(len(h) for h in self.event_handlers.values())
        }
