import unittest
from pathlib import Path
import importlib.util


def _load_worktree_trainer():
    trainer_path = Path(__file__).resolve().parents[2] / "src" / "model" / "trainer.py"
    spec = importlib.util.spec_from_file_location("worktree_trainer", trainer_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.MemeModelTrainer


MemeModelTrainer = _load_worktree_trainer()


class TestTrainerMetadata(unittest.TestCase):
    def test_build_metadata_contains_gate_and_format_priority(self):
        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        meta = trainer._build_model_metadata(
            timestamp="20260215_000000",
            features=["f1"],
            target="is_moon",
            metrics={"is_moon": {"roc_auc": 0.9}},
            gate_result={"passed_gate": True, "offline_pass": True, "backtest_pass": True},
            threshold_scan=[{"threshold": 0.8, "precision": 0.9, "recall": 0.2, "samples": 10}],
            regressor={"status": "trained", "metrics": {"rmse": 1.0, "r2": 0.1}},
        )

        self.assertEqual(meta["model_format_priority"], ["json", "pkl"])
        self.assertIn("gate_result", meta)
        self.assertIn("threshold_scan", meta)
        self.assertIn("regressor", meta)
        self.assertEqual(meta["gate_thresholds"], trainer._gate_thresholds())
        self.assertEqual(meta["gate_thresholds"]["backtest"]["prob_threshold"], 0.70)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["reg_min_return"], 70.0)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["max_age_seconds"], 120)
        self.assertTrue(meta["gate_thresholds"]["backtest"]["auto_tune_entry"])
        self.assertEqual(meta["gate_thresholds"]["backtest"]["target_score_weight"], 0.35)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["selection_min_trades_soft"], 8)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["selection_low_trade_penalty"], 3.0)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["first_take_profit"], 2.0)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["first_exit_ratio"], 0.6)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["drawdown_stop"], 0.25)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["first_take_profit_candidates"], [0.8, 1.0, 1.5, 2.0])
        self.assertEqual(meta["gate_thresholds"]["backtest"]["first_exit_ratio_candidates"], [0.5, 0.6, 0.7])
        self.assertEqual(meta["gate_thresholds"]["backtest"]["drawdown_stop_candidates"], [0.20, 0.25, 0.30])
        self.assertEqual(meta["gate_thresholds"]["backtest"]["auto_tune_strategy"], "staged")
        self.assertEqual(meta["gate_thresholds"]["backtest"]["entry_stage_top_n"], 10)

    def test_resolve_training_profile(self):
        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        balanced = trainer._resolve_training_profile("balanced")
        self.assertIn("xgb_overrides", balanced)
        self.assertIn("lgb_overrides", balanced)
        self.assertEqual(balanced["scale_pos_weight_multiplier"], 1.0)

        with self.assertRaises(ValueError):
            trainer._resolve_training_profile("unknown")

    def test_resolve_target_thresholds(self):
        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        defaults = trainer._resolve_target_thresholds(None)
        self.assertEqual(defaults, [60.0, 80.0, 100.0, 120.0, 150.0, 200.0, 250.0])

        custom = trainer._resolve_target_thresholds([200, 80, 100, 80])
        self.assertEqual(custom, [80.0, 100.0, 200.0])

        with self.assertRaises(ValueError):
            trainer._resolve_target_thresholds([0, -10])

    def test_build_target_labels(self):
        import pandas as pd

        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        df = pd.DataFrame({"max_return_pct": [50.0, 80.0, 120.0]})
        labels = trainer._build_target_labels(df, 80.0)
        self.assertListEqual(labels.tolist(), [0, 1, 1])

    def test_training_profiles_contains_extended_profiles(self):
        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        self.assertIn("aggressive_profit", trainer.TRAINING_PROFILES)
        self.assertIn("low_drawdown", trainer.TRAINING_PROFILES)
        self.assertIn("early_signal", trainer.TRAINING_PROFILES)

    def test_build_metadata_supports_strategy_recommendation(self):
        trainer = MemeModelTrainer(data_dir="data/datasets", model_dir="data/models")

        recommendation = {
            "prob_threshold": 0.35,
            "reg_min_return": 60.0,
            "max_age_seconds": 150,
            "source_calibration_file": "data/models/calibration_20260215_000000.json",
        }

        meta = trainer._build_model_metadata(
            timestamp="20260215_000000",
            features=["f1"],
            target="is_moon",
            metrics={"is_moon": {"roc_auc": 0.9}},
            gate_result={"passed_gate": True, "offline_pass": True, "backtest_pass": True},
            threshold_scan=[{"threshold": 0.8, "precision": 0.9, "recall": 0.2, "samples": 10}],
            regressor={"status": "trained", "metrics": {"rmse": 1.0, "r2": 0.1}},
            strategy_recommendation=recommendation,
        )

        self.assertIn("strategy_recommendation", meta)
        self.assertEqual(meta["strategy_recommendation"]["prob_threshold"], 0.35)
        self.assertEqual(meta["strategy_recommendation"]["reg_min_return"], 60.0)
        self.assertEqual(meta["strategy_recommendation"]["max_age_seconds"], 150)
        self.assertEqual(
            meta["strategy_recommendation"]["source_calibration_file"],
            "data/models/calibration_20260215_000000.json",
        )


if __name__ == "__main__":
    unittest.main()
