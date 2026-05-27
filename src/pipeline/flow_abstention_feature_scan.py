from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_BAD_CLASSES = frozenset((
    "dead_flow_timeout",
    "replay_dead_flow_timeout",
    "flat_timeout",
    "stop_first",
    "stop_first_after_entry",
))
DEFAULT_PROTECTED_CLASSES = frozenset((
    "fast_profit",
    "fast_profit_then_collapse",
    "slow_runner",
    "profitable_exit",
))
CAUSAL_EXACT_FIELDS = frozenset((
    "age_seconds",
    "buy_probability",
    "entry_price_volatility",
    "entry_volume_30s",
    "pred_return",
    "price_volatility",
    "prob",
    "token_age_seconds",
    "volume_30s",
))
CAUSAL_FLOW_FIELDS = frozenset(
    (
        "flow_buyer_set_churn_10s_vs_prev50s",
        "flow_recent_seller_reentry_ratio_30s",
        "flow_buy_sell_overlap_ratio_60s",
    )
    + tuple(
        f"flow_{name}_{window}s"
        for window in (10, 30, 60)
        for name in (
            "buy_volume",
            "sell_volume",
            "total_volume",
            "event_count",
            "sell_pressure",
            "buy_sell_ratio",
            "signed_imbalance",
        )
    )
)
MAX_THRESHOLD_VALUES = 25


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


def _candidate_collection(report: Mapping[str, Any]) -> Sequence[Any]:
    rejected_paths = report.get("rejected_signal_paths")
    if isinstance(rejected_paths, Mapping):
        rows = rejected_paths.get("candidate_sample")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return rows

    for key in ("candidate_sample", "candidates", "trade_sample", "trades"):
        rows = report.get(key)
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return rows
    return []


def candidate_rows_from_report(report: Mapping[str, Any], *, source_name: str) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(_candidate_collection(report)):
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        item["source_report"] = str(source_name)
        item["source_row_index"] = int(index)
        rows.append(item)
    return rows


def _row_outcome(row: Mapping[str, Any]) -> str:
    for key in ("barrier_class", "failure_label", "classification"):
        value = row.get(key)
        if value:
            return str(value)
    policy = str(row.get("recommended_policy") or "").strip()
    return policy or "unknown"


def _is_causal_numeric_field(field: str) -> bool:
    if field in CAUSAL_EXACT_FIELDS:
        return True
    return field in CAUSAL_FLOW_FIELDS


def _feature_values(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[float]]:
    values: dict[str, list[float]] = {}
    for row in rows:
        for field, raw_value in row.items():
            if not _is_causal_numeric_field(str(field)):
                continue
            value = _as_float(raw_value)
            if value is None:
                continue
            values.setdefault(str(field), []).append(value)
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
        return {
            "count": 0,
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "max": None,
            "mean": None,
        }
    return {
        "count": len(finite),
        "min": finite[0],
        "p25": _quantile(finite, 0.25),
        "median": _quantile(finite, 0.50),
        "p75": _quantile(finite, 0.75),
        "max": finite[-1],
        "mean": sum(finite) / len(finite),
    }


def _class_feature_summaries(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_outcome: dict[str, list[Mapping[str, Any]]] = {}
    fields = sorted(_feature_values(rows))
    for row in rows:
        by_outcome.setdefault(_row_outcome(row), []).append(row)

    summaries: dict[str, Any] = {}
    for outcome, outcome_rows in sorted(by_outcome.items()):
        feature_summary = {}
        for field in fields:
            values = [_as_float(row.get(field)) for row in outcome_rows]
            finite_values = [value for value in values if value is not None]
            if finite_values:
                summary = _numeric_summary(finite_values)
                summary["coverage"] = len(finite_values) / len(outcome_rows)
                feature_summary[field] = summary
        summaries[outcome] = {
            "row_count": len(outcome_rows),
            "features": feature_summary,
        }
    return summaries


def _feature_contrast_rank_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -abs(float(row.get("robust_effect_size") or 0.0)),
        -int(row.get("bad_count") or 0),
        -int(row.get("protected_count") or 0),
        _feature_priority(str(row.get("feature") or "")),
        str(row.get("feature") or ""),
    )


def _bad_vs_protected_feature_contrast(
    rows: Sequence[Mapping[str, Any]],
    *,
    bad_classes: set[str],
    protected_classes: set[str],
) -> list[dict[str, Any]]:
    features = _feature_values(rows)
    contrasts = []
    for feature, all_values in sorted(features.items()):
        bad_values = [
            value
            for row in rows
            if _row_outcome(row) in bad_classes
            for value in [_as_float(row.get(feature))]
            if value is not None
        ]
        protected_values = [
            value
            for row in rows
            if _row_outcome(row) in protected_classes
            for value in [_as_float(row.get(feature))]
            if value is not None
        ]
        if not bad_values or not protected_values:
            continue
        all_summary = _numeric_summary(all_values)
        bad_summary = _numeric_summary(bad_values)
        protected_summary = _numeric_summary(protected_values)
        bad_median = bad_summary["median"]
        protected_median = protected_summary["median"]
        if bad_median is None or protected_median is None:
            continue
        spread = (all_summary["p75"] or 0.0) - (all_summary["p25"] or 0.0)
        if not math.isfinite(spread) or abs(spread) < 1e-12:
            spread = max(abs(max(all_values) - min(all_values)), 1e-12)
        delta = float(bad_median) - float(protected_median)
        contrasts.append({
            "feature": feature,
            "bad_count": len(bad_values),
            "protected_count": len(protected_values),
            "bad_median": float(bad_median),
            "protected_median": float(protected_median),
            "median_delta_bad_minus_protected": delta,
            "robust_effect_size": delta / spread,
            "bad_higher": delta > 0.0,
            "bad_summary": bad_summary,
            "protected_summary": protected_summary,
        })
    return sorted(contrasts, key=_feature_contrast_rank_key)


def _threshold_values(values: Sequence[float], *, max_threshold_values: int = MAX_THRESHOLD_VALUES) -> list[float]:
    unique = sorted({float(value) for value in values if math.isfinite(float(value))})
    if len(unique) <= max_threshold_values:
        return unique
    indexes = {
        round(index * (len(unique) - 1) / (max_threshold_values - 1))
        for index in range(max_threshold_values)
    }
    return [unique[index] for index in sorted(indexes)]


def _matches(row: Mapping[str, Any], *, feature: str, operator: str, threshold: float) -> bool:
    value = _as_float(row.get(feature))
    if value is None:
        return False
    if operator == "<=":
        return value <= threshold
    if operator == ">=":
        return value >= threshold
    raise ValueError(f"unsupported operator: {operator}")


def _feature_priority(feature: str) -> int:
    return 0 if feature.startswith("flow_") else 1


def _evaluate_rule(
    *,
    rows: Sequence[Mapping[str, Any]],
    feature: str,
    operator: str,
    threshold: float,
    bad_classes: set[str],
    protected_classes: set[str],
) -> dict[str, Any]:
    selected = [dict(row) for row in rows if _matches(row, feature=feature, operator=operator, threshold=threshold)]
    selected_outcomes = [_row_outcome(row) for row in selected]
    bad_count = sum(1 for outcome in selected_outcomes if outcome in bad_classes)
    protected_count = sum(1 for outcome in selected_outcomes if outcome in protected_classes)
    unknown_count = len(selected) - bad_count - protected_count
    selected_count = len(selected)
    selected_symbols = [str(row.get("symbol") or row.get("token") or "") for row in selected[:20]]
    return {
        "feature": feature,
        "operator": operator,
        "threshold": float(threshold),
        "selected_count": selected_count,
        "bad_count": bad_count,
        "protected_count": protected_count,
        "unknown_count": unknown_count,
        "bad_precision": (bad_count / selected_count) if selected_count else 0.0,
        "selected_outcome_counts": dict(sorted(Counter(selected_outcomes).items())),
        "selected_symbols": selected_symbols,
    }


def _rank_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -int(row.get("bad_count") or 0),
        int(row.get("protected_count") or 0),
        -float(row.get("bad_precision") or 0.0),
        _feature_priority(str(row.get("feature") or "")),
        str(row.get("feature") or ""),
        str(row.get("operator") or ""),
        float(row.get("threshold") or 0.0),
    )


def scan_feature_rules(
    rows: Sequence[Mapping[str, Any]],
    *,
    bad_classes: Iterable[str] = DEFAULT_BAD_CLASSES,
    protected_classes: Iterable[str] = DEFAULT_PROTECTED_CLASSES,
    min_selected: int = 3,
    min_bad_precision: float = 0.8,
    max_protected_selected: int = 0,
) -> dict[str, Any]:
    bad_set = {str(value) for value in bad_classes}
    protected_set = {str(value) for value in protected_classes}
    features = _feature_values(rows)
    rule_results = []
    for feature in sorted(features):
        for threshold in _threshold_values(features[feature]):
            for operator in ("<=", ">="):
                result = _evaluate_rule(
                    rows=rows,
                    feature=feature,
                    operator=operator,
                    threshold=threshold,
                    bad_classes=bad_set,
                    protected_classes=protected_set,
                )
                eligible = (
                    result["selected_count"] >= int(min_selected)
                    and result["bad_count"] > 0
                    and result["bad_precision"] >= float(min_bad_precision)
                    and result["protected_count"] <= int(max_protected_selected)
                )
                result["eligible"] = bool(eligible)
                rule_results.append(result)

    rule_results = sorted(rule_results, key=_rank_key)
    return {
        "scanned_features": sorted(features),
        "rule_results": rule_results,
        "eligible_rule_results": [row for row in rule_results if row["eligible"]],
    }


def build_scan_report(
    *,
    reports: Sequence[Mapping[str, Any]],
    source_names: Sequence[str] | None = None,
    bad_classes: Iterable[str] = DEFAULT_BAD_CLASSES,
    protected_classes: Iterable[str] = DEFAULT_PROTECTED_CLASSES,
    min_selected: int = 3,
    min_bad_precision: float = 0.8,
    max_protected_selected: int = 0,
) -> dict[str, Any]:
    bad_classes = list(bad_classes)
    protected_classes = list(protected_classes)
    names = list(source_names or [f"report_{index}" for index in range(len(reports))])
    if len(names) != len(reports):
        raise ValueError("source_names length must match reports length")
    rows: list[dict[str, Any]] = []
    for report, source_name in zip(reports, names):
        rows.extend(candidate_rows_from_report(report, source_name=source_name))

    outcome_counts = Counter(_row_outcome(row) for row in rows)
    bad_set = {str(value) for value in bad_classes}
    protected_set = {str(value) for value in protected_classes}
    scan = scan_feature_rules(
        rows,
        bad_classes=bad_set,
        protected_classes=protected_set,
        min_selected=min_selected,
        min_bad_precision=min_bad_precision,
        max_protected_selected=max_protected_selected,
    )
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
        },
        "parameters": {
            "bad_classes": sorted(str(value) for value in bad_classes),
            "protected_classes": sorted(str(value) for value in protected_classes),
            "min_selected": int(min_selected),
            "min_bad_precision": float(min_bad_precision),
            "max_protected_selected": int(max_protected_selected),
        },
        "candidate_counts": {
            "input_reports": len(reports),
            "candidate_rows": len(rows),
            "outcome_counts": dict(sorted(outcome_counts.items())),
        },
        "class_feature_summaries": _class_feature_summaries(rows),
        "bad_vs_protected_feature_contrast": _bad_vs_protected_feature_contrast(
            rows,
            bad_classes=bad_set,
            protected_classes=protected_set,
        )[:100],
        "feature_scan": {
            "scanned_features": scan["scanned_features"],
            "rule_results": scan["rule_results"][:200],
        },
        "eligible_rule_results": scan["eligible_rule_results"][:50],
        "decision": "probe_only_replay_required" if scan["eligible_rule_results"] else "no_abstention_rule_candidate",
    }
