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
                {"f1": 1.0, "token_address": "A", "sample_time": 1, "time_since_launch": 10, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 2.0, "token_address": "A", "sample_time": 2, "time_since_launch": 20, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 3.0, "token_address": "B", "sample_time": 1, "time_since_launch": 10, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
                {"f1": 4.0, "token_address": "C", "sample_time": 1, "time_since_launch": 10, "is_moon_200": 0, "min_return_pct": -5.0, "max_return_pct": 20.0},
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90, 2.0: 0.95, 3.0: 0.92, 4.0: 0.95})
            fake_reg = _FakeReg({1.0: 60.0, 2.0: 70.0, 3.0: 60.0, 4.0: 40.0})

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
            fake_reg = _FakeReg({1.0: 60.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(model_dir=model_dir, test_df=df, feature_cols=["f1"], threshold=0.8)

        self.assertGreater(result["return_pct"], 0.0)

    def test_backtest_gate_first_take_profit_is_200_percent(self):
        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "is_moon_200": 1,
                    "min_return_pct": -5.0,
                    "max_return_pct": 300.0,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
            (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
            fake_clf = _FakeClf({1.0: 0.90})
            fake_reg = _FakeReg({1.0: 60.0})

            with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
                result = self.trainer._run_backtest_gate(model_dir=model_dir, test_df=df, feature_cols=["f1"], threshold=0.8)

        expected_actual_return = 0.6 * 2.0 + 0.4 * 3.0
        size = 0.1
        effective_entry = size / 1.2
        gross_value = effective_entry * (1 + expected_actual_return)
        net_value = gross_value * 0.95 * 0.98
        expected_profit = net_value - size
        expected_return_pct = expected_profit * 100

        self.assertAlmostEqual(result["return_pct"], expected_return_pct, places=6)


if __name__ == "__main__":
    unittest.main()
