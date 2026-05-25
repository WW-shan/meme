from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np

from src.pipeline import candidate_meta_label_probe as label_probe
from src.pipeline import support_action_policy_probe as support_probe


DECISION_TIME_FIELDS = support_probe.DECISION_TIME_FIELDS
ACTION_POSITIVE_POLICIES = {
    *support_probe.POSITIVE_POLICIES,
    "lock_profit",
    "continue_hold",
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


def _candidate_rows(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    effective_report = report
    rejected_paths = report.get("rejected_signal_paths")
    if isinstance(rejected_paths, Mapping):
        effective_report = rejected_paths
    rows = effective_report.get("candidates") or effective_report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)]


def _positive_label(row: Mapping[str, Any]) -> bool:
    return row.get("recommended_policy") in ACTION_POSITIVE_POLICIES


def _normalized_rows(
    *,
    reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None,
    family: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    report_list = list(reports)
    names = list(source_names or [f"{family}_{index}" for index in range(len(report_list))])
    if len(report_list) != len(names):
        raise ValueError(f"{family} source_names length must match reports")
    rows: list[dict[str, Any]] = []
    for report, source_name in zip(report_list, names):
        for row in _candidate_rows(report):
            normalized = dict(row)
            normalized["source_family"] = family
            normalized["source_group"] = str(source_name)
            normalized["source_report"] = str(source_name)
            normalized["label_positive"] = _positive_label(row)
            rows.append(normalized)
    return rows, [str(name) for name in names]


def _unique_preserving(values: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _label_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    row_list = list(rows)
    positives = sum(1 for row in row_list if row.get("label_positive"))
    total = len(row_list)
    return {
        "total": total,
        "positive": positives,
        "negative": total - positives,
    }


def _finite_feature_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    row_list = list(rows)
    return {
        field: sum(1 for row in row_list if _finite_float(row.get(field)) is not None)
        for field in sorted(DECISION_TIME_FIELDS)
    }


def _feature_parity(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    accepted_rows = [row for row in rows if row.get("source_family") == "accepted"]
    rejected_rows = [row for row in rows if row.get("source_family") == "rejected"]
    accepted_counts = _finite_feature_counts(accepted_rows)
    rejected_counts = _finite_feature_counts(rejected_rows)
    common = [
        field
        for field in sorted(DECISION_TIME_FIELDS)
        if accepted_counts.get(field, 0) > 0 and rejected_counts.get(field, 0) > 0
    ]
    return {
        "accepted_finite_counts": accepted_counts,
        "rejected_finite_counts": rejected_counts,
        "common_feature_names": common,
    }


def _candidate_sample(rows: list[Mapping[str, Any]], limit: int = 100) -> dict[str, Any]:
    return {
        "included": min(len(rows), limit),
        "total": len(rows),
        "truncated": len(rows) > limit,
        "rows": [
            {
                "symbol": row.get("symbol") or row.get("token"),
                "source_family": row.get("source_family"),
                "source_group": row.get("source_group"),
                "recommended_policy": row.get("recommended_policy"),
                "label_positive": bool(row.get("label_positive")),
            }
            for row in rows[:limit]
        ],
    }


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
    selected_only = [row for row, _probability in selected]
    selected_positive = [row for row in selected_only if row.get("label_positive")]
    base_precision = len(positives) / total if total else 0.0
    selected_precision = len(selected_positive) / len(selected_only) if selected_only else 0.0
    selected_family_counts = Counter(str(row.get("source_family") or "") for row in selected_only)
    selected_policy_counts = Counter(str(row.get("recommended_policy") or "") for row in selected_only)
    selected_class_counts = Counter(
        str(row.get("barrier_class") or row.get("classification") or "unknown")
        for row in selected_only
    )
    return {
        "candidate_count": total,
        "positive_count": len(positives),
        "base_precision": base_precision,
        "selected_count": len(selected_only),
        "selected_positive_count": len(selected_positive),
        "precision": selected_precision,
        "precision_lift_vs_base": (
            selected_precision / base_precision if base_precision > 0.0 and selected_only else 0.0
        ),
        "selected_family_counts": dict(sorted(selected_family_counts.items())),
        "selected_policy_counts": dict(sorted(selected_policy_counts.items())),
        "selected_class_counts": dict(sorted(selected_class_counts.items())),
        "selected_symbols": [
            str(row.get("symbol") or row.get("token") or "")
            for row in selected_only[:25]
        ],
        "selected_probabilities": [probability for _row, probability in selected[:25]],
        "selected_sample": [
            {
                "symbol": row.get("symbol") or row.get("token"),
                "source_family": row.get("source_family"),
                "source_group": row.get("source_group"),
                "recommended_policy": row.get("recommended_policy"),
                "evidence_class": row.get("barrier_class") or row.get("classification"),
                "label_positive": bool(row.get("label_positive")),
                "meta_probability": probability,
            }
            for row, probability in selected[:25]
        ],
    }


def _class_counts(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        class_name = row.get("barrier_class") or row.get("classification") or "unknown"
        counts[str(class_name)] += 1
    return dict(sorted(counts.items()))


def _base_report(
    *,
    rows: list[dict[str, Any]],
    rejected_names: list[str],
    accepted_names: list[str],
    source_group_order: list[str],
    generated_at: dt.datetime | None,
    validation_source_count: int,
    probability_threshold: float,
    min_validation_selected: int,
    max_depth: int,
    min_samples_leaf: int,
    min_family_candidates: int,
    min_common_features: int,
    min_validation_selected_per_family: int,
) -> dict[str, Any]:
    family_counts = Counter(str(row.get("source_family")) for row in rows)
    policy_counts = Counter(str(row.get("recommended_policy") or "") for row in rows)
    parity = _feature_parity(rows)
    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "diagnostic_only_not_evaluated",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": "features are restricted to decision-time numeric fields",
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "accepted_rejected_action_policy_meta_label_support_probe",
        },
        "inputs": {},
        "parameters": {
            "validation_source_count": int(validation_source_count),
            "probability_threshold": float(probability_threshold),
            "min_validation_selected": int(min_validation_selected),
            "max_depth": int(max_depth),
            "min_samples_leaf": int(min_samples_leaf),
            "min_family_candidates": int(min_family_candidates),
            "min_common_features": int(min_common_features),
            "min_validation_selected_per_family": int(min_validation_selected_per_family),
        },
        "source_groups": {
            "order": source_group_order,
            "rejected": rejected_names,
            "accepted": accepted_names,
        },
        "source_family_counts": {
            "rejected": int(family_counts.get("rejected", 0)),
            "accepted": int(family_counts.get("accepted", 0)),
        },
        "candidate_counts": {
            **_label_counts(rows),
            "source_groups": len(source_group_order),
        },
        "policy_counts": dict(sorted(policy_counts.items())),
        "class_counts": _class_counts(rows),
        "feature_parity": parity,
        "support_gate": {
            "passes": False,
            "reasons": [],
        },
        "split": {
            "train_source_groups": [],
            "validation_source_groups": [],
            "train_candidate_count": 0,
            "validation_candidate_count": 0,
        },
        "meta_label_model": {
            "trained": False,
            "feature_names": [],
            "imputed_feature_medians": {},
            "feature_importances": [],
        },
        "train": {},
        "validation": {},
        "candidate_sample": _candidate_sample(rows),
    }


def build_action_policy_meta_label_report(
    *,
    rejected_reports: Iterable[Mapping[str, Any]],
    accepted_reports: Iterable[Mapping[str, Any]],
    rejected_source_names: Iterable[str] | None = None,
    accepted_source_names: Iterable[str] | None = None,
    validation_source_count: int = 1,
    probability_threshold: float = 0.5,
    min_validation_selected: int = 3,
    max_depth: int = 3,
    min_samples_leaf: int = 3,
    min_family_candidates: int = 3,
    min_common_features: int = 1,
    min_validation_selected_per_family: int = 1,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(probability_threshold) <= 1.0:
        raise ValueError("probability_threshold must be between 0 and 1")
    if validation_source_count <= 0:
        raise ValueError("validation_source_count must be positive")

    rejected_rows, rejected_names = _normalized_rows(
        reports=rejected_reports,
        source_names=rejected_source_names,
        family="rejected",
    )
    accepted_rows, accepted_names = _normalized_rows(
        reports=accepted_reports,
        source_names=accepted_source_names,
        family="accepted",
    )
    rows = rejected_rows + accepted_rows
    source_group_order = _unique_preserving([*rejected_names, *accepted_names])
    report = _base_report(
        rows=rows,
        rejected_names=rejected_names,
        accepted_names=accepted_names,
        source_group_order=source_group_order,
        generated_at=generated_at,
        validation_source_count=validation_source_count,
        probability_threshold=probability_threshold,
        min_validation_selected=min_validation_selected,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        min_family_candidates=min_family_candidates,
        min_common_features=min_common_features,
        min_validation_selected_per_family=min_validation_selected_per_family,
    )

    gate_reasons = []
    if report["source_family_counts"]["rejected"] < int(min_family_candidates):
        gate_reasons.append("rejected_family_below_min_candidates")
    if report["source_family_counts"]["accepted"] < int(min_family_candidates):
        gate_reasons.append("accepted_family_below_min_candidates")
    if len(report["feature_parity"]["common_feature_names"]) < int(min_common_features):
        gate_reasons.append("common_decision_features_below_min")
    if len(source_group_order) <= int(validation_source_count):
        gate_reasons.append("validation_source_count_leaves_no_train_source")

    if gate_reasons:
        if "common_decision_features_below_min" in gate_reasons:
            report["decision"] = "diagnostic_only_feature_parity_blocked"
        elif "validation_source_count_leaves_no_train_source" in gate_reasons:
            report["decision"] = "diagnostic_only_split_support_blocked"
        else:
            report["decision"] = "diagnostic_only_small_family_support"
        report["support_gate"] = {"passes": False, "reasons": gate_reasons}
        return report

    validation_groups = source_group_order[-int(validation_source_count):]
    train_groups = source_group_order[:-int(validation_source_count)]
    train_rows = [row for row in rows if row.get("source_group") in set(train_groups)]
    validation_rows = [row for row in rows if row.get("source_group") in set(validation_groups)]
    report["split"] = {
        "train_source_groups": train_groups,
        "validation_source_groups": validation_groups,
        "train_candidate_count": len(train_rows),
        "validation_candidate_count": len(validation_rows),
    }

    train_label_counts = _label_counts(train_rows)
    all_label_counts = _label_counts(rows)
    split_reasons = []
    if all_label_counts["positive"] == 0 or all_label_counts["negative"] == 0:
        split_reasons.append("combined_labels_missing_positive_or_negative")
    if train_label_counts["positive"] == 0 or train_label_counts["negative"] == 0:
        split_reasons.append("train_labels_missing_positive_or_negative")
    if len(validation_rows) < int(min_validation_selected):
        split_reasons.append("validation_candidates_below_min_selected")
    if split_reasons:
        report["decision"] = "diagnostic_only_split_support_blocked"
        report["support_gate"] = {"passes": False, "reasons": split_reasons}
        return report

    common_features = list(report["feature_parity"]["common_feature_names"])
    train_feature_names = [
        field
        for field in common_features
        if any(_finite_float(row.get(field)) is not None for row in train_rows)
    ]
    if len(train_feature_names) < int(min_common_features):
        report["decision"] = "diagnostic_only_feature_parity_blocked"
        report["support_gate"] = {
            "passes": False,
            "reasons": ["train_common_decision_features_below_min"],
        }
        return report

    x_train, medians = label_probe._feature_matrix(train_rows, train_feature_names)
    y_train = np.asarray([1 if row.get("label_positive") else 0 for row in train_rows], dtype=int)
    x_validation, _ = label_probe._feature_matrix(validation_rows, train_feature_names, medians=medians)
    model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    model.fit(x_train, y_train)
    train_probabilities = model.predict_positive_probability(x_train)
    validation_probabilities = model.predict_positive_probability(x_validation)
    train_selected = _selected_rows(train_rows, train_probabilities, float(probability_threshold))
    validation_selected = _selected_rows(validation_rows, validation_probabilities, float(probability_threshold))

    report["decision"] = "probe_only_replay_required"
    report["support_gate"] = {"passes": True, "reasons": []}
    report["meta_label_model"] = {
        "trained": True,
        "feature_names": train_feature_names,
        "imputed_feature_medians": medians,
        "feature_importances": label_probe._feature_importance_block(model, train_feature_names),
    }
    report["train"] = _evaluation_block(train_rows, train_selected)
    report["validation"] = _evaluation_block(validation_rows, validation_selected)
    selected_family_counts = report["validation"]["selected_family_counts"]
    selected_family_reasons = []
    if selected_family_counts.get("accepted", 0) < int(min_validation_selected_per_family):
        selected_family_reasons.append("validation_accepted_selection_below_min")
    if selected_family_counts.get("rejected", 0) < int(min_validation_selected_per_family):
        selected_family_reasons.append("validation_rejected_selection_below_min")
    if selected_family_reasons:
        report["decision"] = "diagnostic_only_selected_family_support_blocked"
        report["support_gate"] = {"passes": False, "reasons": selected_family_reasons}
    return report
