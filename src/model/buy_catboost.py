from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence

import numpy as np

try:
    from catboost import CatBoostClassifier
except Exception:  # pragma: no cover - fallback for environments without catboost
    class CatBoostClassifier:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("catboost is required to use BuyCatBoostModel")


def build_focal_like_weights(y: Iterable[int], gamma: float = 2.0, alpha_pos: float = 2.0) -> List[float]:
    y_arr = np.asarray(list(y), dtype=int)
    if y_arr.size == 0:
        return []

    pos_rate = float(np.mean(y_arr == 1))
    neg_rate = 1.0 - pos_rate

    weights: List[float] = []
    for label in y_arr:
        if label == 1:
            weight = alpha_pos * ((1.0 - pos_rate) ** gamma)
        else:
            weight = (1.0 - neg_rate) ** gamma
        weights.append(float(max(weight, 1e-8)))

    return weights


DEFAULT_CATBOOST_PARAMS = {
    "iterations": 500,
    "learning_rate": 0.05,
    "depth": 5,
    "l2_leaf_reg": 10.0,
    "random_strength": 1.0,
    "bagging_temperature": 1.0,
    "rsm": 0.8,
    "od_type": "Iter",
    "od_wait": 50,
}


class BuyCatBoostModel:
    def __init__(
        self,
        cat_feature_names: Sequence[str] | None = None,
        random_state: int = 42,
        catboost_params: Mapping[str, object] | None = None,
    ):
        self.cat_feature_names = list(cat_feature_names or [])
        self.random_state = int(random_state)
        self.catboost_params = dict(DEFAULT_CATBOOST_PARAMS)
        self.catboost_params.update(dict(catboost_params or {}))
        self.model = None

    def _cat_feature_indices(self, X) -> List[int]:
        if not hasattr(X, "columns"):
            return []
        return [int(X.columns.get_loc(name)) for name in self.cat_feature_names if name in X.columns]

    def fit(self, X, y, eval_set=None):
        cat_indices = self._cat_feature_indices(X)
        sample_weight = build_focal_like_weights(y)

        self.model = CatBoostClassifier(
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=self.random_state,
            verbose=False,
            allow_writing_files=False,
            **self.catboost_params,
        )
        fit_kwargs = {
            "sample_weight": sample_weight,
            "cat_features": cat_indices or None,
        }
        if eval_set is not None:
            fit_kwargs["eval_set"] = eval_set
            fit_kwargs["use_best_model"] = True
        self.model.fit(X, y, **fit_kwargs)
        return self

    def predict_proba(self, X):
        if self.model is None:
            raise ValueError("model is not fitted")
        return self.model.predict_proba(X)

    def select_threshold(
        self,
        y_true: Sequence[int],
        prob,
        min_precision: float = 0.10,
        min_threshold: float = 0.0,
        min_predictions: int = 1,
    ) -> float:
        y_arr = np.asarray(y_true, dtype=int)
        prob_arr = np.asarray(prob, dtype=float)

        if prob_arr.ndim == 2:
            pos_prob = prob_arr[:, 1]
        else:
            pos_prob = prob_arr

        threshold_floor = max(0.0, min(1.0, float(min_threshold)))
        required_predictions = max(1, int(min_predictions))
        thresholds = np.unique(pos_prob)
        thresholds = np.concatenate(([threshold_floor], thresholds, [1.0]))

        best_threshold = 1.0
        best_recall = -1.0
        best_precision = -1.0
        found_feasible = False

        for threshold in thresholds:
            if threshold < threshold_floor:
                continue
            pred = pos_prob >= threshold
            pred_count = int(np.sum(pred == 1))
            if pred_count < required_predictions:
                continue
            tp = int(np.sum((pred == 1) & (y_arr == 1)))
            fp = int(np.sum((pred == 1) & (y_arr == 0)))
            fn = int(np.sum((pred == 0) & (y_arr == 1)))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            if precision >= min_precision and (
                recall > best_recall
                or (recall == best_recall and precision > best_precision)
                or (recall == best_recall and precision == best_precision and float(threshold) > best_threshold)
            ):
                found_feasible = True
                best_recall = recall
                best_precision = precision
                best_threshold = float(threshold)

        if not found_feasible:
            return 1.0

        return float(best_threshold)
