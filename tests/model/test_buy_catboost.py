import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util

import pandas as pd


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "model" / "buy_catboost.py"
    spec = importlib.util.spec_from_file_location("buy_catboost", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBuyCatBoost(unittest.TestCase):
    def test_build_focal_like_weights_increases_positive_weight(self):
        module = _load_module()
        y = [0, 0, 0, 1]
        w = module.build_focal_like_weights(y, gamma=2.0, alpha_pos=3.0)
        self.assertEqual(len(w), 4)
        self.assertGreater(w[-1], w[0])

    def test_fit_passes_cat_feature_indices(self):
        module = _load_module()
        df = pd.DataFrame(
            {
                "creator_id": ["a", "b", "c", "a"],
                "price_change_pct": [1.0, 2.0, 3.0, 4.0],
                "target": [0, 0, 1, 1],
            }
        )
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.4, 0.6]] * len(df)

        with patch.object(module, "CatBoostClassifier", return_value=fake_model):
            model = module.BuyCatBoostModel(cat_feature_names=["creator_id"])
            model.fit(df.drop(columns=["target"]), df["target"])

        self.assertTrue(fake_model.fit.called)


if __name__ == "__main__":
    unittest.main()
