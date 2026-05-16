import unittest
import json
from pathlib import Path


class TestEnvTemplateRpcSections(unittest.TestCase):
    def _env_value(self, content: str, key: str) -> str:
        for raw_line in content.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith('#') or '=' not in stripped:
                continue
            found_key, raw_value = stripped.split('=', 1)
            if found_key.strip() == key:
                return raw_value.split('#', 1)[0].strip()
        self.fail(f'Missing env key: {key}')

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
            'MAX_CONCURRENT_POSITIONS=8',
            'POSITION_SIZE=0.10',
            'FIXED_STAKE_BNB=',
            'MAX_ENTRY_SIZE_BNB=',
            'BUY_CONFIRM_POLL_INTERVAL_SECONDS=0.25',
            'BUY_CONFIRM_TIMEOUT_SECONDS=120',
            'BUY_USE_LIFECYCLE_FAST_STATUS=true',
            'BUY_FAST_STATUS_MAX_STALENESS_SECONDS=3',
            'BUY_FAST_STATUS_MAX_CHAIN_LAG_SECONDS=8',
            'TX_RECEIPT_POLL_LATENCY_SECONDS=0.25',
            'MODEL_DIR=data/models/20260516_v67_v65_thr9715_tr35_12',
            'DATASET_LABEL_ENTRY_FIXED_COST_BNB=0',
            'DATASET_LABEL_EXIT_FIXED_COST_BNB=0',
            'DATASET_LABEL_FIXED_STAKE_BNB=',
            'DATASET_LABEL_ENTRY_PRICE_PROTECTION_PCT=',
            'MIN_ENTRY_VOLUME_30S=1.5',
            'MIN_ENTRY_PRICE_VOLATILITY=0',
        ]

        for entry in required_entries:
            self.assertIn(entry, content)

        self.assertNotIn('BSC_LOG_HTTP_WEIGHTS=', content)
        self.assertIn('Deprecated legacy combined HTTP RPC', content)

    def test_env_example_selected_model_entry_guards_match_manifest(self):
        root = Path(__file__).resolve().parents[2]
        env_example_path = root / '.env.example'
        content = env_example_path.read_text(encoding='utf-8')

        model_dir = root / self._env_value(content, 'MODEL_DIR')
        manifest = json.loads((model_dir / 'hybrid_manifest.json').read_text(encoding='utf-8'))
        evaluation = manifest['evaluation']

        self.assertEqual(float(self._env_value(content, 'POSITION_SIZE')), evaluation['position_fraction'])
        self.assertEqual(int(self._env_value(content, 'MAX_CONCURRENT_POSITIONS')), evaluation['max_open_positions'])
        self.assertEqual(float(self._env_value(content, 'MIN_ENTRY_VOLUME_30S')), evaluation['min_entry_volume_30s'])


if __name__ == '__main__':
    unittest.main()
