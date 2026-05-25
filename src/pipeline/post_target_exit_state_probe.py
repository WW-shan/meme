from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence

from src.pipeline import flow_activation_probe, reentry_probe, time_to_barrier_probe
from src.pipeline import support_action_policy_probe


DECISION_TIME_FIELDS = support_action_policy_probe.DECISION_TIME_FIELDS
DECISION_FIELD_ALIASES = {
    "prob": ("buy_prob",),
    "pred_return": ("entry_score",),
}


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _trade_token(trade: Mapping[str, Any]) -> str:
    return reentry_probe.normalize_token(_first_non_empty(trade.get("token"), trade.get("token_address"), trade.get("address")))


def _trade_entry_time(trade: Mapping[str, Any]) -> dt.datetime | None:
    value = _first_non_empty(trade.get("entry_time"), trade.get("entry_signal_time"), trade.get("signal_time"), trade.get("time"))
    if value is None:
        return None
    try:
        return reentry_probe.parse_time(value)
    except (TypeError, ValueError):
        return None


def _trade_entry_price(trade: Mapping[str, Any]) -> float | None:
    value = _first_non_empty(trade.get("entry_price"), trade.get("open_price"), trade.get("price"))
    price = reentry_probe.safe_float(value, default=0.0)
    return price if price > 0.0 else None


def _decision_fields_from_trade(trade: Mapping[str, Any]) -> dict[str, Any]:
    fields = {
        field: trade.get(field)
        for field in DECISION_TIME_FIELDS
        if field in trade
    }
    for field, aliases in DECISION_FIELD_ALIASES.items():
        if field in fields:
            continue
        for alias in aliases:
            if alias in trade:
                fields[field] = trade.get(alias)
                break
    return fields


def _entry_time_flow_fields(lifecycle: Mapping[str, Any], entry_time: dt.datetime | None) -> dict[str, Any]:
    if entry_time is None:
        return {"flow_metrics_available": False}
    return time_to_barrier_probe._signal_time_flow_fields(dict(lifecycle or {}), entry_time)


def _pct_return(price: float, anchor_price: float) -> float:
    return ((float(price) / float(anchor_price)) - 1.0) * 100.0


def _ratio_return(price: float, anchor_price: float) -> float:
    return (float(price) / float(anchor_price)) - 1.0


def _threshold_hit(pct_return: float, threshold: float) -> bool:
    return pct_return >= float(threshold) if threshold >= 0.0 else pct_return <= float(threshold)


def _latest_return_at_or_before(
    path: Sequence[reentry_probe.PricePoint],
    *,
    anchor_price: float,
    target_time: dt.datetime,
) -> float | None:
    latest = None
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        point_time = reentry_probe.parse_time(point.time)
        if point_time <= target_time and float(point.price) > 0.0:
            latest = point
    if latest is None:
        return None
    return round(_pct_return(float(latest.price), anchor_price), 10)


def _post_target_window_returns(
    path: Sequence[reentry_probe.PricePoint],
    *,
    entry_price: float,
    entry_time: dt.datetime,
    target_hit_time: dt.datetime,
    horizon_seconds: float,
    post_target_windows: Sequence[float],
) -> dict[str, float | None]:
    horizon_end = entry_time + dt.timedelta(seconds=float(horizon_seconds))
    returns: dict[str, float | None] = {}
    for window in post_target_windows:
        key = f"{float(window):g}"
        target_time = min(target_hit_time + dt.timedelta(seconds=float(window)), horizon_end)
        returns[key] = _latest_return_at_or_before(
            path,
            anchor_price=entry_price,
            target_time=target_time,
        )
    return returns


def _flow_report(lifecycle: Mapping[str, Any], *, target_hit_time: dt.datetime, entry_time: dt.datetime) -> dict[str, Any]:
    events = flow_activation_probe.flow_events_from_lifecycle(lifecycle)
    if not events:
        return {
            "flow_window_seconds": max(0.0, (target_hit_time - entry_time).total_seconds()),
            "flow_event_count": 0,
            "pre_buy_volume_bnb": 0.0,
            "pre_sell_volume_bnb": 0.0,
            "pre_buy_pressure": 0.0,
        }
    window_seconds = max(0.0, (target_hit_time - entry_time).total_seconds())
    return flow_activation_probe._flow_metrics(
        anchor_time=target_hit_time,
        flow_events=events,
        flow_window_seconds=window_seconds,
    )


def score_trade_post_target_exit_state(
    trade: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    *,
    path: Sequence[reentry_probe.PricePoint] | None = None,
    target_pct: float = 0.25,
    continuation_pct: float = 0.60,
    collapse_pct: float = -0.18,
    horizon_seconds: float = 900.0,
    post_target_windows: Sequence[float] = (15.0, 30.0, 60.0, 120.0),
) -> dict[str, Any]:
    entry_time = _trade_entry_time(trade)
    entry_price = _trade_entry_price(trade)
    token = _trade_token(trade)
    base = {
        "token": token,
        "symbol": trade.get("symbol") or lifecycle.get("symbol"),
        "entry_time": entry_time,
        "entry_price": entry_price,
        "target_pct": target_pct,
        "continuation_pct": continuation_pct,
        "collapse_pct": collapse_pct,
        "horizon_seconds": horizon_seconds,
        "candidate_type": "accepted_trade_post_target_exit_state",
        **_decision_fields_from_trade(trade),
        **_entry_time_flow_fields(lifecycle, entry_time),
    }
    if entry_time is None or entry_price is None:
        return {
            **base,
            "classification": "missing_path",
            "recommended_policy": "no_action",
            "target_hit": False,
            "missing_path": True,
            "reason": "invalid_entry_anchor",
        }

    price_path = list(path) if path is not None else reentry_probe.price_path_from_lifecycle(dict(lifecycle or {}))
    price_path = sorted(price_path, key=lambda point: reentry_probe.parse_time(point.time))
    if not price_path:
        return {
            **base,
            "classification": "missing_path",
            "recommended_policy": "no_action",
            "target_hit": False,
            "missing_path": True,
            "reason": "no_price_path",
        }

    target_hit_time = None
    continuation_time = None
    collapse_time = None
    target_hit_return_pct = None
    mfe_pct = None
    mae_pct = None
    for point in price_path:
        point_time = reentry_probe.parse_time(point.time)
        seconds = (point_time - entry_time).total_seconds()
        if seconds < 0.0 or seconds > float(horizon_seconds) or float(point.price) <= 0.0:
            continue
        ratio = _ratio_return(float(point.price), entry_price)
        pct = round(ratio * 100.0, 10)
        mfe_pct = pct if mfe_pct is None else max(mfe_pct, pct)
        mae_pct = pct if mae_pct is None else min(mae_pct, pct)
        if target_hit_time is None and _threshold_hit(ratio, target_pct):
            target_hit_time = point_time
            target_hit_return_pct = pct
        if target_hit_time is None or point_time < target_hit_time:
            continue
        if continuation_time is None and _threshold_hit(ratio, continuation_pct):
            continuation_time = point_time
        if collapse_time is None and _threshold_hit(ratio, collapse_pct):
            collapse_time = point_time

    if target_hit_time is None:
        return {
            **base,
            "classification": "target_not_hit",
            "recommended_policy": "no_action",
            "target_hit": False,
            "missing_path": False,
            "mfe_pct": mfe_pct,
            "mae_pct": mae_pct,
            "time_to_target_seconds": None,
            "time_to_continuation_seconds": None,
            "time_to_post_target_collapse_seconds": None,
        }

    target_seconds = (target_hit_time - entry_time).total_seconds()
    continuation_seconds = (continuation_time - entry_time).total_seconds() if continuation_time is not None else None
    collapse_seconds = (collapse_time - entry_time).total_seconds() if collapse_time is not None else None
    if collapse_time is not None and (continuation_time is None or collapse_time < continuation_time):
        classification = "post_target_collapse"
        recommended_policy = "lock_profit"
    elif continuation_time is not None:
        classification = "post_target_continuation"
        recommended_policy = "continue_hold"
    else:
        classification = "post_target_unresolved"
        recommended_policy = "monitor_after_target"

    return {
        **base,
        "classification": classification,
        "recommended_policy": recommended_policy,
        "target_hit": True,
        "missing_path": False,
        "target_hit_time": target_hit_time,
        "target_hit_return_pct": target_hit_return_pct,
        "mfe_pct": mfe_pct,
        "mae_pct": mae_pct,
        "time_to_target_seconds": target_seconds,
        "time_to_continuation_seconds": continuation_seconds,
        "time_to_post_target_collapse_seconds": collapse_seconds,
        "post_target_window_returns_pct": _post_target_window_returns(
            price_path,
            entry_price=entry_price,
            entry_time=entry_time,
            target_hit_time=target_hit_time,
            horizon_seconds=horizon_seconds,
            post_target_windows=post_target_windows,
        ),
        "flow": _flow_report(lifecycle, target_hit_time=target_hit_time, entry_time=entry_time),
    }


def build_probe_report(
    *,
    trades: Iterable[Mapping[str, Any]],
    lifecycles: Mapping[str, Mapping[str, Any]],
    generated_at: dt.datetime | None = None,
    target_pct: float = 0.25,
    continuation_pct: float = 0.60,
    collapse_pct: float = -0.18,
    horizon_seconds: float = 900.0,
    post_target_windows: Sequence[float] = (15.0, 30.0, 60.0, 120.0),
) -> dict[str, Any]:
    trade_rows = [dict(trade) for trade in trades or []]
    normalized_lifecycles = {
        reentry_probe.normalize_token(token): dict(lifecycle)
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    candidates = [
        score_trade_post_target_exit_state(
            trade,
            normalized_lifecycles.get(_trade_token(trade), {}),
            target_pct=target_pct,
            continuation_pct=continuation_pct,
            collapse_pct=collapse_pct,
            horizon_seconds=horizon_seconds,
            post_target_windows=post_target_windows,
        )
        for trade in trade_rows
    ]
    class_counts = Counter(candidate["classification"] for candidate in candidates)
    policy_counts = Counter(candidate["recommended_policy"] for candidate in candidates)
    for name in ("missing_path", "target_not_hit", "post_target_collapse", "post_target_continuation", "post_target_unresolved"):
        class_counts.setdefault(name, 0)
    for name in ("no_action", "lock_profit", "continue_hold", "monitor_after_target"):
        policy_counts.setdefault(name, 0)

    return {
        "generated_at": generated_at
        or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
        },
        "parameters": {
            "target_pct": target_pct,
            "continuation_pct": continuation_pct,
            "collapse_pct": collapse_pct,
            "horizon_seconds": horizon_seconds,
            "post_target_windows": list(post_target_windows),
            "position_fraction": 0.10,
            "max_open_positions": 8,
        },
        "candidate_counts": {
            "trade_log_rows": len(trade_rows),
            "scored_candidates": len(candidates),
            "target_hit_candidates": sum(1 for candidate in candidates if candidate.get("target_hit")),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "policy_counts": dict(sorted(policy_counts.items())),
        "candidate_sample": candidates[:100],
    }
