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
from config.config import Config

try:
    from web3.providers.rpc import AsyncHTTPProvider
except ModuleNotFoundError:
    AsyncHTTPProvider = None

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
        self.blocks_skipped = 0  # 跳过的区块数
        self.max_block_lag = 0  # 最大落后区块数
        self.last_check_time = time.time()  # 上次检查时间
        self.connection_errors = 0  # 连接错误次数

        # Dedicated HTTP providers for get_logs polling
        self.log_http_endpoints = self.config.get('log_http_endpoints', [])
        self.log_http_weights = self.config.get('log_http_weights', [])
        self.log_w3_pool: List[AsyncWeb3] = []
        self.log_schedule: List[int] = []
        self.log_schedule_cursor = 0
        self.log_provider_errors: Dict[int, int] = {}
        self.log_provider_switches = 0
        self.log_range_splits = 0
        self.log_last_provider_index: Optional[int] = None
        self.log_last_request_ms = 0.0
        self._build_log_providers()

    def _build_log_providers(self):
        """Build dedicated AsyncWeb3 HTTP providers for get_logs."""
        endpoints = [endpoint.strip() for endpoint in self.log_http_endpoints if endpoint and endpoint.strip()]
        if not endpoints or AsyncHTTPProvider is None:
            self.log_w3_pool = []
            self.log_schedule = []
            self.log_schedule_cursor = 0
            return

        self.log_w3_pool = []
        for endpoint in endpoints:
            try:
                provider = AsyncHTTPProvider(endpoint)
                self.log_w3_pool.append(AsyncWeb3(provider))
            except Exception as exc:
                logger.warning(f"Failed to initialize log HTTP provider {endpoint}: {exc}")

        if len(self.log_w3_pool) != len(endpoints):
            logger.warning(
                "Log HTTP provider pool partially available "
                f"({len(self.log_w3_pool)}/{len(endpoints)} initialized)"
            )

        self.log_schedule = self._build_log_schedule(len(self.log_w3_pool), self.log_http_weights)
        self.log_schedule_cursor = 0
        self.log_provider_errors = {index: 0 for index in range(len(self.log_w3_pool))}

    def _build_log_schedule(self, provider_count: int, weights: List[int]) -> List[int]:
        """Expand weighted provider sequence into deterministic schedule."""
        if provider_count <= 0:
            return []

        if len(weights) != provider_count or any(weight <= 0 for weight in weights):
            weights = [1] * provider_count

        schedule: List[int] = []
        for index, weight in enumerate(weights):
            schedule.extend([index] * weight)
        return schedule

    def _next_log_provider_index(self, skip_index: Optional[int] = None) -> Optional[int]:
        """Get next provider index from schedule, optionally skipping one index."""
        if not self.log_schedule:
            return None

        attempts = 0
        max_attempts = len(self.log_schedule)
        while attempts < max_attempts:
            index = self.log_schedule[self.log_schedule_cursor]
            self.log_schedule_cursor = (self.log_schedule_cursor + 1) % len(self.log_schedule)
            if skip_index is None or index != skip_index:
                return index
            attempts += 1

        return None

    async def _get_logs_via_provider(self, provider_index: Optional[int], from_block: int, to_block: int):
        """Fetch logs via selected provider, fallback to listener ws provider."""
        payload = {
            'address': self.contract_address,
            'fromBlock': from_block,
            'toBlock': to_block
        }

        start = time.perf_counter()
        if provider_index is None:
            logs = await self.w3.eth.get_logs(payload)
            self.log_last_provider_index = None
            self.log_last_request_ms = (time.perf_counter() - start) * 1000
            return logs, None

        logs = await self.log_w3_pool[provider_index].eth.get_logs(payload)
        self.log_last_provider_index = provider_index
        self.log_last_request_ms = (time.perf_counter() - start) * 1000
        return logs, provider_index

    @staticmethod
    def _is_timeout_or_rate_limit_error(error: Exception) -> bool:
        """Identify timeout/rate-limit style transient get_logs failures."""
        message = str(error).lower()
        markers = [
            'invalid block range',
            'eth_getlogs is limited',
            'limit exceeded',
            '429',
            'rate limit',
            'too many requests',
            'timeout',
            'timed out',
            'time-out',
            'gateway timeout',
            'request timeout',
            'temporarily unavailable'
        ]
        return any(marker in message for marker in markers)

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
            historical_ok = await self._process_block_range(start_block, current_block)
            if historical_ok:
                logger.info("✅ Historical scan complete")
                self.last_block_processed = current_block
            else:
                logger.warning(
                    "Historical scan completed with failures; "
                    "continuing from current head without advancing processed checkpoint"
                )
                self.last_block_processed = start_block - 1 if start_block > 0 else 0
        else:
            self.last_block_processed = current_block

        logger.info(f"✅ Event subscription active (starting from block {current_block})")

        # Poll for new blocks and events
        while True:
            try:
                # Get latest block number
                latest_block = await self.w3.eth.block_number

                # Process new blocks
                if latest_block > self.last_block_processed:
                    gap = latest_block - self.last_block_processed
                    
                    # 记录最大落后
                    if gap > self.max_block_lag:
                        self.max_block_lag = gap

                    # 落后超过1000块（~50min），跳过中间部分，保留最近200块
                    if gap > 1000:
                        skip_to = latest_block - 200
                        skipped = skip_to - self.last_block_processed
                        self.blocks_skipped += skipped
                        logger.warning(f"⚠️ Listener lagging {gap} blocks, skipping {skipped} blocks to {skip_to} (keeping last 200)")
                        self.last_block_processed = skip_to
                        gap = latest_block - self.last_block_processed

                    if gap > 50:
                        logger.warning(f"⚠️ Listener {gap} blocks behind, catching up...")

                    # 低延迟目标：控制每次拉取窗口，避免常态大范围拉取
                    chunk = 40 if gap > 200 else (20 if gap > 50 else 8)
                    to_block = min(latest_block, self.last_block_processed + chunk)

                    processed_ok = await self._process_block_range(
                        self.last_block_processed + 1,
                        to_block
                    )
                    if processed_ok:
                        self.last_block_processed = to_block
                    else:
                        logger.warning(
                            f"Failed to process blocks {self.last_block_processed + 1}-{to_block}; "
                            "will retry on next poll"
                        )
                        await asyncio.sleep(0.2)
                        continue

                    # 如果还是落后，不进入 sleep，继续 catchup
                    if self.last_block_processed < latest_block:
                        continue

                # Wait before next check
                await asyncio.sleep(0.5) # 缩短到 0.5 秒，提高响应速度

            except Exception as e:
                self.connection_errors += 1
                logger.error(f"Error polling events: {repr(e)}", exc_info=True)

                # Try to ensure connection if ws_manager is available
                if self.ws_manager:
                    try:
                        await self.ws_manager.ensure_connection()
                        # Update w3 reference in case it changed
                        self.w3 = self.ws_manager.get_web3()
                        self._load_contract() # Re-load contract with new w3
                    except Exception as conn_err:
                        logger.error(f"Failed to reconnect: {repr(conn_err)}", exc_info=True)

                await asyncio.sleep(5)

    async def _process_block_range(self, from_block: int, to_block: int, retry_count: int = 0) -> bool:
        """Process events in a block range and return success/failure."""
        try:
            provider_index = self._next_log_provider_index()
            logs, selected_provider = await self._get_logs_via_provider(provider_index, from_block, to_block)
            if selected_provider is None:
                logger.debug(
                    f"get_logs provider=ws blocks={from_block}-{to_block} req_ms={self.log_last_request_ms:.1f}"
                )
            else:
                logger.debug(
                    f"get_logs provider_index={selected_provider} endpoint={self.log_http_endpoints[selected_provider]} "
                    f"blocks={from_block}-{to_block} req_ms={self.log_last_request_ms:.1f}"
                )

            if logs:
                logger.debug(f"Found {len(logs)} events in blocks {from_block}-{to_block}")
                tasks = [self._parse_and_process_event(log, None) for log in logs]
                await asyncio.gather(*tasks, return_exceptions=True)

            return True

        except Exception as exc:
            if provider_index is not None and provider_index in self.log_provider_errors:
                self.log_provider_errors[provider_index] += 1
            if self._is_timeout_or_rate_limit_error(exc):
                alternate_index = self._next_log_provider_index(skip_index=provider_index)
                if alternate_index is not None:
                    try:
                        self.log_provider_switches += 1
                        logger.warning(
                            f"get_logs failed on provider {provider_index} for {from_block}-{to_block}; "
                            f"retrying once with provider {alternate_index}: {exc}"
                        )
                        logs, _ = await self._get_logs_via_provider(alternate_index, from_block, to_block)
                        if logs:
                            logger.debug(f"Found {len(logs)} events in blocks {from_block}-{to_block} on alternate provider")
                            tasks = [self._parse_and_process_event(log, None) for log in logs]
                            await asyncio.gather(*tasks, return_exceptions=True)
                        return True
                    except Exception as alt_exc:
                        if not self._is_timeout_or_rate_limit_error(alt_exc):
                            logger.error(
                                f"Error processing blocks {from_block}-{to_block} on alternate provider: {repr(alt_exc)}",
                                exc_info=True
                            )
                            return False
                        exc = alt_exc

                if from_block >= to_block:
                    logger.warning(
                        f"Skipping block {from_block} after provider retry exhaustion due to transient get_logs error: {exc}"
                    )
                    return False

                delay = min(0.2 * (2 ** retry_count), 2.0)
                await asyncio.sleep(delay)

                self.log_range_splits += 1
                mid = (from_block + to_block) // 2
                logger.warning(
                    f"Splitting blocks {from_block}-{to_block} into {from_block}-{mid} and {mid + 1}-{to_block} "
                    f"after get_logs transient failure: {exc}"
                )

                left_ok = await self._process_block_range(from_block, mid, retry_count + 1)
                right_ok = await self._process_block_range(mid + 1, to_block, retry_count + 1)
                return left_ok and right_ok

            logger.error(f"Error processing blocks {from_block}-{to_block}: {repr(exc)}", exc_info=True)
            return False

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
            'handlers_registered': sum(len(h) for h in self.event_handlers.values()),
            'blocks_skipped': self.blocks_skipped,
            'max_block_lag': self.max_block_lag,
            'connection_errors': self.connection_errors,
            'uptime_seconds': int(time.time() - self.last_check_time),
            'log_last_provider_index': self.log_last_provider_index,
            'log_last_request_ms': round(self.log_last_request_ms, 2),
            'log_provider_switches': self.log_provider_switches,
            'log_range_splits': self.log_range_splits,
            'log_provider_errors': dict(self.log_provider_errors),
        }
