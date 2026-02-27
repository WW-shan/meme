import importlib
import sys
import types
import unittest
from unittest.mock import patch


def _build_trader_stubs():
    web3_stub = types.ModuleType('web3')

    class _AsyncWeb3:
        def __init__(self, provider=None):
            self.provider = provider

    web3_stub.AsyncWeb3 = _AsyncWeb3

    providers_stub = types.ModuleType('web3.providers')

    class _AsyncHTTPProvider:
        def __init__(self, endpoint_uri):
            self.endpoint_uri = endpoint_uri

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


if __name__ == '__main__':
    unittest.main()
