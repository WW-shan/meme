from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from src.pipeline import action_policy_meta_label_probe as meta_probe
from src.pipeline import candidate_meta_label_probe as label_probe


DECISION_TIME_FIELDS = meta_probe.DECISION_TIME_FIELDS


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
    rejected_paths = report.get("rejected_signal_paths")
    effective_report = rejected_paths if isinstance(rejected_paths, Mapping) else report
    rows = effective_report.get("candidates") or effective_report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)]


def _post_target_window_return(row: Mapping[str, Any], window_seconds: float) -> float | None:
    returns = row.get("post_target_window_returns_pct")
    if not isinstance(returns, Mapping):
        return None
    keys = [
        str(int(window_seconds)) if float(window_seconds).is_integer() else str(window_seconds),
        str(float(window_seconds)),
    ]
    for key in keys:
        parsed = _finite_float(returns.get(key))
        if parsed is not None:
            return parsed
    return None


def _rejected_action_reward(
    row: Mapping[str, Any],
    *,
    quick_take_profit_pct: float,
    stop_loss_pct: float,
) -> tuple[str, float, bool]:
    plus_25 = _finite_float(row.get("time_to_plus_25_seconds"))
    minus_18 = _finite_float(row.get("time_to_minus_18_seconds"))
    if plus_25 is not None and (minus_18 is None or plus_25 <= minus_18):
        return "quick_take_profit", float(quick_take_profit_pct), True
    if minus_18 is not None:
        return "stop_loss", float(stop_loss_pct), True
    if row.get("missing_path"):
        return "missing_path", 0.0, False
    return "timeout_or_skip", 0.0, True


def _accepted_action_reward(
    row: Mapping[str, Any],
    *,
    post_target_window_seconds: float,
    default_lock_profit_pct: float,
) -> tuple[str, float, bool]:
    classification = str(row.get("classification") or "")
    if classification == "post_target_continuation":
        reward = _post_target_window_return(row, post_target_window_seconds)
        if reward is None:
            reward = _finite_float(row.get("continuation_pct"))
        return "continue_hold", float(reward or 0.0), reward is not None
    if classification == "post_target_collapse":
        lock_reward = _finite_float(row.get("target_hit_return_pct"))
        if lock_reward is None:
            lock_reward = _finite_float(row.get("target_pct"))
            if lock_reward is not None and abs(lock_reward) <= 1.0:
                lock_reward *= 100.0
        if lock_reward is None:
            lock_reward = float(default_lock_profit_pct)
        return "lock_profit", float(lock_reward), True
    if row.get("missing_path"):
        return "missing_path", 0.0, False
    return "no_action", 0.0, True


def _row_reward(
    row: Mapping[str, Any],
    *,
    quick_take_profit_pct: float,
    stop_loss_pct: float,
    post_target_window_seconds: float,
) -> tuple[str, float, bool]:
    if row.get("source_family") == "accepted":
        return _accepted_action_reward(
            row,
            post_target_window_seconds=post_target_window_seconds,
            default_lock_profit_pct=quick_take_profit_pct,
        )
    return _rejected_action_reward(
        row,
        quick_take_profit_pct=quick_take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )


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
    report_list = list(reports)
    names = list(source_names or [f"{split}_{source_family}_{index}" for index in range(len(report_list))])
    if len(report_list) != len(names):
        raise ValueError(f"{split} {source_family} source_names length must match reports")
    rows: list[dict[str, Any]] = []
    for report, source_name in zip(report_list, names):
        for row in _candidate_rows(report):
            normalized = dict(row)
            reward_policy, reward_pct, reward_known = _row_reward(
                {**normalized, "source_family": source_family},
                quick_take_profit_pct=quick_take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                post_target_window_seconds=post_target_window_seconds,
            )
            normalized.update(
                {
                    "source_family": source_family,
                    "source_split": split,
                    "source_group": str(source_name),
                    "label_positive": meta_probe._positive_label(row),
                    "replay_reward_policy": reward_policy,
                    "replay_reward_pct": reward_pct,
                    "replay_reward_known": reward_known,
                }
            )
            rows.append(normalized)
    return rows, [str(name) for name in names]


def _source_family_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("source_family") or "") for row in rows)
    return dict(sorted(counts.items()))


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    positives = sum(1 for row in rows if row.get("label_positive"))
    total = len(rows)
    return {"total": total, "positive": positives, "negative": total - positives}


def _family_has_feature(rows: Sequence[Mapping[str, Any]], family: str, field: str) -> bool:
    return any(
        row.get("source_family") == family and _finite_float(row.get(field)) is not None
        for row in rows
    )


def _feature_names(train_rows: Sequence[Mapping[str, Any]], eval_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    names = []
    for field in sorted(DECISION_TIME_FIELDS):
        train_has = (
            _family_has_feature(train_rows, "accepted", field)
            and _family_has_feature(train_rows, "rejected", field)
        )
        eval_has = any(_finite_float(row.get(field)) is not None for row in eval_rows)
        if train_has and eval_has:
            names.append(field)
    return names


def _selected_rows(
    rows: Sequence[Mapping[str, Any]],
    probabilities: np.ndarray,
    threshold: float,
) -> list[tuple[Mapping[str, Any], float]]:
    selected = []
    for row, probability in zip(rows, probabilities):
        parsed = float(probability)
        if parsed >= threshold:
            selected.append((row, parsed))
    selected.sort(key=lambda item: item[1], reverse=True)
    return selected


def _evaluation_block(
    rows: Sequence[Mapping[str, Any]],
    selected: Sequence[tuple[Mapping[str, Any], float]],
) -> dict[str, Any]:
    selected_rows = [row for row, _probability in selected]
    selected_reward = sum(float(row.get("replay_reward_pct") or 0.0) for row in selected_rows)
    selected_reward_count = len(selected_rows)
    selected_known_count = sum(1 for row in selected_rows if row.get("replay_reward_known"))
    selected_family_counts = _source_family_counts(selected_rows)
    selected_policy_counts = Counter(str(row.get("replay_reward_policy") or "") for row in selected_rows)
    selected_class_counts = Counter(
        str(row.get("barrier_class") or row.get("classification") or "unknown")
        for row in selected_rows
    )
    return {
        "candidate_count": len(rows),
        "source_family_counts": _source_family_counts(rows),
        "base_label_counts": _label_counts(rows),
        "all_candidate_reward_pct": sum(float(row.get("replay_reward_pct") or 0.0) for row in rows),
        "selected_count": selected_reward_count,
        "selected_reward_known_count": selected_known_count,
        "selected_reward_pct": selected_reward,
        "selected_average_reward_pct": selected_reward / selected_reward_count if selected_reward_count else 0.0,
        "selected_family_counts": selected_family_counts,
        "selected_reward_policy_counts": dict(sorted(selected_policy_counts.items())),
        "selected_class_counts": dict(sorted(selected_class_counts.items())),
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected_rows[:25]],
        "selected_sample": [
            {
                "symbol": row.get("symbol") or row.get("token"),
                "source_family": row.get("source_family"),
                "source_group": row.get("source_group"),
                "evidence_class": row.get("barrier_class") or row.get("classification"),
                "recommended_policy": row.get("recommended_policy"),
                "replay_reward_policy": row.get("replay_reward_policy"),
                "replay_reward_pct": row.get("replay_reward_pct"),
                "meta_probability": probability,
            }
            for row, probability in selected[:25]
        ],
    }


def _split_support_reasons(block: Mapping[str, Any], *, min_selected_per_family: int, prefix: str) -> list[str]:
    selected_counts = block.get("selected_family_counts") if isinstance(block, Mapping) else {}
    if not isinstance(selected_counts, Mapping):
        selected_counts = {}
    reasons = []
    for family in ("accepted", "rejected"):
        if int(selected_counts.get(family) or 0) < int(min_selected_per_family):
            reasons.append(f"{prefix}_{family}_selection_below_min")
    return reasons


def build_action_policy_reward_report(
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
    probability_threshold: float = 0.5,
    max_depth: int = 3,
    min_samples_leaf: int = 3,
    min_common_features: int = 1,
    min_selected_per_family: int = 1,
    quick_take_profit_pct: float = 25.0,
    stop_loss_pct: float = -18.0,
    post_target_window_seconds: float = 60.0,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(probability_threshold) <= 1.0:
        raise ValueError("probability_threshold must be between 0 and 1")

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
    feature_names = _feature_names(train_rows, eval_rows or validation_rows)
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
            "intended_use": "direct_method_shadow_reward_probe",
            "warning": "support-limited OPE-style diagnostic, not a deployable policy",
        },
        "parameters": {
            "probability_threshold": float(probability_threshold),
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
        "label_counts": {
            "train": _label_counts(train_rows),
            "validation": _label_counts(validation_rows),
            "final": _label_counts(final_rows),
        },
        "support_gate": {"passes": False, "reasons": []},
        "model": {
            "trained": False,
            "feature_names": feature_names,
            "imputed_feature_medians": {},
            "feature_importances": [],
        },
        "train": {},
        "validation": {},
        "final": {},
    }

    support_reasons = []
    train_labels = _label_counts(train_rows)
    if train_labels["positive"] == 0 or train_labels["negative"] == 0:
        support_reasons.append("train_labels_missing_positive_or_negative")
    if len(feature_names) < int(min_common_features):
        support_reasons.append("common_decision_features_below_min")
    if not validation_rows:
        support_reasons.append("validation_candidates_missing")
    if support_reasons:
        report["decision"] = "diagnostic_only_support_blocked"
        report["support_gate"] = {"passes": False, "reasons": support_reasons}
        return report

    x_train, medians = label_probe._feature_matrix(train_rows, feature_names)
    y_train = np.asarray([1 if row.get("label_positive") else 0 for row in train_rows], dtype=int)
    model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    model.fit(x_train, y_train)
    train_probabilities = model.predict_positive_probability(x_train)
    validation_matrix, _ = label_probe._feature_matrix(validation_rows, feature_names, medians=medians)
    validation_probabilities = model.predict_positive_probability(validation_matrix)
    train_selected = _selected_rows(train_rows, train_probabilities, float(probability_threshold))
    validation_selected = _selected_rows(validation_rows, validation_probabilities, float(probability_threshold))

    report["model"] = {
        "trained": True,
        "feature_names": feature_names,
        "imputed_feature_medians": medians,
        "feature_importances": label_probe._feature_importance_block(model, feature_names),
    }
    report["train"] = _evaluation_block(train_rows, train_selected)
    report["validation"] = _evaluation_block(validation_rows, validation_selected)

    if final_rows:
        final_matrix, _ = label_probe._feature_matrix(final_rows, feature_names, medians=medians)
        final_probabilities = model.predict_positive_probability(final_matrix)
        final_selected = _selected_rows(final_rows, final_probabilities, float(probability_threshold))
        report["final"] = _evaluation_block(final_rows, final_selected)

    validation_support_reasons = _split_support_reasons(
        report["validation"],
        min_selected_per_family=min_selected_per_family,
        prefix="validation",
    )
    final_support_reasons = (
        _split_support_reasons(
            report["final"],
            min_selected_per_family=min_selected_per_family,
            prefix="final",
        )
        if final_rows
        else []
    )
    all_support_reasons = validation_support_reasons + final_support_reasons
    if all_support_reasons:
        report["decision"] = "shadow_only_support_limited"
        report["support_gate"] = {"passes": False, "reasons": all_support_reasons}
        return report

    reward = float(report["validation"]["selected_reward_pct"])
    if final_rows:
        reward = min(reward, float(report["final"]["selected_reward_pct"]))
    report["support_gate"] = {"passes": True, "reasons": []}
    report["decision"] = (
        "shadow_reward_positive_replay_required"
        if reward > 0.0
        else "shadow_reward_non_positive_rejected"
    )
    return report
