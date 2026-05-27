from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from src.pipeline import action_policy_reward_probe as reward_probe
from src.pipeline import candidate_meta_label_probe as label_probe


DECISION_TIME_FIELDS = reward_probe.DECISION_TIME_FIELDS
SKIP_ROUTE = "skip"
SKIP_LIKE_POLICIES = {
    "",
    "missing_path",
    "no_action",
    "skip",
    "stop_loss",
    "timeout_or_skip",
}
POSITIVE_ROUTE_POLICIES = {
    "conditional_slow_hold",
    "continue_hold",
    "lock_profit",
    "quick_take_profit",
}


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


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


def _route_label(row: Mapping[str, Any]) -> str:
    recommended = str(row.get("recommended_policy") or "")
    reward_policy = str(row.get("replay_reward_policy") or "")
    if recommended in {"conditional_slow_hold", "quick_take_profit"}:
        return recommended
    if recommended in {"continue_hold", "lock_profit"}:
        return recommended
    if reward_policy in POSITIVE_ROUTE_POLICIES:
        return reward_policy
    return SKIP_ROUTE


def _row_policy_reward(row: Mapping[str, Any], predicted_route: str) -> float:
    if predicted_route == SKIP_ROUTE:
        return 0.0
    route_label = str(row.get("route_label") or SKIP_ROUTE)
    if predicted_route != route_label:
        if route_label == SKIP_ROUTE:
            return float(row.get("replay_reward_pct") or 0.0)
        return 0.0
    return float(row.get("route_reward_pct") or 0.0)


def _normalize_rows(
    *,
    reports: Iterable[Mapping[str, Any]],
    source_family: str,
    split: str,
    source_names: Iterable[str] | None,
    quick_take_profit_pct: float,
    stop_loss_pct: float,
    post_target_window_seconds: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows, names = reward_probe._normalize_rows(
        reports=reports,
        source_family=source_family,
        split=split,
        source_names=source_names,
        quick_take_profit_pct=quick_take_profit_pct,
        stop_loss_pct=stop_loss_pct,
        post_target_window_seconds=post_target_window_seconds,
    )
    normalized = []
    for row in rows:
        item = dict(row)
        route = _route_label(item)
        item["route_label"] = route
        item["route_reward_pct"] = float(item.get("replay_reward_pct") or 0.0)
        normalized.append(item)
    return normalized, names


def _route_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("route_label") or SKIP_ROUTE) for row in rows)
    return dict(sorted(counts.items()))


def _source_family_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("source_family") or "") for row in rows)
    return dict(sorted(counts.items()))


def _route_names(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    names = sorted({str(row.get("route_label") or SKIP_ROUTE) for row in rows})
    if SKIP_ROUTE in names:
        names = [name for name in names if name != SKIP_ROUTE] + [SKIP_ROUTE]
    return names


def _fit_route_models(
    train_rows: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    route_names: Sequence[str],
    *,
    max_depth: int,
    min_samples_leaf: int,
) -> tuple[dict[str, label_probe._SmallDecisionTree], dict[str, float], dict[str, float]]:
    x_train, medians = label_probe._feature_matrix(list(train_rows), list(feature_names))
    priors: dict[str, float] = {}
    models: dict[str, label_probe._SmallDecisionTree] = {}
    for route in route_names:
        y_train = np.asarray(
            [1 if str(row.get("route_label") or SKIP_ROUTE) == route else 0 for row in train_rows],
            dtype=int,
        )
        priors[route] = float(np.mean(y_train)) if len(y_train) else 0.0
        model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
        model.fit(x_train, y_train)
        models[route] = model
    return models, medians, priors


def _predict_route_probabilities(
    models: Mapping[str, label_probe._SmallDecisionTree],
    medians: Mapping[str, float],
    feature_names: Sequence[str],
    route_names: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(route_names)), dtype=float)
    x_rows, _ = label_probe._feature_matrix(list(rows), list(feature_names), medians=dict(medians))
    columns = []
    for route in route_names:
        columns.append(models[route].predict_positive_probability(x_rows).reshape(-1))
    matrix = np.vstack(columns).T if columns else np.zeros((len(rows), 0), dtype=float)
    sums = matrix.sum(axis=1)
    normalized = matrix.copy()
    for index, total in enumerate(sums):
        if total > 0.0 and math.isfinite(float(total)):
            normalized[index, :] = normalized[index, :] / total
    return normalized


def _feature_importances_by_route(
    models: Mapping[str, label_probe._SmallDecisionTree],
    feature_names: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    return {
        route: label_probe._feature_importance_block(model, list(feature_names))
        for route, model in sorted(models.items())
    }


def _aggregate_feature_importances(
    by_route: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    totals: Counter[str] = Counter()
    for rows in by_route.values():
        for row in rows:
            feature = str(row.get("feature") or "")
            importance = _finite_float(row.get("importance")) or 0.0
            if feature:
                totals[feature] += importance
    total = sum(float(value) for value in totals.values())
    if total <= 0.0:
        return []
    return [
        {"feature": feature, "importance": float(value) / total}
        for feature, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]


def _prediction_rows(
    rows: Sequence[Mapping[str, Any]],
    probabilities: np.ndarray,
    route_names: Sequence[str],
    confidence_threshold: float,
) -> list[dict[str, Any]]:
    predictions = []
    for row, probability_row in zip(rows, probabilities):
        best_index = int(np.argmax(probability_row)) if len(probability_row) else 0
        predicted_route = route_names[best_index] if route_names else SKIP_ROUTE
        confidence = float(probability_row[best_index]) if len(probability_row) else 0.0
        if confidence < float(confidence_threshold):
            predicted_route = SKIP_ROUTE
        reward_pct = _row_policy_reward(row, predicted_route)
        predictions.append(
            {
                "row": row,
                "predicted_route": predicted_route,
                "confidence": confidence,
                "reward_pct": reward_pct,
                "route_probabilities": {
                    route: float(probability)
                    for route, probability in zip(route_names, probability_row)
                },
            }
        )
    return predictions


def _evaluation_block(
    rows: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    selected = [item for item in predictions if item.get("predicted_route") != SKIP_ROUTE]
    selected_rows = [item["row"] for item in selected]
    routed_policy_counts = Counter(str(item.get("predicted_route") or "") for item in selected)
    selected_family_counts = _source_family_counts(selected_rows)
    confusion: dict[str, dict[str, int]] = {}
    correct = 0
    for row, prediction in zip(rows, predictions):
        actual = str(row.get("route_label") or SKIP_ROUTE)
        predicted = str(prediction.get("predicted_route") or SKIP_ROUTE)
        confusion.setdefault(actual, {})
        confusion[actual][predicted] = confusion[actual].get(predicted, 0) + 1
        if actual == predicted:
            correct += 1
    selected_reward = sum(float(item.get("reward_pct") or 0.0) for item in selected)
    return {
        "candidate_count": len(rows),
        "route_counts": _route_counts(rows),
        "route_accuracy": correct / len(rows) if rows else 0.0,
        "selected_count": len(selected),
        "selected_reward_pct": selected_reward,
        "selected_average_reward_pct": selected_reward / len(selected) if selected else 0.0,
        "selected_family_counts": selected_family_counts,
        "routed_policy_counts": dict(sorted(routed_policy_counts.items())),
        "confusion_matrix": {
            actual: dict(sorted(predicted_counts.items()))
            for actual, predicted_counts in sorted(confusion.items())
        },
        "selected_symbols": [
            str(item["row"].get("symbol") or item["row"].get("token") or "")
            for item in selected[:25]
        ],
        "selected_routes": [
            {
                "symbol": item["row"].get("symbol") or item["row"].get("token"),
                "source_family": item["row"].get("source_family"),
                "source_group": item["row"].get("source_group"),
                "actual_route": item["row"].get("route_label"),
                "predicted_route": item.get("predicted_route"),
                "confidence": item.get("confidence"),
                "reward_pct": item.get("reward_pct"),
                "recommended_policy": item["row"].get("recommended_policy"),
                "replay_reward_policy": item["row"].get("replay_reward_policy"),
            }
            for item in selected[:50]
        ],
    }


def _split_support_reasons(block: Mapping[str, Any], *, min_selected_per_family: int, prefix: str) -> list[str]:
    if min_selected_per_family <= 0:
        return []
    selected_counts = block.get("selected_family_counts") if isinstance(block, Mapping) else {}
    if not isinstance(selected_counts, Mapping):
        selected_counts = {}
    reasons = []
    for family in ("accepted", "rejected"):
        if int(selected_counts.get(family) or 0) < int(min_selected_per_family):
            reasons.append(f"{prefix}_{family}_selection_below_min")
    return reasons


def build_action_policy_router_report(
    *,
    train_rejected_reports: Iterable[Mapping[str, Any]],
    train_accepted_reports: Iterable[Mapping[str, Any]],
    validation_rejected_reports: Iterable[Mapping[str, Any]],
    validation_accepted_reports: Iterable[Mapping[str, Any]],
    final_rejected_reports: Iterable[Mapping[str, Any]] | None = None,
    final_accepted_reports: Iterable[Mapping[str, Any]] | None = None,
    train_rejected_source_names: Iterable[str] | None = None,
    train_accepted_source_names: Iterable[str] | None = None,
    validation_rejected_source_names: Iterable[str] | None = None,
    validation_accepted_source_names: Iterable[str] | None = None,
    final_rejected_source_names: Iterable[str] | None = None,
    final_accepted_source_names: Iterable[str] | None = None,
    route_confidence_threshold: float = 0.5,
    max_depth: int = 3,
    min_samples_leaf: int = 3,
    min_common_features: int = 1,
    min_selected_per_family: int = 1,
    quick_take_profit_pct: float = 25.0,
    stop_loss_pct: float = -18.0,
    post_target_window_seconds: float = 60.0,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(route_confidence_threshold) <= 1.0:
        raise ValueError("route_confidence_threshold must be between 0 and 1")

    normalize_kwargs = {
        "quick_take_profit_pct": float(quick_take_profit_pct),
        "stop_loss_pct": float(stop_loss_pct),
        "post_target_window_seconds": float(post_target_window_seconds),
    }
    train_rejected, train_rejected_names = _normalize_rows(
        reports=train_rejected_reports,
        source_family="rejected",
        split="train",
        source_names=train_rejected_source_names,
        **normalize_kwargs,
    )
    train_accepted, train_accepted_names = _normalize_rows(
        reports=train_accepted_reports,
        source_family="accepted",
        split="train",
        source_names=train_accepted_source_names,
        **normalize_kwargs,
    )
    validation_rejected, validation_rejected_names = _normalize_rows(
        reports=validation_rejected_reports,
        source_family="rejected",
        split="validation",
        source_names=validation_rejected_source_names,
        **normalize_kwargs,
    )
    validation_accepted, validation_accepted_names = _normalize_rows(
        reports=validation_accepted_reports,
        source_family="accepted",
        split="validation",
        source_names=validation_accepted_source_names,
        **normalize_kwargs,
    )
    final_rejected, final_rejected_names = _normalize_rows(
        reports=final_rejected_reports or [],
        source_family="rejected",
        split="final",
        source_names=final_rejected_source_names,
        **normalize_kwargs,
    )
    final_accepted, final_accepted_names = _normalize_rows(
        reports=final_accepted_reports or [],
        source_family="accepted",
        split="final",
        source_names=final_accepted_source_names,
        **normalize_kwargs,
    )

    train_rows = train_rejected + train_accepted
    validation_rows = validation_rejected + validation_accepted
    final_rows = final_rejected + final_accepted
    eval_rows = validation_rows + final_rows
    feature_names = reward_probe._feature_names(train_rows, eval_rows or validation_rows)
    route_names = _route_names(train_rows)

    report: dict[str, Any] = {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "diagnostic_only_not_evaluated",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": False,
        },
        "evidence_scope": {
            "features_must_be_decision_time": True,
            "labels_and_rewards_use_ex_post_paths": True,
            "intended_use": "multi_policy_action_router_shadow_probe",
            "warning": "one-vs-rest diagnostic router; not a deployable live policy",
        },
        "parameters": {
            "route_confidence_threshold": float(route_confidence_threshold),
            "max_depth": int(max_depth),
            "min_samples_leaf": int(min_samples_leaf),
            "min_common_features": int(min_common_features),
            "min_selected_per_family": int(min_selected_per_family),
            "quick_take_profit_pct": float(quick_take_profit_pct),
            "stop_loss_pct": float(stop_loss_pct),
            "post_target_window_seconds": float(post_target_window_seconds),
        },
        "source_groups": {
            "train_rejected": train_rejected_names,
            "train_accepted": train_accepted_names,
            "validation_rejected": validation_rejected_names,
            "validation_accepted": validation_accepted_names,
            "final_rejected": final_rejected_names,
            "final_accepted": final_accepted_names,
        },
        "candidate_counts": {
            "train": len(train_rows),
            "validation": len(validation_rows),
            "final": len(final_rows),
        },
        "source_family_counts": {
            "train": _source_family_counts(train_rows),
            "validation": _source_family_counts(validation_rows),
            "final": _source_family_counts(final_rows),
        },
        "route_counts": {
            "train": _route_counts(train_rows),
            "validation": _route_counts(validation_rows),
            "final": _route_counts(final_rows),
        },
        "support_gate": {"passes": False, "reasons": []},
        "model": {
            "trained": False,
            "route_names": route_names,
            "feature_names": feature_names,
            "imputed_feature_medians": {},
            "feature_importances": [],
            "feature_importances_by_route": {},
        },
        "train": {},
        "validation": {},
        "final": {},
    }

    support_reasons = []
    train_route_counts = _route_counts(train_rows)
    if len(train_route_counts) < 2:
        support_reasons.append("train_route_labels_below_two_classes")
    if sum(count for route, count in train_route_counts.items() if route != SKIP_ROUTE) <= 0:
        support_reasons.append("train_positive_route_labels_missing")
    if len(feature_names) < int(min_common_features):
        support_reasons.append("common_decision_features_below_min")
    if not validation_rows:
        support_reasons.append("validation_candidates_missing")
    if support_reasons:
        report["decision"] = "diagnostic_only_support_blocked"
        report["support_gate"] = {"passes": False, "reasons": support_reasons}
        return report

    models, medians, priors = _fit_route_models(
        train_rows,
        feature_names,
        route_names,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
    )
    by_route = _feature_importances_by_route(models, feature_names)
    report["model"] = {
        "trained": True,
        "route_names": route_names,
        "route_priors": priors,
        "feature_names": feature_names,
        "imputed_feature_medians": medians,
        "feature_importances": _aggregate_feature_importances(by_route),
        "feature_importances_by_route": by_route,
    }

    train_probabilities = _predict_route_probabilities(models, medians, feature_names, route_names, train_rows)
    validation_probabilities = _predict_route_probabilities(models, medians, feature_names, route_names, validation_rows)
    train_predictions = _prediction_rows(train_rows, train_probabilities, route_names, route_confidence_threshold)
    validation_predictions = _prediction_rows(
        validation_rows,
        validation_probabilities,
        route_names,
        route_confidence_threshold,
    )
    report["train"] = _evaluation_block(train_rows, train_predictions)
    report["validation"] = _evaluation_block(validation_rows, validation_predictions)

    if final_rows:
        final_probabilities = _predict_route_probabilities(models, medians, feature_names, route_names, final_rows)
        final_predictions = _prediction_rows(final_rows, final_probabilities, route_names, route_confidence_threshold)
        report["final"] = _evaluation_block(final_rows, final_predictions)

    support_reasons = _split_support_reasons(
        report["validation"],
        min_selected_per_family=min_selected_per_family,
        prefix="validation",
    )
    if final_rows:
        support_reasons += _split_support_reasons(
            report["final"],
            min_selected_per_family=min_selected_per_family,
            prefix="final",
        )
    if support_reasons:
        report["decision"] = "shadow_only_support_limited"
        report["support_gate"] = {"passes": False, "reasons": support_reasons}
        return report

    reward = float(report["validation"]["selected_reward_pct"])
    if final_rows:
        reward = min(reward, float(report["final"]["selected_reward_pct"]))
    report["support_gate"] = {"passes": True, "reasons": []}
    report["decision"] = (
        "shadow_router_positive_replay_required"
        if reward > 0.0
        else "shadow_router_non_positive_rejected"
    )
    return report
