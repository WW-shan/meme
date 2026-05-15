import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


def _build_trader_stubs():
    web3_stub = types.ModuleType('web3')

    class _AsyncWeb3:
        def __init__(self, provider=None):
            self.provider = provider

    web3_stub.AsyncWeb3 = _AsyncWeb3

    providers_stub = types.ModuleType('web3.providers')

    class _AsyncHTTPProvider:
        def __init__(self, endpoint_uri, request_kwargs=None):
            self.endpoint_uri = endpoint_uri
            self.request_kwargs = request_kwargs or {}

    providers_stub.AsyncHTTPProvider = _AsyncHTTPProvider

    eth_account_stub = types.ModuleType('eth_account')

    class _Account:
        @staticmethod
        def from_key(_key):
            return types.SimpleNamespace(address='0x0000000000000000000000000000000000000000')

    eth_account_stub.Account = _Account

    config_module_stub = types.ModuleType('config.config')
    config_module_stub.Config = types.SimpleNamespace(FOURMEME_CONTRACT='0x0')

    trading_config_stub = types.ModuleType('config.trading_config')
    trading_config_stub.TradingConfig = types.SimpleNamespace(
        ENABLE_TRADING=False,
        PRIVATE_KEY='',
        ENABLE_BACKTEST=False,
        GAS_MULTIPLIER=1.0,
        BASE_GAS_PRICE_GWEI=0.1,
        MAX_GAS_PRICE_GWEI=1.0,
    )

    return {
        'web3': web3_stub,
        'web3.providers': providers_stub,
        'eth_account': eth_account_stub,
        'config.config': config_module_stub,
        'config.trading_config': trading_config_stub,
    }


def _load_trade_executor_class():
    try:
        module = importlib.import_module('src.core.trader')
        module = importlib.reload(module)
        return module.TradeExecutor
    except ModuleNotFoundError as exc:
        missing = (exc.name or '').split('.')[0]
        if missing not in {'web3', 'eth_account'}:
            raise
        with patch.dict(sys.modules, _build_trader_stubs(), clear=False):
            module = importlib.import_module('src.core.trader')
            module = importlib.reload(module)
            return module.TradeExecutor
    finally:
        sys.modules.pop('src.core.trader', None)


class TestTradeHttpEnv(unittest.TestCase):
    def test_prefers_bsc_trade_http_rpc_over_bsc_http_rpc(self):
        trade_executor_cls = _load_trade_executor_class()
        with patch.dict(
            'os.environ',
            {
                'BSC_TRADE_HTTP_RPC': 'https://trade.primary,https://trade.secondary',
                'BSC_HTTP_RPC': 'https://legacy.primary,https://legacy.secondary',
            },
            clear=False,
        ):
            self.assertEqual(
                trade_executor_cls._get_http_endpoints(),
                ['https://trade.primary', 'https://trade.secondary'],
            )

    def test_falls_back_to_bsc_http_rpc_when_trade_env_empty(self):
        trade_executor_cls = _load_trade_executor_class()
        with patch.dict(
            'os.environ',
            {
                'BSC_TRADE_HTTP_RPC': '',
                'BSC_HTTP_RPC': 'https://legacy.primary,https://legacy.secondary',
            },
            clear=False,
        ):
            self.assertEqual(
                trade_executor_cls._get_http_endpoints(),
                ['https://legacy.primary', 'https://legacy.secondary'],
            )

    def test_create_http_w3_passes_local_proxy_request_kwargs(self):
        trade_executor_cls = _load_trade_executor_class()
        executor = object.__new__(trade_executor_cls)
        executor.HTTP_RPC_ENDPOINTS = ['https://trade.primary']

        class _AsyncHTTPProvider:
            def __init__(self, endpoint_uri, request_kwargs=None):
                self.endpoint_uri = endpoint_uri
                self.request_kwargs = request_kwargs or {}

        class _AsyncWeb3:
            def __init__(self, provider):
                self.provider = provider

        globals_map = trade_executor_cls._create_http_w3.__globals__
        with patch.dict(globals_map, {
            'AsyncHTTPProvider': _AsyncHTTPProvider,
            'AsyncWeb3': _AsyncWeb3,
            'Config': types.SimpleNamespace(
                get_http_request_kwargs=lambda: {'proxy': 'http://127.0.0.1:10808'}
            ),
        }):
            w3 = executor._create_http_w3()

        self.assertEqual(w3.provider.endpoint_uri, 'https://trade.primary')
        self.assertEqual(w3.provider.request_kwargs, {'proxy': 'http://127.0.0.1:10808'})

    def test_helper_retry_delay_matches_buy_confirmation_poll_interval(self):
        trade_executor_cls = _load_trade_executor_class()
        executor = object.__new__(trade_executor_cls)

        helper_calls = []

        class _Call:
            async def call(self):
                helper_calls.append("call")
                if len(helper_calls) == 1:
                    raise RuntimeError("revert")
                return (
                    1,
                    "0x0000000000000000000000000000000000000001",
                    "0x0000000000000000000000000000000000000002",
                    123,
                    0,
                    0,
                    456,
                    0,
                    0,
                    0,
                    0,
                    False,
                )

        helper = MagicMock()
        helper.functions.getTokenInfo.return_value = _Call()
        executor.helper = helper
        executor.w3 = MagicMock()
        executor.w3.eth.get_code = AsyncMock(return_value=b"\x60")

        sleep_mock = AsyncMock()
        globals_map = trade_executor_cls._get_token_info_from_helper.__globals__
        with patch.dict(globals_map, {
            'asyncio': types.SimpleNamespace(sleep=sleep_mock),
        }, clear=False):
            result = importlib.import_module('asyncio').run(executor._get_token_info_from_helper('0xToken'))

        self.assertIsNotNone(result)
        sleep_mock.assert_awaited_once_with(0.25)

    def test_prefetch_next_nonce_warms_local_nonce_without_consuming_it(self):
        trade_executor_cls = _load_trade_executor_class()
        executor = object.__new__(trade_executor_cls)
        executor.wallet_address = "0xWallet"
        executor.local_nonce = None
        executor.nonce_lock = importlib.import_module("asyncio").Lock()
        executor.w3 = MagicMock()
        executor.w3.eth.get_transaction_count = AsyncMock(return_value=7)

        asyncio = importlib.import_module("asyncio")
        asyncio.run(executor.prefetch_next_nonce())
        next_nonce = asyncio.run(executor._get_next_nonce())

        self.assertEqual(next_nonce, 7)
        self.assertEqual(executor.local_nonce, 8)
        executor.w3.eth.get_transaction_count.assert_awaited_once_with("0xWallet")

    def test_ensure_approve_skips_allowance_rpc_when_amount_is_cached(self):
        trade_executor_cls = _load_trade_executor_class()
        executor = object.__new__(trade_executor_cls)
        executor.wallet_address = "0xWallet"
        executor.contract_address = "0xSpender"
        executor._approved_token_amounts = {"0xtoken": 10**18}
        executor.w3 = MagicMock()
        executor.w3.to_checksum_address.return_value = "0xToken"
        token = MagicMock()
        token.functions.allowance.return_value.call = AsyncMock(return_value=10**18)
        executor.w3.eth.contract.return_value = token

        asyncio = importlib.import_module("asyncio")
        asyncio.run(executor._ensure_approve("0xToken", 10**18))

        executor.w3.eth.contract.assert_not_called()

    def test_ensure_approve_caches_allowance_that_is_already_large_enough(self):
        trade_executor_cls = _load_trade_executor_class()
        executor = object.__new__(trade_executor_cls)
        executor.wallet_address = "0xWallet"
        executor.contract_address = "0xSpender"
        executor._approved_token_amounts = {}
        executor.w3 = MagicMock()
        executor.w3.to_checksum_address.return_value = "0xToken"

        token = MagicMock()
        token.functions.allowance.return_value.call = AsyncMock(return_value=10**18)
        executor.w3.eth.contract.return_value = token

        asyncio = importlib.import_module("asyncio")
        asyncio.run(executor._ensure_approve("0xToken", 5 * 10**17))

        self.assertEqual(executor._approved_token_amounts["0xtoken"], 10**18)
        token.functions.approve.assert_not_called()


if __name__ == '__main__':
    unittest.main()
