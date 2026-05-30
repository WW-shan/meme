from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from statistics import median
from typing import Any, Iterable, Mapping

from src.pipeline import reentry_probe


DEFAULT_MAX_HOLD_SECONDS = 560.0
DEFAULT_HORIZON_SECONDS = 10800.0
DEFAULT_MIN_SUPPORT = 7


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


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
        default=_json_default,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _safe_float_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _optional_time(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    return reentry_probe.parse_time(value)


def _time_in_window(value: Any, *, since_time: dt.datetime | None, until_time: dt.datetime | None) -> bool:
    parsed = reentry_probe.parse_time(value)
    if since_time is not None and parsed < since_time:
        return False
    if until_time is not None and parsed > until_time:
        return False
    return True


def iter_entry_protection_skips(
    rows: Iterable[Mapping[str, Any]],
    *,
    since: Any = None,
    until: Any = None,
) -> Iterable[dict[str, Any]]:
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    for row in rows:
        if str(row.get("action") or "").upper() != "ENTRY_PRICE_PROTECTION_SKIP":
            continue
        if row.get("time") is None:
            continue
        try:
            if not _time_in_window(row.get("time"), since_time=since_time, until_time=until_time):
                continue
        except (TypeError, ValueError):
            continue
        parsed = dict(row)
        parsed["token"] = reentry_probe.normalize_token(row.get("token") or row.get("token_address"))
        parsed["time"] = reentry_probe.parse_time(row.get("time"))
        yield parsed


def _point_with_return(
    point: reentry_probe.PricePoint | None,
    *,
    anchor_time: dt.datetime,
    anchor_price: float,
) -> dict[str, Any] | None:
    if point is None or anchor_price <= 0.0:
        return None
    return {
        "time": reentry_probe.parse_time(point.time),
        "seconds_after_skip": (reentry_probe.parse_time(point.time) - anchor_time).total_seconds(),
        "price": float(point.price),
        "kind": point.kind,
        "return_pct": ((float(point.price) / anchor_price) - 1.0) * 100.0,
    }


def _last_point_within(
    path: Iterable[reentry_probe.PricePoint],
    *,
    anchor_time: dt.datetime,
    horizon_seconds: float,
) -> reentry_probe.PricePoint | None:
    selected = None
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        seconds = (reentry_probe.parse_time(point.time) - anchor_time).total_seconds()
        if seconds < 0:
            continue
        if seconds > horizon_seconds:
            break
        selected = point
    return selected


def _first_stop_seconds(metrics: Mapping[str, Any]) -> float | None:
    values = [
        _safe_float_or_none(metrics.get("time_to_minus_18_seconds")),
        _safe_float_or_none(metrics.get("time_to_minus_25_seconds")),
    ]
    valid = [value for value in values if value is not None]
    return min(valid) if valid else None


def _plus25_before_stop(metrics: Mapping[str, Any]) -> bool:
    plus25 = _safe_float_or_none(metrics.get("time_to_plus_25_seconds"))
    if plus25 is None:
        return False
    first_stop = _first_stop_seconds(metrics)
    return first_stop is None or plus25 < first_stop


def _stop_before_plus25(metrics: Mapping[str, Any]) -> bool:
    first_stop = _first_stop_seconds(metrics)
    if first_stop is None:
        return False
    plus25 = _safe_float_or_none(metrics.get("time_to_plus_25_seconds"))
    return plus25 is None or first_stop <= plus25


def _classify_within_hold(metrics: Mapping[str, Any], timeout_point: Mapping[str, Any] | None) -> str:
    if _plus25_before_stop(metrics):
        return "missed_within_hold_profit"
    if _stop_before_plus25(metrics):
        return "protected_stop_first_within_hold"
    timeout_return = _safe_float_or_none((timeout_point or {}).get("return_pct"))
    if timeout_return is None:
        return "insufficient_hold_path"
    if timeout_return >= 5.0:
        return "protected_small_gain_timeout"
    if timeout_return <= -5.0:
        return "protected_weak_timeout"
    return "protected_flat_timeout"


def _classify_extended(
    *,
    hold_metrics: Mapping[str, Any],
    extended_metrics: Mapping[str, Any],
    max_hold_seconds: float,
) -> str:
    if _plus25_before_stop(hold_metrics):
        return "profit_within_hold"
    plus25 = _safe_float_or_none(extended_metrics.get("time_to_plus_25_seconds"))
    if plus25 is not None and plus25 > float(max_hold_seconds):
        first_stop = _first_stop_seconds(extended_metrics)
        if first_stop is None or plus25 < first_stop:
            return "late_profit_after_hold"
    if _stop_before_plus25(extended_metrics):
        return "extended_stop_first"
    if plus25 is not None:
        return "extended_profit_after_early_stop_or_tie"
    return "no_extended_profit"


def score_skip_event(
    skip: Mapping[str, Any],
    path: Iterable[reentry_probe.PricePoint],
    *,
    max_hold_seconds: float = DEFAULT_MAX_HOLD_SECONDS,
    horizon_seconds: float = DEFAULT_HORIZON_SECONDS,
) -> dict[str, Any]:
    token = reentry_probe.normalize_token(skip.get("token") or skip.get("token_address"))
    skip_time = reentry_probe.parse_time(skip.get("time"))
    signal_price = _safe_float_or_none(skip.get("signal_price"))
    candidate_price = _safe_float_or_none(skip.get("candidate_price"))
    raw_slippage = _safe_float_or_none(skip.get("entry_slippage_pct"))
    base = {
        "token": token,
        "symbol": skip.get("symbol"),
        "skip_time": skip_time,
        "prob": _safe_float_or_none(skip.get("prob")),
        "pred_return": _safe_float_or_none(skip.get("pred_return")),
        "signal_price": signal_price,
        "candidate_price": candidate_price,
        "reported_entry_slippage_fraction": raw_slippage,
        "reported_entry_slippage_pct": raw_slippage * 100.0 if raw_slippage is not None else None,
        "entry_price_protection_pct": _safe_float_or_none(skip.get("entry_price_protection_pct")),
        "signal_to_candidate_jump_pct": (
            ((candidate_price / signal_price) - 1.0) * 100.0
            if signal_price is not None and signal_price > 0.0 and candidate_price is not None
            else None
        ),
    }
    if candidate_price is None or candidate_price <= 0.0:
        return {
            **base,
            "path_point_count": 0,
            "within_hold_label": "missing_candidate_price",
            "extended_label": "missing_candidate_price",
            "supports_relaxing_entry_protection": False,
        }

    path_points = [
        point
        for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time))
        if (reentry_probe.parse_time(point.time) - skip_time).total_seconds() >= 0
    ]
    if not path_points:
        return {
            **base,
            "path_point_count": 0,
            "within_hold_label": "missing_path",
            "extended_label": "missing_path",
            "supports_relaxing_entry_protection": False,
        }

    hold_metrics = reentry_probe.path_metrics(
        path_points,
        anchor_time=skip_time,
        anchor_price=candidate_price,
        horizon_seconds=float(max_hold_seconds),
    )
    extended_metrics = reentry_probe.path_metrics(
        path_points,
        anchor_time=skip_time,
        anchor_price=candidate_price,
        horizon_seconds=float(horizon_seconds),
    )
    timeout_point = _point_with_return(
        _last_point_within(path_points, anchor_time=skip_time, horizon_seconds=float(max_hold_seconds)),
        anchor_time=skip_time,
        anchor_price=candidate_price,
    )
    extended_last_point = _point_with_return(path_points[-1], anchor_time=skip_time, anchor_price=candidate_price)
    max_point = _point_with_return(
        max(path_points, key=lambda point: float(point.price)),
        anchor_time=skip_time,
        anchor_price=candidate_price,
    )
    min_point = _point_with_return(
        min(path_points, key=lambda point: float(point.price)),
        anchor_time=skip_time,
        anchor_price=candidate_price,
    )
    within_hold_label = _classify_within_hold(hold_metrics, timeout_point)
    extended_label = _classify_extended(
        hold_metrics=hold_metrics,
        extended_metrics=extended_metrics,
        max_hold_seconds=max_hold_seconds,
    )
    return {
        **base,
        "path_point_count": len(path_points),
        "max_hold_seconds": float(max_hold_seconds),
        "horizon_seconds": float(horizon_seconds),
        "within_hold_label": within_hold_label,
        "extended_label": extended_label,
        "supports_relaxing_entry_protection": within_hold_label == "missed_within_hold_profit",
        "hold_metrics": hold_metrics,
        "extended_metrics": extended_metrics,
        "timeout_point": timeout_point,
        "extended_last_point": extended_last_point,
        "max_point": max_point,
        "min_point": min_point,
    }


def _counts(rows: Iterable[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field) or "") for row in rows if str(row.get(field) or "")).items()))


def _median(values: Iterable[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(median(valid)) if valid else None


def _average(values: Iterable[float | None]) -> float | None:
    valid = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return float(sum(valid) / len(valid)) if valid else None


def _decision(*, scored: list[dict[str, Any]], min_support: int) -> dict[str, Any]:
    support = [row for row in scored if row.get("supports_relaxing_entry_protection")]
    with_path = [row for row in scored if int(row.get("path_point_count") or 0) > 0]
    if not scored:
        return {
            "status": "no_skip_events",
            "outcome_tier": "Rejected",
            "reason": "No ENTRY_PRICE_PROTECTION_SKIP events were available in the selected window.",
            "safe_for_live_switch": False,
        }
    if len(support) >= int(min_support):
        return {
            "status": "research_alpha_skip_relaxation_candidate",
            "outcome_tier": "Research Alpha",
            "reason": (
                "Skipped candidates reached +25% before stop within the current hold window often enough to justify "
                "a replay-only entry-protection calibration experiment. This is not live-switch evidence."
            ),
            "safe_for_live_switch": False,
        }
    if not with_path:
        return {
            "status": "insufficient_lifecycle_coverage",
            "outcome_tier": "Rejected",
            "reason": "Skip events exist, but none had lifecycle path coverage for outcome scoring.",
            "safe_for_live_switch": False,
        }
    return {
        "status": "reject_relaxation_no_within_hold_support",
        "outcome_tier": "Rejected",
        "reason": (
            "Entry-protection skip outcomes did not show enough +25% before stop within the current hold window. "
            "Do not loosen live entry protection from this evidence."
        ),
        "safe_for_live_switch": False,
    }


def build_skip_outcome_report(
    *,
    signal_rows: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, Mapping[str, Any]],
    generated_at: dt.datetime | None = None,
    since: Any = None,
    until: Any = None,
    active_model: str | None = None,
    max_hold_seconds: float = DEFAULT_MAX_HOLD_SECONDS,
    horizon_seconds: float = DEFAULT_HORIZON_SECONDS,
    min_support: int = DEFAULT_MIN_SUPPORT,
    max_sample: int = 100,
) -> dict[str, Any]:
    normalized_lifecycles = {
        reentry_probe.normalize_token(token): dict(lifecycle)
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    skips = list(iter_entry_protection_skips(signal_rows, since=since, until=until))
    scored = [
        score_skip_event(
            skip,
            reentry_probe.price_path_for_token(normalized_lifecycles, skip.get("token")),
            max_hold_seconds=max_hold_seconds,
            horizon_seconds=horizon_seconds,
        )
        for skip in skips
    ]
    support = [row for row in scored if row.get("supports_relaxing_entry_protection")]
    timeout_returns = [
        _safe_float_or_none((row.get("timeout_point") or {}).get("return_pct"))
        for row in scored
    ]
    full_horizon_returns = [
        _safe_float_or_none((row.get("extended_last_point") or {}).get("return_pct"))
        for row in scored
    ]
    sample_limit = int(max_sample)
    emitted = scored if sample_limit == 0 else scored[: max(0, sample_limit)]
    generated = generated_at or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None)
    return {
        "generated_at": generated,
        "timezone": "UTC+8",
        "active_model": active_model,
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
        },
        "parameters": {
            "since": _optional_time(since),
            "until": _optional_time(until),
            "max_hold_seconds": float(max_hold_seconds),
            "horizon_seconds": float(horizon_seconds),
            "min_support": int(min_support),
            "max_sample": sample_limit,
        },
        "summary": {
            "skip_count": len(scored),
            "with_path_count": sum(1 for row in scored if int(row.get("path_point_count") or 0) > 0),
            "missing_path_count": sum(1 for row in scored if row.get("within_hold_label") == "missing_path"),
            "supports_relaxing_entry_protection_count": len(support),
            "within_hold_label_counts": _counts(scored, "within_hold_label"),
            "extended_label_counts": _counts(scored, "extended_label"),
            "timeout_return_pct_avg": _average(timeout_returns),
            "timeout_return_pct_median": _median(timeout_returns),
            "extended_last_return_pct_avg": _average(full_horizon_returns),
            "extended_last_return_pct_median": _median(full_horizon_returns),
            "signal_to_candidate_jump_pct_median": _median(
                row.get("signal_to_candidate_jump_pct") for row in scored
            ),
        },
        "decision": _decision(scored=scored, min_support=int(min_support)),
        "skip_sample": emitted,
        "unemitted_skip_count": max(0, len(scored) - len(emitted)),
    }


def to_markdown_text(report: Mapping[str, Any]) -> str:
    summary = _json_sanitize(report.get("summary") or {})
    decision = _json_sanitize(report.get("decision") or {})
    params = _json_sanitize(report.get("parameters") or {})
    lines = [
        "# Entry Protection Skip Outcome Probe",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(params, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Decision",
        "",
        "```json",
        json.dumps(decision, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Sample",
        "",
        "```json",
        json.dumps(
            _json_sanitize(report.get("skip_sample") or [])[:10],
            default=_json_default,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        "```",
        "",
    ]
    return "\n".join(lines)
