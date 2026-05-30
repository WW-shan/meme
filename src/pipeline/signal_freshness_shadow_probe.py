from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from src.pipeline import reentry_probe, time_to_barrier_probe


NUMERIC_POLICY_FIELDS = (
    "lifecycle_status_chain_lag_seconds",
    "lifecycle_status_staleness_seconds",
)
BOOLEAN_POLICY_FIELDS = (
    "lifecycle_status_fast_status_eligible",
    "lifecycle_status_has_chain_update",
    "lifecycle_status_has_local_update",
)
FRESHNESS_FIELDS = NUMERIC_POLICY_FIELDS + BOOLEAN_POLICY_FIELDS + (
    "lifecycle_status_fast_status_enabled",
    "buy_fast_status_max_staleness_seconds",
    "buy_fast_status_max_chain_lag_seconds",
)
OPPORTUNITY_CLASSES = {"fast_profit", "fast_profit_then_collapse", "slow_runner"}
CORRECT_SKIP_CLASSES = {"flat_timeout", "stop_first"}
MAX_THRESHOLD_VALUES = 40


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    rows: list[dict[str, Any]] = []
    with resolved.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


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


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _optional_time(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return reentry_probe.parse_time(value)
    except (TypeError, ValueError):
        return None


def _in_window(row: Mapping[str, Any], *, since: Any = None, until: Any = None) -> bool:
    row_time = _optional_time(row.get("time") or row.get("timestamp"))
    if row_time is None:
        return False
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    if since_time is not None and row_time < since_time:
        return False
    if until_time is not None and row_time > until_time:
        return False
    return True


def iter_signal_decisions(
    rows: Iterable[Mapping[str, Any]],
    *,
    since: Any = None,
    until: Any = None,
    decisions: Sequence[str] = ("queued", "rejected"),
) -> list[dict[str, Any]]:
    allowed_decisions = {str(decision).strip().lower() for decision in decisions}
    parsed: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("action") or "").upper() != "SIGNAL_DECISION":
            continue
        decision = str(row.get("decision") or "").strip().lower()
        if decision not in allowed_decisions:
            continue
        token = reentry_probe.normalize_token(row.get("token") or row.get("token_address"))
        if not token:
            continue
        if not _in_window(row, since=since, until=until):
            continue
        copied = dict(row)
        copied["token"] = token
        copied["decision"] = decision
        copied["time"] = reentry_probe.parse_time(row.get("time") or row.get("timestamp"))
        parsed.append(copied)
    return parsed


def _signal_rank_key(row: Mapping[str, Any]) -> tuple[float, float, dt.datetime]:
    return (
        reentry_probe.safe_float(row.get("pred_return"), default=-1e9),
        reentry_probe.safe_float(row.get("prob"), default=-1e9),
        reentry_probe.parse_time(row.get("time")),
    )


def _dedupe_by_token(signals: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    best_by_token: dict[str, dict[str, Any]] = {}
    for signal in signals:
        token = reentry_probe.normalize_token(signal.get("token"))
        if not token:
            continue
        current = best_by_token.get(token)
        candidate = dict(signal)
        if current is None or _signal_rank_key(candidate) > _signal_rank_key(current):
            best_by_token[token] = candidate
    return sorted(best_by_token.values(), key=lambda row: reentry_probe.parse_time(row.get("time")))


def _freshness_fields(signal: Mapping[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for field in NUMERIC_POLICY_FIELDS:
        fields[field] = _as_float(signal.get(field))
    for field in BOOLEAN_POLICY_FIELDS:
        fields[field] = _as_bool(signal.get(field))
    fields["lifecycle_status_fast_status_enabled"] = _as_bool(signal.get("lifecycle_status_fast_status_enabled"))
    fields["buy_fast_status_max_staleness_seconds"] = _as_float(signal.get("buy_fast_status_max_staleness_seconds"))
    fields["buy_fast_status_max_chain_lag_seconds"] = _as_float(signal.get("buy_fast_status_max_chain_lag_seconds"))
    fields["freshness_fields_present"] = any(fields.get(field) is not None for field in NUMERIC_POLICY_FIELDS + BOOLEAN_POLICY_FIELDS)
    return fields


def _score_candidates(
    signals: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, dict[str, Any]],
    *,
    horizon_seconds: float,
    quick_profit_seconds: float,
) -> list[dict[str, Any]]:
    normalized_lifecycles = {
        reentry_probe.normalize_token(token): lifecycle
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    candidates: list[dict[str, Any]] = []
    for signal in _dedupe_by_token(signals):
        token = reentry_probe.normalize_token(signal.get("token"))
        lifecycle = normalized_lifecycles.get(token)
        scored = time_to_barrier_probe.score_signal_time_to_barrier(
            dict(signal),
            reentry_probe.price_path_for_token(normalized_lifecycles, token),
            lifecycle=lifecycle,
            horizon_seconds=horizon_seconds,
            quick_profit_seconds=quick_profit_seconds,
        )
        scored.update(_freshness_fields(signal))
        scored["decision"] = signal.get("decision")
        scored["freshness_shadow_candidate"] = bool(scored.get("freshness_fields_present"))
        candidates.append(scored)
    return candidates


def _candidate_value_thresholds(candidates: Iterable[Mapping[str, Any]], field: str) -> list[float]:
    values = sorted({float(value) for row in candidates if (value := _as_float(row.get(field))) is not None})
    if len(values) <= MAX_THRESHOLD_VALUES:
        return values
    step = max(1, len(values) // MAX_THRESHOLD_VALUES)
    sampled = values[::step]
    if values[-1] not in sampled:
        sampled.append(values[-1])
    return sampled[:MAX_THRESHOLD_VALUES]


def _rule_label(rule: Mapping[str, Any]) -> str:
    if rule.get("type") == "numeric_gte":
        return f"{rule.get('field')} >= {float(rule.get('threshold')):.6g}"
    if rule.get("type") == "bool_eq":
        return f"{rule.get('field')} == {str(rule.get('value')).lower()}"
    return str(rule)


def _rule_matches(rule: Mapping[str, Any], row: Mapping[str, Any]) -> bool:
    if rule.get("type") == "numeric_gte":
        value = _as_float(row.get(str(rule.get("field"))))
        return value is not None and value >= float(rule.get("threshold"))
    if rule.get("type") == "bool_eq":
        value = _as_bool(row.get(str(rule.get("field"))))
        return value is not None and value is bool(rule.get("value"))
    return False


def _rules(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for field in NUMERIC_POLICY_FIELDS:
        for threshold in _candidate_value_thresholds(candidates, field):
            rules.append({"type": "numeric_gte", "field": field, "threshold": threshold, "label": f"{field} >= {threshold:.6g}"})
    for field in BOOLEAN_POLICY_FIELDS:
        observed = {_as_bool(row.get(field)) for row in candidates}
        for value in sorted(item for item in observed if item is not None):
            rules.append({"type": "bool_eq", "field": field, "value": value, "label": f"{field} == {str(value).lower()}"})
    return rules


def _evaluate_rule(rule: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]], *, opportunity_penalty: float) -> dict[str, Any]:
    selected = [dict(row) for row in candidates if _rule_matches(rule, row)]
    class_counts = Counter(str(row.get("barrier_class") or "") for row in selected)
    opportunity_count = sum(class_counts.get(label, 0) for label in OPPORTUNITY_CLASSES)
    correct_skip_count = sum(class_counts.get(label, 0) for label in CORRECT_SKIP_CLASSES)
    selected_count = len(selected)
    utility = float(correct_skip_count) - float(opportunity_penalty) * float(opportunity_count)
    return {
        "rule": dict(rule),
        "label": str(rule.get("label") or _rule_label(rule)),
        "selected_count": selected_count,
        "selected_class_counts": dict(sorted(class_counts.items())),
        "correct_skip_count": int(correct_skip_count),
        "opportunity_miss_count": int(opportunity_count),
        "correct_skip_precision": (float(correct_skip_count) / selected_count) if selected_count else 0.0,
        "shadow_abstention_utility": utility,
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected[:25]],
    }


def _feature_summary(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for field in NUMERIC_POLICY_FIELDS:
        values = [float(value) for row in candidates if (value := _as_float(row.get(field))) is not None]
        if values:
            ordered = sorted(values)
            summary[field] = {
                "count": len(ordered),
                "min": ordered[0],
                "median": ordered[len(ordered) // 2],
                "max": ordered[-1],
                "mean": sum(ordered) / len(ordered),
            }
        else:
            summary[field] = {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    for field in BOOLEAN_POLICY_FIELDS:
        summary[field] = dict(sorted(Counter(str(row.get(field)) for row in candidates).items()))
    return summary


def _candidate_time(row: Mapping[str, Any]) -> dt.datetime:
    return reentry_probe.parse_time(row.get("signal_time") or row.get("time"))


def _split_candidates(
    candidates: Sequence[Mapping[str, Any]],
    *,
    train_fraction: float,
    validation_fraction: float,
) -> dict[str, list[dict[str, Any]]]:
    ordered = sorted((dict(row) for row in candidates), key=_candidate_time)
    total = len(ordered)
    train_end = int(total * float(train_fraction))
    validation_end = int(total * (float(train_fraction) + float(validation_fraction)))
    train_end = min(max(train_end, 0), total)
    validation_end = min(max(validation_end, train_end), total)
    return {
        "train": ordered[:train_end],
        "validation": ordered[train_end:validation_end],
        "final": ordered[validation_end:],
    }


def _split_counts(splits: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for name, rows in splits.items():
        counts[name] = {
            "candidate_count": len(rows),
            "class_counts": dict(sorted(Counter(str(row.get("barrier_class") or "") for row in rows).items())),
            "decision_counts": dict(sorted(Counter(str(row.get("decision") or "") for row in rows).items())),
        }
    return counts


def _passes_split_gate(
    evaluation: Mapping[str, Any],
    *,
    min_selected: int,
    min_correct_skip_precision: float,
    max_opportunity_misses: int,
) -> bool:
    return (
        int(evaluation.get("selected_count") or 0) >= int(min_selected)
        and float(evaluation.get("correct_skip_precision") or 0.0) >= float(min_correct_skip_precision)
        and int(evaluation.get("opportunity_miss_count") or 0) <= int(max_opportunity_misses)
        and float(evaluation.get("shadow_abstention_utility") or 0.0) > 0.0
    )


def _evaluate_rule_splits(
    rule: Mapping[str, Any],
    splits: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    opportunity_penalty: float,
) -> dict[str, Any]:
    result = {
        "rule": dict(rule),
        "label": str(rule.get("label") or _rule_label(rule)),
    }
    for split_name in ("train", "validation", "final"):
        result[split_name] = _evaluate_rule(
            rule,
            splits.get(split_name, []),
            opportunity_penalty=float(opportunity_penalty),
        )
    result["all"] = _evaluate_rule(
        rule,
        [
            row
            for split_name in ("train", "validation", "final")
            for row in splits.get(split_name, [])
        ],
        opportunity_penalty=float(opportunity_penalty),
    )
    return result


def build_signal_freshness_split_report(
    *,
    signal_rows: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, dict[str, Any]],
    since: Any = None,
    until: Any = None,
    decisions: Sequence[str] = ("queued", "rejected"),
    horizon_seconds: float = 600.0,
    quick_profit_seconds: float = 120.0,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    min_candidates: int = 30,
    min_split_candidates: int = 5,
    min_selected: int = 5,
    min_split_selected: int = 1,
    min_correct_skip_precision: float = 0.75,
    max_opportunity_misses: int = 0,
    opportunity_penalty: float = 2.0,
    max_candidate_sample: int = 100,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    signals = iter_signal_decisions(signal_rows, since=since, until=until, decisions=decisions)
    candidates = _score_candidates(
        signals,
        lifecycles,
        horizon_seconds=float(horizon_seconds),
        quick_profit_seconds=float(quick_profit_seconds),
    )
    freshness_candidates = [row for row in candidates if bool(row.get("freshness_fields_present"))]
    class_counts = Counter(str(row.get("barrier_class") or "") for row in freshness_candidates)
    decision_counts = Counter(str(row.get("decision") or "") for row in freshness_candidates)
    missing_path_count = int(class_counts.get("missing_path", 0))
    path_evaluable_count = max(0, len(freshness_candidates) - missing_path_count)
    splits = _split_candidates(
        freshness_candidates,
        train_fraction=float(train_fraction),
        validation_fraction=float(validation_fraction),
    )
    split_candidate_counts = {name: len(rows) for name, rows in splits.items()}

    evaluated = [
        _evaluate_rule_splits(rule, splits, opportunity_penalty=float(opportunity_penalty))
        for rule in _rules(splits.get("train", []))
    ]
    evaluated.sort(
        key=lambda row: (
            -float((row.get("train") or {}).get("shadow_abstention_utility") or 0.0),
            -float((row.get("train") or {}).get("correct_skip_precision") or 0.0),
            -int((row.get("train") or {}).get("selected_count") or 0),
            -float((row.get("validation") or {}).get("shadow_abstention_utility") or 0.0),
            -float((row.get("final") or {}).get("shadow_abstention_utility") or 0.0),
            str(row.get("label") or ""),
        )
    )
    train_eligible = [
        row for row in evaluated
        if _passes_split_gate(
            row.get("train") or {},
            min_selected=int(min_selected),
            min_correct_skip_precision=float(min_correct_skip_precision),
            max_opportunity_misses=int(max_opportunity_misses),
        )
    ]
    stable = [
        row for row in train_eligible
        if _passes_split_gate(
            row.get("validation") or {},
            min_selected=int(min_split_selected),
            min_correct_skip_precision=float(min_correct_skip_precision),
            max_opportunity_misses=int(max_opportunity_misses),
        )
        and _passes_split_gate(
            row.get("final") or {},
            min_selected=int(min_split_selected),
            min_correct_skip_precision=float(min_correct_skip_precision),
            max_opportunity_misses=int(max_opportunity_misses),
        )
    ]
    selected = stable[0] if stable else (train_eligible[0] if train_eligible else (evaluated[0] if evaluated else None))

    if len(freshness_candidates) < int(min_candidates):
        outcome_tier = "Rejected"
        decision = "insufficient_signal_freshness_split_support"
    elif path_evaluable_count < int(min_candidates):
        outcome_tier = "Rejected"
        decision = "insufficient_signal_freshness_split_path_coverage"
    elif any(count < int(min_split_candidates) for count in split_candidate_counts.values()):
        outcome_tier = "Rejected"
        decision = "insufficient_signal_freshness_split_holdout_support"
    elif stable:
        outcome_tier = "Research Alpha"
        decision = "research_alpha_signal_freshness_split_stable"
    elif train_eligible:
        outcome_tier = "Rejected"
        decision = "signal_freshness_train_rule_failed_holdout"
    else:
        outcome_tier = "Rejected"
        decision = "no_signal_freshness_train_rule_passed"

    sample_limit = int(max_candidate_sample)
    sample = freshness_candidates if sample_limit == 0 else freshness_candidates[: max(0, sample_limit)]
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc),
        "outcome_tier": outcome_tier,
        "decision": decision,
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "uses_post_signal_order_fields_as_policy": False,
            "split_stability_evidence": True,
        },
        "parameters": {
            "since": _optional_time(since),
            "until": _optional_time(until),
            "decisions": list(decisions),
            "horizon_seconds": float(horizon_seconds),
            "quick_profit_seconds": float(quick_profit_seconds),
            "train_fraction": float(train_fraction),
            "validation_fraction": float(validation_fraction),
            "min_candidates": int(min_candidates),
            "min_split_candidates": int(min_split_candidates),
            "min_selected": int(min_selected),
            "min_split_selected": int(min_split_selected),
            "min_correct_skip_precision": float(min_correct_skip_precision),
            "max_opportunity_misses": int(max_opportunity_misses),
            "opportunity_penalty": float(opportunity_penalty),
            "max_candidate_sample": sample_limit,
        },
        "candidate_counts": {
            "signal_decisions": len(signals),
            "per_token_candidates": len(candidates),
            "freshness_candidate_count": len(freshness_candidates),
            "path_evaluable_candidate_count": path_evaluable_count,
            "missing_path_count": missing_path_count,
            "candidate_sample_count": len(sample),
            "unemitted_candidate_count": max(0, len(freshness_candidates) - len(sample)),
        },
        "split_counts": _split_counts(splits),
        "class_counts": dict(sorted(class_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "feature_summary": _feature_summary(freshness_candidates),
        "selected_rule": selected,
        "stable_rule_count": len(stable),
        "train_eligible_rule_count": len(train_eligible),
        "evaluated_rule_count": len(evaluated),
        "top_rules": evaluated[:20],
        "candidate_sample": sample,
    }


def build_signal_freshness_shadow_report(
    *,
    signal_rows: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, dict[str, Any]],
    since: Any = None,
    until: Any = None,
    decisions: Sequence[str] = ("queued", "rejected"),
    horizon_seconds: float = 600.0,
    quick_profit_seconds: float = 120.0,
    min_candidates: int = 20,
    min_selected: int = 5,
    min_correct_skip_precision: float = 0.75,
    max_opportunity_misses: int = 0,
    opportunity_penalty: float = 2.0,
    max_candidate_sample: int = 100,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    signals = iter_signal_decisions(signal_rows, since=since, until=until, decisions=decisions)
    candidates = _score_candidates(
        signals,
        lifecycles,
        horizon_seconds=float(horizon_seconds),
        quick_profit_seconds=float(quick_profit_seconds),
    )
    freshness_candidates = [row for row in candidates if bool(row.get("freshness_fields_present"))]
    evaluated = [
        _evaluate_rule(rule, freshness_candidates, opportunity_penalty=float(opportunity_penalty))
        for rule in _rules(freshness_candidates)
    ]
    evaluated.sort(
        key=lambda row: (
            -float(row.get("shadow_abstention_utility") or 0.0),
            -float(row.get("correct_skip_precision") or 0.0),
            -int(row.get("selected_count") or 0),
            str(row.get("label") or ""),
        )
    )
    eligible = [
        row for row in evaluated
        if int(row.get("selected_count") or 0) >= int(min_selected)
        and float(row.get("correct_skip_precision") or 0.0) >= float(min_correct_skip_precision)
        and int(row.get("opportunity_miss_count") or 0) <= int(max_opportunity_misses)
        and float(row.get("shadow_abstention_utility") or 0.0) > 0.0
    ]
    selected = eligible[0] if eligible else (evaluated[0] if evaluated else None)
    class_counts = Counter(str(row.get("barrier_class") or "") for row in freshness_candidates)
    decision_counts = Counter(str(row.get("decision") or "") for row in freshness_candidates)
    missing_path_count = int(class_counts.get("missing_path", 0))
    path_evaluable_count = max(0, len(freshness_candidates) - missing_path_count)
    if len(freshness_candidates) < int(min_candidates):
        outcome_tier = "Rejected"
        decision = "insufficient_signal_freshness_shadow_support"
    elif path_evaluable_count < int(min_candidates):
        outcome_tier = "Rejected"
        decision = "insufficient_signal_freshness_path_coverage"
    elif eligible:
        outcome_tier = "Research Alpha"
        decision = "research_alpha_signal_freshness_shadow_candidate"
    else:
        outcome_tier = "Rejected"
        decision = "no_signal_freshness_shadow_rule_passed"
    sample_limit = int(max_candidate_sample)
    sample = freshness_candidates if sample_limit == 0 else freshness_candidates[: max(0, sample_limit)]
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc),
        "outcome_tier": outcome_tier,
        "decision": decision,
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "uses_post_signal_order_fields_as_policy": False,
        },
        "parameters": {
            "since": _optional_time(since),
            "until": _optional_time(until),
            "decisions": list(decisions),
            "horizon_seconds": float(horizon_seconds),
            "quick_profit_seconds": float(quick_profit_seconds),
            "min_candidates": int(min_candidates),
            "min_selected": int(min_selected),
            "min_correct_skip_precision": float(min_correct_skip_precision),
            "max_opportunity_misses": int(max_opportunity_misses),
            "opportunity_penalty": float(opportunity_penalty),
            "max_candidate_sample": sample_limit,
        },
        "candidate_counts": {
            "signal_decisions": len(signals),
            "per_token_candidates": len(candidates),
            "freshness_candidate_count": len(freshness_candidates),
            "path_evaluable_candidate_count": path_evaluable_count,
            "missing_path_count": missing_path_count,
            "candidate_sample_count": len(sample),
            "unemitted_candidate_count": max(0, len(freshness_candidates) - len(sample)),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "feature_summary": _feature_summary(freshness_candidates),
        "selected_rule": selected,
        "eligible_rule_count": len(eligible),
        "evaluated_rule_count": len(evaluated),
        "top_rules": evaluated[:20],
        "candidate_sample": sample,
    }


def to_markdown_text(report: Mapping[str, Any]) -> str:
    selected = report.get("selected_rule") or {}
    split_mode = bool((report.get("probe_contract") or {}).get("split_stability_evidence"))
    lines = [
        "# Signal Freshness Split Probe" if split_mode else "# Signal Freshness Shadow Probe",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only shadow evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.",
        "",
        "## Decision",
        "",
        f"- Outcome tier: `{report.get('outcome_tier')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Selected rule: `{selected.get('label') if isinstance(selected, Mapping) else None}`",
        (
            f"- Stable rules: `{report.get('stable_rule_count')}`; "
            f"train-eligible rules: `{report.get('train_eligible_rule_count')}` / `{report.get('evaluated_rule_count')}`"
            if split_mode
            else f"- Eligible rules: `{report.get('eligible_rule_count')}` / `{report.get('evaluated_rule_count')}`"
        ),
        "",
        "## Coverage",
        "",
        f"- Candidate counts: `{json.dumps(_json_sanitize(report.get('candidate_counts') or {}), ensure_ascii=False, sort_keys=True)}`",
        f"- Decisions: `{json.dumps(_json_sanitize(report.get('decision_counts') or {}), ensure_ascii=False, sort_keys=True)}`",
        f"- Barrier classes: `{json.dumps(_json_sanitize(report.get('class_counts') or {}), ensure_ascii=False, sort_keys=True)}`",
        "",
    ]
    if split_mode:
        lines.extend([
            "## Split Counts",
            "",
            "```json",
            json.dumps(_json_sanitize(report.get("split_counts") or {}), ensure_ascii=False, sort_keys=True, indent=2),
            "```",
            "",
        ])
    lines.extend([
        "## Selected Rule",
        "",
        "```json",
        json.dumps(_json_sanitize(selected), ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Top Rules",
        "",
        "```json",
        json.dumps(_json_sanitize((report.get("top_rules") or [])[:10]), ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Interpretation",
        "",
    ])
    if report.get("decision") == "insufficient_signal_freshness_shadow_support":
        lines.append("Freshness fields are landing, but the post-restart signal/path sample is still too small for a model gate.")
    elif report.get("decision") == "insufficient_signal_freshness_path_coverage":
        lines.append("Freshness fields are landing, but too many candidates lack a post-signal lifecycle path for outcome attribution.")
    elif report.get("decision") in {
        "insufficient_signal_freshness_split_support",
        "insufficient_signal_freshness_split_holdout_support",
    }:
        lines.append("Freshness fields are landing, but the chronological split support is still too small for a stable shadow rule.")
    elif report.get("decision") == "insufficient_signal_freshness_split_path_coverage":
        lines.append("Freshness fields are landing, but too many split candidates lack a post-signal lifecycle path for outcome attribution.")
    elif report.get("decision") == "signal_freshness_train_rule_failed_holdout":
        lines.append("A train-selected freshness rule did not survive validation/final holdout gates, so this should not be promoted.")
    elif report.get("decision") == "research_alpha_signal_freshness_split_stable":
        lines.append("A train-selected freshness rule passed validation and final shadow gates, but this is still not replay/stress/walk-forward evidence and cannot support a live switch.")
    elif report.get("outcome_tier") == "Research Alpha":
        lines.append("A signal-level freshness rule passed the shadow gate, but this is not replay/stress/walk-forward evidence and cannot support a live switch.")
    else:
        lines.append("No signal-level freshness rule passed the configured shadow gate.")
    lines.append("")
    return "\n".join(lines)
