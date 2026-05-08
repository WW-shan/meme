import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util
import json
import tempfile


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "model" / "hybrid_inference.py"
    spec = importlib.util.spec_from_file_location("hybrid_inference", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestHybridInference(unittest.TestCase):
    def test_predict_buy_returns_prob_and_decision(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.3, 0.7]]
        hybrid = m.HybridModel(buy_model=fake_model, buy_threshold=0.5, sell_policy=None)
        features = {"current_price": 1.0, "buy_pressure": 0.6}
        prob, should_buy = hybrid.predict_buy(features)
        self.assertAlmostEqual(prob, 0.7)
        self.assertTrue(should_buy)

    def test_predict_buy_rejects_below_threshold(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.8, 0.2]]
        hybrid = m.HybridModel(buy_model=fake_model, buy_threshold=0.5, sell_policy=None)
        prob, should_buy = hybrid.predict_buy({"current_price": 1.0})
        self.assertAlmostEqual(prob, 0.2)
        self.assertFalse(should_buy)

    def test_predict_buy_reorders_features_to_schema(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.2, 0.8]]
        hybrid = m.HybridModel(
            buy_model=fake_model,
            buy_threshold=0.5,
            sell_policy=None,
            feature_names=["buy_pressure", "current_price"],
        )

        prob, should_buy = hybrid.predict_buy({"current_price": 1.0, "buy_pressure": 0.6})

        self.assertAlmostEqual(prob, 0.8)
        self.assertTrue(should_buy)
        called_X = fake_model.predict_proba.call_args[0][0]
        self.assertEqual(list(called_X.columns), ["buy_pressure", "current_price"])
        self.assertEqual(called_X.iloc[0].to_dict(), {"buy_pressure": 0.6, "current_price": 1.0})

    def test_predict_buy_raises_on_missing_features(self):
        m = _load_module()
        fake_model = MagicMock()
        hybrid = m.HybridModel(
            buy_model=fake_model,
            buy_threshold=0.5,
            sell_policy=None,
            feature_names=["a", "b"],
        )

        with self.assertRaisesRegex(ValueError, "Missing expected features: b"):
            hybrid.predict_buy({"a": 1.0})

    def test_predict_buy_raises_on_extra_features(self):
        m = _load_module()
        fake_model = MagicMock()
        hybrid = m.HybridModel(
            buy_model=fake_model,
            buy_threshold=0.5,
            sell_policy=None,
            feature_names=["a", "b"],
        )

        with self.assertRaisesRegex(ValueError, "Unexpected extra features: c"):
            hybrid.predict_buy({"a": 1.0, "b": 2.0, "c": 3.0})

    def test_predict_buy_raises_on_non_mapping_when_schema_enforced(self):
        m = _load_module()
        fake_model = MagicMock()
        hybrid = m.HybridModel(
            buy_model=fake_model,
            buy_threshold=0.5,
            sell_policy=None,
            feature_names=["a", "b"],
        )

        with self.assertRaisesRegex(ValueError, "features_dict must be a mapping"):
            hybrid.predict_buy([("a", 1.0), ("b", 2.0)])

    def test_build_feature_frame_many_orders_rows_to_schema(self):
        m = _load_module()

        frame = m.build_feature_frame_many(
            [
                {"b": 2.0, "a": 1.0, "ignored": 9.0},
                {"b": 4.0, "a": 3.0, "ignored": 8.0},
            ],
            ["a", "b"],
            ["ignored"],
        )

        self.assertEqual(list(frame.columns), ["a", "b"])
        self.assertEqual(
            frame.to_dict("records"),
            [{"a": 1.0, "b": 2.0}, {"a": 3.0, "b": 4.0}],
        )

    def test_build_feature_frame_many_rejects_missing_features(self):
        m = _load_module()

        with self.assertRaisesRegex(ValueError, "Missing expected features: b"):
            m.build_feature_frame_many([{"a": 1.0}], ["a", "b"])

    def test_build_feature_frame_many_rejects_extra_features(self):
        m = _load_module()

        with self.assertRaisesRegex(ValueError, "Unexpected extra features: c"):
            m.build_feature_frame_many([{"a": 1.0, "b": 2.0, "c": 3.0}], ["a", "b"])

    def test_hybrid_model_rejects_malformed_inline_feature_names_type(self):
        m = _load_module()
        with self.assertRaisesRegex(ValueError, "feature_names must be a list"):
            m.HybridModel(
                buy_model=MagicMock(),
                buy_threshold=0.5,
                sell_policy=None,
                feature_names="current_price",
            )

    def test_load_schema_enforces_reordering_during_predict_buy(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.1, 0.9]]

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "feature_schema.json").write_text(
                json.dumps({"feature_names": ["buy_pressure", "current_price"]}),
                encoding="utf-8",
            )
            with patch.object(m, "_load_catboost_model", return_value=fake_model):
                hybrid = m.HybridModel.load(tmpdir)

            prob, should_buy = hybrid.predict_buy({"current_price": 1.0, "buy_pressure": 0.6})

        self.assertAlmostEqual(prob, 0.9)
        self.assertTrue(should_buy)
        called_X = fake_model.predict_proba.call_args[0][0]
        self.assertEqual(list(called_X.columns), ["buy_pressure", "current_price"])

    def test_load_ignores_schema_dropped_features_during_predict_buy(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.2, 0.8]]

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "feature_schema.json").write_text(
                json.dumps(
                    {
                        "feature_names": ["current_price"],
                        "dropped_features": {
                            "invalid": ["future_window"],
                            "constant": ["constant_feature"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(m, "_load_catboost_model", return_value=fake_model):
                hybrid = m.HybridModel.load(tmpdir)

            prob, should_buy = hybrid.predict_buy(
                {
                    "current_price": 1.0,
                    "future_window": 240,
                    "constant_feature": 7.0,
                }
            )

        self.assertAlmostEqual(prob, 0.8)
        self.assertTrue(should_buy)
        called_X = fake_model.predict_proba.call_args[0][0]
        self.assertEqual(list(called_X.columns), ["current_price"])

    def test_predict_sell_returns_action_from_policy(self):
        m = _load_module()
        fake_policy = MagicMock()
        fake_policy.predict.return_value = (2, None)
        hybrid = m.HybridModel(buy_model=MagicMock(), buy_threshold=0.5, sell_policy=fake_policy)
        action = hybrid.predict_sell([1.0, 0.5, 0.3, 2.0, 40.0])
        self.assertEqual(action, 2)

    def test_predict_sell_accepts_numpy_array_action(self):
        import numpy as np

        m = _load_module()
        fake_policy = MagicMock()
        fake_policy.predict.return_value = (np.array([2]), None)
        hybrid = m.HybridModel(buy_model=MagicMock(), buy_threshold=0.5, sell_policy=fake_policy)

        action = hybrid.predict_sell([1.0, 0.5, 0.3, 2.0, 40.0])

        self.assertEqual(action, 2)

    def test_load_reads_artifacts_from_directory(self):
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "buy_threshold.json").write_text(
                json.dumps({"threshold": 0.42}), encoding="utf-8"
            )
            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                hybrid = m.HybridModel.load(tmpdir)

            self.assertAlmostEqual(hybrid.buy_threshold, 0.42)
            self.assertIsNone(hybrid.sell_policy)

    def test_load_reads_feature_schema_metadata_when_present(self):
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "feature_schema.json").write_text(
                json.dumps({"feature_names": ["buy_pressure", "current_price"]}),
                encoding="utf-8",
            )
            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                hybrid = m.HybridModel.load(tmpdir)

            self.assertEqual(hybrid.feature_names, ["buy_pressure", "current_price"])
    def test_load_ignores_schema_without_feature_names_key(self):
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "feature_schema.json").write_text(
                json.dumps({"version": 1}),
                encoding="utf-8",
            )
            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                hybrid = m.HybridModel.load(tmpdir)

            self.assertIsNone(hybrid.feature_names)

    def test_load_raises_on_malformed_feature_names_metadata(self):
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "feature_schema.json").write_text(
                json.dumps({"feature_names": "not-a-list"}),
                encoding="utf-8",
            )
            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                with self.assertRaisesRegex(ValueError, "feature_schema.json field 'feature_names' must be a list"):
                    m.HybridModel.load(tmpdir)

    def test_load_keeps_buy_model_when_optional_sell_policy_fails(self):
        m = _load_module()
        fake_buy_model = MagicMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "buy_threshold.json").write_text(
                json.dumps({"threshold": 0.42}), encoding="utf-8"
            )
            Path(tmpdir, "sell_policy.zip").write_text("broken", encoding="utf-8")
            with patch.object(m, "_load_catboost_model", return_value=fake_buy_model), \
                 patch.object(m, "_load_sb3_policy", side_effect=RuntimeError("broken policy")):
                hybrid = m.HybridModel.load(tmpdir)

        self.assertIs(hybrid.buy_model, fake_buy_model)
        self.assertIsNone(hybrid.sell_policy)
        self.assertAlmostEqual(hybrid.buy_threshold, 0.42)
