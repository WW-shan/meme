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
        self.assertEqual(meta["gate_thresholds"]["backtest"]["prob_threshold"], 0.20)
        self.assertEqual(meta["gate_thresholds"]["backtest"]["reg_min_return"], 50.0)

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
