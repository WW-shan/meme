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

    def test_prepare_training_rows_rejects_empty_samples(self):
        m = _load_module()
        with self.assertRaises(ValueError):
            m._prepare_training_rows([], "max_return_pct", 80.0)

    def test_prepare_training_rows_rejects_single_class_target(self):
        m = _load_module()
        samples = [
            {
                "features": {"current_price": 1.0, "buy_pressure": 0.6},
                "label": {"max_return_pct": 10.0},
                "meta": {"token_address": "A", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.1, "buy_pressure": 0.7},
                "label": {"max_return_pct": 12.0},
                "meta": {"token_address": "B", "sample_time": 110},
            },
        ]
        with self.assertRaises(ValueError):
            m._prepare_training_rows(samples, "max_return_pct", 80.0)

    def test_train_buy_model_saves_model_and_threshold(self):
        import tempfile
        m = _load_module()
        samples = [
            {"features": {"current_price": 1.0, "buy_pressure": 0.4}, "label": {"max_return_pct": 20.0}, "meta": {"token_address": "A", "sample_time": 100}},
            {"features": {"current_price": 1.1, "buy_pressure": 0.8}, "label": {"max_return_pct": 120.0}, "meta": {"token_address": "B", "sample_time": 110}},
            {"features": {"current_price": 1.2, "buy_pressure": 0.3}, "label": {"max_return_pct": 10.0}, "meta": {"token_address": "C", "sample_time": 120}},
            {"features": {"current_price": 1.3, "buy_pressure": 0.9}, "label": {"max_return_pct": 200.0}, "meta": {"token_address": "D", "sample_time": 130}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_load_samples", return_value=samples), \
                 patch.object(m, "BuyCatBoostModel") as MockModel:
                fake = MagicMock()
                fake.predict_proba.return_value = [[0.3, 0.7]] * len(samples)
                fake.select_threshold.return_value = 0.42
                fake.model = MagicMock()
                def _save_model(path):
                    Path(path).write_text("cbm", encoding="utf-8")
                fake.model.save_model.side_effect = _save_model
                MockModel.return_value = fake

                out = m.train_buy_model({"output_dir": tmpdir, "target_label_column": "max_return_pct", "target_threshold_value": 80.0})

            self.assertTrue(Path(out["model_path"]).exists())
            self.assertTrue(Path(out["threshold_path"]).exists())
            self.assertIn("labels", out)

    def test_build_sell_env_creates_trading_env_bundle(self):
        m = _load_module()
        buy_artifact = {
            "samples": [
                {
                    "features": {
                        "current_price": 1.0,
                        "launch_fee": 0.5,
                        "buy_pressure": 0.7,
                        "holder_count": 40,
                        "total_buy_volume": 3.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "A", "sample_time": 100},
                },
                {
                    "features": {
                        "current_price": 1.1,
                        "launch_fee": 0.5,
                        "buy_pressure": 0.6,
                        "holder_count": 42,
                        "total_buy_volume": 4.0,
                        "total_sell_volume": 2.0,
                    },
                    "meta": {"token_address": "A", "sample_time": 110},
                },
            ]
        }

        bundle = m.build_sell_env({"liquidity_floor": 0.05, "stall_steps": 2}, buy_artifact)

        self.assertIn("env", bundle)
        self.assertGreater(bundle["episode_count"], 0)

    def test_run_bc_warmstart_saves_weights(self):
        import tempfile
        m = _load_module()
        env_bundle = {
            "episodes": [
                [
                    {"mid_price": 1.0, "lp_depth": 1.0, "sell_pressure": 0.2, "buy_sell_ratio": 2.0, "holders": 40},
                    {"mid_price": 0.9, "lp_depth": 1.0, "sell_pressure": 1.4, "buy_sell_ratio": 0.7, "holders": 38},
                ]
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "train_bc", return_value={"net.0.weight": [1.0]}), \
                 patch.object(m, "_as_torch_tensors", return_value=(object(), object())), \
                 patch.object(m, "_torch_save") as mock_save:
                out = m.run_bc_warmstart({"output_dir": tmpdir, "bc_epochs": 3}, env_bundle)

        self.assertTrue(out["weights"].endswith("bc.pt"))
        mock_save.assert_called_once()

    def test_run_ppo_finetune_saves_policy_with_bc_init(self):
        import tempfile
        m = _load_module()
        fake_model = MagicMock()
        env_bundle = {"env": object()}
        bc_artifact = {"weights": "dummy-bc.pt"}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_torch_load", return_value={"k": 1.0}), \
                 patch.object(m, "train_ppo", return_value=fake_model) as mock_train:
                out = m.run_ppo_finetune({"output_dir": tmpdir, "total_timesteps": 64, "ppo_seed": 9}, env_bundle, bc_artifact)

        mock_train.assert_called_once()
        fake_model.save.assert_called_once()
        self.assertTrue(out["policy_path"].endswith("sell_policy.zip"))

    def test_run_hybrid_training_returns_non_placeholder_evaluation(self):
        m = _load_module()
        with patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.45, "labels": [0, 1, 1], "samples": [{}]}), \
             patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
             patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
             patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128}):
            result = m.run_hybrid_training({"output_dir": "data/models"})

        self.assertIn("pipeline_status", result["evaluation"])
        self.assertEqual(result["evaluation"]["pipeline_status"], "ok")
        self.assertIn("buy_positive_rate", result["evaluation"])


if __name__ == "__main__":
    unittest.main()
