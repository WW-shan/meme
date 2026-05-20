import unittest

import numpy as np

from src.pipeline.train_hybrid import _run_eval_replay, run_ab_evaluation


class _AlwaysBuyModel:
    def predict_proba(self, X):
        return np.array([[0.01, 0.99] for _ in range(len(X))], dtype=float)


def _sample(token, sample_time, price, *, age=9, volume_30s=3.2, price_volatility=0.27):
    return {
        "features": {
            "current_price": price,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "total_buy_volume": 1.0,
            "total_sell_volume": 0.0,
        },
        "label": {},
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - age,
        },
    }


def _episode(token="0xpathstate", **overrides):
    first = _sample(token, 100, 1.0, **overrides)
    second = _sample(token, 101, 1.05, **overrides)
    third = _sample(token, 103, 1.10, **overrides)
    return [first, second, third]


def _base_replay_kwargs(**overrides):
    kwargs = {
        "episodes": [_episode()],
        "buy_model": None,
        "threshold": 0.98,
        "sell_policy": None,
        "stop_loss": -0.50,
        "position_fraction": 0.1,
        "max_position_fraction": 0.1,
        "include_trade_log": True,
        "one_entry_per_token": True,
        "max_hold_seconds": 2,
        "initial_equity_bnb": 1.0,
        "max_open_positions": 8,
        "entry_ranking_mode": "entry_value",
        "min_entry_score": 35.0,
        "min_entry_volume_30s": 1.5,
        "min_entry_price_volatility": 0.10,
        "buy_probabilities_by_episode": [{0: 0.989}],
        "entry_scores_by_episode": [{0: 40.0}],
    }
    kwargs.update(overrides)
    return kwargs


class TestPathStateMetaGateReplay(unittest.TestCase):
    def test_path_state_meta_gate_default_off_preserves_primary_entry(self):
        result = _run_eval_replay(**_base_replay_kwargs())

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["path_state_meta_gate_signal_count"], 0)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 0)
        self.assertEqual(result["path_state_meta_gate_reject_count"], 0)

    def test_path_state_meta_gate_rejects_low_scored_primary_candidate(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                path_state_scores_by_episode=[{0: 0.25}],
                buy_path_state_meta_gate_min_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["path_state_meta_gate_signal_count"], 1)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 0)
        self.assertEqual(result["path_state_meta_gate_reject_count"], 1)

    def test_path_state_meta_gate_allows_high_scored_primary_candidate(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                path_state_scores_by_episode=[{0: 0.75, "__episode_meta__": {
                    "token": "0xpathstate",
                    "sample_count": 3,
                    "start_time": 100,
                    "end_time": 103,
                }}],
                buy_path_state_meta_gate_min_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["path_state_meta_gate_signal_count"], 1)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 1)
        self.assertEqual(result["path_state_meta_gate_reject_count"], 0)

    def test_path_state_meta_gate_accepts_json_roundtripped_numeric_keys(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                path_state_scores_by_episode=[{"0": 0.75}],
                buy_path_state_meta_gate_min_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 1)
        self.assertEqual(result["path_state_meta_gate_reject_count"], 0)

    def test_path_state_meta_gate_rejects_missing_score_when_enabled(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                path_state_scores_by_episode=[{}],
                buy_path_state_meta_gate_min_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["path_state_meta_gate_signal_count"], 1)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 0)
        self.assertEqual(result["path_state_meta_gate_reject_count"], 1)

    def test_run_ab_evaluation_requires_path_state_score_map_metadata_when_gate_enabled(self):
        config = {
            "eval_samples": _episode("0xA"),
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "initial_equity_bnb": 1.0,
            "max_open_positions": 8,
            "one_entry_per_token": True,
            "max_hold_seconds": 2,
            "path_state_scores_by_episode": [{0: 0.75}],
            "buy_path_state_meta_gate_min_score": 0.5,
            "skip_all_in_replay": True,
        }

        with self.assertRaisesRegex(ValueError, "path_state_scores_by_episode.*metadata"):
            run_ab_evaluation(
                config,
                {"model": _AlwaysBuyModel(), "threshold": 0.98},
                {"model": object(), "total_timesteps": 0},
                {"bc_samples": 0},
            )

    def test_run_ab_evaluation_propagates_path_state_scores_to_stress_replay(self):
        config = {
            "eval_samples": _episode(),
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "initial_equity_bnb": 1.0,
            "max_open_positions": 8,
            "one_entry_per_token": True,
            "max_hold_seconds": 2,
            "path_state_scores_by_episode": [{0: 0.75, "__episode_meta__": {
                "token": "0xpathstate",
                "sample_count": 3,
                "start_time": 100,
                "end_time": 103,
            }}],
            "buy_path_state_meta_gate_min_score": 0.5,
            "stress_replay_scenarios": [{"name": "same_execution"}],
            "skip_all_in_replay": True,
        }

        result = run_ab_evaluation(
            config,
            {"model": _AlwaysBuyModel(), "threshold": 0.98},
            {"model": object(), "total_timesteps": 0},
            {"bc_samples": 0},
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["path_state_meta_gate_entry_count"], 1)
        self.assertEqual(len(result["stress_replay"]), 1)
        self.assertEqual(result["stress_replay"][0]["total_trades"], 1)
        self.assertEqual(result["stress_replay"][0]["path_state_meta_gate_entry_count"], 1)

    def test_run_ab_evaluation_rejects_path_state_score_map_count_mismatch_when_gate_enabled(self):
        config = {
            "eval_samples": [*_episode("0xA"), *_episode("0xB")],
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "initial_equity_bnb": 1.0,
            "max_open_positions": 8,
            "one_entry_per_token": True,
            "max_hold_seconds": 2,
            "path_state_scores_by_episode": [{0: 0.75}],
            "buy_path_state_meta_gate_min_score": 0.5,
            "skip_all_in_replay": True,
        }

        with self.assertRaisesRegex(ValueError, "path_state_scores_by_episode.*2.*1"):
            run_ab_evaluation(
                config,
                {"model": _AlwaysBuyModel(), "threshold": 0.98},
                {"model": object(), "total_timesteps": 0},
                {"bc_samples": 0},
            )

    def test_run_ab_evaluation_rejects_path_state_score_map_metadata_mismatch_when_gate_enabled(self):
        config = {
            "eval_samples": _episode("0xA"),
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "initial_equity_bnb": 1.0,
            "max_open_positions": 8,
            "one_entry_per_token": True,
            "max_hold_seconds": 2,
            "path_state_scores_by_episode": [{
                "__episode_meta__": {"token": "0xnot_a", "sample_count": 3, "start_time": 100, "end_time": 103},
                0: 0.75,
            }],
            "buy_path_state_meta_gate_min_score": 0.5,
            "skip_all_in_replay": True,
        }

        with self.assertRaisesRegex(ValueError, "path_state_scores_by_episode.*metadata"):
            run_ab_evaluation(
                config,
                {"model": _AlwaysBuyModel(), "threshold": 0.98},
                {"model": object(), "total_timesteps": 0},
                {"bc_samples": 0},
            )


if __name__ == "__main__":
    unittest.main()
