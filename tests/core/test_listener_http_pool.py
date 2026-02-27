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


if __name__ == '__main__':
    unittest.main()
