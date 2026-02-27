import importlib
import sys
import types
import unittest
from unittest.mock import patch


def _build_web3_stubs():
    web3_stub = types.ModuleType('web3')
    web3_stub.AsyncWeb3 = object

    providers_stub = types.ModuleType('web3.providers')

    class _WebSocketProvider:
        def __init__(self, *args, **kwargs):
            pass

    providers_stub.WebSocketProvider = _WebSocketProvider

    middleware_stub = types.ModuleType('web3.middleware')
    middleware_stub.ExtraDataToPOAMiddleware = object

    return {
        'web3': web3_stub,
        'web3.providers': providers_stub,
        'web3.middleware': middleware_stub,
    }


def _load_ws_manager_class():
    try:
        module = importlib.import_module('src.core.ws_manager')
        module = importlib.reload(module)
        return module.WSConnectionManager
    except ModuleNotFoundError as exc:
        missing = (exc.name or '').split('.')[0]
        if missing != 'web3':
            raise
        with patch.dict(sys.modules, _build_web3_stubs(), clear=False):
            module = importlib.import_module('src.core.ws_manager')
            module = importlib.reload(module)
            return module.WSConnectionManager
    finally:
        sys.modules.pop('src.core.ws_manager', None)


class TestWSConnectionManagerScheme(unittest.TestCase):
    def test_rejects_https_url(self):
        ws_manager = _load_ws_manager_class()
        with self.assertRaises(ValueError):
            ws_manager('https://rpc.ankr.com/bsc')

    def test_accepts_wss_url(self):
        ws_manager = _load_ws_manager_class()
        manager = ws_manager('wss://bsc.publicnode.com')
        self.assertEqual(manager.ws_url, 'wss://bsc.publicnode.com')


if __name__ == '__main__':
    unittest.main()
