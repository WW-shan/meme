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

    def test_weighted_schedule_sequence_3_to_1(self):
        listener_cls = _load_listener_class()
        listener = listener_cls(
            w3=types.SimpleNamespace(),
            config={
                'contract_address': '0x1',
                'contract_abi': [],
                'log_http_endpoints': ['https://rpc.a', 'https://rpc.b'],
                'log_http_weights': [3, 1],
            },
            ws_manager=None,
        )

        listener.log_schedule = listener._build_log_schedule(2, [3, 1])
        listener.log_schedule_cursor = 0

        sequence = [listener._next_log_provider_index() for _ in range(8)]
        self.assertEqual(sequence, [0, 0, 0, 1, 0, 0, 0, 1])

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


if __name__ == '__main__':
    unittest.main()
