from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from typing import Any, Iterable, Mapping

MIN_RESCUE_PROB = 0.985
MIN_RESCUE_PRED_RETURN = 30.0
MAX_RESCUE_MAE_PCT = -18.0
ACTION_TAXONOMY = [
    "skip",
    "rescue_quick_tp",
    "conditional_slow_hold",
    "post_target_lock",
    "continue_hold",
    "monitor_after_target",
]


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        default=_json_default,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else default


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def classify_time_to_barrier_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    barrier_class = str(candidate.get("barrier_class") or "")
    prob = _finite_float(candidate.get("prob"))
    pred_return = _finite_float(candidate.get("pred_return"))
    mfe_pct = _finite_float(candidate.get("mfe_pct"))
    mae_pct = _finite_float(candidate.get("mae_pct"))
    time_to_plus_25 = _finite_float(candidate.get("time_to_plus_25_seconds"))
    reject_reasons: list[str] = []
    if candidate.get("missing_path"):
        reject_reasons.append("missing_path")
    if barrier_class == "stop_first":
        reject_reasons.append("stop_first")
    if barrier_class not in {"fast_profit", "fast_profit_then_collapse", "slow_runner"}:
        reject_reasons.append("not_fast_profit")
    if prob is None:
        reject_reasons.append("prob_missing_or_nonfinite")
    elif prob < MIN_RESCUE_PROB:
        reject_reasons.append("prob_below_rescue_min")
    if pred_return is None:
        reject_reasons.append("pred_return_missing_or_nonfinite")
    elif pred_return < MIN_RESCUE_PRED_RETURN:
        reject_reasons.append("pred_return_below_rescue_min")
    if mae_pct is None:
        reject_reasons.append("mae_missing_or_nonfinite")
    elif mae_pct <= MAX_RESCUE_MAE_PCT:
        reject_reasons.append("mae_breached_stop")
    if mfe_pct is None:
        reject_reasons.append("mfe_pct_missing_or_nonfinite")
    if time_to_plus_25 is None:
        reject_reasons.append("time_to_plus_25_seconds_missing_or_nonfinite")
    eligible = not reject_reasons
    if eligible and barrier_class == "slow_runner":
        action = "conditional_slow_hold"
        risk_policy = "conditional_hold_probe_only"
    elif eligible:
        action = "rescue_quick_tp"
        risk_policy = "quick_take_profit_only"
    else:
        action = "skip"
        risk_policy = "no_trade"
    return {
        "token": candidate.get("token"),
        "symbol": candidate.get("symbol"),
        "source": "time_to_barrier",
        "evidence_class": barrier_class,
        "action": action,
        "eligible": eligible,
        "risk_policy": risk_policy,
        "reject_reasons": reject_reasons,
        "prob": candidate.get("prob"),
        "pred_return": candidate.get("pred_return"),
        "mfe_pct": candidate.get("mfe_pct"),
        "mae_pct": candidate.get("mae_pct"),
        "time_to_plus_25_seconds": candidate.get("time_to_plus_25_seconds"),
    }


def classify_post_target_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    classification = str(candidate.get("classification") or "")
    target_hit = bool(candidate.get("target_hit"))
    time_to_target = _finite_float(candidate.get("time_to_target_seconds"))
    time_to_collapse = _finite_float(candidate.get("time_to_post_target_collapse_seconds"))
    time_to_continuation = _finite_float(candidate.get("time_to_continuation_seconds"))
    reject_reasons: list[str] = []
    if candidate.get("missing_path"):
        reject_reasons.append("missing_path")
    action = "monitor_after_target"
    if classification == "post_target_collapse":
        action = "post_target_lock"
        if not target_hit:
            reject_reasons.append("target_not_hit")
        if time_to_target is None:
            reject_reasons.append("time_to_target_seconds_missing_or_nonfinite")
        if time_to_collapse is None:
            reject_reasons.append("time_to_post_target_collapse_seconds_missing_or_nonfinite")
    elif classification == "post_target_continuation":
        action = "continue_hold"
        if not target_hit:
            reject_reasons.append("target_not_hit")
        if time_to_target is None:
            reject_reasons.append("time_to_target_seconds_missing_or_nonfinite")
        if time_to_continuation is None:
            reject_reasons.append("time_to_continuation_seconds_missing_or_nonfinite")
    elif classification == "target_not_hit":
        action = "monitor_after_target"
    if reject_reasons:
        action = "monitor_after_target"
    return {
        "token": candidate.get("token"),
        "symbol": candidate.get("symbol"),
        "source": "post_target",
        "evidence_class": classification,
        "action": action,
        "eligible": action in {"post_target_lock", "continue_hold"},
        "risk_policy": "post_target_decision_only",
        "reject_reasons": reject_reasons,
        "target_hit": candidate.get("target_hit"),
        "time_to_target_seconds": candidate.get("time_to_target_seconds"),
        "time_to_post_target_collapse_seconds": candidate.get("time_to_post_target_collapse_seconds"),
        "time_to_continuation_seconds": candidate.get("time_to_continuation_seconds"),
    }


def _candidate_list(report: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], str]:
    if report.get("candidates"):
        rows = report.get("candidates") or []
        return [row for row in rows if isinstance(row, Mapping)], "candidates"
    rows = report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)], "candidate_sample"


def _reported_total(report: Mapping[str, Any], keys: Iterable[str], fallback: int) -> int:
    counts = report.get("candidate_counts") or {}
    if not isinstance(counts, Mapping):
        return fallback
    for key in keys:
        value = counts.get(key)
        if isinstance(value, int):
            return value
    return fallback


def _truncation_warning(*, source: str, field: str, processed: int, reported: int) -> dict[str, Any] | None:
    if field == "candidate_sample" and reported > processed:
        return {
            "source": source,
            "candidate_field": field,
            "processed_candidates": processed,
            "reported_candidates": reported,
            "warning": "input_report_only_contains_truncated_candidate_sample",
        }
    return None


def build_action_report(
    *,
    time_to_barrier_report: Mapping[str, Any],
    post_target_report: Mapping[str, Any],
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    time_rows, time_field = _candidate_list(time_to_barrier_report)
    post_rows, post_field = _candidate_list(post_target_report)
    time_reported = _reported_total(time_to_barrier_report, ("per_token_candidates",), len(time_rows))
    post_reported = _reported_total(post_target_report, ("scored_candidates", "trade_log_rows"), len(post_rows))
    input_warnings = [
        warning
        for warning in (
            _truncation_warning(source="time_to_barrier", field=time_field, processed=len(time_rows), reported=time_reported),
            _truncation_warning(source="post_target", field=post_field, processed=len(post_rows), reported=post_reported),
        )
        if warning is not None
    ]
    actions = [classify_time_to_barrier_action(row) for row in time_rows]
    actions.extend(classify_post_target_action(row) for row in post_rows)
    action_counts = Counter(row["action"] for row in actions)
    source_counts = Counter(row["source"] for row in actions)
    action_sample_limit = 200
    action_sample_truncated = len(actions) > action_sample_limit
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "action_labels_use_ex_post_outcomes": True,
            "causal_policy": False,
            "intended_use": "oracle_taxonomy_for_replay_experiment_design",
            "warning": "not_a_deployable_action_policy",
        },
        "parameters": {
            "min_rescue_prob": MIN_RESCUE_PROB,
            "min_rescue_pred_return": MIN_RESCUE_PRED_RETURN,
            "max_rescue_mae_pct": MAX_RESCUE_MAE_PCT,
            "position_fraction": 0.10,
            "max_open_positions": 8,
        },
        "action_taxonomy": ACTION_TAXONOMY,
        "source_counts": {
            "time_to_barrier_candidates": len(time_rows),
            "post_target_candidates": len(post_rows),
            "time_to_barrier_reported_candidates": time_reported,
            "post_target_reported_candidates": post_reported,
            **dict(sorted(source_counts.items())),
        },
        "action_counts": {action: action_counts.get(action, 0) for action in ACTION_TAXONOMY},
        "input_warnings": input_warnings,
        "decision": "probe_only_sample_limited" if input_warnings else "probe_only_replay_required",
        "actions_total": len(actions),
        "action_sample": {
            "included": min(len(actions), action_sample_limit),
            "limit": action_sample_limit,
            "total": len(actions),
            "truncated": action_sample_truncated,
            "warning": "actions_field_is_truncated_sample" if action_sample_truncated else None,
        },
        "actions": actions[:action_sample_limit],
    }
