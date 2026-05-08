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
        fit_kwargs = fake_model.fit.call_args.kwargs
        self.assertEqual(fit_kwargs["cat_features"], [0])
        self.assertEqual(len(fit_kwargs["sample_weight"]), len(df))

    def test_fit_passes_regularized_params_and_eval_set(self):
        module = _load_module()
        train_df = pd.DataFrame(
            {
                "creator_id": ["a", "b", "c", "a"],
                "price_change_pct": [1.0, 2.0, 3.0, 4.0],
            }
        )
        eval_df = pd.DataFrame(
            {
                "creator_id": ["b", "d"],
                "price_change_pct": [5.0, 6.0],
            }
        )
        fake_model = MagicMock()

        with patch.object(module, "CatBoostClassifier", return_value=fake_model) as mock_cls:
            model = module.BuyCatBoostModel(
                cat_feature_names=["creator_id"],
                catboost_params={
                    "iterations": 200,
                    "depth": 4,
                    "l2_leaf_reg": 12.0,
                    "random_strength": 1.5,
                    "od_type": "Iter",
                    "od_wait": 25,
                },
            )
            model.fit(
                train_df,
                [0, 0, 1, 1],
                eval_set=(eval_df, [0, 1]),
            )

        cls_kwargs = mock_cls.call_args.kwargs
        self.assertEqual(cls_kwargs["iterations"], 200)
        self.assertEqual(cls_kwargs["depth"], 4)
        self.assertEqual(cls_kwargs["l2_leaf_reg"], 12.0)
        self.assertEqual(cls_kwargs["random_strength"], 1.5)
        self.assertEqual(cls_kwargs["od_type"], "Iter")
        self.assertEqual(cls_kwargs["od_wait"], 25)

        fit_kwargs = fake_model.fit.call_args.kwargs
        self.assertEqual(fit_kwargs["cat_features"], [0])
        self.assertIs(fit_kwargs["eval_set"][0], eval_df)
        self.assertEqual(list(fit_kwargs["eval_set"][1]), [0, 1])
        self.assertTrue(fit_kwargs["use_best_model"])

    def test_select_threshold_meets_precision_floor_when_feasible(self):
        module = _load_module()
        model = module.BuyCatBoostModel()

        y_true = [1, 0, 0, 0]
        prob = [
            [0.1, 0.9],
            [0.2, 0.8],
            [0.8, 0.2],
            [0.9, 0.1],
        ]

        threshold = model.select_threshold(y_true, prob, min_precision=0.8)

        pos_prob = [row[1] for row in prob]
        pred = [p >= threshold for p in pos_prob]
        tp = sum(1 for p, y in zip(pred, y_true) if p and y == 1)
        fp = sum(1 for p, y in zip(pred, y_true) if p and y == 0)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        self.assertGreaterEqual(precision, 0.8)

    def test_select_threshold_respects_min_threshold_and_min_predictions(self):
        module = _load_module()
        model = module.BuyCatBoostModel()

        y_true = [1, 0, 1, 0]
        prob = [
            [0.9, 0.1],
            [0.8, 0.2],
            [0.2, 0.8],
            [0.1, 0.9],
        ]

        threshold = model.select_threshold(
            y_true,
            prob,
            min_precision=0.5,
            min_threshold=0.5,
            min_predictions=2,
        )

        self.assertEqual(threshold, 0.8)

    def test_select_threshold_returns_conservative_value_when_min_predictions_infeasible(self):
        module = _load_module()
        model = module.BuyCatBoostModel()

        y_true = [1, 0, 1]
        prob = [
            [0.1, 0.9],
            [0.2, 0.8],
            [0.3, 0.7],
        ]

        threshold = model.select_threshold(
            y_true,
            prob,
            min_precision=0.5,
            min_threshold=0.0,
            min_predictions=4,
        )

        self.assertEqual(threshold, 1.0)

    def test_select_threshold_returns_conservative_value_when_infeasible(self):
        module = _load_module()
        model = module.BuyCatBoostModel()

        y_true = [1, 0, 0]
        prob = [
            [0.3, 0.7],
            [0.1, 0.9],
            [0.2, 0.8],
        ]

        threshold = model.select_threshold(y_true, prob, min_precision=0.9)

        self.assertEqual(threshold, 1.0)


if __name__ == "__main__":
    unittest.main()
