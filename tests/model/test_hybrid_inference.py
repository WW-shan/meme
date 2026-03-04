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


if __name__ == "__main__":
    unittest.main()
