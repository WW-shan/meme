from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np

from src.pipeline import support_action_policy_probe as support_probe


POSITIVE_POLICIES = support_probe.POSITIVE_POLICIES
DECISION_TIME_FIELDS = support_probe.DECISION_TIME_FIELDS


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _candidate_rows(report: Mapping[str, Any], source_name: str) -> list[dict[str, Any]]:
    rows = report.get("candidates") or report.get("candidate_sample") or []
    candidates = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        tagged = dict(row)
        tagged["source_report"] = str(source_name)
        tagged["label_positive"] = row.get("recommended_policy") in POSITIVE_POLICIES
        candidates.append(tagged)
    return candidates


def _source_tagged_rows(
    reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    report_list = list(reports)
    names = list(source_names or [f"report_{index}" for index in range(len(report_list))])
    if len(report_list) != len(names):
        raise ValueError("source_names length must match time_to_barrier_reports")
    if len(report_list) < 2:
        raise ValueError("at least two source reports are required")

    rows: list[dict[str, Any]] = []
    for report, name in zip(report_list, names):
        rows.extend(_candidate_rows(report, name))
    return rows, names


def _label_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    row_list = list(rows)
    positives = sum(1 for row in row_list if row.get("label_positive"))
    total = len(row_list)
    return {
        "total": total,
        "positive": positives,
        "negative": total - positives,
    }


def _feature_names(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    present = set()
    for row in rows:
        for field in DECISION_TIME_FIELDS:
            if _finite_float(row.get(field)) is not None:
                present.add(field)
    return sorted(present)


def _feature_matrix(
    rows: list[Mapping[str, Any]],
    feature_names: list[str],
    *,
    medians: dict[str, float] | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    if medians is None:
        medians = {}
        for feature in feature_names:
            values = [_finite_float(row.get(feature)) for row in rows]
            finite_values = [value for value in values if value is not None]
            medians[feature] = float(np.median(finite_values)) if finite_values else 0.0

    matrix = []
    for row in rows:
        values = []
        for feature in feature_names:
            value = _finite_float(row.get(feature))
            values.append(medians[feature] if value is None else value)
        matrix.append(values)
    return np.asarray(matrix, dtype=float), medians


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _selected_rows(
    rows: list[Mapping[str, Any]],
    probabilities: np.ndarray,
    threshold: float,
) -> list[tuple[Mapping[str, Any], float]]:
    selected = []
    for row, probability in zip(rows, probabilities):
        parsed_probability = float(probability)
        if parsed_probability >= threshold:
            selected.append((row, parsed_probability))
    selected.sort(key=lambda item: item[1], reverse=True)
    return selected


def _evaluation_block(
    rows: list[Mapping[str, Any]],
    selected: list[tuple[Mapping[str, Any], float]],
) -> dict[str, Any]:
    total = len(rows)
    positives = [row for row in rows if row.get("label_positive")]
    selected_rows = [row for row, _probability in selected]
    selected_positive = [row for row in selected_rows if row.get("label_positive")]
    base_precision = len(positives) / total if total else 0.0
    selected_precision = len(selected_positive) / len(selected_rows) if selected_rows else 0.0
    return {
        "candidate_count": total,
        "positive_count": len(positives),
        "base_precision": base_precision,
        "selected_count": len(selected_rows),
        "selected_positive_count": len(selected_positive),
        "precision": selected_precision,
        "precision_lift_vs_base": (
            selected_precision / base_precision if base_precision > 0 and selected_rows else 0.0
        ),
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected_rows[:25]],
        "selected_probabilities": [probability for _row, probability in selected[:25]],
    }


def _feature_importance_block(model: Any, feature_names: list[str]) -> list[dict[str, Any]]:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    pairs = [
        {"feature": feature, "importance": float(importance)}
        for feature, importance in zip(feature_names, importances)
        if float(importance) > 0.0
    ]
    return sorted(pairs, key=lambda row: row["importance"], reverse=True)


class _TreeNode:
    def __init__(
        self,
        *,
        probability: float,
        feature_index: int | None = None,
        threshold: float | None = None,
        left: "_TreeNode | None" = None,
        right: "_TreeNode | None" = None,
    ) -> None:
        self.probability = probability
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right

    def predict_probability(self, values: np.ndarray) -> float:
        if self.feature_index is None or self.threshold is None:
            return self.probability
        if values[self.feature_index] <= self.threshold:
            return self.left.predict_probability(values) if self.left is not None else self.probability
        return self.right.predict_probability(values) if self.right is not None else self.probability


class _SmallDecisionTree:
    def __init__(self, *, max_depth: int, min_samples_leaf: int) -> None:
        self.max_depth = max(1, int(max_depth))
        self.min_samples_leaf = max(1, int(min_samples_leaf))
        self.feature_importances_: list[float] = []
        self.root: _TreeNode | None = None

    @staticmethod
    def _gini(labels: np.ndarray) -> float:
        if len(labels) == 0:
            return 0.0
        probability = float(np.mean(labels))
        return 1.0 - probability**2 - (1.0 - probability) ** 2

    def fit(self, x: np.ndarray, y: np.ndarray) -> "_SmallDecisionTree":
        self.feature_importances_ = [0.0 for _index in range(x.shape[1])]
        self.root = self._build_node(x, y, depth=0)
        total_gain = sum(self.feature_importances_)
        if total_gain > 0:
            self.feature_importances_ = [value / total_gain for value in self.feature_importances_]
        return self

    def _candidate_thresholds(self, values: np.ndarray) -> list[float]:
        unique_values = sorted({float(value) for value in values})
        if len(unique_values) < 2:
            return []
        return [
            (left + right) / 2.0
            for left, right in zip(unique_values, unique_values[1:])
            if math.isfinite((left + right) / 2.0)
        ]

    def _best_split(self, x: np.ndarray, y: np.ndarray) -> tuple[int, float, float] | None:
        parent_gini = self._gini(y)
        best: tuple[float, int, float] | None = None
        for feature_index in range(x.shape[1]):
            for threshold in self._candidate_thresholds(x[:, feature_index]):
                left_mask = x[:, feature_index] <= threshold
                right_mask = ~left_mask
                left_count = int(np.sum(left_mask))
                right_count = int(np.sum(right_mask))
                if left_count < self.min_samples_leaf or right_count < self.min_samples_leaf:
                    continue
                weighted_gini = (
                    left_count / len(y) * self._gini(y[left_mask])
                    + right_count / len(y) * self._gini(y[right_mask])
                )
                gain = parent_gini - weighted_gini
                candidate = (gain, feature_index, threshold)
                if best is None or candidate > best:
                    best = candidate
        if best is None or best[0] <= 0:
            return None
        gain, feature_index, threshold = best
        return feature_index, threshold, gain

    def _build_node(self, x: np.ndarray, y: np.ndarray, *, depth: int) -> _TreeNode:
        probability = float(np.mean(y)) if len(y) else 0.0
        if depth >= self.max_depth or len(set(int(value) for value in y)) < 2:
            return _TreeNode(probability=probability)

        split = self._best_split(x, y)
        if split is None:
            return _TreeNode(probability=probability)
        feature_index, threshold, gain = split
        self.feature_importances_[feature_index] += gain
        left_mask = x[:, feature_index] <= threshold
        right_mask = ~left_mask
        return _TreeNode(
            probability=probability,
            feature_index=feature_index,
            threshold=threshold,
            left=self._build_node(x[left_mask], y[left_mask], depth=depth + 1),
            right=self._build_node(x[right_mask], y[right_mask], depth=depth + 1),
        )

    def predict_positive_probability(self, x: np.ndarray) -> np.ndarray:
        if self.root is None:
            raise ValueError("model is not fitted")
        return np.asarray([self.root.predict_probability(row) for row in x], dtype=float)


def build_candidate_meta_label_report(
    *,
    time_to_barrier_reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None = None,
    validation_report_count: int = 1,
    probability_threshold: float = 0.5,
    min_validation_selected: int = 3,
    max_depth: int = 3,
    min_samples_leaf: int = 3,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    rows, names = _source_tagged_rows(time_to_barrier_reports, source_names)
    if validation_report_count <= 0 or validation_report_count >= len(names):
        raise ValueError("validation_report_count must leave at least one train and one validation source")
    if not 0.0 <= probability_threshold <= 1.0:
        raise ValueError("probability_threshold must be between 0 and 1")

    validation_sources = names[-validation_report_count:]
    train_sources = names[:-validation_report_count]
    train_rows = [row for row in rows if row.get("source_report") in set(train_sources)]
    validation_rows = [row for row in rows if row.get("source_report") in set(validation_sources)]

    all_label_counts = _label_counts(rows)
    if all_label_counts["positive"] == 0 or all_label_counts["negative"] == 0:
        raise ValueError("candidate labels must include both positive and negative outcomes")
    if len(validation_rows) < min_validation_selected:
        raise ValueError("validation set has fewer candidates than min_validation_selected")
    train_label_counts = _label_counts(train_rows)
    if train_label_counts["positive"] == 0 or train_label_counts["negative"] == 0:
        raise ValueError("training set must include both positive and negative outcomes")

    feature_names = _feature_names(train_rows)
    if not feature_names:
        raise ValueError("no finite decision-time numeric features found")

    x_train, medians = _feature_matrix(train_rows, feature_names)
    y_train = np.asarray([1 if row.get("label_positive") else 0 for row in train_rows], dtype=int)
    x_validation, _ = _feature_matrix(validation_rows, feature_names, medians=medians)
    model = _SmallDecisionTree(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
    )
    model.fit(x_train, y_train)

    train_probabilities = model.predict_positive_probability(x_train)
    validation_probabilities = model.predict_positive_probability(x_validation)
    train_selected = _selected_rows(train_rows, train_probabilities, probability_threshold)
    validation_selected = _selected_rows(validation_rows, validation_probabilities, probability_threshold)

    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "probe_only_replay_required",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": "features are restricted to decision-time numeric fields",
        },
        "inputs": {},
        "parameters": {
            "validation_report_count": validation_report_count,
            "probability_threshold": probability_threshold,
            "min_validation_selected": min_validation_selected,
            "max_depth": max_depth,
            "min_samples_leaf": min_samples_leaf,
        },
        "split": {
            "train_sources": train_sources,
            "validation_sources": validation_sources,
            "train_candidate_count": len(train_rows),
            "validation_candidate_count": len(validation_rows),
        },
        "candidate_counts": {
            "input_reports": len(names),
            "input_candidates": len(rows),
            "positive_candidates": all_label_counts["positive"],
            "negative_candidates": all_label_counts["negative"],
        },
        "model": {
            "type": "SmallDecisionTree",
            "feature_names": feature_names,
            "imputed_feature_medians": medians,
            "feature_importances": _feature_importance_block(model, feature_names),
        },
        "train": _evaluation_block(train_rows, train_selected),
        "validation": _evaluation_block(validation_rows, validation_selected),
    }
