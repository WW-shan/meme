import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTrainHybridPipeline(unittest.TestCase):
    def test_run_hybrid_training_returns_artifact_manifest(self):
        m = _load_module()

        with patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.42}), \
             patch.object(m, "build_sell_env", return_value=MagicMock()), \
             patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt"}), \
             patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip"}), \
             patch.object(m, "run_ab_evaluation", return_value={"maxdd_delta": -0.25, "sortino_delta": 0.2}):
            result = m.run_hybrid_training({"output_dir": "data/models"})

        self.assertIn("buy_model", result["artifacts"])
        self.assertIn("sell_policy", result["artifacts"])
        self.assertIn("evaluation", result)


if __name__ == "__main__":
    unittest.main()
