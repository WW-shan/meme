import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _SellNonePolicy:
    def predict(self, obs, deterministic=True):
        return 0, None


class _BuyModel:
    def predict_proba(self, rows):
        return [[0.01, 0.99] for _row in rows]


class _EntryValueModel:
    def predict(self, rows):
        return [45.0 for _row in rows]


def _sample(
    token="0xflow",
    sample_time=100,
    price=1.0,
    volume_30s=1.0,
    price_volatility=0.10,
    create_timestamp=80,
):
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }


class TestFlowActivationReplay(unittest.TestCase):
    def test_flow_activation_gate_allows_ramping_primary_candidate(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=0.8, price_volatility=0.08),
            _sample(sample_time=110, price=1.0, volume_30s=2.4, price_volatility=0.14),
            _sample(sample_time=120, price=1.35, volume_30s=2.8, price_volatility=0.16),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{1: 0.99}],
            entry_scores_by_episode=[{0: 36.0, 1: 46.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_flow_activation_min_prob=0.98,
            buy_flow_activation_min_pred_return=35.0,
            buy_flow_activation_max_age_seconds=60,
            buy_flow_activation_lookback_seconds=30,
            buy_flow_activation_min_volume_ramp_ratio=2.0,
            buy_flow_activation_min_volume_ramp_delta=1.0,
            buy_flow_activation_min_pred_return_delta=5.0,
            buy_flow_activation_min_price_volatility_delta=0.04,
            buy_flow_activation_min_current_volume_30s=1.5,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["flow_activation_signal_count"], 1)
        self.assertEqual(result["flow_activation_entry_count"], 1)
        self.assertEqual(result["flow_activation_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)
        self.assertTrue(result["trade_log"][0]["flow_activation_used"])

    def test_flow_activation_gate_rejects_flat_volume_candidate(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=1.5, price_volatility=0.10),
            _sample(sample_time=110, price=1.0, volume_30s=1.6, price_volatility=0.11),
            _sample(sample_time=120, price=0.82, volume_30s=1.4, price_volatility=0.09),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{1: 0.99}],
            entry_scores_by_episode=[{0: 36.0, 1: 40.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_flow_activation_min_prob=0.98,
            buy_flow_activation_min_pred_return=35.0,
            buy_flow_activation_max_age_seconds=60,
            buy_flow_activation_lookback_seconds=30,
            buy_flow_activation_min_volume_ramp_ratio=2.0,
            buy_flow_activation_min_volume_ramp_delta=1.0,
            buy_flow_activation_min_pred_return_delta=5.0,
            buy_flow_activation_min_price_volatility_delta=0.04,
            buy_flow_activation_min_current_volume_30s=1.5,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["flow_activation_signal_count"], 1)
        self.assertEqual(result["flow_activation_entry_count"], 0)
        self.assertEqual(result["flow_activation_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])

    def test_dead_flow_exit_closes_position_before_time_exit(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=2.0, price_volatility=0.12),
            _sample(sample_time=160, price=1.03, volume_30s=0.1, price_volatility=0.02),
            _sample(sample_time=660, price=1.02, volume_30s=0.0, price_volatility=0.01),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 45.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_flow_exit_min_hold_seconds=60,
            buy_dead_flow_exit_max_mfe_pct=0.05,
            max_hold_seconds=560,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_flow_exit_count"], 1)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "DEAD_FLOW_TIME_EXIT")

    def test_dead_flow_exit_count_requires_successful_exit_execution(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=2.0, price_volatility=0.12),
            _sample(sample_time=160, price=1.03, volume_30s=0.1, price_volatility=0.02),
            _sample(sample_time=660, price=1.02, volume_30s=0.0, price_volatility=0.01),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 45.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_flow_exit_min_hold_seconds=60,
            buy_dead_flow_exit_max_mfe_pct=0.05,
            exit_execution_failure_rate=1.0,
            max_hold_seconds=560,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_flow_exit_count"], 0)
        self.assertGreaterEqual(result["exit_execution_failure_count"], 1)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "REPLAY_END")

    def test_delayed_dead_flow_exit_counts_after_successful_fill(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=2.0, price_volatility=0.12),
            _sample(sample_time=160, price=1.03, volume_30s=0.1, price_volatility=0.02),
            _sample(sample_time=170, price=1.02, volume_30s=0.1, price_volatility=0.02),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 45.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_flow_exit_min_hold_seconds=60,
            buy_dead_flow_exit_max_mfe_pct=0.05,
            exit_delay_seconds=1,
            max_hold_seconds=560,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_flow_exit_count"], 1)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "DEAD_FLOW_TIME_EXIT")

    def test_run_ab_evaluation_passes_flow_activation_config_to_runtime_replay(self):
        m = _load_module()
        captured = []

        def fake_replay(*args, **kwargs):
            captured.append(kwargs)
            return {
                "total_trades": 1,
                "entry_count": 1,
                "entry_rate": 1.0,
                "win_rate": 1.0,
                "net_return_pct": 10.0,
                "max_drawdown_pct": 0.0,
                "sortino_ratio": 0.0,
                "final_equity_bnb": 1.1,
                "net_profit_bnb": 0.1,
                "account_multiple": 1.1,
                "flow_activation_signal_count": 1,
                "flow_activation_entry_count": 1,
                "flow_activation_reject_count": 0,
                "dead_flow_exit_count": 0,
            }

        config = {
            "eval_samples": [
                _sample(sample_time=100, price=1.0, volume_30s=1.0, price_volatility=0.10),
                _sample(sample_time=110, price=1.1, volume_30s=2.0, price_volatility=0.16),
            ],
            "skip_all_in_replay": True,
            "buy_flow_activation_min_prob": 0.98,
            "buy_flow_activation_min_pred_return": 35.0,
            "buy_flow_activation_max_age_seconds": 60.0,
            "buy_flow_activation_lookback_seconds": 30.0,
            "buy_flow_activation_min_volume_ramp_ratio": 2.0,
            "buy_flow_activation_min_volume_ramp_delta": 1.0,
            "buy_flow_activation_min_pred_return_delta": 5.0,
            "buy_flow_activation_min_price_volatility_delta": 0.04,
            "buy_flow_activation_min_current_volume_30s": 1.5,
            "buy_dead_flow_exit_min_hold_seconds": 60.0,
            "buy_dead_flow_exit_max_mfe_pct": 0.05,
        }
        buy_artifact = {
            "model": _BuyModel(),
            "threshold": 0.98,
            "feature_names": [
                "current_price",
                "holder_count",
                "volume_30s",
                "price_volatility",
            ],
            "entry_value_model": {"model": _EntryValueModel()},
        }

        with patch.object(m, "_run_eval_replay", side_effect=fake_replay):
            result = m.run_ab_evaluation(config, buy_artifact, {"model": _SellNonePolicy()}, {})

        self.assertEqual(result["flow_activation_entry_count"], 1)
        runtime_kwargs = captured[0]
        for key in (
            "buy_flow_activation_min_prob",
            "buy_flow_activation_min_pred_return",
            "buy_flow_activation_max_age_seconds",
            "buy_flow_activation_lookback_seconds",
            "buy_flow_activation_min_volume_ramp_ratio",
            "buy_flow_activation_min_volume_ramp_delta",
            "buy_flow_activation_min_pred_return_delta",
            "buy_flow_activation_min_price_volatility_delta",
            "buy_flow_activation_min_current_volume_30s",
            "buy_dead_flow_exit_min_hold_seconds",
            "buy_dead_flow_exit_max_mfe_pct",
        ):
            self.assertEqual(runtime_kwargs[key], config[key])
