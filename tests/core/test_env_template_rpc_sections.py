import unittest
from pathlib import Path


class TestEnvTemplateRpcSections(unittest.TestCase):
    def test_env_example_contains_required_rpc_role_keys(self):
        env_example_path = Path(__file__).resolve().parents[2] / '.env.example'
        content = env_example_path.read_text(encoding='utf-8')

        required_entries = [
            'LISTENER_MODE=hybrid',
            'BSC_WSS_URL=',
            'BSC_LOG_HTTP_ENDPOINTS=',
            'BSC_TRADE_HTTP_RPC=',
            'BSC_HTTP_RPC=',
            'SCAN_HISTORICAL=false',
        ]

        for entry in required_entries:
            self.assertIn(entry, content)

        self.assertNotIn('BSC_LOG_HTTP_WEIGHTS=', content)
        self.assertIn('Deprecated legacy combined HTTP RPC', content)


if __name__ == '__main__':
    unittest.main()
