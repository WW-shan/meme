import unittest
import tempfile
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


class TestTrainerMetrics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        data_dir = Path(self.tmp.name) / "datasets"
        model_dir = Path(self.tmp.name) / "models"
        data_dir.mkdir(parents=True, exist_ok=True)
        model_dir.mkdir(parents=True, exist_ok=True)
        self.trainer = MemeModelTrainer(data_dir=str(data_dir), model_dir=str(model_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_thresholds_returns_expected_keys(self):
        y_true = [0, 0, 1, 1, 1]
        y_prob = [0.1, 0.35, 0.75, 0.9, 0.95]

        rows = self.trainer._scan_thresholds(y_true, y_prob, thresholds=[0.7, 0.8, 0.9])

        self.assertEqual(len(rows), 3)
        self.assertIn("threshold", rows[0])
        self.assertIn("precision", rows[0])
        self.assertIn("recall", rows[0])
        self.assertIn("samples", rows[0])

    def test_evaluate_gate_applies_business_thresholds(self):
        thresholds = self.trainer._gate_thresholds()
        gate = self.trainer._evaluate_gate(
            offline={
                "roc_auc": thresholds["offline"]["roc_auc_min"] + 0.01,
                "precision_at_80": thresholds["offline"]["precision_at_80_min"] + 0.01,
                "samples_at_80": thresholds["offline"]["samples_at_80_min"] + 1,
                "reg_rmse": thresholds["offline"]["reg_rmse_max"] - 5.0,
                "reg_r2": thresholds["offline"]["reg_r2_min"] + 0.01,
            },
            backtest={
                "return_pct": thresholds["backtest"]["return_pct_min"] + 10.0,
                "max_drawdown_pct": thresholds["backtest"]["max_drawdown_pct_max"] - 15.0,
                "trades": 1,
            },
            gate_thresholds=thresholds,
        )

        self.assertTrue(gate["passed_gate"])
        self.assertTrue(gate["offline_pass"])
        self.assertTrue(gate["backtest_pass"])
        self.assertEqual(gate["failed_checks"], [])
        self.assertTrue(gate["checks"]["offline"]["reg_r2_pass"])

    def test_evaluate_gate_fails_when_thresholds_missed(self):
        thresholds = self.trainer._gate_thresholds()
        gate = self.trainer._evaluate_gate(
            offline={
                "roc_auc": thresholds["offline"]["roc_auc_min"] - 0.01,
                "precision_at_80": thresholds["offline"]["precision_at_80_min"] - 0.01,
                "samples_at_80": thresholds["offline"]["samples_at_80_min"] - 1,
                "reg_rmse": thresholds["offline"]["reg_rmse_max"] + 10.0,
                "reg_r2": thresholds["offline"]["reg_r2_min"] - 0.1,
            },
            backtest={
                "return_pct": thresholds["backtest"]["return_pct_min"] - 0.1,
                "max_drawdown_pct": thresholds["backtest"]["max_drawdown_pct_max"] + 5.0,
                "trades": 999,
            },
            gate_thresholds=thresholds,
        )

        self.assertFalse(gate["passed_gate"])
        self.assertFalse(gate["offline_pass"])
        self.assertFalse(gate["backtest_pass"])
        self.assertGreaterEqual(len(gate["failed_checks"]), 3)
        self.assertIn("offline:roc_auc_pass", gate["failed_checks"])
        self.assertIn("backtest:max_drawdown_pass", gate["failed_checks"])

    def test_evaluate_gate_boundary_values_align_with_thresholds(self):
        thresholds = self.trainer._gate_thresholds()

        gate = self.trainer._evaluate_gate(
            offline={
                "roc_auc": thresholds["offline"]["roc_auc_min"],
                "precision_at_80": thresholds["offline"]["precision_at_80_min"],
                "samples_at_80": thresholds["offline"]["samples_at_80_min"],
                "reg_rmse": thresholds["offline"]["reg_rmse_max"],
                "reg_r2": thresholds["offline"]["reg_r2_min"],
            },
            backtest={
                "return_pct": thresholds["backtest"]["return_pct_min"],
                "max_drawdown_pct": thresholds["backtest"]["max_drawdown_pct_max"],
                "trades": 0,
            },
            gate_thresholds=thresholds,
        )

        self.assertTrue(gate["passed_gate"])
        self.assertEqual(gate["failed_checks"], [])


if __name__ == "__main__":
    unittest.main()
