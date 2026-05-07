import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util
import sys


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTrainHybridPipeline(unittest.TestCase):
    def test_run_hybrid_training_returns_artifact_manifest(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=(fake_files[:1], fake_files[1:], 0)), \
                 patch.object(m, "_load_samples", return_value=[]), \
                 patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.42, "threshold_path": "buy_threshold.json", "feature_schema_path": "feature_schema.json", "feature_names": ["current_price"]}), \
                 patch.object(m, "build_sell_env", return_value=MagicMock()), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt"}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip"}), \
                 patch.object(m, "run_ab_evaluation", return_value={"maxdd_delta": -0.25, "sortino_delta": 0.2}):
                result = m.run_hybrid_training({"output_dir": tmpdir})

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

    def test_train_buy_model_writes_feature_schema(self):
        import json
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

            schema_path = Path(out["feature_schema_path"])
            self.assertTrue(schema_path.exists())
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["feature_names"], ["buy_pressure", "current_price"])
            self.assertEqual(out["feature_names"], ["buy_pressure", "current_price"])

    def test_train_buy_model_writes_stable_feature_schema_order(self):
        import json
        import tempfile

        m = _load_module()
        samples = [
            {"features": {"buy_pressure": 0.4, "current_price": 1.0}, "label": {"max_return_pct": 20.0}, "meta": {"token_address": "A", "sample_time": 100}},
            {"features": {"current_price": 1.1, "buy_pressure": 0.8}, "label": {"max_return_pct": 120.0}, "meta": {"token_address": "B", "sample_time": 110}},
            {"features": {"buy_pressure": 0.3, "current_price": 1.2}, "label": {"max_return_pct": 10.0}, "meta": {"token_address": "C", "sample_time": 120}},
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

            schema_path = Path(out["feature_schema_path"])
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["feature_names"], ["buy_pressure", "current_price"])

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

    def test_build_sell_env_uses_multi_episode_env_for_ppo(self):
        m = _load_module()
        buy_artifact = {
            "samples": [
                {
                    "features": {
                        "current_price": 1.0,
                        "launch_fee": 0.5,
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
                        "holder_count": 42,
                        "total_buy_volume": 4.0,
                        "total_sell_volume": 2.0,
                    },
                    "meta": {"token_address": "A", "sample_time": 110},
                },
                {
                    "features": {
                        "current_price": 2.0,
                        "launch_fee": 0.6,
                        "holder_count": 45,
                        "total_buy_volume": 5.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "B", "sample_time": 120},
                },
                {
                    "features": {
                        "current_price": 2.2,
                        "launch_fee": 0.6,
                        "holder_count": 47,
                        "total_buy_volume": 6.0,
                        "total_sell_volume": 2.0,
                    },
                    "meta": {"token_address": "B", "sample_time": 130},
                },
            ]
        }

        bundle = m.build_sell_env({"liquidity_floor": 0.05, "stall_steps": 2}, buy_artifact)

        self.assertEqual(bundle["episode_count"], 2)
        self.assertEqual(type(bundle["env"]).__name__, "MultiEpisodeTradingEnv")

    def test_run_bc_warmstart_saves_weights(self):
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
        self.assertIs(out["model"], fake_model)

    def test_run_ab_evaluation_uses_eval_sample_features_for_buy_inference(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.9, 0.1] for _ in range(len(X))]

        buy_model = _FakeBuyModel()
        buy_artifact = {
            "model": buy_model,
            "threshold": 0.5,
        }
        ppo_artifact = {"total_timesteps": 0}
        bc_artifact = {"bc_samples": 0}

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            buy_artifact,
            ppo_artifact,
            bc_artifact,
        )

        self.assertEqual(out["sell_episode_count"], 1)
        self.assertGreaterEqual(len(buy_model.frames), 1)
        first_buy_input = buy_model.frames[0].iloc[0].to_dict()
        self.assertEqual(first_buy_input["total_buy_volume"], 123.0)
        self.assertEqual(first_buy_input["total_sell_volume"], 45.0)

    def test_run_ab_evaluation_batches_buy_inference_per_episode_and_skips_last_sample(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xbatched", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 11.0,
                    "total_sell_volume": 2.0,
                },
                "meta": {"token_address": "0xbatched", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 12.0,
                    "total_sell_volume": 3.0,
                },
                "meta": {"token_address": "0xbatched", "sample_time": 120},
            },
        ]

        buy_model = _FakeBuyModel()
        m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": buy_model, "threshold": 0.5},
            {"total_timesteps": 0},
            {"bc_samples": 0},
        )

        self.assertEqual(len(buy_model.frames), 1)
        self.assertEqual(len(buy_model.frames[0]), 2)
        self.assertEqual(list(buy_model.frames[0]["current_price"]), [1.0, 1.1])

    def test_run_ab_evaluation_loads_ppo_policy_from_policy_path(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                if self.calls == 1:
                    return [[0.1, 0.9] for _ in range(len(X))]
                return [[0.9, 0.1] for _ in range(len(X))]

        class _FakePolicy:
            def __init__(self):
                self.predict_calls = 0

            def predict(self, obs, deterministic=True):
                self.predict_calls += 1
                return 3, None

        fake_policy = _FakePolicy()

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 110},
            },
        ]

        with patch.object(m, "_load_ppo_policy", return_value=fake_policy) as mock_load:
            out = m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {"model": _FakeBuyModel(), "threshold": 0.5},
                {"policy_path": "sell_policy.zip", "total_timesteps": 128},
                {"bc_samples": 10},
            )

        mock_load.assert_called_once_with("sell_policy.zip")
        self.assertGreater(fake_policy.predict_calls, 0)

    def test_run_ab_evaluation_counts_forced_episode_end_liquidation_as_trade(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                if self.calls == 1:
                    return [[0.1, 0.9] for _ in range(len(X))]
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x2", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x2", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(out["win_rate"], 1.0)

    def test_run_ab_evaluation_partial_sell_preserves_cost_basis(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                if self.calls == 1:
                    return [[0.1, 0.9] for _ in range(len(X))]
                return [[0.9, 0.1] for _ in range(len(X))]

        class _FakePolicy:
            def __init__(self):
                self.calls = 0

            def predict(self, obs, deterministic=True):
                self.calls += 1
                if self.calls == 1:
                    return 1, None
                return 0, None

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x3", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x3", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x3", "sample_time": 120},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _FakePolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 2)
        self.assertEqual(out["win_rate"], 1.0)
        self.assertAlmostEqual(out["net_return_pct"], 20.0, places=6)

    def test_run_ab_evaluation_skips_last_sample_instant_entry(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x4", "sample_time": 100},
            }
        ]

        with self.assertRaisesRegex(ValueError, "no eval episodes"):
            m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {"model": _FakeBuyModel(), "threshold": 0.5},
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

    def test_run_ab_evaluation_aligns_eval_features_to_training_schema(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "holder_count": 10.0,
                    "launch_fee": 0.5,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x5", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "holder_count": 11.0,
                    "launch_fee": 0.6,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x5", "sample_time": 110},
            },
        ]

        buy_model = _FakeBuyModel()
        m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {
                "model": buy_model,
                "threshold": 0.5,
                "feature_names": ["current_price", "holder_count", "launch_fee", "total_buy_volume", "total_sell_volume"],
            },
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        first_frame = buy_model.frames[0]
        self.assertEqual(
            list(first_frame.columns),
            ["current_price", "holder_count", "launch_fee", "total_buy_volume", "total_sell_volume"],
        )
        self.assertEqual(first_frame.iloc[0]["holder_count"], 10.0)
        self.assertEqual(first_frame.iloc[0]["launch_fee"], 0.5)

    def test_run_ab_evaluation_raises_on_missing_eval_features_for_training_schema(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x5a", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x5a", "sample_time": 110},
            },
        ]

        with self.assertRaisesRegex(ValueError, "Missing expected features: holder_count, launch_fee"):
            m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {
                    "model": _FakeBuyModel(),
                    "threshold": 0.5,
                    "feature_names": ["current_price", "holder_count", "launch_fee", "total_buy_volume", "total_sell_volume"],
                },
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

    def test_run_ab_evaluation_raises_on_extra_eval_features_for_training_schema(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "holder_count": 10.0,
                    "launch_fee": 0.5,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                    "unexpected_feature": 7.0,
                },
                "meta": {"token_address": "0x5b", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "holder_count": 11.0,
                    "launch_fee": 0.6,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                    "unexpected_feature": 8.0,
                },
                "meta": {"token_address": "0x5b", "sample_time": 110},
            },
        ]

        with self.assertRaisesRegex(ValueError, "Unexpected extra features: unexpected_feature"):
            m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {
                    "model": _FakeBuyModel(),
                    "threshold": 0.5,
                    "feature_names": ["current_price", "holder_count", "launch_fee", "total_buy_volume", "total_sell_volume"],
                },
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

    def test_run_ab_evaluation_raises_on_malformed_inline_feature_schema(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x6a", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x6a", "sample_time": 110},
            },
        ]

        with self.assertRaisesRegex(ValueError, "feature_names must be a list"):
            m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {
                    "model": _FakeBuyModel(),
                    "threshold": 0.5,
                    "feature_names": "current_price",
                },
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

    def test_run_ab_evaluation_loads_feature_schema_from_artifact_path(self):
        import json
        import tempfile

        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x6", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x6", "sample_time": 110},
            },
        ]

        buy_model = _FakeBuyModel()
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "feature_schema.json"
            schema_path.write_text(
                json.dumps({"feature_names": ["current_price", "total_buy_volume", "total_sell_volume"]}),
                encoding="utf-8",
            )
            m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {
                    "model": buy_model,
                    "threshold": 0.5,
                    "feature_schema_path": str(schema_path),
                },
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

        first_frame = buy_model.frames[0]
        self.assertEqual(
            list(first_frame.columns),
            ["current_price", "total_buy_volume", "total_sell_volume"],
        )

    def test_run_ab_evaluation_raises_on_invalid_feature_schema_file_metadata(self):
        import json
        import tempfile

        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x6b", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x6b", "sample_time": 110},
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "feature_schema.json"
            schema_path.write_text(json.dumps({"feature_names": "bad"}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "feature_schema.json field 'feature_names' must be a list"):
                m.run_ab_evaluation(
                    {"eval_samples": eval_samples},
                    {
                        "model": _FakeBuyModel(),
                        "threshold": 0.5,
                        "feature_schema_path": str(schema_path),
                    },
                    {"total_timesteps": 128},
                    {"bc_samples": 10},
                )

    def test_run_ab_evaluation_raises_on_unreadable_feature_schema_file(self):
        import tempfile

        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "total_buy_volume": 123.0,
                    "total_sell_volume": 45.0,
                },
                "meta": {"token_address": "0x6c", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x6c", "sample_time": 110},
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "feature_schema.json"
            schema_path.write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "failed to read feature schema"):
                m.run_ab_evaluation(
                    {"eval_samples": eval_samples},
                    {
                        "model": _FakeBuyModel(),
                        "threshold": 0.5,
                        "feature_schema_path": str(schema_path),
                    },
                    {"total_timesteps": 128},
                    {"bc_samples": 10},
                )

    def test_run_ab_evaluation_does_not_open_on_last_sample_only_signal(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                if self.calls == 1:
                    return [[0.9, 0.1] for _ in range(len(X))]
                return [[0.1, 0.9] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x7", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.3,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 20.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x7", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 0)
        self.assertEqual(out["net_return_pct"], 0.0)

    def test_run_ab_evaluation_returns_zero_metrics_when_threshold_blocks_all_entries(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 11.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.95},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 0)
        self.assertEqual(out["win_rate"], 0.0)
        self.assertEqual(out["net_return_pct"], 0.0)
        self.assertEqual(out["max_drawdown_pct"], 0.0)
        self.assertEqual(out["sortino_ratio"], 0.0)

    def test_run_ab_evaluation_non_zero_replay_metrics(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                probs = []
                for i in range(len(X)):
                    if i == 0:
                        probs.append([0.1, 0.9])
                    else:
                        probs.append([0.9, 0.1])
                return probs

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 0.8,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x1", "sample_time": 120},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(out["win_rate"], 1.0)
        self.assertAlmostEqual(out["net_return_pct"], 20.0, places=6)
        self.assertLessEqual(out["max_drawdown_pct"], 0.0)
        self.assertEqual(out["sortino_ratio"], 0.0)

    def test_run_ab_evaluation_raises_when_no_eval_episodes_built(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        with self.assertRaisesRegex(ValueError, "no eval episodes"):
            m.run_ab_evaluation(
                {"eval_samples": []},
                {"model": _FakeBuyModel(), "threshold": 0.5},
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

    def test_run_hybrid_training_orchestrates_train_eval_file_partitions(self):
        import json
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            lifecycle_dir = tmp_path / "lifecycle"
            lifecycle_dir.mkdir(parents=True, exist_ok=True)

            all_files = [
                lifecycle_dir / "lifecycle_incremental_001.jsonl",
                lifecycle_dir / "lifecycle_incremental_002.jsonl",
                lifecycle_dir / "lifecycle_incremental_003.jsonl",
            ]
            for path in all_files:
                path.write_text("\n", encoding="utf-8")

            train_files = all_files[:2]
            eval_files = all_files[2:]
            eval_samples = [
                {
                    "features": {"current_price": 1.0, "total_buy_volume": 10.0, "total_sell_volume": 1.0},
                    "meta": {"token_address": "0xe1", "sample_time": 100},
                },
                {
                    "features": {"current_price": 1.1, "total_buy_volume": 1.0, "total_sell_volume": 9.0},
                    "meta": {"token_address": "0xe1", "sample_time": 110},
                },
            ]

            def _fake_eval(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                self.assertEqual(eval_config.get("eval_samples"), eval_samples)
                self.assertEqual(eval_config.get("train_file_count"), 2)
                self.assertEqual(eval_config.get("eval_file_count"), 1)
                self.assertEqual(eval_config.get("overlap_token_count"), 0)
                self.assertEqual(eval_config.get("raw_overlap_token_count"), 7)
                self.assertEqual(eval_config.get("excluded_eval_token_count"), 7)
                return {
                    "total_trades": 1,
                    "win_rate": 1.0,
                    "net_return_pct": 10.0,
                    "max_drawdown_pct": -1.0,
                    "sortino_ratio": 0.5,
                    "buy_threshold": 0.5,
                    "sell_episode_count": 1,
                    "bc_samples": 10,
                    "ppo_total_timesteps": 128,
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "raw_overlap_token_count": eval_config["raw_overlap_token_count"],
                    "excluded_eval_token_count": eval_config["excluded_eval_token_count"],
                    "pipeline_status": "ok",
                }

            with patch.object(m, "_discover_lifecycle_files", return_value=all_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=(train_files, eval_files, 7)), \
                 patch.object(m, "_collect_raw_token_addresses", return_value={"0xe1"}) as mock_collect_train_tokens, \
                 patch.object(
                     m,
                     "train_buy_model",
                     side_effect=lambda cfg: {
                         "model_path": "buy_model.cbm",
                         "threshold": 0.5,
                         "threshold_path": "buy_threshold.json",
                         "feature_schema_path": "feature_schema.json",
                         "feature_names": ["current_price", "launch_fee", "holder_count", "total_buy_volume", "total_sell_volume"],
                         "model": MagicMock(),
                     },
                 ) as mock_train_buy, \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128}), \
                 patch.object(m, "_load_samples", return_value=eval_samples) as mock_load_samples, \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_eval):
                result = m.run_hybrid_training({"output_dir": tmpdir, "lifecycle_dir": str(lifecycle_dir)})

            train_cfg = mock_train_buy.call_args.args[0]
            self.assertEqual(train_cfg.get("lifecycle_paths"), train_files)
            mock_collect_train_tokens.assert_called_once_with(train_files)
            self.assertEqual(mock_load_samples.call_count, 1)
            self.assertEqual(mock_load_samples.call_args.args[0].get("lifecycle_paths"), eval_files)
            self.assertEqual(mock_load_samples.call_args.args[0].get("exclude_token_addresses"), {"0xe1"})

            required = {
                "total_trades",
                "win_rate",
                "net_return_pct",
                "max_drawdown_pct",
                "sortino_ratio",
                "buy_threshold",
                "sell_episode_count",
                "bc_samples",
                "ppo_total_timesteps",
                "train_file_count",
                "eval_file_count",
                "overlap_token_count",
                "raw_overlap_token_count",
                "excluded_eval_token_count",
                "pipeline_status",
            }
            self.assertTrue(required.issubset(set(result["evaluation"].keys())))
            self.assertEqual(result["evaluation"]["train_file_count"], 2)
            self.assertEqual(result["evaluation"]["eval_file_count"], 1)
            self.assertEqual(result["evaluation"]["overlap_token_count"], 0)
            self.assertEqual(result["evaluation"]["raw_overlap_token_count"], 7)
            self.assertEqual(result["evaluation"]["excluded_eval_token_count"], 7)

            manifest = json.loads((Path(tmpdir) / "hybrid_manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(set(manifest["evaluation"].keys())))
            self.assertEqual(manifest["evaluation"]["train_file_count"], 2)
            self.assertEqual(manifest["evaluation"]["eval_file_count"], 1)
            self.assertEqual(manifest["evaluation"]["overlap_token_count"], 0)
            self.assertEqual(manifest["evaluation"]["raw_overlap_token_count"], 7)
            self.assertEqual(manifest["evaluation"]["excluded_eval_token_count"], 7)


    def test_run_hybrid_training_respects_explicit_lifecycle_paths(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit_files = [
                Path(tmpdir) / "lifecycle_incremental_003.jsonl",
                Path(tmpdir) / "lifecycle_incremental_001.jsonl",
                Path(tmpdir) / "lifecycle_incremental_002.jsonl",
            ]
            for path in explicit_files:
                path.write_text("{}\n", encoding="utf-8")

            observed = {}

            def _fake_train_buy_model(cfg):
                observed["train_config"] = dict(cfg)
                return {
                    "model_path": "buy_model.cbm",
                    "threshold": 0.42,
                    "threshold_path": "buy_threshold.json",
                    "feature_schema_path": "feature_schema.json",
                    "feature_names": ["current_price"],
                    "model": MagicMock(),
                }

            def _fake_run_ab_evaluation(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                observed["eval_config"] = dict(eval_config)
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "net_return_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "sortino_ratio": 0.0,
                    "buy_threshold": buy_artifact["threshold"],
                    "sell_episode_count": 0,
                    "bc_samples": bc_artifact["bc_samples"],
                    "ppo_total_timesteps": ppo_artifact["total_timesteps"],
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "pipeline_status": "ok",
                }

            fake_eval_samples = [
                {"features": {"current_price": 1.0}, "meta": {"token_address": "0x1", "sample_time": 100}},
                {"features": {"current_price": 1.1}, "meta": {"token_address": "0x1", "sample_time": 110}},
            ]

            with patch.object(m, "_discover_lifecycle_files") as mock_discover, \
                 patch.object(m, "_load_samples", return_value=fake_eval_samples), \
                 patch.object(m, "train_buy_model", side_effect=_fake_train_buy_model), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": object()}), \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_run_ab_evaluation):
                m.run_hybrid_training({
                    "output_dir": tmpdir,
                    "lifecycle_paths": explicit_files,
                    "train_split_ratio": 2 / 3,
                    "min_eval_files": 1,
                })

            mock_discover.assert_not_called()
            self.assertEqual(observed["train_config"]["lifecycle_paths"], [explicit_files[1], explicit_files[2]])
            self.assertEqual(observed["eval_config"]["lifecycle_paths"], [explicit_files[0]])

    def test_run_hybrid_training_preserves_explicit_eval_samples(self):
        import tempfile

        m = _load_module()
        explicit_eval_samples = [
            {"features": {"current_price": 1.0}, "meta": {"token_address": "0x9", "sample_time": 100}},
            {"features": {"current_price": 1.1}, "meta": {"token_address": "0x9", "sample_time": 110}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            def _fake_eval(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                self.assertEqual(eval_config.get("eval_samples"), explicit_eval_samples)
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "net_return_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "sortino_ratio": 0.0,
                    "buy_threshold": buy_artifact["threshold"],
                    "sell_episode_count": 0,
                    "bc_samples": bc_artifact["bc_samples"],
                    "ppo_total_timesteps": ppo_artifact["total_timesteps"],
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "pipeline_status": "ok",
                }

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=([fake_files[0]], [fake_files[1]], 0)), \
                 patch.object(m, "_load_samples") as mock_load_samples, \
                 patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.5, "threshold_path": "buy_threshold.json", "feature_schema_path": "feature_schema.json", "feature_names": ["current_price"], "model": MagicMock()}), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": object()}), \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_eval):
                m.run_hybrid_training({"output_dir": tmpdir, "eval_samples": explicit_eval_samples})

            mock_load_samples.assert_not_called()

    def test_run_hybrid_training_preserves_explicit_empty_eval_samples(self):
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            def _fake_eval(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                self.assertEqual(eval_config.get("eval_samples"), [])
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "net_return_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "sortino_ratio": 0.0,
                    "buy_threshold": buy_artifact["threshold"],
                    "sell_episode_count": 0,
                    "bc_samples": bc_artifact["bc_samples"],
                    "ppo_total_timesteps": ppo_artifact["total_timesteps"],
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "pipeline_status": "ok",
                }

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=([fake_files[0]], [fake_files[1]], 0)), \
                 patch.object(m, "_load_samples") as mock_load_samples, \
                 patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.5, "threshold_path": "buy_threshold.json", "feature_schema_path": "feature_schema.json", "feature_names": ["current_price", "launch_fee", "holder_count", "total_buy_volume", "total_sell_volume"], "model": MagicMock()}), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": object()}), \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_eval):
                m.run_hybrid_training({"output_dir": tmpdir, "eval_samples": []})

            mock_load_samples.assert_not_called()

    def test_run_hybrid_training_defers_eval_sample_loading_until_training_succeeds(self):
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=([fake_files[0]], [fake_files[1]], 0)), \
                 patch.object(m, "_load_samples") as mock_load_samples, \
                 patch.object(m, "train_buy_model", side_effect=RuntimeError("train failed")):
                with self.assertRaisesRegex(RuntimeError, "train failed"):
                    m.run_hybrid_training({"output_dir": tmpdir})

            mock_load_samples.assert_not_called()

    def test_run_hybrid_training_calls_run_ab_evaluation_without_env_bundle(self):
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            observed = {}

            def _fake_eval(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                observed["args"] = (eval_config, buy_artifact, ppo_artifact, bc_artifact)
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "net_return_pct": 0.0,
                    "max_drawdown_pct": 0.0,
                    "sortino_ratio": 0.0,
                    "buy_threshold": buy_artifact["threshold"],
                    "sell_episode_count": 0,
                    "bc_samples": bc_artifact["bc_samples"],
                    "ppo_total_timesteps": ppo_artifact["total_timesteps"],
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "pipeline_status": "ok",
                }

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=([fake_files[0]], [fake_files[1]], 0)), \
                 patch.object(m, "_load_samples", return_value=[]), \
                 patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.5, "threshold_path": "buy_threshold.json", "feature_schema_path": "feature_schema.json", "feature_names": ["current_price"], "model": MagicMock()}), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": object()}), \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_eval):
                m.run_hybrid_training({"output_dir": tmpdir})

            self.assertEqual(len(observed["args"]), 4)

    def test_run_hybrid_training_preserves_explicit_empty_lifecycle_paths(self):
        m = _load_module()

        with patch.object(m, "_discover_lifecycle_files") as mock_discover:
            with self.assertRaisesRegex(ValueError, "no lifecycle files found"):
                m.run_hybrid_training({"output_dir": "/tmp/out", "lifecycle_paths": []})

        mock_discover.assert_not_called()

    def test_run_hybrid_training_manifest_omits_non_serializable_ppo_model(self):
        import json
        import tempfile

        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.9, 0.1] for _ in range(len(X))]

        class _NonSerializablePolicy:
            pass

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0x8", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0x8", "sample_time": 110},
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=(fake_files[:1], fake_files[1:], 0)), \
                 patch.object(m, "_load_samples", return_value=eval_samples), \
                 patch.object(
                     m,
                     "train_buy_model",
                     return_value={
                         "model_path": "buy_model.cbm",
                         "threshold": 0.5,
                         "threshold_path": "buy_threshold.json",
                         "feature_schema_path": "feature_schema.json",
                         "feature_names": ["current_price", "launch_fee", "holder_count", "total_buy_volume", "total_sell_volume"],
                         "model": _FakeBuyModel(),
                     },
                 ), patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), patch.object(
                     m,
                     "run_bc_warmstart",
                     return_value={"weights": "bc.pt", "bc_samples": 10},
                 ), patch.object(
                     m,
                     "run_ppo_finetune",
                     return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": _NonSerializablePolicy()},
                 ):
                result = m.run_hybrid_training({"output_dir": tmpdir, "eval_samples": eval_samples})

            manifest = json.loads(Path(tmpdir, "hybrid_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["artifacts"]["sell_policy"], {"policy_path": "sell_policy.zip", "total_timesteps": 128})
        self.assertEqual(result["artifacts"]["sell_policy"], {"policy_path": "sell_policy.zip", "total_timesteps": 128})

    def test_pipeline_reuses_dataset_builder_lifecycle_order_helper(self):
        import tempfile
        import types

        with tempfile.TemporaryDirectory() as tmpdir:
            helper_path = Path(tmpdir) / "dataset_builder_helper.py"
            helper_path.write_text(
                "calls = []\n"
                "def stable_lifecycle_order(files, *, log=None):\n"
                "    calls.append([str(x) for x in files])\n"
                "    return list(reversed(files))\n",
                encoding="utf-8",
            )
            spec = importlib.util.spec_from_file_location("dataset_builder_helper", helper_path)
            helper_module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(helper_module)

            stub_dataset_builder = types.ModuleType("src.data.dataset_builder")
            stub_dataset_builder.DatasetBuilder = object
            stub_dataset_builder.stable_lifecycle_order = helper_module.stable_lifecycle_order

            fake_buy_catboost = types.ModuleType("src.model.buy_catboost")
            fake_buy_catboost.BuyCatBoostModel = object

            fake_hybrid_inference = types.ModuleType("src.model.hybrid_inference")
            fake_hybrid_inference.build_feature_frame = lambda features, feature_names=None: features
            fake_hybrid_inference.coerce_action = int
            fake_hybrid_inference.load_feature_names_from_schema = lambda path: None
            fake_hybrid_inference.normalize_feature_names = lambda names, **kwargs: names

            fake_trading_env = types.ModuleType("src.rl.trading_env")
            fake_trading_env.MultiEpisodeTradingEnv = object
            fake_trading_env.build_sell_observation = lambda event: event
            fake_trading_env.sell_fraction_for_action = lambda action: float(action)

            fake_train_ppo = types.ModuleType("src.rl.train_ppo")
            fake_train_ppo.train_ppo = lambda *args, **kwargs: None

            with patch.dict(
                sys.modules,
                {
                    "src.data.dataset_builder": stub_dataset_builder,
                    "src.model.buy_catboost": fake_buy_catboost,
                    "src.model.hybrid_inference": fake_hybrid_inference,
                    "src.rl.trading_env": fake_trading_env,
                    "src.rl.train_ppo": fake_train_ppo,
                },
            ):
                m = _load_module()

            files = [Path("/tmp/lifecycle_incremental_003.jsonl"), Path("/tmp/lifecycle_incremental_001.jsonl")]
            ordered = m._stable_lifecycle_order(files)

        self.assertEqual(ordered, list(reversed(files)))
        self.assertEqual(helper_module.calls, [[str(x) for x in files]])

    def test_stable_order_prefers_filename_order(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            f3 = tmp / "lifecycle_incremental_003.jsonl"
            f1 = tmp / "lifecycle_incremental_001.jsonl"
            f2 = tmp / "lifecycle_incremental_002.jsonl"
            for p in (f1, f2, f3):
                p.write_text("", encoding="utf-8")

            ordered = m._stable_lifecycle_order([f3, f1, f2])

        self.assertEqual(ordered, [f1, f2, f3])

    def test_stable_order_handles_timestamp_style_incremental_filenames(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            newer = tmp / "lifecycle_incremental_20260321_123456.jsonl"
            older = tmp / "lifecycle_incremental_20260320_235959.jsonl"
            older.write_text("", encoding="utf-8")
            newer.write_text("", encoding="utf-8")

            ordered = m._stable_lifecycle_order([newer, older])

        self.assertEqual(ordered, [older, newer])

    def test_stable_order_places_incremental_part_files_after_base_file(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            base = tmp / "lifecycle_incremental_20260406_212641.jsonl"
            part2 = tmp / "lifecycle_incremental_20260406_212641_part002.jsonl"
            part1 = tmp / "lifecycle_incremental_20260406_212641_part001.jsonl"
            newer = tmp / "lifecycle_incremental_20260407_000000.jsonl"
            for path in (newer, part2, base, part1):
                path.write_text("", encoding="utf-8")

            ordered = m._stable_lifecycle_order([newer, part2, base, part1])

        self.assertEqual(ordered, [base, part1, part2, newer])

    def test_stable_order_falls_back_to_mtime_and_logs(self):
        import os
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            older = tmp / "alpha.jsonl"
            newer = tmp / "beta.jsonl"
            older.write_text("", encoding="utf-8")
            newer.write_text("", encoding="utf-8")
            os.utime(older, (1000, 1000))
            os.utime(newer, (2000, 2000))

            with patch.object(m.logger, "info") as log_info:
                ordered = m._stable_lifecycle_order([newer, older])

        self.assertEqual(ordered, [older, newer])
        log_info.assert_any_call("Lifecycle ordering fallback to mtime for non-standard filenames")

    def test_stable_order_keeps_standard_files_first_and_fallbacks_non_standard_by_mtime(self):
        import os
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            std2 = tmp / "lifecycle_incremental_002.jsonl"
            std1 = tmp / "lifecycle_incremental_001.jsonl"
            weird_old = tmp / "alpha.jsonl"
            weird_new = tmp / "beta.jsonl"
            for p in (std1, std2, weird_old, weird_new):
                p.write_text("", encoding="utf-8")
            os.utime(weird_old, (1000, 1000))
            os.utime(weird_new, (2000, 2000))

            with patch.object(m.logger, "info") as log_info:
                ordered = m._stable_lifecycle_order([weird_new, std2, weird_old, std1])

        self.assertEqual(ordered, [std1, std2, weird_old, weird_new])
        log_info.assert_any_call("Lifecycle ordering fallback to mtime for non-standard filenames")

    def test_discover_lifecycle_files_supports_timestamp_style_snapshot_when_no_incrementals_exist(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            older = tmp / "lifecycle_20260320_235959.jsonl"
            newer = tmp / "lifecycle_20260321_123456.jsonl"
            older.write_text("{}\n", encoding="utf-8")
            newer.write_text("{}\n", encoding="utf-8")

            discovered = m._discover_lifecycle_files(tmpdir)

        self.assertEqual(discovered, [older, newer])

    def test_discover_lifecycle_files_prefers_incremental_files_over_snapshot_duplicates(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            inc1 = tmp / "lifecycle_incremental_001.jsonl"
            inc2 = tmp / "lifecycle_incremental_002.jsonl"
            snapshot = tmp / "lifecycle_999999.jsonl"
            inc1.write_text("{}\n", encoding="utf-8")
            inc2.write_text("{}\n", encoding="utf-8")
            snapshot.write_text("{}\n", encoding="utf-8")

            discovered = m._discover_lifecycle_files(tmpdir)

        self.assertEqual(discovered, [inc1, inc2])

    def test_discover_lifecycle_files_raises_when_no_files_found(self):
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "no lifecycle files found"):
                m._discover_lifecycle_files(tmpdir)

    def test_split_lifecycle_files_raises_on_invalid_split_ratio(self):
        m = _load_module()
        files = [
            Path("/tmp/lifecycle_incremental_001.jsonl"),
            Path("/tmp/lifecycle_incremental_002.jsonl"),
        ]

        with self.assertRaisesRegex(ValueError, "train_split_ratio must be between 0 and 1"):
            m._split_lifecycle_files(files, train_split_ratio=-0.1, min_eval_files=1)

        with self.assertRaisesRegex(ValueError, "train_split_ratio must be between 0 and 1"):
            m._split_lifecycle_files(files, train_split_ratio=1.1, min_eval_files=1)

    def test_split_lifecycle_files_raises_when_no_train_files_after_split(self):
        m = _load_module()
        files = [Path("/tmp/lifecycle_incremental_001.jsonl")]
        with self.assertRaisesRegex(ValueError, "train_split_ratio must be between 0 and 1"):
            m._split_lifecycle_files(files, train_split_ratio=0.0, min_eval_files=1)

    def test_split_lifecycle_files_raises_when_eval_split_is_empty(self):
        m = _load_module()
        files = [
            Path("/tmp/lifecycle_incremental_001.jsonl"),
            Path("/tmp/lifecycle_incremental_002.jsonl"),
        ]
        with self.assertRaisesRegex(ValueError, "train_split_ratio must be between 0 and 1"):
            m._split_lifecycle_files(files, train_split_ratio=1.0, min_eval_files=1)


    def test_split_lifecycle_files_raises_when_train_eval_tokens_overlap(self):
        import json
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            train_path = tmp_path / "lifecycle_incremental_001.jsonl"
            eval_path = tmp_path / "lifecycle_incremental_002.jsonl"
            train_path.write_text(json.dumps({"token_address": "0xabc"}) + "\n", encoding="utf-8")
            eval_path.write_text(json.dumps({"token_address": "0xAbC"}) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "train/eval leakage detected"):
                m._split_lifecycle_files([train_path, eval_path], train_split_ratio=0.5, min_eval_files=1)

    def test_split_lifecycle_files_can_report_overlap_without_raising(self):
        import json
        import tempfile

        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            train_path = tmp_path / "lifecycle_incremental_001.jsonl"
            eval_path = tmp_path / "lifecycle_incremental_002.jsonl"
            train_path.write_text(json.dumps({"token_address": "0xabc"}) + "\n", encoding="utf-8")
            eval_path.write_text(json.dumps({"token_address": "0xAbC"}) + "\n", encoding="utf-8")

            train_files, eval_files, overlap = m._split_lifecycle_files(
                [train_path, eval_path],
                train_split_ratio=0.5,
                min_eval_files=1,
                enforce_no_overlap=False,
            )

        self.assertEqual(train_files, [train_path])
        self.assertEqual(eval_files, [eval_path])
        self.assertEqual(overlap, 1)

    def test_split_lifecycle_files_raises_when_multiple_train_eval_tokens_overlap(self):
        import json
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            train_path = tmp_path / "lifecycle_incremental_001.jsonl"
            eval_path = tmp_path / "lifecycle_incremental_002.jsonl"

            train_rows = [
                {"token_address": "0xAAA"},
                {"token_address": "0xaaa"},
                {"token_address": "0xBBB"},
            ]
            eval_rows = [
                {"token_address": "0xAaA"},
                {"token_address": "0xCCC"},
            ]

            train_path.write_text("\n".join(json.dumps(r) for r in train_rows) + "\n", encoding="utf-8")
            eval_path.write_text("\n".join(json.dumps(r) for r in eval_rows) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "train/eval leakage detected"):
                m._split_lifecycle_files(
                    [train_path, eval_path],
                    train_split_ratio=0.5,
                    min_eval_files=1,
                )

    def test_sample_to_event_path_can_reach_highest_bc_action_bucket(self):
        m = _load_module()

        sample = {
            "features": {
                "current_price": 1.0,
                "launch_fee": 0.5,
                "holder_count": 10,
                "total_buy_volume": 0.0,
                "total_sell_volume": 10.0,
            },
            "meta": {"sample_time": 123},
        }

        event = m._sample_to_event(sample)
        _, actions = m._build_bc_arrays([[event]])

        self.assertLessEqual(event["sell_pressure"], 1.0)
        self.assertEqual(int(actions[0]), 3)

    def test_build_bc_arrays_reuses_rule_exit_action_thresholds(self):
        m = _load_module()
        event = {
            "mid_price": 1.0,
            "lp_depth": 1.0,
            "sell_pressure": 0.92,
            "buy_sell_ratio": 0.5,
            "holders": 10,
        }

        _, actions = m._build_bc_arrays([[event]])

        self.assertEqual(int(actions[0]), 3)


if __name__ == "__main__":
    unittest.main()
