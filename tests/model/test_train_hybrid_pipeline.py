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

    def test_limit_samples_per_token_keeps_even_time_coverage(self):
        m = _load_module()
        samples = [
            {
                "features": {"current_price": float(index)},
                "label": {"max_return_pct": float(index)},
                "meta": {"token_address": "A", "sample_time": 100 + index, "sample_interval": index},
            }
            for index in range(10)
        ]

        limited = m._limit_samples_per_token(samples, 4)

        self.assertEqual([sample["meta"]["sample_interval"] for sample in limited], [0, 3, 6, 9])

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

    def test_train_buy_model_defaults_to_executable_return_target(self):
        import tempfile
        m = _load_module()
        samples = [
            {"features": {"current_price": 1.0, "signal": 0.1}, "label": {"max_return_pct": 200.0, "executable_return_pct": 10.0}, "meta": {"token_address": "A", "sample_time": 100}},
            {"features": {"current_price": 1.1, "signal": 0.2}, "label": {"max_return_pct": 10.0, "executable_return_pct": 120.0}, "meta": {"token_address": "B", "sample_time": 110}},
            {"features": {"current_price": 1.2, "signal": 0.3}, "label": {"max_return_pct": 160.0, "executable_return_pct": 20.0}, "meta": {"token_address": "C", "sample_time": 120}},
            {"features": {"current_price": 1.3, "signal": 0.4}, "label": {"max_return_pct": 5.0, "executable_return_pct": 140.0}, "meta": {"token_address": "D", "sample_time": 130}},
        ]
        observed = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_load_samples", return_value=samples), \
                 patch.object(m, "BuyCatBoostModel") as MockModel:
                fake = MagicMock()

                def _fit(X, y, eval_set=None):
                    observed["labels"] = list(y)
                    return fake

                def _predict_proba(X):
                    return [[0.4, 0.6] for _ in range(len(X))]

                def _save_model(path):
                    Path(path).write_text("cbm", encoding="utf-8")

                fake.fit.side_effect = _fit
                fake.predict_proba.side_effect = _predict_proba
                fake.select_threshold.return_value = 0.42
                fake.model = MagicMock()
                fake.model.save_model.side_effect = _save_model
                MockModel.return_value = fake

                out = m.train_buy_model(
                    {
                        "output_dir": tmpdir,
                        "target_threshold_value": 80.0,
                        "buy_calibration_ratio": 0.0,
                    }
                )

        self.assertEqual(observed["labels"], [0, 1, 0, 1])
        self.assertEqual(out["target_label_column"], "executable_return_pct")

    def test_load_samples_passes_execution_label_controls_to_builder(self):
        m = _load_module()
        fake_builder = MagicMock()
        fake_builder.samples = []

        with patch.object(m, "DatasetBuilder", return_value=fake_builder) as MockBuilder:
            samples = m._load_samples(
                {
                    "lifecycle_dir": "data/training",
                    "fee_bps": 80.0,
                    "slippage_bps": 150.0,
                    "stop_loss": -0.4,
                    "target_threshold_value": 60.0,
                    "max_samples_per_token": 10,
                }
            )

        self.assertEqual(samples, [])
        kwargs = MockBuilder.call_args.kwargs
        self.assertEqual(kwargs["label_fee_bps"], 80.0)
        self.assertEqual(kwargs["label_slippage_bps"], 150.0)
        self.assertEqual(kwargs["label_stop_loss_pct"], -40.0)
        self.assertEqual(kwargs["label_target_return_pct"], 60.0)
        fake_builder.load_lifecycle_files.assert_called_once()

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

    def test_train_buy_model_uses_calibration_samples_for_threshold_selection(self):
        import tempfile

        m = _load_module()
        samples = [
            {"features": {"signal": 0.10, "current_price": 1.0}, "label": {"max_return_pct": 10.0}, "meta": {"token_address": "A", "sample_time": 100}},
            {"features": {"signal": 0.20, "current_price": 1.1}, "label": {"max_return_pct": 120.0}, "meta": {"token_address": "B", "sample_time": 110}},
            {"features": {"signal": 0.30, "current_price": 1.2}, "label": {"max_return_pct": 20.0}, "meta": {"token_address": "C", "sample_time": 120}},
            {"features": {"signal": 0.40, "current_price": 1.3}, "label": {"max_return_pct": 160.0}, "meta": {"token_address": "D", "sample_time": 130}},
            {"features": {"signal": 0.50, "current_price": 1.4}, "label": {"max_return_pct": 15.0}, "meta": {"token_address": "E", "sample_time": 140}},
            {"features": {"signal": 0.60, "current_price": 1.5}, "label": {"max_return_pct": 180.0}, "meta": {"token_address": "F", "sample_time": 150}},
            {"features": {"signal": 0.70, "current_price": 1.6}, "label": {"max_return_pct": 25.0}, "meta": {"token_address": "G", "sample_time": 160}},
            {"features": {"signal": 0.80, "current_price": 1.7}, "label": {"max_return_pct": 220.0}, "meta": {"token_address": "H", "sample_time": 170}},
        ]

        observed = {}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_load_samples", return_value=samples), \
                 patch.object(m, "BuyCatBoostModel") as MockModel:
                fake = MagicMock()

                def _fit(X, y, eval_set=None):
                    observed["fit_len"] = len(X)
                    observed["eval_len"] = len(eval_set[0])
                    observed["eval_labels"] = list(eval_set[1])
                    return fake

                def _predict_proba(X):
                    observed["predict_len"] = len(X)
                    return [[0.4, 0.6] for _ in range(len(X))]

                def _save_model(path):
                    Path(path).write_text("cbm", encoding="utf-8")

                fake.fit.side_effect = _fit
                fake.predict_proba.side_effect = _predict_proba
                fake.select_threshold.return_value = 0.64
                fake.model = MagicMock()
                fake.model.save_model.side_effect = _save_model
                MockModel.return_value = fake

                out = m.train_buy_model(
                    {
                        "output_dir": tmpdir,
                        "target_label_column": "max_return_pct",
                        "target_threshold_value": 80.0,
                        "buy_calibration_ratio": 0.5,
                        "min_calibration_samples": 2,
                        "buy_min_calibration_predictions": 1,
                    }
                )

        self.assertLess(observed["fit_len"], len(samples))
        self.assertGreater(observed["eval_len"], 0)
        self.assertEqual(observed["predict_len"], observed["eval_len"])
        self.assertEqual(len(fake.select_threshold.call_args.args[0]), observed["eval_len"])
        self.assertEqual(out["threshold_source"], "calibration")
        self.assertEqual(out["calibration"]["sample_count"], observed["eval_len"])

    def test_train_buy_model_prunes_invalid_and_constant_features_from_schema(self):
        import json
        import tempfile

        m = _load_module()
        samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "future_window": 240,
                    "target_hint": 0.1,
                    "label_debug": 1,
                    "constant_feature": 7.0,
                },
                "label": {"max_return_pct": 20.0},
                "meta": {"token_address": "A", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "future_window": 240,
                    "target_hint": 0.2,
                    "label_debug": 0,
                    "constant_feature": 7.0,
                },
                "label": {"max_return_pct": 120.0},
                "meta": {"token_address": "B", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.4,
                    "future_window": 240,
                    "target_hint": 0.3,
                    "label_debug": 1,
                    "constant_feature": 7.0,
                },
                "label": {"max_return_pct": 10.0},
                "meta": {"token_address": "C", "sample_time": 120},
            },
            {
                "features": {
                    "current_price": 1.6,
                    "future_window": 240,
                    "target_hint": 0.4,
                    "label_debug": 0,
                    "constant_feature": 7.0,
                },
                "label": {"max_return_pct": 200.0},
                "meta": {"token_address": "D", "sample_time": 130},
            },
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

                out = m.train_buy_model(
                    {
                        "output_dir": tmpdir,
                        "target_label_column": "max_return_pct",
                        "target_threshold_value": 80.0,
                        "buy_calibration_ratio": 0.0,
                    }
                )

            schema_path = Path(out["feature_schema_path"])
            schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["feature_names"], ["current_price"])
        self.assertEqual(out["feature_names"], ["current_price"])
        self.assertIn("future_window", out["dropped_features"]["invalid"])
        self.assertIn("target_hint", out["dropped_features"]["invalid"])
        self.assertIn("label_debug", out["dropped_features"]["invalid"])
        self.assertIn("constant_feature", out["dropped_features"]["constant"])

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

    def test_build_sell_env_prefers_fit_samples_over_calibration_samples(self):
        m = _load_module()
        buy_artifact = {
            "samples": [
                {
                    "features": {
                        "current_price": 9.0,
                        "launch_fee": 0.5,
                        "holder_count": 10,
                        "total_buy_volume": 1.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "CAL", "sample_time": 100},
                },
                {
                    "features": {
                        "current_price": 9.1,
                        "launch_fee": 0.5,
                        "holder_count": 11,
                        "total_buy_volume": 1.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "CAL", "sample_time": 110},
                },
            ],
            "sell_training_samples": [
                {
                    "features": {
                        "current_price": 1.0,
                        "launch_fee": 0.5,
                        "holder_count": 20,
                        "total_buy_volume": 2.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "FIT", "sample_time": 100},
                },
                {
                    "features": {
                        "current_price": 1.1,
                        "launch_fee": 0.5,
                        "holder_count": 21,
                        "total_buy_volume": 2.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "FIT", "sample_time": 110},
                },
            ],
        }

        bundle = m.build_sell_env({"liquidity_floor": 0.05, "stall_steps": 2}, buy_artifact)

        self.assertEqual(bundle["episode_count"], 1)
        self.assertEqual(bundle["episodes"][0][0]["mid_price"], 1.0)

    def test_build_sell_env_passes_execution_and_reward_controls(self):
        m = _load_module()
        buy_artifact = {
            "sell_training_samples": [
                {
                    "features": {
                        "current_price": 1.0,
                        "launch_fee": 0.5,
                        "holder_count": 10,
                        "total_buy_volume": 10.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "FIT", "sample_time": 100},
                },
                {
                    "features": {
                        "current_price": 1.1,
                        "launch_fee": 0.5,
                        "holder_count": 11,
                        "total_buy_volume": 10.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "FIT", "sample_time": 110},
                },
            ],
        }

        bundle = m.build_sell_env(
            {
                "fee_bps": 100.0,
                "slippage_bps": 200.0,
                "sell_drawdown_penalty_weight": 0.5,
                "sell_hold_penalty_per_step": 0.01,
                "sell_turnover_penalty": 0.02,
                "allow_partial_exits": True,
            },
            buy_artifact,
        )

        env = bundle["env"]
        self.assertAlmostEqual(env.fee_bps, 100.0)
        self.assertAlmostEqual(env.slippage_bps, 200.0)
        self.assertAlmostEqual(env.drawdown_penalty_weight, 0.5)
        self.assertAlmostEqual(env.hold_penalty_per_step, 0.01)
        self.assertAlmostEqual(env.turnover_penalty, 0.02)
        self.assertTrue(env.allow_partial_exits)

    def test_tune_buy_threshold_by_replay_prefers_feasible_drawdown(self):
        m = _load_module()

        class _ScoreBuyModel:
            def predict_proba(self, X):
                return [[1.0 - float(row["score"]), float(row["score"])] for _, row in X.iterrows()]

        samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "score": 0.6,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "LOSE", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 0.4,
                    "score": 0.6,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "LOSE", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.0,
                    "score": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 20,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "WIN", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.5,
                    "score": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 21,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "WIN", "sample_time": 110},
            },
        ]

        tuned = m._tune_buy_threshold_by_replay(
            {
                "risk_tune_buy_threshold": True,
                "risk_tune_thresholds": [0.5, 0.8],
                "risk_tune_min_trades": 1,
                "risk_tune_max_drawdown_pct": -30.0,
                "position_fraction": 1.0,
            },
            {
                "model": _ScoreBuyModel(),
                "threshold": 0.5,
                "calibration_samples": samples,
            },
            {"model": None},
        )

        self.assertGreaterEqual(tuned["threshold"], 0.8)
        self.assertEqual(tuned["replay"]["total_trades"], 1)
        self.assertGreaterEqual(tuned["replay"]["max_drawdown_pct"], -30.0)

    def test_tune_buy_threshold_by_replay_rejects_excessive_turnover(self):
        m = _load_module()

        class _ScoreBuyModel:
            def predict_proba(self, X):
                return [[1.0 - float(row["score"]), float(row["score"])] for _, row in X.iterrows()]

        samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "score": 0.6,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "LOW", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "score": 0.6,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "LOW", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.0,
                    "score": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 20,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "HIGH", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "score": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 21,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "HIGH", "sample_time": 110},
            },
        ]

        tuned = m._tune_buy_threshold_by_replay(
            {
                "risk_tune_buy_threshold": True,
                "risk_tune_thresholds": [0.5, 0.8],
                "risk_tune_min_trades": 1,
                "risk_tune_max_trades": 1,
                "risk_tune_max_drawdown_pct": -30.0,
                "risk_tune_min_win_rate": 0.0,
                "position_fraction": 1.0,
                "one_entry_per_token": False,
            },
            {
                "model": _ScoreBuyModel(),
                "threshold": 0.5,
                "calibration_samples": samples,
            },
            {"model": None},
        )

        self.assertGreaterEqual(tuned["threshold"], 0.8)
        self.assertEqual(tuned["replay"]["total_trades"], 1)
        low_candidate = next(candidate for candidate in tuned["candidates"] if candidate["threshold"] == 0.5)
        self.assertFalse(low_candidate["feasible"])
        self.assertEqual(tuned["constraints"]["max_trades"], 1)

    def test_tune_buy_threshold_by_replay_uses_probability_coverage_candidates(self):
        m = _load_module()

        class _ScoreBuyModel:
            def predict_proba(self, X):
                return [[1.0 - float(row["score"]), float(row["score"])] for _, row in X.iterrows()]

        samples = []
        for token, score in [
            ("T1", 0.93),
            ("T2", 0.91),
            ("T3", 0.89),
            ("T4", 0.87),
        ]:
            samples.extend(
                [
                    {
                        "features": {
                            "current_price": 1.0,
                            "score": score,
                            "launch_fee": 0.5,
                            "holder_count": 20,
                            "total_buy_volume": 10.0,
                            "total_sell_volume": 1.0,
                        },
                        "meta": {"token_address": token, "sample_time": 100},
                    },
                    {
                        "features": {
                            "current_price": 1.2,
                            "score": score,
                            "launch_fee": 0.5,
                            "holder_count": 21,
                            "total_buy_volume": 1.0,
                            "total_sell_volume": 9.0,
                        },
                        "meta": {"token_address": token, "sample_time": 110},
                    },
                ]
            )

        tuned = m._tune_buy_threshold_by_replay(
            {
                "risk_tune_buy_threshold": True,
                "risk_tune_min_threshold": 0.0,
                "risk_tune_candidate_entry_rates": [0.75],
                "risk_tune_min_trades": 3,
                "risk_tune_max_trades": 3,
                "risk_tune_max_drawdown_pct": -50.0,
                "risk_tune_min_win_rate": 0.0,
                "position_fraction": 1.0,
            },
            {
                "model": _ScoreBuyModel(),
                "threshold": 1.0,
                "calibration_samples": samples,
            },
            {"model": None},
        )

        self.assertEqual(tuned["status"], "selected")
        self.assertEqual(tuned["replay"]["entry_count"], 3)
        self.assertEqual(tuned["replay"]["total_trades"], 3)
        self.assertGreater(tuned["threshold"], 0.87)
        self.assertLessEqual(tuned["threshold"], 0.89)

    def test_risk_tune_replay_score_prefers_target_entry_rate(self):
        m = _load_module()
        config = {
            "risk_tune_turnover_penalty": 0.0,
            "risk_tune_target_entry_rate": 0.5,
            "risk_tune_entry_rate_penalty": 1.0,
        }
        base = {
            "total_trades": 5,
            "net_return_pct": 10.0,
            "max_drawdown_pct": -5.0,
            "episode_count": 10,
        }

        on_target = dict(base, entry_count=5, entry_rate=0.5)
        under_target = dict(base, entry_count=1, entry_rate=0.1)

        self.assertGreater(
            m._risk_tune_replay_score(config, on_target),
            m._risk_tune_replay_score(config, under_target),
        )

    def test_risk_tune_turnover_penalty_uses_entry_rate_not_absolute_count(self):
        m = _load_module()
        config = {
            "risk_tune_turnover_penalty": 1.0,
            "risk_tune_target_entry_rate": None,
            "risk_tune_entry_rate_penalty": 0.0,
        }
        small_calibration = {
            "total_trades": 10,
            "entry_count": 10,
            "entry_rate": 1.0,
            "episode_count": 10,
            "net_return_pct": 100.0,
            "max_drawdown_pct": -5.0,
        }
        large_calibration = {
            "total_trades": 1000,
            "entry_count": 1000,
            "entry_rate": 1.0,
            "episode_count": 1000,
            "net_return_pct": 100.0,
            "max_drawdown_pct": -5.0,
        }

        self.assertAlmostEqual(
            m._risk_tune_replay_score(config, small_calibration),
            m._risk_tune_replay_score(config, large_calibration),
        )

    def test_tune_buy_threshold_by_replay_rejects_entry_rate_above_max(self):
        m = _load_module()

        class _ScoreBuyModel:
            def predict_proba(self, X):
                return [[1.0 - float(row["score"]), float(row["score"])] for _, row in X.iterrows()]

        samples = []
        for token, score in [("LOW", 0.6), ("HIGH", 0.9)]:
            samples.extend(
                [
                    {
                        "features": {
                            "current_price": 1.0,
                            "score": score,
                            "launch_fee": 0.5,
                            "holder_count": 10,
                            "total_buy_volume": 10.0,
                            "total_sell_volume": 1.0,
                        },
                        "meta": {"token_address": token, "sample_time": 100},
                    },
                    {
                        "features": {
                            "current_price": 1.1,
                            "score": score,
                            "launch_fee": 0.5,
                            "holder_count": 11,
                            "total_buy_volume": 1.0,
                            "total_sell_volume": 9.0,
                        },
                        "meta": {"token_address": token, "sample_time": 110},
                    },
                ]
            )

        tuned = m._tune_buy_threshold_by_replay(
            {
                "risk_tune_buy_threshold": True,
                "risk_tune_thresholds": [0.5, 0.8],
                "risk_tune_min_trades": 1,
                "risk_tune_max_drawdown_pct": -50.0,
                "risk_tune_min_win_rate": 0.0,
                "risk_tune_max_entry_rate": 0.5,
                "position_fraction": 1.0,
            },
            {
                "model": _ScoreBuyModel(),
                "threshold": 0.5,
                "calibration_samples": samples,
            },
            {"model": None},
        )

        self.assertEqual(tuned["status"], "selected")
        self.assertGreater(tuned["threshold"], 0.5)
        self.assertLessEqual(tuned["replay"]["entry_rate"], 0.5)
        low_candidate = next(candidate for candidate in tuned["candidates"] if candidate["threshold"] == 0.5)
        self.assertFalse(low_candidate["feasible"])
        self.assertEqual(tuned["constraints"]["max_entry_rate"], 0.5)

    def test_risk_tune_reuses_buy_probabilities_across_threshold_candidates(self):
        m = _load_module()

        class _CountingBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                return [[1.0 - float(row["score"]), float(row["score"])] for _, row in X.iterrows()]

        buy_model = _CountingBuyModel()
        samples = [
            {
                "features": {"current_price": 1.0, "score": 0.92},
                "meta": {"token_address": "0xreuse", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.1, "score": 0.10},
                "meta": {"token_address": "0xreuse", "sample_time": 110},
            },
        ]

        tuned = m._tune_buy_threshold_by_replay(
            {
                "risk_tune_buy_threshold": True,
                "risk_tune_thresholds": [0.5, 0.7, 0.9],
                "risk_tune_min_threshold": 0.0,
                "risk_tune_min_trades": 1,
                "risk_tune_max_drawdown_pct": -100.0,
                "risk_tune_min_win_rate": 0.0,
                "position_fraction": 1.0,
            },
            {"model": buy_model, "threshold": 1.0, "calibration_samples": samples},
            {"model": None},
        )

        self.assertEqual(tuned["status"], "selected")
        self.assertEqual(buy_model.calls, 1)

    def test_risk_tune_threshold_candidates_do_not_include_raw_probability_grid_by_default(self):
        m = _load_module()

        probability_values = [index / 1000.0 for index in range(1000)]

        candidates = m._risk_tune_threshold_candidates(
            {
                "risk_tune_min_threshold": 0.0,
                "risk_tune_candidate_entry_rates": [0.10, 0.25, 0.50],
                "risk_tune_target_entry_rate": 0.15,
            },
            0.5,
            probability_values,
        )

        self.assertLessEqual(len(candidates), 20)

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

    def test_run_ab_evaluation_reuses_buy_probabilities_for_all_in_replay(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.calls = 0

            def predict_proba(self, X):
                self.calls += 1
                return [[0.1, 0.9] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {"current_price": 1.0, "signal": 0.9},
                "meta": {"token_address": "0xreuse-eval", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.2, "signal": 0.8},
                "meta": {"token_address": "0xreuse-eval", "sample_time": 110},
            },
        ]

        buy_model = _FakeBuyModel()
        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "position_fraction": 0.1},
            {"model": buy_model, "threshold": 0.5},
            {"total_timesteps": 0},
            {"bc_samples": 0},
        )

        self.assertEqual(buy_model.calls, 1)
        self.assertEqual(out["entry_rate"], out["runtime_replay"]["entry_rate"])

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
            {"eval_samples": eval_samples, "allow_partial_exits": True},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _FakePolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 2)
        self.assertEqual(out["win_rate"], 1.0)
        self.assertAlmostEqual(out["net_return_pct"], 2.0, places=6)
        self.assertTrue(out["allow_partial_exits"])

    def test_run_ab_evaluation_canonicalizes_partial_policy_actions_when_partial_exits_disabled(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellHalfPolicy:
            def predict(self, obs, deterministic=True):
                return 2, None

        eval_samples = [
            {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10 + idx,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xsingleexit", "sample_time": 100 + idx},
            }
            for idx, price in enumerate([1.0, 1.1, 1.2, 1.3])
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "include_trade_log": True},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _SellHalfPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["entry_count"], 1)
        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(out["runtime_replay"]["episode_count"], 1)
        self.assertAlmostEqual(out["runtime_replay"]["entry_rate"], 1.0)
        self.assertEqual(len(out["trade_log"]), 1)
        self.assertEqual(out["trade_log"][0]["exit_reason"], "SELL100")
        self.assertEqual(out["trade_log"][0]["requested_size_fraction"], 1.0)
        self.assertEqual(out["trade_log"][0]["size_fraction"], 1.0)
        self.assertFalse(out["allow_partial_exits"])

    def test_run_ab_evaluation_orders_exits_by_sample_time(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        def sample(token, sample_time, price):
            return {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": token, "sample_time": sample_time},
            }

        eval_samples = [
            sample("0xslow", 100, 1.0),
            sample("0xslow", 200, 2.0),
            sample("0xfast", 150, 1.0),
            sample("0xfast", 160, 2.0),
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "include_trade_log": True, "position_fraction": 0.1},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual([trade["exit_time"] for trade in out["trade_log"]], [160, 200])

    def test_run_ab_evaluation_caps_position_stake_fraction(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        eval_samples = []
        for token_index, start_time in enumerate([100, 200]):
            for offset, price in enumerate([1.0, 2.0]):
                eval_samples.append(
                    {
                        "features": {
                            "current_price": price,
                            "launch_fee": 0.5,
                            "holder_count": 10,
                            "total_buy_volume": 10.0,
                            "total_sell_volume": 1.0,
                        },
                        "meta": {
                            "token_address": f"0xcap{token_index}",
                            "sample_time": start_time + offset,
                        },
                    }
                )

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "position_fraction": 1.0,
                "max_position_fraction": 0.1,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 2)
        self.assertAlmostEqual(out["net_return_pct"], 20.0, places=6)
        self.assertEqual(out["max_position_fraction"], 0.1)

    def test_run_ab_evaluation_enforces_stop_loss_before_policy_exit(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _HoldPolicy:
            def __init__(self):
                self.calls = 0

            def predict(self, obs, deterministic=True):
                self.calls += 1
                return 0, None

        policy = _HoldPolicy()
        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xstop", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 0.4,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0xstop", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 2.0,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xstop", "sample_time": 120},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "stop_loss": -0.5},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": policy},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(out["win_rate"], 0.0)
        self.assertAlmostEqual(out["net_return_pct"], -6.0, places=6)
        self.assertEqual(policy.calls, 0)

    def test_run_ab_evaluation_position_fraction_reduces_runtime_drawdown(self):
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
                "meta": {"token_address": "0xsize", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 0.4,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0xsize", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "stop_loss": -0.5,
                "position_fraction": 0.1,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertAlmostEqual(out["net_return_pct"], -6.0, places=6)
        self.assertAlmostEqual(out["max_drawdown_pct"], -6.0, places=6)
        self.assertAlmostEqual(out["all_in_replay"]["net_return_pct"], -60.0, places=6)
        self.assertAlmostEqual(out["runtime_replay"]["net_return_pct"], -6.0, places=6)

    def test_run_ab_evaluation_applies_entry_and_exit_costs(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xcost", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 2.0,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xcost", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "fee_bps": 100.0,
                "slippage_bps": 100.0,
                "include_trade_log": True,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertLess(out["net_return_pct"], 100.0)
        self.assertAlmostEqual(out["fee_bps"], 100.0)
        self.assertAlmostEqual(out["slippage_bps"], 100.0)
        self.assertLess(out["trade_log"][0]["return_pct"], 100.0)

    def test_run_ab_evaluation_entry_delay_uses_later_fill_price(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        def sample(sample_time, price, buy_volume=10.0, sell_volume=1.0):
            return {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": buy_volume,
                    "total_sell_volume": sell_volume,
                },
                "meta": {"token_address": "0xdelayentry", "sample_time": sample_time},
            }

        eval_samples = [
            sample(100, 1.0),
            sample(103, 2.0),
            sample(110, 3.0, buy_volume=1.0, sell_volume=9.0),
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "include_trade_log": True, "entry_delay_seconds": 2},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["trade_log"][0]["entry_time"], 103)
        self.assertEqual(out["trade_log"][0]["entry_index"], 1)
        self.assertAlmostEqual(out["trade_log"][0]["entry_price"], 2.0)
        self.assertAlmostEqual(out["trade_log"][0]["return_pct"], 50.0)
        self.assertEqual(out["runtime_replay"]["entry_delay_seconds"], 2)

    def test_run_ab_evaluation_exit_delay_uses_later_fill_price(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        def sample(sample_time, price):
            return {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xdelayexit", "sample_time": sample_time},
            }

        eval_samples = [sample(100, 1.0), sample(110, 2.0), sample(115, 1.0)]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "include_trade_log": True, "exit_delay_seconds": 3},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["trade_log"][0]["exit_time"], 115)
        self.assertAlmostEqual(out["trade_log"][0]["exit_price"], 1.0)
        self.assertAlmostEqual(out["trade_log"][0]["return_pct"], 0.0)
        self.assertEqual(out["runtime_replay"]["exit_delay_seconds"], 3)

    def test_run_ab_evaluation_max_open_positions_limits_concurrent_entries(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        def sample(token, sample_time, price):
            return {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": token, "sample_time": sample_time},
            }

        eval_samples = [
            sample("0xcapone", 100, 1.0),
            sample("0xcaptwo", 100, 1.0),
            sample("0xcapone", 110, 2.0),
            sample("0xcaptwo", 110, 2.0),
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "include_trade_log": True, "max_open_positions": 1},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["entry_count"], 1)
        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(out["runtime_replay"]["max_open_positions"], 1)

    def test_run_ab_evaluation_one_entry_per_token_blocks_reentry(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        eval_samples = [
            {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10 + idx,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xrepeat", "sample_time": 100 + idx},
            }
            for idx, price in enumerate([1.0, 1.1, 1.2, 1.3])
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "one_entry_per_token": True,
                "include_trade_log": True,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["total_trades"], 1)
        self.assertEqual(len(out["trade_log"]), 1)
        self.assertTrue(out["one_entry_per_token"])

    def test_run_ab_evaluation_includes_trade_log_when_requested(self):
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
                "meta": {"token_address": "0xlog", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 0.4,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0xlog", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "stop_loss": -0.5,
                "position_fraction": 0.1,
                "include_trade_log": True,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(len(out["trade_log"]), 1)
        trade = out["trade_log"][0]
        self.assertEqual(trade["token"], "0xlog")
        self.assertEqual(trade["exit_reason"], "STOP_LOSS")
        self.assertAlmostEqual(trade["entry_price"], 1.0)
        self.assertAlmostEqual(trade["exit_price"], 0.4)
        self.assertAlmostEqual(trade["return_pct"], -60.0)
        self.assertAlmostEqual(trade["buy_prob"], 0.9)
        self.assertAlmostEqual(trade["max_adverse_excursion_pct"], -60.0)
        self.assertAlmostEqual(trade["max_favorable_excursion_pct"], 0.0)

    def test_run_ab_evaluation_min_policy_hold_delays_policy_sell(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _ImmediateSellPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xminhold", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xminhold", "sample_time": 103},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xminhold", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "include_trade_log": True,
                "min_policy_hold_seconds": 5,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _ImmediateSellPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(out["trade_log"][0]["exit_time"], 110)
        self.assertEqual(out["trade_log"][0]["exit_reason"], "SELL100")
        self.assertEqual(out["min_policy_hold_seconds"], 5)

    def test_run_ab_evaluation_trailing_stop_exits_before_policy_hold(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _HoldPolicy:
            def __init__(self):
                self.calls = 0

            def predict(self, obs, deterministic=True):
                self.calls += 1
                return 0, None

        policy = _HoldPolicy()
        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xtrail", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.5,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xtrail", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 12,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xtrail", "sample_time": 120},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "include_trade_log": True,
                "trailing_start_pct": 0.2,
                "trailing_stop_pct": 0.2,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": policy},
            {"bc_samples": 10},
        )

        self.assertEqual(out["trade_log"][0]["exit_reason"], "TRAILING_STOP")
        self.assertEqual(policy.calls, 2)

    def test_run_ab_evaluation_rug_guard_exits_before_policy_hold(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _HoldPolicy:
            def __init__(self):
                self.calls = 0

            def predict(self, obs, deterministic=True):
                self.calls += 1
                return 0, None

        policy = _HoldPolicy()
        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xrug", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 99.0,
                },
                "meta": {"token_address": "0xrug", "sample_time": 110},
            },
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "include_trade_log": True,
                "rug_sell_pressure": 0.95,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": policy},
            {"bc_samples": 10},
        )

        self.assertEqual(out["trade_log"][0]["exit_reason"], "RUG_EXIT")
        self.assertEqual(policy.calls, 0)

    def test_run_ab_evaluation_passes_position_state_to_sell_policy(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _CapturePolicy:
            def __init__(self):
                self.observations = []

            def predict(self, obs, deterministic=True):
                self.observations.append(list(obs))
                return 0, None

        policy = _CapturePolicy()
        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xstate", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xstate", "sample_time": 110},
            },
        ]

        m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128, "model": policy},
            {"bc_samples": 10},
        )

        self.assertEqual(len(policy.observations), 2)
        obs = policy.observations[0]
        self.assertEqual(len(obs), 11)
        self.assertAlmostEqual(float(obs[5]), 10.0)
        self.assertAlmostEqual(float(obs[6]), 10.0)
        self.assertAlmostEqual(float(obs[7]), 0.2, places=6)
        self.assertAlmostEqual(float(obs[8]), 0.2, places=6)
        self.assertAlmostEqual(float(obs[9]), 0.0, places=6)
        self.assertAlmostEqual(float(obs[10]), 1.0)

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

    def test_run_ab_evaluation_batches_schema_validation_for_buy_inference(self):
        import pandas as pd

        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {"current_price": 1.0, "signal": 0.8},
                "meta": {"token_address": "0xbatch-schema", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.2, "signal": 0.7},
                "meta": {"token_address": "0xbatch-schema", "sample_time": 110},
            },
            {
                "features": {"current_price": 1.1, "signal": 0.6},
                "meta": {"token_address": "0xbatch-schema", "sample_time": 120},
            },
        ]

        def _batch_feature_frame(rows, feature_names=None, ignored_feature_names=None):
            return pd.DataFrame(list(rows), columns=feature_names)

        with patch.object(m, "build_feature_frame", side_effect=AssertionError("single-row validation used")), \
             patch.object(m, "build_feature_frame_many", side_effect=_batch_feature_frame, create=True) as mock_batch:
            out = m.run_ab_evaluation(
                {"eval_samples": eval_samples},
                {
                    "model": _FakeBuyModel(),
                    "threshold": 0.5,
                    "feature_names": ["signal", "current_price"],
                },
                {"total_timesteps": 128},
                {"bc_samples": 10},
            )

        self.assertEqual(out["total_trades"], 1)
        self.assertGreaterEqual(mock_batch.call_count, 1)

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

    def test_run_ab_evaluation_ignores_schema_dropped_features(self):
        m = _load_module()

        class _FakeBuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.1, 0.9] for _ in range(len(X))]

        eval_samples = [
            {
                "features": {
                    "current_price": 1.0,
                    "future_window": 240,
                    "constant_feature": 7.0,
                },
                "meta": {"token_address": "0x6drop", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "future_window": 240,
                    "constant_feature": 7.0,
                },
                "meta": {"token_address": "0x6drop", "sample_time": 110},
            },
        ]

        buy_model = _FakeBuyModel()
        m.run_ab_evaluation(
            {"eval_samples": eval_samples},
            {
                "model": buy_model,
                "threshold": 0.5,
                "feature_names": ["current_price"],
                "dropped_features": {
                    "invalid": ["future_window"],
                    "constant": ["constant_feature"],
                },
            },
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        first_frame = buy_model.frames[0]
        self.assertEqual(list(first_frame.columns), ["current_price"])

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

    def test_run_ab_evaluation_reports_walk_forward_segments(self):
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
                "meta": {"token_address": "0xwf1", "sample_time": 100},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "launch_fee": 0.5,
                    "holder_count": 11,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0xwf1", "sample_time": 110},
            },
            {
                "features": {
                    "current_price": 1.0,
                    "launch_fee": 0.5,
                    "holder_count": 20,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": "0xwf2", "sample_time": 200},
            },
            {
                "features": {
                    "current_price": 0.9,
                    "launch_fee": 0.5,
                    "holder_count": 21,
                    "total_buy_volume": 1.0,
                    "total_sell_volume": 9.0,
                },
                "meta": {"token_address": "0xwf2", "sample_time": 210},
            },
        ]

        out = m.run_ab_evaluation(
            {"eval_samples": eval_samples, "walk_forward_segments": 2, "position_fraction": 0.1},
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertEqual(len(out["walk_forward"]), 2)
        self.assertEqual(out["walk_forward"][0]["segment_index"], 0)
        self.assertEqual(out["walk_forward"][0]["episode_count"], 1)
        self.assertEqual(out["walk_forward"][1]["segment_index"], 1)
        self.assertEqual(out["walk_forward"][1]["episode_count"], 1)
        self.assertEqual(out["walk_forward_segment_count"], 2)
        self.assertEqual(
            out["walk_forward_worst_net_return_pct"],
            min(segment["net_return_pct"] for segment in out["walk_forward"]),
        )
        self.assertEqual(
            out["walk_forward_worst_max_drawdown_pct"],
            min(segment["max_drawdown_pct"] for segment in out["walk_forward"]),
        )
        self.assertEqual(
            out["walk_forward_min_win_rate"],
            min(segment["win_rate"] for segment in out["walk_forward"]),
        )

    def test_run_ab_evaluation_reports_stress_replay_scenarios(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        def sample(token, sample_time, price):
            return {
                "features": {
                    "current_price": price,
                    "launch_fee": 0.5,
                    "holder_count": 10,
                    "total_buy_volume": 10.0,
                    "total_sell_volume": 1.0,
                },
                "meta": {"token_address": token, "sample_time": sample_time},
            }

        eval_samples = [
            sample("0xstress", 100, 1.0),
            sample("0xstress", 103, 2.0),
            sample("0xstress", 110, 3.0),
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "position_fraction": 0.1,
                "stress_replay_scenarios": [
                    {
                        "name": "mild",
                        "entry_delay_seconds": 2,
                        "exit_delay_seconds": 2,
                        "slippage_bps": 100.0,
                        "max_open_positions": 3,
                    }
                ],
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _SellAllPolicy()},
            {"bc_samples": 10},
        )

        self.assertEqual(len(out["stress_replay"]), 1)
        scenario = out["stress_replay"][0]
        self.assertEqual(scenario["name"], "mild")
        self.assertEqual(scenario["entry_delay_seconds"], 2)
        self.assertEqual(scenario["exit_delay_seconds"], 2)
        self.assertEqual(scenario["max_open_positions"], 3)
        self.assertAlmostEqual(scenario["slippage_bps"], 100.0)
        self.assertEqual(scenario["total_trades"], 1)

    def test_build_eval_episodes_sorts_by_episode_start_time(self):
        m = _load_module()

        eval_samples = [
            {
                "features": {"current_price": 2.0},
                "meta": {"token_address": "0xb", "sample_time": 200},
            },
            {
                "features": {"current_price": 1.0},
                "meta": {"token_address": "0xa", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.1},
                "meta": {"token_address": "0xa", "sample_time": 110},
            },
            {
                "features": {"current_price": 2.1},
                "meta": {"token_address": "0xb", "sample_time": 210},
            },
        ]

        episodes = m._build_eval_episodes(eval_samples)

        self.assertEqual([episode[0]["meta"]["token_address"] for episode in episodes], ["0xa", "0xb"])

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
        self.assertAlmostEqual(out["net_return_pct"], 2.0, places=6)
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

    def test_run_hybrid_training_rewrites_threshold_after_risk_tuning(self):
        import json
        import tempfile

        m = _load_module()

        explicit_eval_samples = [
            {"features": {"current_price": 1.0}, "meta": {"token_address": "0xeval", "sample_time": 100}},
            {"features": {"current_price": 1.1}, "meta": {"token_address": "0xeval", "sample_time": 110}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            threshold_path = Path(tmpdir) / "buy_threshold.json"
            threshold_path.write_text(json.dumps({"threshold": 0.5}), encoding="utf-8")
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            def _fake_eval(eval_config, buy_artifact, ppo_artifact, bc_artifact):
                self.assertEqual(buy_artifact["threshold"], 0.8)
                saved = json.loads(threshold_path.read_text(encoding="utf-8"))
                self.assertEqual(saved["threshold"], 0.8)
                return {
                    "total_trades": 1,
                    "win_rate": 1.0,
                    "net_return_pct": 10.0,
                    "max_drawdown_pct": -1.0,
                    "sortino_ratio": 0.5,
                    "buy_threshold": 0.8,
                    "sell_episode_count": 1,
                    "bc_samples": bc_artifact["bc_samples"],
                    "ppo_total_timesteps": ppo_artifact["total_timesteps"],
                    "train_file_count": eval_config["train_file_count"],
                    "eval_file_count": eval_config["eval_file_count"],
                    "overlap_token_count": eval_config["overlap_token_count"],
                    "pipeline_status": "ok",
                }

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=([fake_files[0]], [fake_files[1]], 0)), \
                 patch.object(
                     m,
                     "train_buy_model",
                     return_value={
                         "model_path": "buy_model.cbm",
                         "threshold": 0.5,
                         "threshold_path": str(threshold_path),
                         "feature_schema_path": "feature_schema.json",
                         "feature_names": ["current_price"],
                         "model": MagicMock(),
                         "samples": [],
                         "calibration_samples": [],
                     },
                 ), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128, "model": object()}), \
                 patch.object(
                     m,
                     "_tune_buy_threshold_by_replay",
                     return_value={"status": "selected", "threshold": 0.8, "previous_threshold": 0.5, "replay": {"total_trades": 1}},
                 ) as mock_tune, \
                 patch.object(m, "run_ab_evaluation", side_effect=_fake_eval):
                result = m.run_hybrid_training(
                    {
                        "output_dir": tmpdir,
                        "eval_samples": explicit_eval_samples,
                        "risk_tune_buy_threshold": True,
                    }
                )

            mock_tune.assert_called_once()
            self.assertEqual(result["artifacts"]["buy_model"]["threshold"], 0.8)
            self.assertEqual(result["artifacts"]["buy_model"]["risk_tuning"]["status"], "selected")

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

    def test_run_hybrid_training_writes_trade_log_sidecar(self):
        import json
        import tempfile

        m = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_files = [Path(tmpdir) / "lifecycle_incremental_001.jsonl", Path(tmpdir) / "lifecycle_incremental_002.jsonl"]
            for path in fake_files:
                path.write_text("{}\n", encoding="utf-8")

            evaluation = {
                "total_trades": 2,
                "win_rate": 0.5,
                "net_return_pct": 1.0,
                "max_drawdown_pct": -2.0,
                "sortino_ratio": 0.1,
                "buy_threshold": 0.8,
                "sell_episode_count": 1,
                "bc_samples": 1,
                "ppo_total_timesteps": 1,
                "train_file_count": 1,
                "eval_file_count": 1,
                "overlap_token_count": 0,
                "pipeline_status": "ok",
                "trade_log": [
                    {"token": "0x1", "return_pct": 10.0, "exit_reason": "SELL100"},
                    {"token": "0x2", "return_pct": -20.0, "exit_reason": "STOP_LOSS"},
                ],
            }

            with patch.object(m, "_discover_lifecycle_files", return_value=fake_files), \
                 patch.object(m, "_split_lifecycle_files", return_value=(fake_files[:1], fake_files[1:], 0)), \
                 patch.object(m, "_load_samples", return_value=[]), \
                 patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.8, "threshold_path": "buy_threshold.json", "feature_schema_path": "feature_schema.json", "feature_names": ["current_price"], "model": MagicMock()}), \
                 patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
                 patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 1}), \
                 patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 1, "model": object()}), \
                 patch.object(m, "run_ab_evaluation", return_value=evaluation):
                result = m.run_hybrid_training({"output_dir": tmpdir, "include_trade_log": True})

            manifest = json.loads(Path(tmpdir, "hybrid_manifest.json").read_text(encoding="utf-8"))
            sidecar_path = Path(result["evaluation"]["trade_log_path"])
            self.assertNotIn("trade_log", result["evaluation"])
            self.assertNotIn("trade_log", manifest["evaluation"])
            self.assertEqual(result["evaluation"]["trade_log_count"], 2)
            self.assertTrue(sidecar_path.exists())
            sidecar_rows = [json.loads(line) for line in sidecar_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(sidecar_rows), 2)
            self.assertEqual(result["evaluation"]["worst_trades"][0]["token"], "0x2")
            self.assertEqual(result["evaluation"]["exit_reason_summary"]["SELL100"]["count"], 1)
            self.assertEqual(result["evaluation"]["exit_reason_summary"]["STOP_LOSS"]["count"], 1)
            self.assertEqual(result["evaluation"]["exit_reason_summary"]["STOP_LOSS"]["mean_return_pct"], -20.0)

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

    def test_profit_path_bc_label_holds_despite_sell_pressure_when_future_upside_remains(self):
        m = _load_module()
        episode = [
            {
                "mid_price": 1.0,
                "lp_depth": 1.0,
                "sell_pressure": 0.95,
                "buy_sell_ratio": 0.1,
                "holders": 10,
                "ts": 100,
            },
            {
                "mid_price": 1.2,
                "lp_depth": 1.0,
                "sell_pressure": 0.95,
                "buy_sell_ratio": 0.1,
                "holders": 12,
                "ts": 110,
            },
            {
                "mid_price": 1.7,
                "lp_depth": 1.0,
                "sell_pressure": 0.2,
                "buy_sell_ratio": 2.0,
                "holders": 14,
                "ts": 120,
            },
        ]

        _, actions = m._build_bc_arrays(
            [episode],
            {"bc_label_mode": "profit_path", "bc_profit_path_sell_margin_pct": 0.05},
        )

        self.assertEqual([int(value) for value in actions[:2]], [0, 0])

    def test_profit_path_bc_label_sells_near_future_peak(self):
        m = _load_module()
        episode = [
            {
                "mid_price": 1.0,
                "lp_depth": 1.0,
                "sell_pressure": 0.1,
                "buy_sell_ratio": 2.0,
                "holders": 10,
                "ts": 100,
            },
            {
                "mid_price": 1.3,
                "lp_depth": 1.0,
                "sell_pressure": 0.1,
                "buy_sell_ratio": 2.0,
                "holders": 12,
                "ts": 110,
            },
            {
                "mid_price": 1.8,
                "lp_depth": 1.0,
                "sell_pressure": 0.1,
                "buy_sell_ratio": 2.0,
                "holders": 14,
                "ts": 120,
            },
            {
                "mid_price": 1.75,
                "lp_depth": 1.0,
                "sell_pressure": 0.1,
                "buy_sell_ratio": 2.0,
                "holders": 16,
                "ts": 130,
            },
        ]

        _, actions = m._build_bc_arrays(
            [episode],
            {
                "bc_label_mode": "profit_path",
                "bc_profit_path_sell_margin_pct": 0.05,
                "bc_profit_path_sell100_pct": 0.75,
            },
        )

        self.assertEqual([int(value) for value in actions[:3]], [0, 0, 3])


if __name__ == "__main__":
    unittest.main()
