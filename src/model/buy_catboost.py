from __future__ import annotations

from typing import Iterable, List, Sequence

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


class BuyCatBoostModel:
    def __init__(self, cat_feature_names: Sequence[str] | None = None, random_state: int = 42):
        self.cat_feature_names = list(cat_feature_names or [])
        self.random_state = int(random_state)
        self.model = None

    def _cat_feature_indices(self, X) -> List[int]:
        if not hasattr(X, "columns"):
            return []
        return [int(X.columns.get_loc(name)) for name in self.cat_feature_names if name in X.columns]

    def fit(self, X, y):
        cat_indices = self._cat_feature_indices(X)
        sample_weight = build_focal_like_weights(y)

        self.model = CatBoostClassifier(
            loss_function="Logloss",
            eval_metric="AUC",
            random_seed=self.random_state,
            verbose=False,
            allow_writing_files=False,
        )
        self.model.fit(
            X,
            y,
            sample_weight=sample_weight,
            cat_features=cat_indices or None,
        )
        return self

    def predict_proba(self, X):
        if self.model is None:
            raise ValueError("model is not fitted")
        return self.model.predict_proba(X)

    def select_threshold(self, y_true: Sequence[int], prob, min_precision: float = 0.10) -> float:
        y_arr = np.asarray(y_true, dtype=int)
        prob_arr = np.asarray(prob, dtype=float)

        if prob_arr.ndim == 2:
            pos_prob = prob_arr[:, 1]
        else:
            pos_prob = prob_arr

        thresholds = np.unique(pos_prob)
        thresholds = np.concatenate(([0.0], thresholds, [1.0]))

        best_threshold = 0.5
        best_recall = -1.0

        for threshold in thresholds:
            pred = pos_prob >= threshold
            tp = int(np.sum((pred == 1) & (y_arr == 1)))
            fp = int(np.sum((pred == 1) & (y_arr == 0)))
            fn = int(np.sum((pred == 0) & (y_arr == 1)))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

            if precision >= min_precision and recall > best_recall:
                best_recall = recall
                best_threshold = float(threshold)

        return float(best_threshold)
