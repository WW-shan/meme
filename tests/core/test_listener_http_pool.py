import asyncio
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch


def _build_listener_stubs():
    web3_stub = types.ModuleType('web3')

    class _AsyncWeb3:
        def __init__(self, provider=None):
            self.provider = provider
            self.eth = types.SimpleNamespace(get_logs=AsyncMock(return_value=[]))

        def to_checksum_address(self, value):
            return value

    web3_stub.AsyncWeb3 = _AsyncWeb3

    contract_stub = types.ModuleType('web3.contract')
    contract_stub.AsyncContract = object

    providers_stub = types.ModuleType('web3.providers')

    providers_rpc_stub = types.ModuleType('web3.providers.rpc')

    class _AsyncHTTPProvider:
        def __init__(self, endpoint_uri):
            self.endpoint_uri = endpoint_uri

    providers_rpc_stub.AsyncHTTPProvider = _AsyncHTTPProvider

    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None

    return {
        'web3': web3_stub,
        'web3.contract': contract_stub,
        'web3.providers': providers_stub,
        'web3.providers.rpc': providers_rpc_stub,
        'dotenv': dotenv_stub,
    }


def _load_listener_class():
    try:
        module = importlib.import_module('src.core.listener')
        module = importlib.reload(module)
        return module.FourMemeListener
    except ModuleNotFoundError as exc:
        missing = (exc.name or '').split('.')[0]
        if missing not in {'web3', 'dotenv'}:
            raise
        with patch.dict(sys.modules, _build_listener_stubs(), clear=False):
            module = importlib.import_module('src.core.listener')
            module = importlib.reload(module)
            return module.FourMemeListener
    finally:
        sys.modules.pop('src.core.listener', None)


class TestListenerHttpPool(unittest.IsolatedAsyncioTestCase):
    def test_compute_chunk_size_is_adaptive(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        self.assertEqual(listener._compute_chunk_size(20), 8)
        self.assertEqual(listener._compute_chunk_size(80), 32)
        self.assertEqual(listener._compute_chunk_size(250), 80)
        self.assertEqual(listener._compute_chunk_size(700), 120)
        self.assertEqual(listener._compute_chunk_size(1200), 160)

    def test_log_provider_order_prefers_primary_then_fallbacks(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a', 'https://rpc.b', 'https://rpc.c'],
            },
            ws_manager=None,
        )

        self.assertEqual(listener._ordered_log_provider_indices(now=100.0), [0, 1, 2])

    def test_log_provider_cooldown_skips_recent_failure(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a', 'https://rpc.b', 'https://rpc.c'],
                            },
            ws_manager=None,
        )
        listener.log_provider_cooldown_seconds = 30.0

        listener._mark_log_provider_failure(0, now=100.0)

        self.assertEqual(listener._ordered_log_provider_indices(now=110.0), [1, 2])
        self.assertEqual(listener._ordered_log_provider_indices(now=131.0), [0, 1, 2])

    def test_ws_reconnect_cooldown_gate(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        self.assertTrue(listener._should_attempt_ws_reconnect(100.0))
        self.assertFalse(listener._should_attempt_ws_reconnect(100.2))
        self.assertTrue(listener._should_attempt_ws_reconnect(101.2))

    def test_lag_skip_disabled_by_default(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        listener.last_block_processed = 100
        listener._apply_lag_skip_if_needed(1500)

        self.assertEqual(listener.last_block_processed, 100)
        self.assertEqual(listener.blocks_skipped, 0)

    def test_lag_skip_applies_when_configured(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
                'max_lag_skip_blocks': 1000,
                'lag_skip_keep_recent_blocks': 200,
            },
            ws_manager=None,
        )

        listener.last_block_processed = 100
        listener._apply_lag_skip_if_needed(1500)

        self.assertEqual(listener.last_block_processed, 1300)
        self.assertEqual(listener.blocks_skipped, 1200)

    async def test_poll_error_recovery_uses_force_reconnect_for_time_exhausted(self):
        listener_cls = _load_listener_class()

        class _WSManager:
            def __init__(self):
                self.ensure_connection = AsyncMock(return_value=True)

            def get_web3(self):
                return types.SimpleNamespace()

        ws_manager = _WSManager()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=ws_manager,
        )
        listener._should_attempt_ws_reconnect = lambda now: True
        listener._load_contract = lambda: None

        recovered = await listener._attempt_ws_recovery(
            Exception('Timed out waiting for response with request id `18` after 30.0 second(s).')
        )

        self.assertTrue(recovered)
        ws_manager.ensure_connection.assert_awaited_once_with(force_reconnect=True)

    async def test_subscribe_skips_processing_when_lag_skip_catches_up_all(self):
        listener_cls = _load_listener_class()

        class _Eth:
            def __init__(self):
                self._calls = 0

            @property
            def block_number(self):
                self._calls += 1

                async def _value():
                    if self._calls == 1:
                        return 100
                    return 1500

                return _value()

        listener = listener_cls(
            w3=types.SimpleNamespace(eth=_Eth()),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
                'scan_historical': False,
                'max_lag_skip_blocks': 1000,
                'lag_skip_keep_recent_blocks': 0,
            },
            ws_manager=None,
        )
        listener.contract = object()
        listener._process_block_range = AsyncMock(return_value=True)

        class _StopLoop(Exception):
            pass

        sleep_mock = AsyncMock(side_effect=_StopLoop())
        with patch.object(listener.subscribe_to_events.__globals__['asyncio'], 'sleep', sleep_mock):
            with self.assertRaises(_StopLoop):
                await listener.subscribe_to_events()

        listener._process_block_range.assert_not_awaited()

    async def test_process_block_range_failure_returns_false(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        listener._get_logs_via_provider = AsyncMock(side_effect=Exception('non-transient failure'))

        result = await listener._process_block_range(100, 110)
        self.assertFalse(result)

    async def test_process_block_range_tries_all_http_providers_until_success(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a', 'https://rpc.b', 'https://rpc.c'],
                            },
            ws_manager=None,
        )

        transient = Exception('request timeout while get_logs')
        logs = [{'idx': 1}]
        listener._get_logs_via_provider = AsyncMock(side_effect=[transient, transient, (logs, 2)])
        listener._parse_and_process_event = AsyncMock(return_value=None)

        result = await listener._process_block_range(100, 110)

        self.assertTrue(result)
        self.assertEqual(listener._get_logs_via_provider.await_count, 3)
        provider_sequence = [call.args[0] for call in listener._get_logs_via_provider.await_args_list]
        self.assertEqual(provider_sequence, [0, 1, 2])
        self.assertEqual(listener.log_provider_switches, 2)

    async def test_process_block_range_reduces_chunk_on_range_limit(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a'],
                            },
            ws_manager=None,
        )

        range_limit_exc = Exception('Block range limit exceeded')
        listener._get_logs_via_provider = AsyncMock(side_effect=[range_limit_exc, ([], 0), ([], 0)])
        listener._process_logs_in_batches = AsyncMock(return_value=None)

        result = await listener._process_block_range(100, 200)

        self.assertTrue(result)
        requested_ranges = [(call.args[1], call.args[2]) for call in listener._get_logs_via_provider.await_args_list]
        self.assertEqual(requested_ranges, [(100, 200), (100, 150), (151, 200)])

    async def test_process_block_range_yields_between_log_batches(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
                'event_batch_size': 2,
            },
            ws_manager=None,
        )

        logs = [{'idx': i} for i in range(5)]
        listener._get_logs_via_provider = AsyncMock(return_value=(logs, None))
        listener._parse_and_process_event = AsyncMock(return_value=None)

        sleep_mock = AsyncMock()
        with patch.object(listener._process_block_range.__globals__['asyncio'], 'sleep', sleep_mock):
            result = await listener._process_block_range(100, 110)

        self.assertTrue(result)
        self.assertEqual(listener._parse_and_process_event.await_count, 5)
        self.assertEqual(sleep_mock.await_count, 2)
        self.assertEqual([call.args[0] for call in sleep_mock.await_args_list], [0, 0])

    async def test_get_logs_via_provider_clamps_to_provider_head(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a'],
            },
            ws_manager=None,
        )

        class _Eth:
            @property
            def block_number(self):
                async def _value():
                    return 100

                return _value()

            def __init__(self):
                self.get_logs = AsyncMock(return_value=[])

        provider = types.SimpleNamespace(eth=_Eth())
        listener.log_w3_pool = [provider]

        logs, selected_provider = await listener._get_logs_via_provider(0, 95, 110)

        self.assertEqual([], logs)
        self.assertEqual(0, selected_provider)
        provider.eth.get_logs.assert_awaited_once()
        payload = provider.eth.get_logs.await_args.args[0]
        self.assertEqual(95, payload['fromBlock'])
        self.assertEqual(100, payload['toBlock'])

    async def test_get_logs_via_provider_skips_when_head_behind_from_block(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a'],
            },
            ws_manager=None,
        )

        class _Eth:
            @property
            def block_number(self):
                async def _value():
                    return 100

                return _value()

            def __init__(self):
                self.get_logs = AsyncMock(return_value=[])

        provider = types.SimpleNamespace(eth=_Eth())
        listener.log_w3_pool = [provider]

        logs, selected_provider = await listener._get_logs_via_provider(0, 105, 110)

        self.assertEqual([], logs)
        self.assertEqual(0, selected_provider)
        provider.eth.get_logs.assert_not_awaited()

    async def test_parse_known_trade_topic_skips_contract_event_decode(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(to_checksum_address=lambda value: value),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        class _ExplodingContract:
            @property
            def events(self):
                raise AssertionError('contract events decode should be skipped for known topic')

        listener.contract = _ExplodingContract()

        event_log = {
            'topics': [bytes.fromhex('0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19')],
            'data': b'\x00' * 32,
            'transactionHash': b'\x01' * 32,
            'blockNumber': 123,
        }

        await listener._parse_and_process_event(event_log)

    async def test_parse_observed_tokensale_topic_uses_known_fast_path(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(to_checksum_address=lambda value: value),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': [],
                'log_http_weights': [],
            },
            ws_manager=None,
        )

        class _FastPathBypassTouched(BaseException):
            pass

        class _ExplodingContract:
            @property
            def events(self):
                raise _FastPathBypassTouched('known TokenSale topic must not touch contract.events fallback decode path')

        listener.contract = _ExplodingContract()

        event_log = {
            'topics': [bytes.fromhex('c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0')],
            'data': b'\x00' * 32,
            'transactionHash': b'\x02' * 32,
            'blockNumber': 124,
        }

        await listener._parse_and_process_event(event_log)

    async def test_alternate_provider_path_yields_between_log_batches(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a', 'https://rpc.b'],
                'log_http_weights': [1, 1],
                'event_batch_size': 2,
            },
            ws_manager=None,
        )

        transient_error = Exception('request timeout while get_logs')
        logs = [{'idx': i} for i in range(5)]
        listener._get_logs_via_provider = AsyncMock(side_effect=[transient_error, (logs, 1)])
        listener._parse_and_process_event = AsyncMock(return_value=None)

        sleep_mock = AsyncMock()
        with patch.object(listener._process_block_range.__globals__['asyncio'], 'sleep', sleep_mock):
            result = await listener._process_block_range(100, 110)

        self.assertTrue(result)
        self.assertEqual(listener._parse_and_process_event.await_count, 5)
        self.assertEqual(sleep_mock.await_count, 2)
        self.assertEqual([call.args[0] for call in sleep_mock.await_args_list], [0, 0])

    def test_timeout_error_type_is_transient(self):
        listener_cls = _load_listener_class()
        self.assertTrue(listener_cls._is_timeout_or_rate_limit_error(asyncio.TimeoutError()))


if __name__ == '__main__':
    unittest.main()
