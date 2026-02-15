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
        gate = self.trainer._evaluate_gate(
            offline={
                "roc_auc": 0.63,
                "precision_at_80": 0.09,
                "samples_at_80": 25,
                "reg_rmse": 90.0,
                "reg_r2": -0.05,
            },
            backtest={
                "return_pct": 10.0,
                "max_drawdown_pct": 20.0,
                "trades": 120,
            },
        )

        self.assertTrue(gate["passed_gate"])
        self.assertTrue(gate["offline_pass"])
        self.assertTrue(gate["backtest_pass"])
        self.assertEqual(gate["failed_checks"], [])
        self.assertTrue(gate["checks"]["offline"]["reg_r2_pass"])

    def test_evaluate_gate_fails_when_thresholds_missed(self):
        gate = self.trainer._evaluate_gate(
            offline={
                "roc_auc": 0.61,
                "precision_at_80": 0.07,
                "samples_at_80": 18,
                "reg_rmse": 110.0,
                "reg_r2": -0.2,
            },
            backtest={
                "return_pct": -3.0,
                "max_drawdown_pct": 40.0,
                "trades": 50,
            },
        )

        self.assertFalse(gate["passed_gate"])
        self.assertFalse(gate["offline_pass"])
        self.assertFalse(gate["backtest_pass"])
        self.assertGreaterEqual(len(gate["failed_checks"]), 3)
        self.assertIn("offline:roc_auc_pass", gate["failed_checks"])
        self.assertIn("backtest:max_drawdown_pass", gate["failed_checks"])


if __name__ == "__main__":
    unittest.main()
