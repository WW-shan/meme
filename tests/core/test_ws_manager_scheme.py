import asyncio
import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


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


class TestWSConnectionManagerReconnect(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_connection_deduplicates_concurrent_reconnects(self):
        ws_manager = _load_ws_manager_class()
        manager = ws_manager('wss://bsc.publicnode.com')
        manager.is_connected = False
        manager.w3 = None

        class _Eth:
            @property
            def block_number(self):
                async def _value():
                    return 123
                return _value()

        async def _reconnect_once():
            manager.is_connected = True
            manager.w3 = types.SimpleNamespace(eth=_Eth())
            return True

        manager.reconnect = AsyncMock(side_effect=_reconnect_once)

        await asyncio.gather(*(manager.ensure_connection() for _ in range(5)))

        self.assertEqual(manager.reconnect.await_count, 1)

    async def test_force_reconnect_skips_health_probe(self):
        ws_manager = _load_ws_manager_class()
        manager = ws_manager('wss://bsc.publicnode.com')
        manager.is_connected = True

        class _Eth:
            @property
            def block_number(self):
                async def _value():
                    raise AssertionError('health probe should be skipped when force_reconnect=True')
                return _value()

        manager.w3 = types.SimpleNamespace(eth=_Eth())
        manager.reconnect = AsyncMock(return_value=True)

        result = await manager.ensure_connection(force_reconnect=True)

        self.assertTrue(result)
        manager.reconnect.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
