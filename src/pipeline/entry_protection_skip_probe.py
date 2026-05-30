from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

from src.pipeline import reentry_probe


DEFAULT_MAX_HOLD_SECONDS = 560.0
DEFAULT_HORIZON_SECONDS = 10800.0
DEFAULT_MIN_SUPPORT = 7
DEFAULT_POST_SKIP_LOOKBACK_SECONDS = 120.0
DEFAULT_POST_SKIP_PATH_HORIZON_SECONDS = 560.0
MAX_POST_SKIP_THRESHOLD_VALUES = 40
POST_SKIP_POLICY_NUMERIC_GTE_FIELDS = (
    "prior_skip_count",
    "prior_skip_max_entry_slippage_pct",
    "prior_skip_max_signal_to_candidate_jump_pct",
    "prior_skip_max_prob",
    "prior_skip_max_pred_return",
)
POST_SKIP_POLICY_NUMERIC_LTE_FIELDS = (
    "prior_skip_last_seconds_before_open",
)


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


def _time_or_none(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return reentry_probe.parse_time(value)
    except (TypeError, ValueError):
        return None


def _first_time(row: Mapping[str, Any], keys: Sequence[str]) -> dt.datetime | None:
    for key in keys:
        parsed = _time_or_none(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _first_float(row: Mapping[str, Any], keys: Sequence[str]) -> float | None:
    for key in keys:
        parsed = _safe_float_or_none(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _trade_sort_time(row: Mapping[str, Any]) -> dt.datetime:
    return (
        _first_time(row, ("entry_signal_time", "signal_time", "time", "sell_started_at"))
        or dt.datetime.min
    )


def pair_real_trade_rows(trade_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    open_by_token: dict[str, list[dict[str, Any]]] = {}
    pairs: list[dict[str, Any]] = []
    rows = [dict(row) for row in trade_rows if _truthy(row.get("is_real_trade"))]
    for row in sorted(rows, key=_trade_sort_time):
        action = str(row.get("action") or "").upper()
        token = reentry_probe.normalize_token(row.get("token") or row.get("token_address"))
        if not token:
            continue
        parsed = dict(row)
        parsed["token"] = token
        if action == "OPEN":
            open_by_token.setdefault(token, []).append(parsed)
            continue
        if action != "CLOSE":
            continue
        pending = open_by_token.get(token)
        if not pending:
            continue
        opened = pending.pop(0)
        pairs.append({
            "token": token,
            "symbol": parsed.get("symbol") or opened.get("symbol"),
            "open": opened,
            "close": parsed,
        })
    return pairs


def _net_profit_bnb(close: Mapping[str, Any]) -> float | None:
    return _first_float(close, ("net_profit_bnb", "net_profit", "profit_bnb", "pnl_bnb"))


def _entry_decision_time(opened: Mapping[str, Any]) -> dt.datetime | None:
    return _first_time(opened, ("entry_signal_time", "signal_time", "time"))


def _actual_open_time(opened: Mapping[str, Any]) -> dt.datetime | None:
    return _first_time(opened, ("time", "opened_at", "buy_started_at", "entry_signal_time", "signal_time"))


def _open_price(opened: Mapping[str, Any]) -> float | None:
    return _first_float(opened, ("entry_price", "buy_price", "price", "price_bnb", "candidate_price"))


def _normalized_percent_from_fraction(value: Any) -> float | None:
    parsed = _safe_float_or_none(value)
    return parsed * 100.0 if parsed is not None else None


def _signal_to_candidate_jump_pct(row: Mapping[str, Any]) -> float | None:
    signal_price = _safe_float_or_none(row.get("signal_price"))
    candidate_price = _safe_float_or_none(row.get("candidate_price"))
    if signal_price is not None and signal_price > 0.0 and candidate_price is not None:
        return ((candidate_price / signal_price) - 1.0) * 100.0
    return _safe_float_or_none(row.get("signal_to_candidate_jump_pct"))


def _skip_event_summary(skip: Mapping[str, Any], *, anchor_time: dt.datetime) -> dict[str, Any]:
    skip_time = reentry_probe.parse_time(skip.get("time"))
    return {
        "skip_time": skip_time,
        "seconds_before_open": (anchor_time - skip_time).total_seconds(),
        "symbol": skip.get("symbol"),
        "prob": _safe_float_or_none(skip.get("prob")),
        "pred_return": _safe_float_or_none(skip.get("pred_return")),
        "entry_slippage_pct": _normalized_percent_from_fraction(skip.get("entry_slippage_pct")),
        "entry_price_protection_pct": _safe_float_or_none(skip.get("entry_price_protection_pct")),
        "signal_to_candidate_jump_pct": _signal_to_candidate_jump_pct(skip),
    }


def _summarize_prior_skips(prior_skips: Sequence[Mapping[str, Any]], *, anchor_time: dt.datetime) -> dict[str, Any]:
    events = [_skip_event_summary(skip, anchor_time=anchor_time) for skip in sorted(prior_skips, key=lambda row: row["time"])]
    if not events:
        return {
            "prior_skip_count": 0,
            "prior_skip_first_seconds_before_open": None,
            "prior_skip_last_seconds_before_open": None,
            "prior_skip_max_entry_slippage_pct": None,
            "prior_skip_latest_entry_slippage_pct": None,
            "prior_skip_max_signal_to_candidate_jump_pct": None,
            "prior_skip_latest_signal_to_candidate_jump_pct": None,
            "prior_skip_max_prob": None,
            "prior_skip_latest_prob": None,
            "prior_skip_max_pred_return": None,
            "prior_skip_latest_pred_return": None,
            "prior_skip_event_sample": [],
        }

    def values(field: str) -> list[float]:
        return [float(event[field]) for event in events if _safe_float_or_none(event.get(field)) is not None]

    latest = events[-1]
    return {
        "prior_skip_count": len(events),
        "prior_skip_first_seconds_before_open": events[0]["seconds_before_open"],
        "prior_skip_last_seconds_before_open": latest["seconds_before_open"],
        "prior_skip_max_entry_slippage_pct": max(values("entry_slippage_pct")) if values("entry_slippage_pct") else None,
        "prior_skip_latest_entry_slippage_pct": latest.get("entry_slippage_pct"),
        "prior_skip_max_signal_to_candidate_jump_pct": (
            max(values("signal_to_candidate_jump_pct")) if values("signal_to_candidate_jump_pct") else None
        ),
        "prior_skip_latest_signal_to_candidate_jump_pct": latest.get("signal_to_candidate_jump_pct"),
        "prior_skip_max_prob": max(values("prob")) if values("prob") else None,
        "prior_skip_latest_prob": latest.get("prob"),
        "prior_skip_max_pred_return": max(values("pred_return")) if values("pred_return") else None,
        "prior_skip_latest_pred_return": latest.get("pred_return"),
        "prior_skip_event_sample": events[:5],
    }


def _post_skip_path_diagnostics(
    *,
    lifecycles: Mapping[str, Mapping[str, Any]],
    token: str,
    opened: Mapping[str, Any],
    horizon_seconds: float,
) -> dict[str, Any]:
    path = reentry_probe.price_path_for_token(dict(lifecycles), token)
    anchor_time = _actual_open_time(opened)
    anchor_price = _open_price(opened)
    if not path or anchor_time is None or anchor_price is None or anchor_price <= 0.0:
        return {
            "path_point_count": len(path),
            "path_horizon_seconds": float(horizon_seconds),
            "mfe_pct": None,
            "mae_pct": None,
            "first_barrier": None,
        }
    metrics = reentry_probe.path_metrics(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        horizon_seconds=float(horizon_seconds),
    )
    return {
        "path_point_count": len(path),
        "path_horizon_seconds": float(horizon_seconds),
        "mfe_pct": metrics.get("mfe_pct"),
        "mae_pct": metrics.get("mae_pct"),
        "first_barrier": metrics.get("first_barrier"),
    }


def post_skip_followup_rows(
    *,
    trade_rows: Iterable[Mapping[str, Any]],
    signal_rows: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, Mapping[str, Any]],
    since: Any = None,
    until: Any = None,
    lookback_seconds: float = DEFAULT_POST_SKIP_LOOKBACK_SECONDS,
    path_horizon_seconds: float = DEFAULT_POST_SKIP_PATH_HORIZON_SECONDS,
) -> list[dict[str, Any]]:
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    skips_by_token: dict[str, list[dict[str, Any]]] = {}
    for skip in iter_entry_protection_skips(signal_rows):
        token = reentry_probe.normalize_token(skip.get("token"))
        if token:
            skips_by_token.setdefault(token, []).append(skip)

    normalized_lifecycles = {
        reentry_probe.normalize_token(token): dict(lifecycle)
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    outcomes: list[dict[str, Any]] = []
    for pair in pair_real_trade_rows(trade_rows):
        opened = dict(pair.get("open") or {})
        close = dict(pair.get("close") or {})
        token = reentry_probe.normalize_token(pair.get("token") or opened.get("token") or close.get("token"))
        if not token:
            continue
        entry_time = _entry_decision_time(opened)
        if entry_time is None:
            continue
        if since_time is not None and entry_time < since_time:
            continue
        if until_time is not None and entry_time > until_time:
            continue
        net_profit = _net_profit_bnb(close)
        prior_skips = []
        for skip in sorted(skips_by_token.get(token, []), key=lambda row: row["time"]):
            seconds = (entry_time - reentry_probe.parse_time(skip.get("time"))).total_seconds()
            if 0.0 < seconds <= float(lookback_seconds):
                prior_skips.append(skip)
        prior_summary = _summarize_prior_skips(prior_skips, anchor_time=entry_time)
        outcome = {
            "token": token,
            "symbol": close.get("symbol") or opened.get("symbol") or pair.get("symbol"),
            "entry_decision_time": entry_time,
            "open_time": _actual_open_time(opened),
            "close_time": _time_or_none(close.get("time")),
            "close_reason": close.get("reason"),
            "net_profit_bnb": float(net_profit or 0.0),
            "is_win": float(net_profit or 0.0) > 0.0,
            "prob": _safe_float_or_none(opened.get("prob")),
            "pred_return": _safe_float_or_none(opened.get("pred_return")),
            "open_entry_slippage_pct": _normalized_percent_from_fraction(opened.get("entry_slippage_pct")),
            **prior_summary,
            **_post_skip_path_diagnostics(
                lifecycles=normalized_lifecycles,
                token=token,
                opened=opened,
                horizon_seconds=path_horizon_seconds,
            ),
        }
        outcomes.append(outcome)
    return sorted(outcomes, key=lambda row: row.get("entry_decision_time") or dt.datetime.min)


def _post_skip_split_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    train_fraction: float,
    validation_fraction: float,
) -> dict[str, list[dict[str, Any]]]:
    if not 0.0 < float(train_fraction) < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0.0 < float(validation_fraction) < 1.0:
        raise ValueError("validation_fraction must be in (0, 1)")
    if float(train_fraction) + float(validation_fraction) >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be < 1")
    ordered = [dict(row) for row in rows]
    train_end = int(len(ordered) * float(train_fraction))
    validation_end = int(len(ordered) * (float(train_fraction) + float(validation_fraction)))
    return {
        "train": ordered[:train_end],
        "validation": ordered[train_end:validation_end],
        "final": ordered[validation_end:],
    }


def _post_skip_threshold_values(values: Sequence[float]) -> list[float]:
    unique = sorted({float(value) for value in values if math.isfinite(float(value))})
    if len(unique) <= MAX_POST_SKIP_THRESHOLD_VALUES:
        return unique
    indexes = {
        round(index * (len(unique) - 1) / (MAX_POST_SKIP_THRESHOLD_VALUES - 1))
        for index in range(MAX_POST_SKIP_THRESHOLD_VALUES)
    }
    return [unique[index] for index in sorted(indexes)]


def _post_skip_rule_label(rule: Mapping[str, Any]) -> str:
    rule_type = str(rule.get("type") or "")
    if rule_type == "numeric_gte":
        return f"{rule.get('field')} >= {float(rule.get('threshold') or 0.0):g}"
    if rule_type == "numeric_lte":
        return f"{rule.get('field')} <= {float(rule.get('threshold') or 0.0):g}"
    return rule_type or "unknown"


def _post_skip_rule_identity(rule: Mapping[str, Any]) -> str:
    return json.dumps(_json_sanitize(rule), sort_keys=True, ensure_ascii=False)


def _matches_post_skip_rule(row: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    rule_type = str(rule.get("type") or "")
    value = _safe_float_or_none(row.get(str(rule.get("field") or "")))
    threshold = _safe_float_or_none(rule.get("threshold"))
    if value is None or threshold is None:
        return False
    if rule_type == "numeric_gte":
        return value >= threshold
    if rule_type == "numeric_lte":
        return value <= threshold
    raise ValueError(f"unsupported post-skip rule type: {rule_type}")


def generate_post_skip_rules(train_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(rule: dict[str, Any]) -> None:
        rule = dict(rule)
        rule["label"] = _post_skip_rule_label(rule)
        identity = _post_skip_rule_identity(rule)
        if identity not in seen:
            seen.add(identity)
            rules.append(rule)

    for field in POST_SKIP_POLICY_NUMERIC_GTE_FIELDS:
        values = [
            value
            for value in (_safe_float_or_none(row.get(field)) for row in train_rows)
            if value is not None and value > 0.0
        ]
        for threshold in _post_skip_threshold_values(values):
            add({"type": "numeric_gte", "field": field, "threshold": float(threshold)})

    for field in POST_SKIP_POLICY_NUMERIC_LTE_FIELDS:
        values = [
            value
            for row in train_rows
            for value in [_safe_float_or_none(row.get(field))]
            if value is not None and int(row.get("prior_skip_count") or 0) > 0
        ]
        for threshold in _post_skip_threshold_values(values):
            add({"type": "numeric_lte", "field": field, "threshold": float(threshold)})

    return rules


def _post_skip_split_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    net_values = [float(row.get("net_profit_bnb") or 0.0) for row in rows]
    wins = [value for value in net_values if value > 0.0]
    skip_rows = [row for row in rows if int(row.get("prior_skip_count") or 0) > 0]
    return {
        "trade_count": len(rows),
        "post_skip_trade_count": len(skip_rows),
        "net_profit_bnb": sum(net_values),
        "win_count": len(wins),
        "loss_count": len(rows) - len(wins),
        "win_rate": len(wins) / len(rows) if rows else None,
        "close_reason_counts": _counts(rows, "close_reason"),
    }


def _post_skip_selected_samples(rows: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected = list(rows) if int(limit) == 0 else list(rows[: max(0, int(limit))])
    fields = (
        "entry_decision_time",
        "open_time",
        "close_time",
        "symbol",
        "token",
        "net_profit_bnb",
        "close_reason",
        "prob",
        "pred_return",
        "prior_skip_count",
        "prior_skip_last_seconds_before_open",
        "prior_skip_max_entry_slippage_pct",
        "prior_skip_max_signal_to_candidate_jump_pct",
        "prior_skip_latest_pred_return",
        "prior_skip_latest_prob",
        "mfe_pct",
        "mae_pct",
        "first_barrier",
    )
    samples = []
    for row in selected:
        sample = {field: row.get(field) for field in fields if field in row}
        sample["prior_skip_event_sample"] = row.get("prior_skip_event_sample") or []
        samples.append(sample)
    return samples


def evaluate_post_skip_rule(
    rows: Sequence[Mapping[str, Any]],
    rule: Mapping[str, Any],
    *,
    max_sample_rows: int = 25,
) -> dict[str, Any]:
    selected = [dict(row) for row in rows if _matches_post_skip_rule(row, rule)]
    selected_net = [float(row.get("net_profit_bnb") or 0.0) for row in selected]
    skipped_winners = [value for value in selected_net if value > 0.0]
    skipped_losses = [value for value in selected_net if value <= 0.0]
    abstention_benefits = [-value for value in selected_net]
    positive_benefits = [value for value in abstention_benefits if value > 0.0]
    delta = sum(abstention_benefits)
    without_top = delta - max(positive_benefits) if positive_benefits else delta
    baseline = _post_skip_split_metrics(rows)
    remaining_count = len(rows) - len(selected)
    remaining_win_count = int(baseline["win_count"]) - len(skipped_winners)
    remaining_net = float(baseline["net_profit_bnb"]) + delta
    sample_limit = int(max_sample_rows)
    emitted_count = len(selected) if sample_limit == 0 else max(0, sample_limit)
    return {
        "rule": {
            **dict(rule),
            "label": _post_skip_rule_label(rule),
        },
        "baseline": baseline,
        "selected_count": len(selected),
        "selected_net_profit_bnb": sum(selected_net),
        "selected_winner_count": len(skipped_winners),
        "selected_loss_count": len(skipped_losses),
        "selected_loss_precision": len(skipped_losses) / len(selected) if selected else 0.0,
        "selected_winner_net_bnb": sum(skipped_winners),
        "selected_loss_net_bnb": sum(skipped_losses),
        "abstention_delta_bnb": delta,
        "abstention_delta_without_top_loss_benefit_bnb": without_top,
        "remaining_trade_count": remaining_count,
        "remaining_net_profit_bnb": remaining_net,
        "remaining_win_count": remaining_win_count,
        "remaining_win_rate": remaining_win_count / remaining_count if remaining_count else None,
        "selected_close_reason_counts": _counts(selected, "close_reason"),
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected[:25]],
        "selected_sample": _post_skip_selected_samples(selected, max_sample_rows),
        "unemitted_selected_count": max(0, len(selected) - emitted_count),
    }


def _passes_post_skip_train_gate(
    result: Mapping[str, Any],
    *,
    min_train_selected: int,
    min_train_loss_precision: float,
    max_train_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_train_selected)
        and float(result.get("selected_loss_precision") or 0.0) >= float(min_train_loss_precision)
        and int(result.get("selected_winner_count") or 0) <= int(max_train_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) > 0.0
    )


def _passes_post_skip_validation_gate(
    result: Mapping[str, Any],
    *,
    min_validation_selected: int,
    max_validation_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_validation_selected)
        and int(result.get("selected_winner_count") or 0) <= int(max_validation_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) > 0.0
    )


def _passes_post_skip_final_gate(
    result: Mapping[str, Any],
    *,
    min_final_selected: int,
    max_final_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_final_selected)
        and int(result.get("selected_winner_count") or 0) <= int(max_final_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) >= 0.0
    )


def _post_skip_top_dependency_passes(result: Mapping[str, Any]) -> bool:
    return float(result.get("abstention_delta_without_top_loss_benefit_bnb") or 0.0) >= 0.0


def _rank_post_skip_train(result: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(result.get("abstention_delta_bnb") or 0.0),
        -int(result.get("selected_loss_count") or 0),
        int(result.get("selected_winner_count") or 0),
        -float(result.get("selected_loss_precision") or 0.0),
        str(result.get("rule", {}).get("label") or ""),
    )


def _rank_post_skip_eval(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
    validation = candidate.get("validation") or {}
    final = candidate.get("final") or {}
    return (
        not bool(candidate.get("passes_research_alpha_proxy_gate")),
        -float(validation.get("abstention_delta_bnb") or 0.0),
        -float(final.get("abstention_delta_bnb") or 0.0),
        int(validation.get("selected_winner_count") or 0) + int(final.get("selected_winner_count") or 0),
        -int(validation.get("selected_count") or 0),
        str(candidate.get("rule", {}).get("label") or ""),
    )


def _post_skip_numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "median": finite[len(finite) // 2],
        "max": finite[-1],
        "mean": sum(finite) / len(finite),
    }


def _post_skip_feature_summaries(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    fields = (
        "prior_skip_count",
        "prior_skip_max_entry_slippage_pct",
        "prior_skip_max_signal_to_candidate_jump_pct",
        "prior_skip_last_seconds_before_open",
        "prior_skip_max_prob",
        "prior_skip_max_pred_return",
        "mfe_pct",
        "mae_pct",
    )
    return {
        field: _post_skip_numeric_summary(
            [value for value in (_safe_float_or_none(row.get(field)) for row in rows) if value is not None]
        )
        for field in fields
    }


def _post_skip_metric_coverage() -> dict[str, str]:
    return {
        "net_profit_bnb": "live_real_trade_proxy_only",
        "expected_utility": "abstention_delta_bnb_proxy_only",
        "trade_count": "live_real_trade_proxy_only",
        "win_rate": "live_real_trade_proxy_only",
        "max_drawdown_pct": "not_computed_proxy_requires_replay",
        "walk_forward": "not_computed_proxy_requires_replay",
        "stress": "not_computed_proxy_requires_replay",
        "paired_trade_delta": "not_computed_proxy_requires_replay",
    }


def build_post_skip_followup_hazard_report(
    *,
    trade_rows: Iterable[Mapping[str, Any]],
    signal_rows: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, Mapping[str, Any]],
    generated_at: dt.datetime | None = None,
    since: Any = None,
    until: Any = None,
    active_model: str | None = None,
    lookback_seconds: float = DEFAULT_POST_SKIP_LOOKBACK_SECONDS,
    path_horizon_seconds: float = DEFAULT_POST_SKIP_PATH_HORIZON_SECONDS,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    min_train_selected: int = 2,
    min_train_loss_precision: float = 0.60,
    max_train_winner_count: int = 3,
    min_validation_selected: int = 1,
    max_validation_winner_count: int = 0,
    min_final_selected: int = 1,
    max_final_winner_count: int = 1,
    max_sample_rows: int = 25,
) -> dict[str, Any]:
    if float(lookback_seconds) <= 0.0:
        raise ValueError("lookback_seconds must be positive")
    if float(path_horizon_seconds) <= 0.0:
        raise ValueError("path_horizon_seconds must be positive")
    if not 0.0 <= float(min_train_loss_precision) <= 1.0:
        raise ValueError("min_train_loss_precision must be between 0 and 1")
    if int(max_sample_rows) < 0:
        raise ValueError("max_sample_rows must be non-negative")

    outcomes = post_skip_followup_rows(
        trade_rows=trade_rows,
        signal_rows=signal_rows,
        lifecycles=lifecycles,
        since=since,
        until=until,
        lookback_seconds=lookback_seconds,
        path_horizon_seconds=path_horizon_seconds,
    )
    splits = _post_skip_split_rows(
        outcomes,
        train_fraction=train_fraction,
        validation_fraction=validation_fraction,
    )
    rules = generate_post_skip_rules(splits["train"])
    train_results = [evaluate_post_skip_rule(splits["train"], rule, max_sample_rows=max_sample_rows) for rule in rules]
    train_results.sort(key=_rank_post_skip_train)
    train_eligible = [
        result
        for result in train_results
        if _passes_post_skip_train_gate(
            result,
            min_train_selected=min_train_selected,
            min_train_loss_precision=min_train_loss_precision,
            max_train_winner_count=max_train_winner_count,
        )
    ]

    evaluated_candidates = []
    for train_result in train_eligible:
        rule = dict(train_result.get("rule") or {})
        validation_result = evaluate_post_skip_rule(splits["validation"], rule, max_sample_rows=max_sample_rows)
        final_result = evaluate_post_skip_rule(splits["final"], rule, max_sample_rows=max_sample_rows)
        validation_passes = _passes_post_skip_validation_gate(
            validation_result,
            min_validation_selected=min_validation_selected,
            max_validation_winner_count=max_validation_winner_count,
        )
        final_passes = _passes_post_skip_final_gate(
            final_result,
            min_final_selected=min_final_selected,
            max_final_winner_count=max_final_winner_count,
        )
        top_dependency_passes = (
            _post_skip_top_dependency_passes(validation_result)
            and _post_skip_top_dependency_passes(final_result)
        )
        evaluated_candidates.append({
            "rule": rule,
            "train": train_result,
            "validation": validation_result,
            "final": final_result,
            "validation_passes": bool(validation_passes),
            "final_passes": bool(final_passes),
            "top_dependency_passes": bool(top_dependency_passes),
            "passes_research_alpha_proxy_gate": bool(validation_passes and final_passes and top_dependency_passes),
        })
    evaluated_candidates.sort(key=_rank_post_skip_eval)
    selected = next(
        (candidate for candidate in evaluated_candidates if candidate["passes_research_alpha_proxy_gate"]),
        evaluated_candidates[0] if evaluated_candidates else None,
    )

    if selected and selected.get("passes_research_alpha_proxy_gate"):
        outcome_tier = "Research Alpha"
        decision = "research_alpha_post_skip_followup_requires_replay_integration"
    elif train_eligible:
        outcome_tier = "Rejected"
        decision = "train_post_skip_candidate_failed_validation_or_final_proxy_gate"
    elif any(int(row.get("prior_skip_count") or 0) > 0 for row in outcomes):
        outcome_tier = "Rejected"
        decision = "no_train_post_skip_followup_candidate"
    else:
        outcome_tier = "Rejected"
        decision = "no_real_trades_with_prior_entry_protection_skip"

    generated = generated_at or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None)
    return {
        "generated_at": generated,
        "timezone": "UTC+8",
        "active_model": active_model,
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "uses_only_pre_open_skip_history_as_policy": True,
            "causal_policy": (
                "rule scan uses only prior ENTRY_PRICE_PROTECTION_SKIP events for the same token before "
                "the later accepted entry decision"
            ),
            "diagnostic_only_fields": [
                "open_entry_slippage_pct",
                "mfe_pct",
                "mae_pct",
                "first_barrier",
            ],
        },
        "method": {
            "name": "post_skip_followup_hazard_probe",
            "hypothesis": (
                "A token that repeatedly triggers entry price protection shortly before a later accepted buy "
                "may represent adverse-selection chase flow; abstaining those follow-up entries can improve utility."
            ),
            "falsification_rule": (
                "Train-only prior-skip rules must improve validation abstention delta, avoid validation winner skips, "
                "and keep final abstention delta non-negative before any replay-integrated feature work."
            ),
            "distinction_from_prior_entry_protection_skip_probe": (
                "This does not test loosening entry protection. It tests whether prior protection skips should become "
                "a pre-open abstention feature for later accepted entries."
            ),
        },
        "parameters": {
            "since": _optional_time(since),
            "until": _optional_time(until),
            "lookback_seconds": float(lookback_seconds),
            "path_horizon_seconds": float(path_horizon_seconds),
            "train_fraction": float(train_fraction),
            "validation_fraction": float(validation_fraction),
            "min_train_selected": int(min_train_selected),
            "min_train_loss_precision": float(min_train_loss_precision),
            "max_train_winner_count": int(max_train_winner_count),
            "min_validation_selected": int(min_validation_selected),
            "max_validation_winner_count": int(max_validation_winner_count),
            "min_final_selected": int(min_final_selected),
            "max_final_winner_count": int(max_final_winner_count),
            "max_sample_rows": int(max_sample_rows),
        },
        "policy_fields": {
            "numeric_gte": list(POST_SKIP_POLICY_NUMERIC_GTE_FIELDS),
            "numeric_lte": list(POST_SKIP_POLICY_NUMERIC_LTE_FIELDS),
        },
        "candidate_counts": {
            "paired_real_trade_count": len(outcomes),
            "post_skip_trade_count": sum(1 for row in outcomes if int(row.get("prior_skip_count") or 0) > 0),
            "train_rows": len(splits["train"]),
            "validation_rows": len(splits["validation"]),
            "final_rows": len(splits["final"]),
            "scanned_rules": len(train_results),
            "train_eligible_rules": len(train_eligible),
            "evaluated_candidates": len(evaluated_candidates),
        },
        "split_baselines": {
            split_name: _post_skip_split_metrics(split_rows)
            for split_name, split_rows in splits.items()
        },
        "feature_summaries": {
            split_name: _post_skip_feature_summaries(split_rows)
            for split_name, split_rows in splits.items()
        },
        "train_top_rules": train_results[:100],
        "train_eligible_rules": train_eligible[:100],
        "evaluated_candidates": evaluated_candidates[:100],
        "selected_candidate": selected,
        "strict_metric_coverage": _post_skip_metric_coverage(),
        "outcome_tier": outcome_tier,
        "decision": decision,
    }


def post_skip_followup_to_markdown_text(report: Mapping[str, Any]) -> str:
    params = _json_sanitize(report.get("parameters") or {})
    counts = _json_sanitize(report.get("candidate_counts") or {})
    baselines = _json_sanitize(report.get("split_baselines") or {})
    selected = _json_sanitize(report.get("selected_candidate") or {})
    lines = [
        "# Post-Skip Follow-Up Hazard Probe",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.",
        "",
        f"Outcome tier: `{report.get('outcome_tier')}`",
        f"Decision: `{report.get('decision')}`",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(params, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Candidate Counts",
        "",
        "```json",
        json.dumps(counts, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Split Baselines",
        "",
        "```json",
        json.dumps(baselines, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
        "## Selected Candidate",
        "",
        "```json",
        json.dumps(selected, default=_json_default, ensure_ascii=False, sort_keys=True, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


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
