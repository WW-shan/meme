import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch

if 'dotenv' not in sys.modules:
    dotenv_stub = types.ModuleType('dotenv')
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules['dotenv'] = dotenv_stub

import config.config as config_module


class TestRpcConfig(unittest.TestCase):
    def test_get_listener_ws_url_requires_bsc_wss_url(self):
        with patch.dict(os.environ, {'BSC_WSS_URL': ''}, clear=False):
            with self.assertRaises(ValueError):
                config_module.Config.get_listener_ws_url()

        with patch.dict(os.environ, {'BSC_WSS_URL': 'wss://listener.node'}, clear=False):
            self.assertEqual(config_module.Config.get_listener_ws_url(), 'wss://listener.node')

    def test_get_log_http_pool_reads_exact_env_names_and_integer_weights(self):
        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': 'https://rpc.a,https://rpc.b',
            'BSC_LOG_HTTP_WEIGHTS': '3,1',
            'BSC_HTTP_RPC': 'https://legacy.should.not.win',
        }, clear=False):
            endpoints, weights = config_module.Config.get_log_http_pool()
            self.assertEqual(endpoints, ['https://rpc.a', 'https://rpc.b'])
            self.assertEqual(weights, [3, 1])

    def test_get_log_http_pool_fallback_is_48club_plus_first_legacy_with_default_weights(self):
        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': '',
            'BSC_LOG_HTTP_WEIGHTS': '',
            'BSC_HTTP_RPC': 'https://legacy.a,https://legacy.b',
        }, clear=False):
            endpoints, weights = config_module.Config.get_log_http_pool()
            self.assertEqual(endpoints, ['https://four.rpc.48.club', 'https://legacy.a'])
            self.assertEqual(weights, [3, 1])

    def test_get_log_http_pool_single_endpoint_default_weight(self):
        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': 'https://rpc.only',
            'BSC_LOG_HTTP_WEIGHTS': '',
            'BSC_HTTP_RPC': 'https://legacy.a',
        }, clear=False):
            endpoints, weights = config_module.Config.get_log_http_pool()
            self.assertEqual(endpoints, ['https://rpc.only'])
            self.assertEqual(weights, [1])

    def test_get_log_http_pool_rejects_weight_alignment_and_non_positive(self):
        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': 'https://rpc.a,https://rpc.b',
            'BSC_LOG_HTTP_WEIGHTS': '1',
        }, clear=False):
            with self.assertRaises(ValueError):
                config_module.Config.get_log_http_pool()

        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': 'https://rpc.a,https://rpc.b',
            'BSC_LOG_HTTP_WEIGHTS': '1,0',
        }, clear=False):
            with self.assertRaises(ValueError):
                config_module.Config.get_log_http_pool()

    def test_get_log_http_pool_rejects_empty_effective_endpoints(self):
        with patch.dict(os.environ, {
            'BSC_LOG_HTTP_ENDPOINTS': ' , ',
            'BSC_LOG_HTTP_WEIGHTS': '',
            'BSC_HTTP_RPC': '',
        }, clear=False):
            with self.assertRaises(ValueError):
                config_module.Config.get_log_http_pool()

    def test_get_trade_http_rpc_prefers_bsc_trade_http_rpc_then_legacy_then_binance_default(self):
        with patch.dict(os.environ, {
            'BSC_TRADE_HTTP_RPC': 'https://trade.primary,https://trade.secondary',
            'BSC_HTTP_RPC': 'https://legacy.trade',
        }, clear=False):
            self.assertEqual(config_module.Config.get_trade_http_rpc(), 'https://trade.primary')

        with patch.dict(os.environ, {
            'BSC_TRADE_HTTP_RPC': '',
            'BSC_HTTP_RPC': 'https://legacy.trade,https://legacy.trade2',
        }, clear=False):
            self.assertEqual(config_module.Config.get_trade_http_rpc(), 'https://legacy.trade')

        with patch.dict(os.environ, {
            'BSC_TRADE_HTTP_RPC': '',
            'BSC_HTTP_RPC': '',
        }, clear=False):
            self.assertEqual(config_module.Config.get_trade_http_rpc(), 'https://bsc-dataseed.binance.org')

    def test_validate_rpc_config_enforces_ws_scheme_for_listener(self):
        with patch.dict(os.environ, {
            'BSC_WSS_URL': 'https://not-ws.allowed',
            'BSC_LOG_HTTP_ENDPOINTS': 'https://logs.a',
            'BSC_LOG_HTTP_WEIGHTS': '1',
            'BSC_TRADE_HTTP_RPC': 'https://trade.valid',
        }, clear=False):
            with self.assertRaises(ValueError):
                config_module.Config.validate_rpc_config()

    def test_validate_rpc_config_passes_with_valid_values(self):
        with patch.dict(os.environ, {
            'BSC_WSS_URL': 'wss://listener.valid',
            'BSC_LOG_HTTP_ENDPOINTS': 'https://logs.a,https://logs.b',
            'BSC_LOG_HTTP_WEIGHTS': '3,1',
            'BSC_TRADE_HTTP_RPC': 'https://trade.valid',
        }, clear=False):
            config_module.Config.validate_rpc_config()

    def test_scan_historical_default_is_false(self):
        with patch.dict(os.environ, {'SCAN_HISTORICAL': ''}, clear=False):
            reloaded = importlib.reload(config_module)
            self.assertFalse(reloaded.Config.SCAN_HISTORICAL)
            importlib.reload(reloaded)


if __name__ == '__main__':
    unittest.main()
