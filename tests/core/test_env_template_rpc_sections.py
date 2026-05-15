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
            'LISTENER_POLL_INTERVAL_SECONDS=0.25',
            'MAX_CONCURRENT_POSITIONS=0',
            'POSITION_SIZE=0.10',
            'FIXED_STAKE_BNB=',
            'MAX_ENTRY_SIZE_BNB=0.1',
            'BUY_CONFIRM_POLL_INTERVAL_SECONDS=0.25',
            'BUY_CONFIRM_TIMEOUT_SECONDS=120',
            'BUY_USE_LIFECYCLE_FAST_STATUS=true',
            'BUY_FAST_STATUS_MAX_STALENESS_SECONDS=3',
            'BUY_FAST_STATUS_MAX_CHAIN_LAG_SECONDS=8',
            'TX_RECEIPT_POLL_LATENCY_SECONDS=0.25',
            'MODEL_DIR=data/models/20260515_v46_live_selected_thr09698',
            'DATASET_LABEL_ENTRY_FIXED_COST_BNB=0',
            'DATASET_LABEL_EXIT_FIXED_COST_BNB=0',
            'DATASET_LABEL_FIXED_STAKE_BNB=',
            'DATASET_LABEL_ENTRY_PRICE_PROTECTION_PCT=',
        ]

        for entry in required_entries:
            self.assertIn(entry, content)

        self.assertNotIn('BSC_LOG_HTTP_WEIGHTS=', content)
        self.assertIn('Deprecated legacy combined HTTP RPC', content)


if __name__ == '__main__':
    unittest.main()
