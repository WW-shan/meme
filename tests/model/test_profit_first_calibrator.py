import unittest
from pathlib import Path
import importlib.util
from unittest.mock import patch


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestProfitFirstCalibrator(unittest.TestCase):
    def test_selects_highest_return_candidate_under_drawdown_guard(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )
        selector = module._select_best_candidate

        candidates = [
            {
                "prob_threshold": 0.20,
                "reg_min_return": 50.0,
                "return_pct": 30.0,
                "max_drawdown_pct": 18.0,
                "trades": 120,
            },
            {
                "prob_threshold": 0.35,
                "reg_min_return": 60.0,
                "return_pct": 40.0,
                "max_drawdown_pct": 24.0,
                "trades": 70,
            },
            {
                "prob_threshold": 0.45,
                "reg_min_return": 80.0,
                "return_pct": 55.0,
                "max_drawdown_pct": 42.0,
                "trades": 50,
            },
        ]

        best = selector(candidates, max_drawdown_limit=35.0, min_trades=20)
        self.assertEqual(best["prob_threshold"], 0.35)
        self.assertEqual(best["reg_min_return"], 60.0)

    def test_selects_candidate_by_trade_rate_target(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )
        selector = module._select_best_candidate

        candidates = [
            {
                "prob_threshold": 0.35,
                "reg_min_return": 50.0,
                "return_pct": 40.0,
                "max_drawdown_pct": 10.0,
                "trades": 25,
                "total_tokens": 1000,
                "trade_rate": 0.025,
            },
            {
                "prob_threshold": 0.45,
                "reg_min_return": 60.0,
                "return_pct": 38.0,
                "max_drawdown_pct": 8.0,
                "trades": 20,
                "total_tokens": 1000,
                "trade_rate": 0.020,
            },
        ]

        best = selector(
            candidates,
            max_drawdown_limit=35.0,
            min_trades=10,
            target_trade_rate=0.02,
            trade_rate_tolerance=0.001,
        )
        self.assertEqual(best["prob_threshold"], 0.45)
        self.assertEqual(best["trade_rate"], 0.020)

    def test_returns_none_when_all_candidates_fail_constraints(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )
        selector = module._select_best_candidate

        candidates = [
            {
                "prob_threshold": 0.50,
                "reg_min_return": 90.0,
                "return_pct": 12.0,
                "max_drawdown_pct": 45.0,
                "trades": 18,
            },
        ]

        best = selector(candidates, max_drawdown_limit=35.0, min_trades=20)
        self.assertIsNone(best)

    def test_run_calibration_builds_ranked_outputs(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )

        def fake_eval(*args, **kwargs):
            return [
                {
                    "prob_threshold": 0.2,
                    "reg_min_return": 50.0,
                    "max_age_seconds": 180,
                    "return_pct": 25.0,
                    "max_drawdown_pct": 20.0,
                    "trades": 100,
                },
                {
                    "prob_threshold": 0.3,
                    "reg_min_return": 60.0,
                    "max_age_seconds": 180,
                    "return_pct": 35.0,
                    "max_drawdown_pct": 30.0,
                    "trades": 70,
                },
                {
                    "prob_threshold": 0.4,
                    "reg_min_return": 70.0,
                    "max_age_seconds": 180,
                    "return_pct": 40.0,
                    "max_drawdown_pct": 38.0,
                    "trades": 50,
                },
            ]

        fake_loaded = {
            "df": None,
            "clf": None,
            "reg": None,
            "feature_cols": ["f1"],
            "dataset_timestamp": "20260215_160001",
            "model_timestamp": "20260215_153845",
        }

        with patch.object(module, "_load_latest_dataset_and_model", return_value=fake_loaded):
            with patch.object(module, "_evaluate_grid", side_effect=fake_eval):
                result = module.run_profit_first_calibration(
                    prob_thresholds=[0.2, 0.3, 0.4],
                    reg_min_returns=[50.0, 60.0, 70.0],
                    max_age_seconds=[180],
                    max_drawdown_limit=35.0,
                    min_trades=20,
                    top_k=2,
                    dataset_timestamp="20260215_160001",
                    model_timestamp="20260215_153845",
                )

        self.assertIn("dataset_timestamp", result)
        self.assertIn("model_timestamp", result)
        self.assertIn("search_space", result)
        self.assertIn("top_candidates", result)
        self.assertIn("recommended", result)
        self.assertEqual(result["recommended"]["prob_threshold"], 0.3)
        self.assertEqual(len(result["top_candidates"]), 2)
        self.assertEqual(result["top_candidates"][0]["return_pct"], 40.0)

    def test_evaluate_single_config_applies_filters_and_one_trade_per_token(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )

        class FakeClf:
            def __init__(self, probs):
                self.probs = probs

            def predict_proba(self, X):
                import numpy as np

                vals = X["f1"].astype(float).to_list()
                p = [self.probs.get(v, 0.0) for v in vals]
                return np.column_stack([1.0 - np.array(p), np.array(p)])

        class FakeReg:
            def __init__(self, preds):
                self.preds = preds

            def predict(self, X):
                import numpy as np

                vals = X["f1"].astype(float).to_list()
                return np.array([self.preds.get(v, 0.0) for v in vals])

        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "is_moon": 0,
                    "unique_buyers": 6,
                    "total_buys": 10,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                },
                {
                    "f1": 2.0,
                    "token_address": "A",
                    "sample_time": 2,
                    "time_since_launch": 20,
                    "is_moon": 0,
                    "unique_buyers": 6,
                    "total_buys": 10,
                    "min_return_pct": -5.0,
                    "max_return_pct": 20.0,
                },
                {
                    "f1": 3.0,
                    "token_address": "B",
                    "sample_time": 1,
                    "time_since_launch": 200,
                    "is_moon": 1,
                    "unique_buyers": 6,
                    "total_buys": 10,
                    "min_return_pct": -5.0,
                    "max_return_pct": 200.0,
                },
                {
                    "f1": 4.0,
                    "token_address": "C",
                    "sample_time": 1,
                    "time_since_launch": 30,
                    "is_moon": 1,
                    "unique_buyers": 6,
                    "total_buys": 10,
                    "min_return_pct": -5.0,
                    "max_return_pct": 200.0,
                },
            ]
        )

        result = module._evaluate_single_config(
            df=df,
            feature_cols=["f1"],
            clf=FakeClf({1.0: 0.9, 2.0: 0.95, 3.0: 0.99, 4.0: 0.95}),
            reg=FakeReg({1.0: 60.0, 2.0: 80.0, 3.0: 90.0, 4.0: 40.0}),
            prob_threshold=0.8,
            reg_min_return=50.0,
            max_age_seconds=180,
            first_take_profit=2.0,
            first_exit_ratio=0.6,
            drawdown_stop=0.25,
        )

        self.assertEqual(result["trades"], 1)
        self.assertEqual(result["prob_threshold"], 0.8)
        self.assertEqual(result["reg_min_return"], 50.0)
        self.assertEqual(result["max_age_seconds"], 180)
        self.assertEqual(result["total_tokens"], 3)
        self.assertAlmostEqual(result["trade_rate"], 1 / 3, places=6)

    def test_evaluate_single_config_supports_exit_params(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )

        class FakeClf:
            def predict_proba(self, X):
                import numpy as np

                return np.column_stack([np.array([0.05]), np.array([0.95])])

        class FakeReg:
            def predict(self, X):
                import numpy as np

                return np.array([80.0])

        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "f1": 1.0,
                    "token_address": "A",
                    "sample_time": 1,
                    "time_since_launch": 10,
                    "is_moon": 0,
                    "unique_buyers": 6,
                    "total_buys": 10,
                    "min_return_pct": -10.0,
                    "max_return_pct": 120.0,
                    "final_return_pct": 20.0,
                }
            ]
        )

        low_tp = module._evaluate_single_config(
            df=df,
            feature_cols=["f1"],
            clf=FakeClf(),
            reg=FakeReg(),
            prob_threshold=0.8,
            reg_min_return=50.0,
            max_age_seconds=180,
            first_take_profit=1.0,
            first_exit_ratio=0.6,
            drawdown_stop=0.25,
        )
        high_tp = module._evaluate_single_config(
            df=df,
            feature_cols=["f1"],
            clf=FakeClf(),
            reg=FakeReg(),
            prob_threshold=0.8,
            reg_min_return=50.0,
            max_age_seconds=180,
            first_take_profit=2.0,
            first_exit_ratio=0.6,
            drawdown_stop=0.25,
        )

        self.assertGreater(low_tp["return_pct"], high_tp["return_pct"])
        self.assertEqual(low_tp["first_take_profit"], 1.0)
        self.assertEqual(low_tp["first_exit_ratio"], 0.6)
        self.assertEqual(low_tp["drawdown_stop"], 0.25)


if __name__ == "__main__":
    unittest.main()
