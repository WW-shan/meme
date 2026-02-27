import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

import numpy as np
import pandas as pd


def _load_worktree_trainer():
    trainer_path = Path(__file__).resolve().parents[2] / "src" / "model" / "trainer.py"
    spec = importlib.util.spec_from_file_location("worktree_trainer", trainer_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.MemeModelTrainer


MemeModelTrainer = _load_worktree_trainer()


class _FakeClf:
    def __init__(self, probs_by_feature):
        self._probs_by_feature = probs_by_feature

    def predict_proba(self, X):
        vals = X.iloc[:, 0].astype(float).to_numpy()
        probs = np.array([self._probs_by_feature.get(v, 0.0) for v in vals], dtype=float)
        return np.column_stack([1.0 - probs, probs])


class _FakeReg:
    def __init__(self, pred_by_feature):
        self._pred_by_feature = pred_by_feature

    def predict(self, X):
        vals = X.iloc[:, 0].astype(float).to_numpy()
        return np.array([self._pred_by_feature.get(v, 0.0) for v in vals], dtype=float)


class TestTrainerBacktestGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        data_dir = Path(self.tmp.name) / "datasets"
        model_dir = Path(self.tmp.name) / "models"
        data_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)
        self.trainer = MemeModelTrainer(data_dir=str(data_dir), model_dir=str(model_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def test_backtest_gate_trades_once_per_token(self):
        df = pd.DataFrame(
            [
                {"f1": 1.0, "token_address": "A", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 2.0, "token_address": "A", "sample_time": 2, "time_since_launch": 20, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 3.0, "token_address": "B", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 4.0, "token_address": "C", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90, 2.0: 0.95, 3.0: 0.92, 4.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 90.0, 3.0: 80.0, 4.0: 40.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(model_dir=model_dir, test_df=df, feature_cols=["f1"], threshold=0.8)

        self.assertEqual(result["trades"], 2)

    def test_backtest_gate_uses_is_moon_200_and_final_return_fallback(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 1,
                    "min_return_pct": -10.0,
                    "max_return_pct": 200.0,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(model_dir=model_dir, test_df=df, feature_cols=["f1"], threshold=0.8)

        self.assertGreater(result["return_pct"], 0.0)

    def test_backtest_gate_uses_configurable_first_take_profit_hit(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["first_take_profit"] = 1.0
        thresholds["backtest"]["first_exit_ratio"] = 0.5
        thresholds["backtest"]["drawdown_stop"] = 0.20

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        expected_actual_return = 0.5 * 1.0 + 0.5 * (((1.0 + 1.2) * (1.0 - 0.20)) - 1.0)
        size = 0.1
        effective_entry = size / 1.2
        gross_value = effective_entry * (1 + expected_actual_return)
        net_value = gross_value * 0.95 * 0.98
        expected_profit = net_value - size
        expected_return_pct = expected_profit * 100

        self.assertAlmostEqual(result["return_pct"], expected_return_pct, places=6)

    def test_backtest_gate_clamps_exit_parameters(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["first_take_profit"] = 1.0
        thresholds["backtest"]["first_exit_ratio"] = 1.5
        thresholds["backtest"]["drawdown_stop"] = -0.2

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        expected_actual_return = 1.0 * 1.0 + 0.0 * 0.2
        size = 0.1
        effective_entry = size / 1.2
        gross_value = effective_entry * (1 + expected_actual_return)
        net_value = gross_value * 0.95 * 0.98
        expected_profit = net_value - size
        expected_return_pct = expected_profit * 100

        self.assertAlmostEqual(result["return_pct"], expected_return_pct, places=6)

    def test_backtest_gate_applies_activity_filters(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 30,
                    "unique_buyers": 2,
                    "total_buys": 8,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                },
                {
                    "f1": 2.0,
                    "token_address": "B",
                    "sample_time": 1,
                    "time_since_launch": 30,
                    "unique_buyers": 5,
                    "total_buys": 4,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                },
                {
                    "f1": 3.0,
                    "token_address": "C",
                    "sample_time": 1,
                    "time_since_launch": 30,
                    "unique_buyers": 5,
                    "total_buys": 7,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95, 2.0: 0.95, 3.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 80.0, 3.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(model_dir=model_dir, test_df=df, feature_cols=["f1"], threshold=0.8)

        self.assertEqual(result["trades"], 1)

    def test_backtest_gate_uses_configured_age_limit(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 100,
                    "unique_buyers": 5,
                    "total_buys": 7,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["max_age_seconds"] = 90

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        self.assertEqual(result["trades"], 0)

    def test_select_backtest_thresholds_auto_tunes_positive_candidate(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 1,
                    "min_return_pct": -5.0,
                    "max_return_pct": 280.0,
                },
                {
                    "f1": 2.0,
                    "token_address": "B",
                    "sample_time": 2,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 0,
                    "min_return_pct": -70.0,
                    "max_return_pct": -10.0,
                },
                {
                    "f1": 3.0,
                    "token_address": "C",
                    "sample_time": 3,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 1,
                    "min_return_pct": -5.0,
                    "max_return_pct": 280.0,
                },
                {
                    "f1": 4.0,
                    "token_address": "D",
                    "sample_time": 4,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 0,
                    "min_return_pct": -70.0,
                    "max_return_pct": -10.0,
                },
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["auto_tune_entry"] = True
        thresholds["backtest"]["prob_threshold_candidates"] = [0.70, 0.90]
        thresholds["backtest"]["reg_min_return_candidates"] = [60.0, 120.0]
        thresholds["backtest"]["max_age_seconds_candidates"] = [120]

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95, 2.0: 0.90, 3.0: 0.95, 4.0: 0.90})
            fake_reg = _FakeReg({1.0: 150.0, 2.0: 80.0, 3.0: 150.0, 4.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg] * 12):
                result, selected = self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertGreaterEqual(result["return_pct"], 0.0)
        self.assertIn(selected["prob_threshold"], [0.7, 0.9])
        self.assertEqual(selected["reg_min_return"], 120.0)

    def test_select_backtest_thresholds_auto_tunes_exit_candidates(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 0,
                    "min_return_pct": -10.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["prob_threshold_candidates"] = [0.8]
        bt["reg_min_return_candidates"] = [60.0]
        bt["max_age_seconds_candidates"] = [120]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.6]
        bt["drawdown_stop_candidates"] = [0.25]

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg] * 6):
                _, selected = self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(selected["first_take_profit"], 1.0)
        self.assertEqual(selected["first_exit_ratio"], 0.6)
        self.assertEqual(selected["drawdown_stop"], 0.25)

    def test_select_backtest_thresholds_non_auto_includes_exit_params(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 0,
                    "min_return_pct": -10.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = False
        bt["prob_threshold"] = 0.8
        bt["reg_min_return"] = 60.0
        bt["max_age_seconds"] = 120
        bt["first_take_profit"] = 1.0
        bt["first_exit_ratio"] = 0.5
        bt["drawdown_stop"] = 0.20

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result, selected = self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertGreater(result["trades"], 0)
        self.assertEqual(selected["first_take_profit"], 1.0)
        self.assertEqual(selected["first_exit_ratio"], 0.5)
        self.assertEqual(selected["drawdown_stop"], 0.20)

    def test_select_backtest_thresholds_logs_auto_tune_progress(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 20,
                    "unique_buyers": 6,
                    "total_buys": 12,
                    "is_moon_200": 0,
                    "min_return_pct": -10.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["prob_threshold_candidates"] = [0.7, 0.8]
        bt["reg_min_return_candidates"] = [60.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5]
        bt["drawdown_stop_candidates"] = [0.2]
        bt["auto_tune_log_every"] = 1

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch("worktree_trainer.logger.info") as mock_info:
                self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        progress_logs = [
            call
            for call in mock_info.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("Auto-tune progress")
        ]
        self.assertGreaterEqual(len(progress_logs), 1)

    def test_split_backtest_selection_df_splits_by_token_time_order(self):
        df = pd.DataFrame(
            [
                {"token_address": "A", "sample_time": 1},
                {"token_address": "B", "sample_time": 2},
                {"token_address": "C", "sample_time": 3},
                {"token_address": "D", "sample_time": 4},
                {"token_address": "E", "sample_time": 5},
            ]
        )

        selection_df, validation_df = self.trainer._split_backtest_selection_df(df)

        self.assertSetEqual(set(selection_df["token_address"].unique().tolist()), {"A", "B", "C"})
        self.assertSetEqual(set(validation_df["token_address"].unique().tolist()), {"D", "E"})

    def test_selection_score_rewards_consistency_over_single_trade_spike(self):
        thresholds = self.trainer._gate_thresholds()["backtest"]

        high_spike_low_trades = {
            "return_pct": 10.0,
            "max_drawdown_pct": 0.0,
            "trades": 1,
        }
        medium_return_many_trades = {
            "return_pct": 8.0,
            "max_drawdown_pct": 2.0,
            "trades": 20,
        }

        spike_score = self.trainer._selection_score(high_spike_low_trades, thresholds)
        robust_score = self.trainer._selection_score(medium_return_many_trades, thresholds)

        self.assertGreater(robust_score, spike_score)

    def test_selection_score_applies_low_trade_soft_penalty(self):
        thresholds = self.trainer._gate_thresholds()["backtest"]

        low_trades = {
            "return_pct": 12.0,
            "max_drawdown_pct": 3.0,
            "trades": 2,
        }
        enough_trades = {
            "return_pct": 12.0,
            "max_drawdown_pct": 3.0,
            "trades": 10,
        }

        low_score = self.trainer._selection_score(low_trades, thresholds)
        enough_score = self.trainer._selection_score(enough_trades, thresholds)

        self.assertGreater(enough_score, low_score)


if __name__ == "__main__":
    unittest.main()
