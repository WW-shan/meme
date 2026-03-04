import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

import numpy as np
import pandas as pd


_TR_MODULE = None


def _load_worktree_trainer():
    global _TR_MODULE
    trainer_path = Path(__file__).resolve().parents[2] / "src" / "model" / "trainer.py"
    spec = importlib.util.spec_from_file_location("worktree_trainer", trainer_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    _TR_MODULE = module
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

    @staticmethod
    def _one_row_backtest_df():
        return pd.DataFrame(
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
                    "first_price": 1.0,
                    "current_price": 1.0,
                }
            ]
        )

    def test_backtest_gate_trades_once_per_token(self):
        df = pd.DataFrame(
            [
                {"f1": 1.0, "token_address": "A", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0, "current_price": 1.0, "first_price": 1.0},
                {"f1": 2.0, "token_address": "A", "sample_time": 2, "time_since_launch": 20, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0, "current_price": 1.0, "first_price": 1.0},
                {"f1": 3.0, "token_address": "B", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0, "current_price": 1.0, "first_price": 1.0},
                {"f1": 4.0, "token_address": "C", "sample_time": 1, "time_since_launch": 10, "unique_buyers": 4, "total_buys": 6, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0, "current_price": 1.0, "first_price": 1.0},
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90, 2.0: 0.95, 3.0: 0.92, 4.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 90.0, 3.0: 80.0, 4.0: 40.0})

            thresholds = self.trainer._gate_thresholds()
            thresholds["backtest"]["reg_min_return"] = 70.0

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

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
                    "first_price": 1.0,
                    "current_price": 1.0,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90})
            fake_reg = _FakeReg({1.0: 80.0})

            thresholds = self.trainer._gate_thresholds()
            thresholds["backtest"]["reg_min_return"] = 60.0
            thresholds["backtest"]["first_take_profit"] = 9.0

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        self.assertLess(result["return_pct"], 0.0)

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
                    "first_price": 1.0,
                    "current_price": 1.0,
                },
                {
                    "f1": 2.0,
                    "token_address": "A",
                    "sample_time": 20,
                    "time_since_launch": 20,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                    "first_price": 1.0,
                    "current_price": 2.0,
                },
                {
                    "f1": 3.0,
                    "token_address": "A",
                    "sample_time": 30,
                    "time_since_launch": 30,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                    "first_price": 1.0,
                    "current_price": 1.5,
                },
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["first_take_profit"] = 1.0
        thresholds["backtest"]["first_exit_ratio"] = 0.5
        thresholds["backtest"]["drawdown_stop"] = 0.20
        thresholds["backtest"]["reg_min_return"] = 60.0

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90, 2.0: 0.95, 3.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 80.0, 3.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        expected_actual_return = 0.5 * 1.0 + 0.5 * 0.5
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
                    "first_price": 1.0,
                    "current_price": 1.0,
                },
                {
                    "f1": 2.0,
                    "token_address": "A",
                    "sample_time": 2,
                    "time_since_launch": 20,
                    "unique_buyers": 4,
                    "total_buys": 6,
                    "is_moon_200": 0,
                    "min_return_pct": -5.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                    "first_price": 1.0,
                    "current_price": 2.0,
                },
            ]
        )

        thresholds = self.trainer._gate_thresholds()
        thresholds["backtest"]["first_take_profit"] = 1.0
        thresholds["backtest"]["first_exit_ratio"] = 1.5
        thresholds["backtest"]["drawdown_stop"] = -0.2
        thresholds["backtest"]["reg_min_return"] = 60.0

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95, 2.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

        expected_actual_return = 1.0
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
                    "first_price": 1.0,
                    "current_price": 1.0,
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
                    "first_price": 1.0,
                    "current_price": 1.0,
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
                    "first_price": 1.0,
                    "current_price": 1.2,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95, 2.0: 0.95, 3.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0, 2.0: 80.0, 3.0: 80.0})

            thresholds = self.trainer._gate_thresholds()
            thresholds["backtest"]["reg_min_return"] = 60.0

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    threshold=0.8,
                    gate_thresholds=thresholds,
                )

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

        self.assertIn(selected["prob_threshold"], [0.7, 0.9])
        self.assertIn(selected["reg_min_return"], [60.0, 120.0])
        self.assertIn("search_meta", selected)

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
        bt["stop_loss"] = -0.35

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

        self.assertGreaterEqual(result["trades"], 0)
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

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(_TR_MODULE.logger, "info") as mock_info:
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

    def test_select_backtest_thresholds_staged_limits_combinations(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "staged"
        bt["entry_stage_top_n"] = 1
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0, 90.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5, 0.6]
        bt["drawdown_stop_candidates"] = [0.2]

        entry_combo_count = (
            len(bt["prob_threshold_candidates"])
            * len(bt["reg_min_return_candidates"])
            * len(bt["max_age_seconds_candidates"])
        )
        exit_combo_count = (
            bt["entry_stage_top_n"]
            * len(bt["first_take_profit_candidates"])
            * len(bt["first_exit_ratio_candidates"])
            * len(bt["drawdown_stop_candidates"])
            * len(bt["stop_loss_candidates"])
        )
        evaluation_df_count = (
            1
            + len(self.trainer._split_backtest_selection_df(df))
            + len(self.trainer._build_rolling_validation_dfs(df, int(bt.get("rolling_validation_folds", 1))))
        )
        expected_count = (entry_combo_count + exit_combo_count) * evaluation_df_count

        seen_combos = []

        def _capture_combo(*, df, probs, pred_returns, threshold, reg_min_return, backtest_thresholds, eval_cache=None):
            seen_combos.append(
                (
                    float(threshold),
                    float(reg_min_return),
                    int(backtest_thresholds["max_age_seconds"]),
                    float(backtest_thresholds["first_take_profit"]),
                    float(backtest_thresholds["first_exit_ratio"]),
                    float(backtest_thresholds["drawdown_stop"]),
                )
            )
            return {"return_pct": 1.0, "max_drawdown_pct": 1.0, "trades": 10}

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
                self.trainer,
                "_run_backtest_gate_precomputed",
                side_effect=_capture_combo,
            ) as mock_run_precomputed:
                _, selected = self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(mock_run_precomputed.call_count, expected_count)
        self.assertEqual(len(seen_combos), expected_count)
        default_first_tp = float(bt["first_take_profit"])
        default_first_ratio = float(bt["first_exit_ratio"])
        default_drawdown = float(bt["drawdown_stop"])

        stage_b_entry_tuples = {
            (combo[0], combo[1], combo[2])
            for combo in seen_combos
            if not (
                combo[3] == default_first_tp
                and combo[4] == default_first_ratio
                and combo[5] == default_drawdown
            )
        }
        self.assertEqual(len(stage_b_entry_tuples), bt["entry_stage_top_n"])
        self.assertIn("first_take_profit", selected)
        self.assertIn("first_exit_ratio", selected)
        self.assertIn("drawdown_stop", selected)

    def test_select_backtest_thresholds_staged_returns_search_meta(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "staged"
        bt["entry_stage_top_n"] = 1
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5]
        bt["drawdown_stop_candidates"] = [0.2]

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                _, selected = self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertIn("search_meta", selected)
        self.assertEqual(selected["search_meta"]["strategy"], "staged")
        self.assertEqual(selected["search_meta"]["stageA_total"], 2)
        self.assertEqual(selected["search_meta"]["stageA_top_n"], 1)
        self.assertEqual(selected["search_meta"]["stageB_total"], 8)
        self.assertEqual(selected["search_meta"]["evaluated_candidates_total"], 10)
        self.assertAlmostEqual(selected["search_meta"]["estimated_reduction_ratio"], 0.375)
        self.assertEqual(selected["search_meta"]["rolling_validation_folds"], 1)
        self.assertEqual(selected["search_meta"]["min_trades_hard"], thresholds["backtest"]["min_trades_hard"])
        self.assertEqual(selected["search_meta"]["min_trades_effective"], thresholds["backtest"]["selection_min_trades_soft"])
        self.assertEqual(selected["search_meta"]["win_rate_floor"], thresholds["backtest"]["selection_win_rate_min_for_bonus"])
        self.assertIsNone(selected["search_meta"]["fallback_reason"])

    def test_select_backtest_thresholds_staged_clamps_top_n(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "staged"
        bt["entry_stage_top_n"] = 999
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0, 90.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5, 0.6]
        bt["drawdown_stop_candidates"] = [0.2]

        entry_combo_count = (
            len(bt["prob_threshold_candidates"])
            * len(bt["reg_min_return_candidates"])
            * len(bt["max_age_seconds_candidates"])
        )
        exit_combo_count = (
            len(bt["first_take_profit_candidates"])
            * len(bt["first_exit_ratio_candidates"])
            * len(bt["drawdown_stop_candidates"])
            * len(bt["stop_loss_candidates"])
        )
        clamped_top_n = min(bt["entry_stage_top_n"], entry_combo_count)
        evaluation_df_count = (
            1
            + len(self.trainer._split_backtest_selection_df(df))
            + len(self.trainer._build_rolling_validation_dfs(df, int(bt.get("rolling_validation_folds", 1))))
        )
        expected_count = (entry_combo_count + (clamped_top_n * exit_combo_count)) * evaluation_df_count

        seen_combos = []

        def _capture_combo(*, df, probs, pred_returns, threshold, reg_min_return, backtest_thresholds, eval_cache=None):
            seen_combos.append(
                (
                    float(threshold),
                    float(reg_min_return),
                    int(backtest_thresholds["max_age_seconds"]),
                    float(backtest_thresholds["first_take_profit"]),
                    float(backtest_thresholds["first_exit_ratio"]),
                    float(backtest_thresholds["drawdown_stop"]),
                )
            )
            return {"return_pct": 1.0, "max_drawdown_pct": 1.0, "trades": 10}

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
                self.trainer,
                "_run_backtest_gate_precomputed",
                side_effect=_capture_combo,
            ) as mock_run_precomputed:
                self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(entry_combo_count, 4)
        self.assertEqual(exit_combo_count, 16)
        self.assertGreaterEqual(evaluation_df_count, 3)
        self.assertEqual(expected_count, 272)
        self.assertEqual(mock_run_precomputed.call_count, expected_count)
        self.assertEqual(len(seen_combos), expected_count)

    def test_select_backtest_thresholds_full_strategy_keeps_cartesian(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "full"
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0, 90.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5, 0.6]
        bt["drawdown_stop_candidates"] = [0.2]

        combo_count = (
            len(bt["prob_threshold_candidates"])
            * len(bt["reg_min_return_candidates"])
            * len(bt["max_age_seconds_candidates"])
            * len(bt["first_take_profit_candidates"])
            * len(bt["first_exit_ratio_candidates"])
            * len(bt["drawdown_stop_candidates"])
            * len(bt["stop_loss_candidates"])
        )
        evaluation_df_count = (
            1
            + len(self.trainer._split_backtest_selection_df(df))
            + len(self.trainer._build_rolling_validation_dfs(df, int(bt.get("rolling_validation_folds", 1))))
        )
        expected_count = combo_count * evaluation_df_count

        seen_combos = []

        def _capture_combo(*, df, probs, pred_returns, threshold, reg_min_return, backtest_thresholds, eval_cache=None):
            seen_combos.append(
                (
                    float(threshold),
                    float(reg_min_return),
                    int(backtest_thresholds["max_age_seconds"]),
                    float(backtest_thresholds["first_take_profit"]),
                    float(backtest_thresholds["first_exit_ratio"]),
                    float(backtest_thresholds["drawdown_stop"]),
                )
            )
            return {"return_pct": 1.0, "max_drawdown_pct": 1.0, "trades": 10}

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
                self.trainer,
                "_run_backtest_gate_precomputed",
                side_effect=_capture_combo,
            ) as mock_run_precomputed:
                self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(mock_run_precomputed.call_count, expected_count)
        self.assertEqual(len(seen_combos), expected_count)

    def test_select_backtest_thresholds_invalid_strategy_logs_warning_and_uses_full(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "bad-mode"
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0, 90.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5, 0.6]
        bt["drawdown_stop_candidates"] = [0.2]

        combo_count = (
            len(bt["prob_threshold_candidates"])
            * len(bt["reg_min_return_candidates"])
            * len(bt["max_age_seconds_candidates"])
            * len(bt["first_take_profit_candidates"])
            * len(bt["first_exit_ratio_candidates"])
            * len(bt["drawdown_stop_candidates"])
            * len(bt["stop_loss_candidates"])
        )
        evaluation_df_count = (
            1
            + len(self.trainer._split_backtest_selection_df(df))
            + len(self.trainer._build_rolling_validation_dfs(df, int(bt.get("rolling_validation_folds", 1))))
        )
        expected_count = combo_count * evaluation_df_count

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
                self.trainer,
                "_run_backtest_gate_precomputed",
                return_value={"return_pct": 1.0, "max_drawdown_pct": 1.0, "trades": 10},
            ) as mock_run_precomputed, patch.object(_TR_MODULE.logger, "warning") as mock_warning:
                self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(mock_run_precomputed.call_count, expected_count)
        self.assertTrue(mock_warning.call_args_list)
        warning_text = "\n".join(str(call.args[0]) for call in mock_warning.call_args_list if call.args)
        self.assertIn("auto_tune_strategy", warning_text)

    def test_select_backtest_thresholds_staged_invalid_top_n_falls_back_to_one(self):
        df = self._one_row_backtest_df()

        thresholds = self.trainer._gate_thresholds()
        bt = thresholds["backtest"]
        bt["auto_tune_entry"] = True
        bt["auto_tune_strategy"] = "staged"
        bt["entry_stage_top_n"] = "oops"
        bt["prob_threshold_candidates"] = [0.70, 0.85]
        bt["reg_min_return_candidates"] = [60.0, 90.0]
        bt["max_age_seconds_candidates"] = [90]
        bt["first_take_profit_candidates"] = [1.0, 2.0]
        bt["first_exit_ratio_candidates"] = [0.5, 0.6]
        bt["drawdown_stop_candidates"] = [0.2]

        entry_combo_count = (
            len(bt["prob_threshold_candidates"])
            * len(bt["reg_min_return_candidates"])
            * len(bt["max_age_seconds_candidates"])
        )
        exit_combo_count = (
            1
            * len(bt["first_take_profit_candidates"])
            * len(bt["first_exit_ratio_candidates"])
            * len(bt["drawdown_stop_candidates"])
            * len(bt["stop_loss_candidates"])
        )
        evaluation_df_count = (
            1
            + len(self.trainer._split_backtest_selection_df(df))
            + len(self.trainer._build_rolling_validation_dfs(df, int(bt.get("rolling_validation_folds", 1))))
        )
        expected_count = (entry_combo_count + exit_combo_count) * evaluation_df_count

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.95})
            fake_reg = _FakeReg({1.0: 80.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
                self.trainer,
                "_run_backtest_gate_precomputed",
                return_value={"return_pct": 1.0, "max_drawdown_pct": 1.0, "trades": 10},
            ) as mock_run_precomputed, patch.object(_TR_MODULE.logger, "warning") as mock_warning:
                self.trainer._select_backtest_thresholds(
                    model_dir=model_dir,
                    test_df=df,
                    feature_cols=["f1"],
                    gate_thresholds=thresholds,
                )

        self.assertEqual(mock_run_precomputed.call_count, expected_count)
        self.assertTrue(mock_warning.call_args_list)
        warning_text = "\n".join(str(call.args[0]) for call in mock_warning.call_args_list if call.args)
        self.assertIn("entry_stage_top_n", warning_text)

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

    def test_train_persists_backtest_search_meta_to_outputs(self):
        expected_search_meta = {
            "strategy": "staged",
            "stageA_total": 6,
            "stageA_top_n": 2,
            "stageB_total": 12,
            "evaluated_candidates_total": 18,
            "estimated_reduction_ratio": 0.5,
        }

        tiny_train = pd.DataFrame({"f1": [1.0], "max_return_pct": [250.0]})
        tiny_val = pd.DataFrame({"f1": [1.0], "max_return_pct": [250.0]})
        tiny_test = pd.DataFrame({"f1": [1.0], "max_return_pct": [250.0]})
        meta = {"feature_names": ["f1"]}

        dummy_clf = _FakeClf({1.0: 0.9})
        backtest_result = {"return_pct": 5.0, "max_drawdown_pct": 1.0, "trades": 3}
        selected_thresholds = {
            "prob_threshold": 0.8,
            "reg_min_return": 60.0,
            "max_age_seconds": 90,
            "first_take_profit": 1.0,
            "first_exit_ratio": 0.5,
            "drawdown_stop": 0.2,
            "stop_loss": -0.35,
            "search_meta": expected_search_meta,
        }

        with patch.object(self.trainer, "load_dataset", return_value=(tiny_train, tiny_val, tiny_test, meta)), patch.object(
            self.trainer,
            "_fit_classifier_for_target",
            return_value=(dummy_clf, {}),
        ), patch.object(
            self.trainer,
            "_evaluate_target_classifier",
            return_value={"precision_at_80": 0.9, "roc_auc": 0.9},
        ), patch.object(self.trainer, "_save_classifier_artifacts", return_value=None), patch.object(
            self.trainer,
            "_train_optional_regressor",
            return_value={"status": "skipped", "metrics": {}},
        ), patch.object(self.trainer, "_scan_thresholds", return_value=[]), patch.object(
            self.trainer,
            "_select_backtest_thresholds",
            return_value=(backtest_result, selected_thresholds),
        ), patch.object(self.trainer, "_evaluate_gate", return_value={"passed_gate": True}), patch.object(
            self.trainer,
            "_selection_score",
            return_value=1.23,
        ), patch.object(
            self.trainer,
            "_weighted_target_score",
            return_value=0.45,
        ):
            final_save_dir = Path(
                self.trainer.train(
                    profile="precision_core",
                    target_thresholds=[200.0],
                    max_parallel_profiles=1,
                )
            )

        with (final_save_dir / "model_metadata.json").open("r", encoding="utf-8") as f:
            model_meta = json.load(f)

        self.assertEqual(
            model_meta["trial_summary"]["backtest_search_meta"],
            expected_search_meta,
        )

        summary_path = final_save_dir.parent / f"{final_save_dir.name}_trials" / "selection_summary.json"
        with summary_path.open("r", encoding="utf-8") as f:
            selection_summary = json.load(f)

        self.assertEqual(
            selection_summary["results"][0]["backtest_search_meta"],
            expected_search_meta,
        )


if __name__ == "__main__":
    unittest.main()
