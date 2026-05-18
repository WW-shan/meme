import unittest
import json
from pathlib import Path
from unittest.mock import patch

from config.trading_config import TradingConfig


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
            'MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate',
            'DATASET_LABEL_ENTRY_FIXED_COST_BNB=0',
            'DATASET_LABEL_EXIT_FIXED_COST_BNB=0',
            'DATASET_LABEL_FIXED_STAKE_BNB=',
            'DATASET_LABEL_ENTRY_PRICE_PROTECTION_PCT=',
            'MIN_ENTRY_VOLUME_30S=1.5',
            'MIN_ENTRY_PRICE_VOLATILITY=0.1',
            'BUY_NEAR_THRESHOLD_MIN_PROB=',
            'BUY_NEAR_MIN_PRED_RETURN=',
            'BUY_NEAR_MIN_ENTRY_VOLUME_30S=',
            'BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY=',
            'BUY_NEAR_MIN_AGE_SECONDS=',
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
        self.assertEqual(
            float(self._env_value(content, 'MIN_ENTRY_PRICE_VOLATILITY')),
            evaluation['min_entry_price_volatility'],
        )

    def test_selected_model_manifest_runtime_replay_matches_selected_evaluation(self):
        root = Path(__file__).resolve().parents[2]
        env_example_path = root / '.env.example'
        content = env_example_path.read_text(encoding='utf-8')

        model_dir = root / self._env_value(content, 'MODEL_DIR')
        manifest = json.loads((model_dir / 'hybrid_manifest.json').read_text(encoding='utf-8'))
        evaluation = manifest['evaluation']
        runtime_replay = evaluation['runtime_replay']

        self.assertEqual(runtime_replay['total_trades'], evaluation['total_trades'])
        self.assertEqual(runtime_replay['net_profit_bnb'], evaluation['net_profit_bnb'])
        self.assertEqual(runtime_replay['net_return_pct'], evaluation['net_return_pct'])
        self.assertEqual(runtime_replay['buy_near_threshold_min_prob'], evaluation['buy_near_threshold_min_prob'])
        self.assertEqual(runtime_replay['buy_near_min_pred_return'], evaluation['buy_near_min_pred_return'])
        self.assertEqual(runtime_replay['buy_near_min_entry_volume_30s'], evaluation['buy_near_min_entry_volume_30s'])
        self.assertEqual(
            runtime_replay['buy_near_min_entry_price_volatility'],
            evaluation['buy_near_min_entry_price_volatility'],
        )

    def test_selected_model_manifest_near_gate_matches_validation_rule(self):
        root = Path(__file__).resolve().parents[2]
        env_example_path = root / '.env.example'
        content = env_example_path.read_text(encoding='utf-8')

        model_dir = root / self._env_value(content, 'MODEL_DIR')
        manifest = json.loads((model_dir / 'hybrid_manifest.json').read_text(encoding='utf-8'))
        selected = manifest['selected_runtime_params']
        rule = manifest['validation_evaluation']['top_candidate']['rule']

        self.assertEqual(rule['near_prob_min'], selected['buy_near_threshold_min_prob'])
        self.assertEqual(rule['near_score_min'], selected['buy_near_min_pred_return'])
        self.assertEqual(rule['near_volume_min'], selected['buy_near_min_entry_volume_30s'])
        self.assertEqual(rule['near_price_vol_min'], selected['buy_near_min_entry_price_volatility'])
        self.assertEqual(rule['age_min'], selected['buy_near_min_age_seconds'])
        self.assertEqual(rule['age_max'], selected['max_entry_age_seconds'])

    def test_trading_config_exposes_near_threshold_gate_defaults(self):
        self.assertIsNone(TradingConfig.BUY_NEAR_THRESHOLD_MIN_PROB)
        self.assertIsNone(TradingConfig.BUY_NEAR_MIN_PRED_RETURN)
        self.assertIsNone(TradingConfig.BUY_NEAR_MIN_ENTRY_VOLUME_30S)
        self.assertIsNone(TradingConfig.BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY)
        self.assertIsNone(TradingConfig.BUY_NEAR_MIN_AGE_SECONDS)

    def test_trading_config_validates_near_threshold_gate_bounds(self):
        invalid_cases = [
            ('BUY_NEAR_THRESHOLD_MIN_PROB', 0.0),
            ('BUY_NEAR_THRESHOLD_MIN_PROB', 1.01),
            ('BUY_NEAR_THRESHOLD_MIN_PROB', float('nan')),
            ('BUY_NEAR_THRESHOLD_MIN_PROB', float('inf')),
            ('BUY_NEAR_MIN_PRED_RETURN', -0.01),
            ('BUY_NEAR_MIN_PRED_RETURN', float('nan')),
            ('BUY_NEAR_MIN_PRED_RETURN', float('inf')),
            ('BUY_NEAR_MIN_ENTRY_VOLUME_30S', -0.01),
            ('BUY_NEAR_MIN_ENTRY_VOLUME_30S', float('nan')),
            ('BUY_NEAR_MIN_ENTRY_VOLUME_30S', float('inf')),
            ('BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY', -0.01),
            ('BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY', float('nan')),
            ('BUY_NEAR_MIN_ENTRY_PRICE_VOLATILITY', float('inf')),
            ('BUY_NEAR_MIN_AGE_SECONDS', -0.01),
            ('BUY_NEAR_MIN_AGE_SECONDS', float('nan')),
            ('BUY_NEAR_MIN_AGE_SECONDS', float('inf')),
        ]

        for attr, value in invalid_cases:
            with self.subTest(attr=attr, value=value), patch.object(TradingConfig, attr, value, create=True):
                with self.assertRaisesRegex(ValueError, attr):
                    TradingConfig.validate()


if __name__ == '__main__':
    unittest.main()
