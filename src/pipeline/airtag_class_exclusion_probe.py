from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


POSITIVE_POLICIES = {"quick_take_profit", "conditional_slow_hold"}
DECISION_TIME_FIELDS = {
    "prob",
    "pred_return",
    "entry_volume_30s",
    "volume_30s",
    "entry_price_volatility",
    "price_volatility",
    "age_seconds",
    "token_age_seconds",
}
OPERATORS = {">=", ">", "<=", "<", "==", "!="}
WILSON_Z_95 = 1.959963984540054


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _candidate_rows(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = report.get("candidates") or report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)]


def _reported_candidate_count(report: Mapping[str, Any], fallback: int) -> int:
    candidate_counts = report.get("candidate_counts") or {}
    if not isinstance(candidate_counts, Mapping):
        return int(fallback)
    try:
        return int(candidate_counts.get("per_token_candidates", fallback) or fallback)
    except (TypeError, ValueError):
        return int(fallback)


def _source_tagged_candidate_rows(report: Mapping[str, Any], source_name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _candidate_rows(report):
        tagged = dict(row)
        if tagged.get("entry_volume_30s") is None and "volume_30s" in tagged:
            tagged["entry_volume_30s"] = tagged.get("volume_30s")
        if tagged.get("volume_30s") is None and "entry_volume_30s" in tagged:
            tagged["volume_30s"] = tagged.get("entry_volume_30s")
        tagged["source_report"] = str(source_name)
        rows.append(tagged)
    return rows


def _condition(field: str, op: str, value: Any) -> dict[str, Any]:
    if field not in DECISION_TIME_FIELDS:
        raise ValueError(f"{field} is not decision-time")
    if op not in OPERATORS:
        raise ValueError(f"unsupported operator {op}")
    return {"field": field, "op": op, "value": value}


def _condition_matches(condition: Mapping[str, Any], row: Mapping[str, Any]) -> bool:
    field = condition.get("field")
    op = condition.get("op")
    if field not in DECISION_TIME_FIELDS:
        raise ValueError(f"{field} is not decision-time")
    if op not in OPERATORS:
        raise ValueError(f"unsupported operator {op}")
    if field not in row:
        return False

    left = row.get(str(field))
    right = condition.get("value")
    if op in {">=", ">", "<=", "<"}:
        parsed_left = _finite_float(left)
        parsed_right = _finite_float(right)
        if parsed_left is None or parsed_right is None:
            return False
        if op == ">=":
            return parsed_left >= parsed_right
        if op == ">":
            return parsed_left > parsed_right
        if op == "<=":
            return parsed_left <= parsed_right
        return parsed_left < parsed_right
    if op == "==":
        return left == right
    return left != right


def _matches_all(conditions: Sequence[Mapping[str, Any]], row: Mapping[str, Any]) -> bool:
    return all(_condition_matches(condition, row) for condition in conditions)


def _validate_conditions(conditions: Sequence[Mapping[str, Any]]) -> None:
    for condition in conditions:
        if not isinstance(condition, Mapping):
            raise ValueError("conditions must be mappings")
        field = condition.get("field")
        op = condition.get("op")
        if field not in DECISION_TIME_FIELDS:
            raise ValueError(f"{field} is not decision-time")
        if op not in OPERATORS:
            raise ValueError(f"unsupported operator {op}")


def _symbol(row: Mapping[str, Any]) -> str:
    symbol = row.get("symbol") or row.get("token") or ""
    return str(symbol)


def _counts(rows: Iterable[Mapping[str, Any]], field: str) -> dict[str, int]:
    counter = Counter(str(row.get(field) or "unknown") for row in rows)
    return dict(sorted(counter.items()))


def _wilson_interval(successes: int, total: int, z: float = WILSON_Z_95) -> dict[str, Any]:
    if total <= 0:
        return {"low": None, "high": None, "z": z}
    p_hat = successes / total
    z2 = z * z
    denominator = 1.0 + z2 / total
    center = (p_hat + z2 / (2.0 * total)) / denominator
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * total)) / total) / denominator
    return {
        "low": max(0.0, center - margin),
        "high": min(1.0, center + margin),
        "z": z,
    }


def _candidate_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "token": row.get("token"),
        "source_report": row.get("source_report"),
        "prob": _finite_float(row.get("prob")),
        "pred_return": _finite_float(row.get("pred_return")),
        "entry_volume_30s": _finite_float(row.get("entry_volume_30s")),
        "entry_price_volatility": _finite_float(row.get("entry_price_volatility")),
        "age_seconds": _finite_float(row.get("age_seconds") or row.get("token_age_seconds")),
        "recommended_policy": row.get("recommended_policy"),
        "barrier_class": row.get("barrier_class"),
        "first_barrier": row.get("first_barrier"),
        "time_to_plus_25_seconds": _finite_float(row.get("time_to_plus_25_seconds")),
        "time_to_minus_18_seconds": _finite_float(row.get("time_to_minus_18_seconds")),
        "mfe_pct": _finite_float(row.get("mfe_pct")),
        "mae_pct": _finite_float(row.get("mae_pct")),
    }


def evaluate_stratum(
    *,
    name: str,
    conditions: Sequence[Mapping[str, Any]],
    candidates: Iterable[Mapping[str, Any]],
    max_candidate_sample: int = 50,
) -> dict[str, Any]:
    _validate_conditions(conditions)
    selected = [row for row in candidates if _matches_all(conditions, row)]
    positives = [row for row in selected if row.get("recommended_policy") in POSITIVE_POLICIES]
    negatives = [row for row in selected if row.get("recommended_policy") not in POSITIVE_POLICIES]
    selected_count = len(selected)
    positive_count = len(positives)
    precision = positive_count / selected_count if selected_count else 0.0

    return {
        "stratum": name,
        "conditions": list(conditions),
        "selected_count": selected_count,
        "positive_count": positive_count,
        "negative_count": len(negatives),
        "precision": precision,
        "precision_wilson_95": _wilson_interval(positive_count, selected_count),
        "class_counts": _counts(selected, "barrier_class"),
        "policy_counts": _counts(selected, "recommended_policy"),
        "selected_symbols": [_symbol(row) for row in selected[:25]],
        "positive_symbols": [_symbol(row) for row in positives[:25]],
        "negative_symbols": [_symbol(row) for row in negatives[:25]],
        "candidate_sample": [_candidate_summary(row) for row in selected[:max_candidate_sample]],
    }


def _strata_definitions(
    *,
    min_prob: float,
    min_pred_return: float,
    min_volume_floor: float,
    high_volume_cut: float,
) -> list[tuple[str, tuple[Mapping[str, Any], ...]]]:
    high_prob = (_condition("prob", ">=", min_prob),)
    high_prob_pred = (
        _condition("prob", ">=", min_prob),
        _condition("pred_return", ">=", min_pred_return),
    )
    high_volume = (_condition("entry_volume_30s", ">=", high_volume_cut),)
    floor_to_high_volume = (
        _condition("entry_volume_30s", ">=", min_volume_floor),
        _condition("entry_volume_30s", "<", high_volume_cut),
    )
    return [
        ("high_prob_positive_pred_all", high_prob_pred),
        ("high_prob_positive_pred_volume_gte_high_cut", high_prob_pred + high_volume),
        (
            "high_prob_positive_pred_volume_floor_to_high_cut",
            high_prob_pred + floor_to_high_volume,
        ),
        ("high_prob_volume_gte_high_cut", high_prob + high_volume),
        ("high_prob_volume_floor_to_high_cut", high_prob + floor_to_high_volume),
    ]


def _boundary_sweep(
    *,
    candidates: list[Mapping[str, Any]],
    min_prob: float,
    min_pred_return: float,
    volume_cuts: Sequence[float],
    max_candidate_sample: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = (
        _condition("prob", ">=", min_prob),
        _condition("pred_return", ">=", min_pred_return),
    )
    for cut in volume_cuts:
        rows.append(
            evaluate_stratum(
                name=f"high_prob_positive_pred_volume_gte_{cut:g}",
                conditions=base + (_condition("entry_volume_30s", ">=", cut),),
                candidates=candidates,
                max_candidate_sample=max_candidate_sample,
            )
        )
        rows.append(
            evaluate_stratum(
                name=f"high_prob_positive_pred_volume_lt_{cut:g}",
                conditions=base + (_condition("entry_volume_30s", "<", cut),),
                candidates=candidates,
                max_candidate_sample=max_candidate_sample,
            )
        )
    return rows


def _validate_numeric_parameter(name: str, value: float) -> float:
    parsed = _finite_float(value)
    if parsed is None:
        raise ValueError(f"{name} must be finite")
    return parsed


def _validate_volume_cuts(volume_cuts: Sequence[float]) -> tuple[float, ...]:
    if not volume_cuts:
        raise ValueError("volume_cuts must be non-empty")
    parsed = tuple(_validate_numeric_parameter("volume_cuts", cut) for cut in volume_cuts)
    return tuple(sorted(dict.fromkeys(parsed)))


def build_exclusion_probe_report(
    *,
    time_to_barrier_reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None = None,
    min_prob: float = 0.985,
    min_pred_return: float = 5.0,
    min_volume_floor: float = 0.75,
    high_volume_cut: float = 1.5,
    volume_cuts: Sequence[float] = (1.25, 1.5, 1.75, 2.0),
    max_candidate_sample: int = 50,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    reports = list(time_to_barrier_reports)
    names = list(source_names or [f"report_{index}" for index in range(len(reports))])
    if len(reports) != len(names):
        raise ValueError("source_names length must match time_to_barrier_reports")
    if not reports:
        raise ValueError("at least one time-to-barrier report is required")

    min_prob = _validate_numeric_parameter("min_prob", min_prob)
    min_pred_return = _validate_numeric_parameter("min_pred_return", min_pred_return)
    min_volume_floor = _validate_numeric_parameter("min_volume_floor", min_volume_floor)
    high_volume_cut = _validate_numeric_parameter("high_volume_cut", high_volume_cut)
    volume_cuts = _validate_volume_cuts(volume_cuts)
    if max_candidate_sample < 0:
        raise ValueError("max_candidate_sample must be non-negative")

    candidates: list[Mapping[str, Any]] = []
    reported_candidates = 0
    for report, source_name in zip(reports, names):
        rows = _source_tagged_candidate_rows(report, source_name)
        candidates.extend(rows)
        reported_candidates += _reported_candidate_count(report, len(rows))

    strata = [
        evaluate_stratum(
            name=name,
            conditions=conditions,
            candidates=candidates,
            max_candidate_sample=max_candidate_sample,
        )
        for name, conditions in _strata_definitions(
            min_prob=min_prob,
            min_pred_return=min_pred_return,
            min_volume_floor=min_volume_floor,
            high_volume_cut=high_volume_cut,
        )
    ]
    high_pred_high_volume = next(
        row for row in strata if row["stratum"] == "high_prob_positive_pred_volume_gte_high_cut"
    )
    false_positive_conditions = (
        _condition("prob", ">=", min_prob),
        _condition("pred_return", ">=", min_pred_return),
        _condition("entry_volume_30s", ">=", high_volume_cut),
    )
    # This watchpoint reports ex-post labels; selectors above stay decision-time only.
    false_positives = [
        row
        for row in candidates
        if (
            _matches_all(false_positive_conditions, row)
            and (
                row.get("recommended_policy") not in POSITIVE_POLICIES
                or row.get("barrier_class") == "stop_first"
            )
        )
    ]

    return {
        "generated_at": (
            generated_at
            or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None)
        ).isoformat(sep=" "),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "airtag_class_exclusion_probe_for_replay_experiment_design",
        },
        "parameters": {
            "min_prob": min_prob,
            "min_pred_return": min_pred_return,
            "min_volume_floor": min_volume_floor,
            "high_volume_cut": high_volume_cut,
            "volume_cuts": list(volume_cuts),
            "positive_policies": sorted(POSITIVE_POLICIES),
            "max_candidate_sample": max_candidate_sample,
        },
        "schema_normalization": {
            "canonical_volume_field": "entry_volume_30s",
            "volume_30s_filled_from_entry_volume_30s_when_missing": True,
            "entry_volume_30s_filled_from_volume_30s_when_missing": True,
        },
        "candidate_counts": {
            "input_reports": len(reports),
            "input_candidates": len(candidates),
            "input_reported_candidates": reported_candidates,
            "sample_limited": reported_candidates > len(candidates),
            "unscored_reported_candidates": max(0, reported_candidates - len(candidates)),
            "positive_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") in POSITIVE_POLICIES
            ),
            "negative_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") not in POSITIVE_POLICIES
            ),
        },
        "class_counts": _counts(candidates, "barrier_class"),
        "policy_counts": _counts(candidates, "recommended_policy"),
        "strata": strata,
        "volume_boundary_sweep": _boundary_sweep(
            candidates=candidates,
            min_prob=min_prob,
            min_pred_return=min_pred_return,
            volume_cuts=volume_cuts,
            max_candidate_sample=max_candidate_sample,
        ),
        "airtag_class_watchpoint": {
            "conditions": list(false_positive_conditions),
            "false_positive_count": len(false_positives),
            "false_positive_symbols": [_symbol(row) for row in false_positives[:25]],
            "false_positive_sample": [
                _candidate_summary(row) for row in false_positives[:max_candidate_sample]
            ],
            "high_prob_positive_pred_high_volume_selected_count": high_pred_high_volume[
                "selected_count"
            ],
            "high_prob_positive_pred_high_volume_negative_count": high_pred_high_volume[
                "negative_count"
            ],
        },
        "decision": "probe_only_small_sample_airtag_class_watchpoint",
    }


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
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
