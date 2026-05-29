from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.pipeline import support_action_policy_probe


DEFAULT_BAD_CLASSES = frozenset(("target_not_hit",))
DEFAULT_PROTECTED_CLASSES = frozenset((
    "post_target_continuation",
    "post_target_collapse",
    "post_target_unresolved",
))
MAX_THRESHOLD_VALUES = 25

DECISION_TIME_FIELDS = frozenset(
    field
    for field in support_action_policy_probe.DECISION_TIME_FIELDS
    if field
    not in {
        "entry_ranking_mode",
        "features_hash",
        "flow_metrics_available",
        "near_threshold_rescue_used",
        "runner_retention_train_boundary_match",
        "use_pred_return_filter",
    }
)


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        default=_json_default,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _candidate_rows(report: Mapping[str, Any]) -> Sequence[Any]:
    for key in ("candidate_sample", "candidates", "trades", "trade_sample"):
        rows = report.get(key)
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return rows
    return []


def rows_from_report(report: Mapping[str, Any], *, split: str, source_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(_candidate_rows(report)):
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        item["source_split"] = str(split)
        item["source_report"] = str(source_name)
        item["source_row_index"] = int(index)
        rows.append(item)
    return rows


def _outcome(row: Mapping[str, Any]) -> str:
    value = row.get("classification") or row.get("failure_label") or row.get("barrier_class")
    return str(value) if value else "unknown"


def _feature_values(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {}
    for row in rows:
        for field in DECISION_TIME_FIELDS:
            value = _as_float(row.get(field))
            if value is not None:
                values.setdefault(field, []).append(value)
    return {
        field: field_values
        for field, field_values in values.items()
        if len(set(field_values)) >= 2
    }


def _quantile(sorted_values: Sequence[float], quantile: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = max(0.0, min(1.0, float(quantile))) * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(sorted_values[lower])
    fraction = position - lower
    return float(sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction)


def _numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "p25": _quantile(finite, 0.25),
        "median": _quantile(finite, 0.50),
        "p75": _quantile(finite, 0.75),
        "max": finite[-1],
        "mean": sum(finite) / len(finite),
    }


def _threshold_values(values: Sequence[float]) -> list[float]:
    unique = sorted({float(value) for value in values if math.isfinite(float(value))})
    if len(unique) <= MAX_THRESHOLD_VALUES:
        return unique
    indexes = {
        round(index * (len(unique) - 1) / (MAX_THRESHOLD_VALUES - 1))
        for index in range(MAX_THRESHOLD_VALUES)
    }
    return [unique[index] for index in sorted(indexes)]


def _matches(row: Mapping[str, Any], *, feature: str, operator: str, threshold: float) -> bool:
    value = _as_float(row.get(feature))
    if value is None:
        return False
    if operator == "<=":
        return value <= float(threshold)
    if operator == ">=":
        return value >= float(threshold)
    raise ValueError(f"unsupported operator: {operator}")


def _post_target_return(row: Mapping[str, Any], preferred_window_seconds: float) -> float | None:
    returns = row.get("post_target_window_returns_pct")
    if not isinstance(returns, Mapping):
        return None
    preferred_keys = [
        str(int(preferred_window_seconds)) if float(preferred_window_seconds).is_integer() else str(preferred_window_seconds),
        str(float(preferred_window_seconds)),
    ]
    for key in preferred_keys:
        value = _as_float(returns.get(key))
        if value is not None:
            return value
    finite_returns = [_as_float(value) for value in returns.values()]
    finite = [value for value in finite_returns if value is not None]
    return finite[-1] if finite else None


def row_utility_proxy_pct(row: Mapping[str, Any], *, post_target_window_seconds: float = 60.0) -> float:
    """Conservative ex-post utility proxy used only to falsify abstention rules.

    Bad never-activated rows contribute their observed downside, while activation-hit rows are treated as
    protected opportunity cost. This is intentionally not a deployable PnL estimate.
    """
    outcome = _outcome(row)
    mfe_pct = _as_float(row.get("mfe_pct"))
    mae_pct = _as_float(row.get("mae_pct"))
    if outcome == "target_not_hit":
        if mae_pct is not None and mae_pct < 0.0:
            return float(mae_pct)
        if mfe_pct is not None and mfe_pct < 0.0:
            return float(mfe_pct)
        return 0.0

    window_return = _post_target_return(row, post_target_window_seconds)
    if window_return is not None:
        return float(window_return)
    if mfe_pct is not None and mfe_pct > 0.0:
        return float(mfe_pct)
    return 0.0


def _benefit_without_top(selected_benefits: Sequence[float]) -> float | None:
    benefits = [float(value) for value in selected_benefits if math.isfinite(float(value))]
    if not benefits:
        return None
    if len(benefits) == 1:
        return 0.0
    return sum(benefits) - max(benefits)


def _evaluate_rule(
    rows: Sequence[Mapping[str, Any]],
    *,
    feature: str,
    operator: str,
    threshold: float,
    bad_classes: set[str],
    protected_classes: set[str],
    post_target_window_seconds: float,
) -> dict[str, Any]:
    selected = [
        dict(row)
        for row in rows
        if _matches(row, feature=feature, operator=operator, threshold=threshold)
    ]
    outcomes = [_outcome(row) for row in selected]
    bad_count = sum(1 for outcome in outcomes if outcome in bad_classes)
    protected_count = sum(1 for outcome in outcomes if outcome in protected_classes)
    selected_utilities = [
        row_utility_proxy_pct(row, post_target_window_seconds=post_target_window_seconds)
        for row in selected
    ]
    abstention_benefits = [-utility for utility in selected_utilities]
    utility_delta = sum(abstention_benefits)
    outcome_counts = Counter(outcomes)
    return {
        "feature": str(feature),
        "operator": str(operator),
        "threshold": float(threshold),
        "selected_count": len(selected),
        "bad_count": bad_count,
        "protected_count": protected_count,
        "neutral_count": len(selected) - bad_count - protected_count,
        "bad_precision": bad_count / len(selected) if selected else 0.0,
        "selected_utility_proxy_pct": sum(selected_utilities),
        "abstention_utility_delta_pct": utility_delta,
        "abstention_utility_delta_without_top_benefit_pct": _benefit_without_top(abstention_benefits),
        "selected_outcome_counts": dict(sorted(outcome_counts.items())),
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected[:25]],
        "selected_sample": [
            {
                "symbol": row.get("symbol") or row.get("token"),
                "classification": _outcome(row),
                "utility_proxy_pct": row_utility_proxy_pct(
                    row,
                    post_target_window_seconds=post_target_window_seconds,
                ),
                "source_report": row.get("source_report"),
                "source_row_index": row.get("source_row_index"),
            }
            for row in selected[:25]
        ],
    }


def _rule_results(
    rows: Sequence[Mapping[str, Any]],
    *,
    bad_classes: set[str],
    protected_classes: set[str],
    post_target_window_seconds: float,
) -> list[dict[str, Any]]:
    features = _feature_values(rows)
    results = []
    for feature in sorted(features):
        for threshold in _threshold_values(features[feature]):
            for operator in ("<=", ">="):
                results.append(
                    _evaluate_rule(
                        rows,
                        feature=feature,
                        operator=operator,
                        threshold=threshold,
                        bad_classes=bad_classes,
                        protected_classes=protected_classes,
                        post_target_window_seconds=post_target_window_seconds,
                    )
                )
    return results


def _train_rank_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(row.get("abstention_utility_delta_pct") or 0.0),
        -int(row.get("bad_count") or 0),
        int(row.get("protected_count") or 0),
        -float(row.get("bad_precision") or 0.0),
        _feature_priority(str(row.get("feature") or "")),
        str(row.get("feature") or ""),
        str(row.get("operator") or ""),
        float(row.get("threshold") or 0.0),
    )


def _validation_rank_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(row.get("abstention_utility_delta_pct") or 0.0),
        -int(row.get("bad_count") or 0),
        int(row.get("protected_count") or 0),
        -float(row.get("bad_precision") or 0.0),
        _feature_priority(str(row.get("feature") or "")),
        str(row.get("feature") or ""),
        str(row.get("operator") or ""),
        float(row.get("threshold") or 0.0),
    )


def _feature_priority(feature: str) -> int:
    return 0 if feature.startswith("flow_") else 1


def _outcome_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(_outcome(row) for row in rows).items()))


def _feature_summaries(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    features = _feature_values(rows)
    by_outcome: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        by_outcome.setdefault(_outcome(row), []).append(row)
    summaries = {}
    for outcome, outcome_rows in sorted(by_outcome.items()):
        feature_block = {}
        for feature in sorted(features):
            values = [_as_float(row.get(feature)) for row in outcome_rows]
            finite = [value for value in values if value is not None]
            if finite:
                feature_block[feature] = _numeric_summary(finite)
        summaries[outcome] = {
            "row_count": len(outcome_rows),
            "features": feature_block,
        }
    return summaries


def _rule_identity(row: Mapping[str, Any]) -> tuple[str, str, float]:
    return (
        str(row.get("feature") or ""),
        str(row.get("operator") or ""),
        float(row.get("threshold") or 0.0),
    )


def _rule_by_identity(results: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, float], dict[str, Any]]:
    return {_rule_identity(row): dict(row) for row in results}


def _passes_train_gate(
    row: Mapping[str, Any],
    *,
    min_train_selected: int,
    min_train_bad_precision: float,
    max_train_protected: int,
) -> bool:
    return (
        int(row.get("selected_count") or 0) >= int(min_train_selected)
        and int(row.get("bad_count") or 0) > 0
        and float(row.get("bad_precision") or 0.0) >= float(min_train_bad_precision)
        and int(row.get("protected_count") or 0) <= int(max_train_protected)
        and float(row.get("abstention_utility_delta_pct") or 0.0) > 0.0
    )


def _passes_eval_gate(
    row: Mapping[str, Any],
    *,
    min_eval_selected: int,
    max_eval_protected: int,
    require_positive_utility: bool,
) -> bool:
    utility = float(row.get("abstention_utility_delta_pct") or 0.0)
    return (
        int(row.get("selected_count") or 0) >= int(min_eval_selected)
        and int(row.get("bad_count") or 0) > 0
        and int(row.get("protected_count") or 0) <= int(max_eval_protected)
        and (utility > 0.0 if require_positive_utility else utility >= 0.0)
    )


def _material_metrics_unavailable() -> dict[str, str]:
    return {
        "net_profit_bnb": "not_computed_probe_only_requires_replay",
        "expected_utility": "utility_proxy_pct_only",
        "trade_count": "not_computed_probe_only_requires_replay",
        "win_rate": "not_computed_probe_only_requires_replay",
        "max_drawdown_pct": "not_computed_probe_only_requires_replay",
        "walk_forward": "not_computed_probe_only_requires_replay",
        "stress": "not_computed_probe_only_requires_replay",
        "paired_trade_delta": "not_computed_probe_only_requires_replay",
    }


def build_activation_survival_abstention_report(
    *,
    train_report: Mapping[str, Any],
    validation_report: Mapping[str, Any],
    final_report: Mapping[str, Any],
    train_source_name: str = "train",
    validation_source_name: str = "validation",
    final_source_name: str = "final",
    bad_classes: Iterable[str] = DEFAULT_BAD_CLASSES,
    protected_classes: Iterable[str] = DEFAULT_PROTECTED_CLASSES,
    min_train_selected: int = 3,
    min_train_bad_precision: float = 0.65,
    max_train_protected: int = 1,
    min_validation_selected: int = 1,
    max_validation_protected: int = 0,
    min_final_selected: int = 1,
    max_final_protected: int = 0,
    post_target_window_seconds: float = 60.0,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(min_train_bad_precision) <= 1.0:
        raise ValueError("min_train_bad_precision must be between 0 and 1")

    bad_set = {str(value) for value in bad_classes}
    protected_set = {str(value) for value in protected_classes}
    train_rows = rows_from_report(train_report, split="train", source_name=train_source_name)
    validation_rows = rows_from_report(validation_report, split="validation", source_name=validation_source_name)
    final_rows = rows_from_report(final_report, split="final", source_name=final_source_name)

    train_results = _rule_results(
        train_rows,
        bad_classes=bad_set,
        protected_classes=protected_set,
        post_target_window_seconds=post_target_window_seconds,
    )
    train_eligible = [
        row
        for row in train_results
        if _passes_train_gate(
            row,
            min_train_selected=min_train_selected,
            min_train_bad_precision=min_train_bad_precision,
            max_train_protected=max_train_protected,
        )
    ]
    train_eligible = sorted(train_eligible, key=_train_rank_key)

    evaluated_candidates = []
    for train_row in train_eligible:
        validation_row = _evaluate_rule(
            validation_rows,
            feature=str(train_row["feature"]),
            operator=str(train_row["operator"]),
            threshold=float(train_row["threshold"]),
            bad_classes=bad_set,
            protected_classes=protected_set,
            post_target_window_seconds=post_target_window_seconds,
        )
        final_row = _evaluate_rule(
            final_rows,
            feature=str(train_row["feature"]),
            operator=str(train_row["operator"]),
            threshold=float(train_row["threshold"]),
            bad_classes=bad_set,
            protected_classes=protected_set,
            post_target_window_seconds=post_target_window_seconds,
        )
        validation_passes = _passes_eval_gate(
            validation_row,
            min_eval_selected=min_validation_selected,
            max_eval_protected=max_validation_protected,
            require_positive_utility=True,
        )
        final_passes = _passes_eval_gate(
            final_row,
            min_eval_selected=min_final_selected,
            max_eval_protected=max_final_protected,
            require_positive_utility=False,
        )
        top_dependency_passes = (
            validation_row.get("abstention_utility_delta_without_top_benefit_pct") is None
            or float(validation_row.get("abstention_utility_delta_without_top_benefit_pct") or 0.0) >= 0.0
        ) and (
            final_row.get("abstention_utility_delta_without_top_benefit_pct") is None
            or float(final_row.get("abstention_utility_delta_without_top_benefit_pct") or 0.0) >= 0.0
        )
        evaluated_candidates.append(
            {
                "rule": {
                    "feature": train_row["feature"],
                    "operator": train_row["operator"],
                    "threshold": train_row["threshold"],
                },
                "train": train_row,
                "validation": validation_row,
                "final": final_row,
                "validation_passes": bool(validation_passes),
                "final_passes": bool(final_passes),
                "top_dependency_passes": bool(top_dependency_passes),
                "passes_research_alpha_proxy_gate": bool(validation_passes and final_passes and top_dependency_passes),
            }
        )
    evaluated_candidates.sort(key=lambda row: _validation_rank_key(row["validation"]))
    selected = next(
        (row for row in evaluated_candidates if row["passes_research_alpha_proxy_gate"]),
        evaluated_candidates[0] if evaluated_candidates else None,
    )

    if selected and selected["passes_research_alpha_proxy_gate"]:
        outcome = "Research Alpha"
        decision = "research_alpha_proxy_requires_replay"
    elif train_eligible:
        outcome = "Rejected"
        decision = "train_candidate_failed_validation_or_final_proxy_gate"
    else:
        outcome = "Rejected"
        decision = "no_train_abstention_candidate"

    return {
        "generated_at": (generated_at or dt.datetime.now(dt.timezone.utc)).isoformat(),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": "rules scan only explicit decision-time numeric fields",
        },
        "method": {
            "name": "activation_survival_abstention_probe",
            "hypothesis": (
                "Accepted candidates that never activate can be represented as no-event/censored "
                "time-to-target rows and selectively abstained using decision-time flow/model features."
            ),
            "falsification_rule": (
                "Reject unless a train-eligible rule improves validation abstention utility without "
                "rejecting activation-hit protected rows and does not lose utility on final."
            ),
        },
        "parameters": {
            "bad_classes": sorted(bad_set),
            "protected_classes": sorted(protected_set),
            "min_train_selected": int(min_train_selected),
            "min_train_bad_precision": float(min_train_bad_precision),
            "max_train_protected": int(max_train_protected),
            "min_validation_selected": int(min_validation_selected),
            "max_validation_protected": int(max_validation_protected),
            "min_final_selected": int(min_final_selected),
            "max_final_protected": int(max_final_protected),
            "post_target_window_seconds": float(post_target_window_seconds),
        },
        "inputs": {
            "train_source_name": train_source_name,
            "validation_source_name": validation_source_name,
            "final_source_name": final_source_name,
        },
        "candidate_counts": {
            "train_rows": len(train_rows),
            "validation_rows": len(validation_rows),
            "final_rows": len(final_rows),
            "train_outcome_counts": _outcome_counts(train_rows),
            "validation_outcome_counts": _outcome_counts(validation_rows),
            "final_outcome_counts": _outcome_counts(final_rows),
            "scanned_train_rules": len(train_results),
            "train_eligible_rules": len(train_eligible),
            "evaluated_candidates": len(evaluated_candidates),
        },
        "feature_summaries": {
            "train": _feature_summaries(train_rows),
            "validation": _feature_summaries(validation_rows),
            "final": _feature_summaries(final_rows),
        },
        "train_top_rules": sorted(train_results, key=_train_rank_key)[:100],
        "train_eligible_rules": train_eligible[:100],
        "evaluated_candidates": evaluated_candidates[:100],
        "selected_candidate": selected,
        "strict_metric_coverage": _material_metrics_unavailable(),
        "outcome_tier": outcome,
        "decision": decision,
    }
