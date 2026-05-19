from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from src.pipeline import reentry_probe


@dataclass(frozen=True)
class SignalEvent:
    token_address: str
    symbol: str
    timestamp: dt.datetime
    decision: str
    buy_probability: float
    pred_return: float
    volume_30s: float
    price_volatility: float
    age_seconds: float | None = None
    near_threshold_rescue_used: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def _first_present(*values: float | None) -> float | None:
    present = [float(value) for value in values if value is not None]
    return min(present) if present else None


def _before_stop(hit_time: float | None, stop_time: float | None) -> bool:
    return hit_time is not None and (stop_time is None or float(hit_time) < float(stop_time))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def iter_signal_events(rows: Iterable[dict[str, Any]]) -> Iterable[SignalEvent]:
    for row in rows:
        if str(row.get("action") or "").upper() != "SIGNAL_DECISION":
            continue
        decision = str(row.get("decision") or "").strip().lower()
        if decision not in {"queued", "rejected"}:
            continue
        token = reentry_probe.normalize_token(
            _first_non_empty(row.get("token"), row.get("token_address"), row.get("address"))
        )
        if not token:
            continue
        timestamp_value = _first_non_empty(row.get("time"), row.get("timestamp"), row.get("signal_time"))
        if timestamp_value is None:
            continue
        age_value = _first_non_empty(row.get("age_seconds"), row.get("token_age_seconds"))
        yield SignalEvent(
            token_address=token,
            symbol=str(row.get("symbol") or ""),
            timestamp=reentry_probe.parse_time(timestamp_value),
            decision=decision,
            buy_probability=reentry_probe.safe_float(
                _first_non_empty(row.get("buy_probability"), row.get("prob"), row.get("probability"), row.get("buy_prob"))
            ),
            pred_return=reentry_probe.safe_float(
                _first_non_empty(row.get("pred_return"), row.get("PredReturn"), row.get("predicted_return"))
            ),
            volume_30s=reentry_probe.safe_float(
                _first_non_empty(row.get("volume_30s"), row.get("entry_volume_30s"), row.get("volume"))
            ),
            price_volatility=reentry_probe.safe_float(
                _first_non_empty(row.get("price_volatility"), row.get("volatility"), row.get("price_vol"))
            ),
            age_seconds=None if age_value is None else reentry_probe.safe_float(age_value),
            near_threshold_rescue_used=_as_bool(row.get("near_threshold_rescue_used")),
            raw=dict(row),
        )


def _event_token(event: SignalEvent) -> str:
    return reentry_probe.normalize_token(event.token_address)


def _event_report(event: SignalEvent) -> dict[str, Any]:
    return {
        "token": _event_token(event),
        "symbol": event.symbol,
        "timestamp": event.timestamp,
        "decision": event.decision,
        "buy_probability": event.buy_probability,
        "pred_return": event.pred_return,
        "volume_30s": event.volume_30s,
        "price_volatility": event.price_volatility,
        "age_seconds": event.age_seconds,
        "near_threshold_rescue_used": event.near_threshold_rescue_used,
    }


def _windowed_history(
    *,
    anchor: SignalEvent,
    signal_history: Sequence[SignalEvent],
    lookback_seconds: float,
) -> list[SignalEvent]:
    window_start = anchor.timestamp - dt.timedelta(seconds=float(lookback_seconds))
    return sorted(
        [
            event
            for event in signal_history
            if _event_token(event) == _event_token(anchor)
            and window_start <= reentry_probe.parse_time(event.timestamp) < anchor.timestamp
        ],
        key=lambda event: event.timestamp,
    )


def _trajectory_metrics(
    *,
    anchor: SignalEvent,
    signal_history: Sequence[SignalEvent],
    lookback_seconds: float,
    min_volume_ramp_ratio: float,
    min_volume_ramp_delta: float,
    min_volatility_ramp_delta: float,
    min_pred_return_delta: float,
) -> dict[str, Any]:
    history = _windowed_history(anchor=anchor, signal_history=signal_history, lookback_seconds=lookback_seconds)
    baseline = history[0] if history else anchor
    volume_ramp_ratio = None
    if baseline.volume_30s > 0.0:
        volume_ramp_ratio = anchor.volume_30s / baseline.volume_30s
    volume_ramp_delta = anchor.volume_30s - baseline.volume_30s
    volatility_ramp_delta = anchor.price_volatility - baseline.price_volatility
    pred_return_delta = anchor.pred_return - baseline.pred_return
    volume_ramped = (
        volume_ramp_ratio is not None
        and float(volume_ramp_ratio) >= float(min_volume_ramp_ratio)
        and volume_ramp_delta >= float(min_volume_ramp_delta)
    )
    ramping_signal = (
        volume_ramped
        and volatility_ramp_delta >= float(min_volatility_ramp_delta)
        and pred_return_delta >= float(min_pred_return_delta)
    )
    return {
        "history_count": len(history),
        "baseline_time": baseline.timestamp,
        "latest_signal_time": anchor.timestamp,
        "volume_ramp_ratio": volume_ramp_ratio,
        "volume_ramp_delta": volume_ramp_delta,
        "volatility_ramp_delta": volatility_ramp_delta,
        "pred_return_delta": pred_return_delta,
        "volume_ramped": volume_ramped,
        "ramping_signal": ramping_signal,
    }


def _flow_event_time(event: Mapping[str, Any]) -> dt.datetime | None:
    timestamp = _first_non_empty(event.get("timestamp"), event.get("time"))
    if timestamp is None:
        return None
    return reentry_probe.parse_time(timestamp)


def _flow_event_side(event: Mapping[str, Any]) -> str:
    side = str(_first_non_empty(event.get("type"), event.get("side"), event.get("event")) or "").strip().lower()
    if side.startswith("buy"):
        return "buy"
    if side.startswith("sell"):
        return "sell"
    return side


def _flow_event_amount(event: Mapping[str, Any]) -> float:
    return reentry_probe.safe_float(
        _first_non_empty(
            event.get("bnb_amount"),
            event.get("amount_bnb"),
            event.get("value_bnb"),
            event.get("amount"),
        )
    )


def _flow_metrics(
    *,
    anchor_time: dt.datetime,
    flow_events: Sequence[dict[str, Any]],
    flow_window_seconds: float,
) -> dict[str, Any]:
    window_start = anchor_time - dt.timedelta(seconds=float(flow_window_seconds))
    buy_volume = 0.0
    sell_volume = 0.0
    used_events = 0
    for event in flow_events:
        event_time = _flow_event_time(event)
        if event_time is None or not (window_start <= event_time < anchor_time):
            continue
        amount = max(0.0, _flow_event_amount(event))
        side = _flow_event_side(event)
        if side == "buy":
            buy_volume += amount
            used_events += 1
        elif side == "sell":
            sell_volume += amount
            used_events += 1
    total = buy_volume + sell_volume
    return {
        "flow_window_seconds": flow_window_seconds,
        "flow_event_count": used_events,
        "pre_buy_volume_bnb": buy_volume,
        "pre_sell_volume_bnb": sell_volume,
        "pre_buy_pressure": (buy_volume / total) if total > 0.0 else 0.0,
    }


def _anchor_price_from_path(path: Sequence[reentry_probe.PricePoint], anchor_time: dt.datetime) -> float | None:
    ordered = sorted(path, key=lambda point: reentry_probe.parse_time(point.time))
    before = [point for point in ordered if reentry_probe.parse_time(point.time) <= anchor_time and float(point.price) > 0.0]
    if before:
        return float(before[-1].price)
    return None


def _configured_path_metrics(
    path: Sequence[reentry_probe.PricePoint],
    *,
    anchor_time: dt.datetime,
    anchor_price: float,
    horizon_seconds: float,
    take_profit_pct: float,
    stop_loss_pct: float,
) -> dict[str, Any]:
    take_time = None
    stop_time = None
    hits: list[tuple[float, str]] = []
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        seconds = (reentry_probe.parse_time(point.time) - anchor_time).total_seconds()
        if seconds < 0 or seconds > float(horizon_seconds):
            continue
        pct = (float(point.price) / float(anchor_price)) - 1.0
        if take_time is None and pct >= float(take_profit_pct):
            take_time = seconds
            hits.append((seconds, "take_profit"))
        if stop_time is None and pct <= float(stop_loss_pct):
            stop_time = seconds
            hits.append((seconds, "stop_loss"))
    return {
        "time_to_take_profit_seconds": take_time,
        "time_to_stop_loss_seconds": stop_time,
        "configured_first_barrier": sorted(hits, key=lambda item: item[0])[0][1] if hits else None,
    }


def _path_report(
    *,
    anchor_time: dt.datetime,
    price_path: Sequence[reentry_probe.PricePoint],
    horizon_seconds: float,
    take_profit_pct: float,
    stop_loss_pct: float,
) -> dict[str, Any]:
    path = list(price_path)
    anchor_price = _anchor_price_from_path(path, anchor_time)
    if anchor_price is None or anchor_price <= 0.0:
        return {
            "missing_path": True,
            "anchor_time": anchor_time,
            "anchor_price": None,
            "horizon_seconds": horizon_seconds,
            "post_anchor_diagnostic": True,
            "mfe_pct": None,
            "mae_pct": None,
            "time_to_plus_25_seconds": None,
            "time_to_plus_60_seconds": None,
            "time_to_minus_18_seconds": None,
            "time_to_minus_25_seconds": None,
            "first_barrier": None,
            "time_to_take_profit_seconds": None,
            "time_to_stop_loss_seconds": None,
            "configured_first_barrier": None,
        }
    standard = reentry_probe.path_metrics(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        horizon_seconds=horizon_seconds,
    )
    configured = _configured_path_metrics(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        horizon_seconds=horizon_seconds,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    return {
        "missing_path": False,
        "anchor_time": anchor_time,
        "anchor_price": anchor_price,
        "horizon_seconds": horizon_seconds,
        "post_anchor_diagnostic": True,
        **standard,
        **configured,
    }


def classify_flow_activation_candidate(
    *,
    anchor: SignalEvent,
    signal_history: Sequence[SignalEvent],
    price_path: Sequence[reentry_probe.PricePoint],
    flow_events: Sequence[dict[str, Any]],
    lookback_seconds: float = 30.0,
    flow_window_seconds: float = 30.0,
    horizon_seconds: float = 300.0,
    take_profit_pct: float = 0.25,
    stop_loss_pct: float = -0.18,
    min_volume_ramp_ratio: float = 1.35,
    min_volume_ramp_delta: float = 0.4,
    min_volatility_ramp_delta: float = 0.04,
    min_pred_return_delta: float = 10.0,
    min_pre_buy_pressure: float = 0.58,
) -> dict[str, Any]:
    trajectory = _trajectory_metrics(
        anchor=anchor,
        signal_history=signal_history,
        lookback_seconds=lookback_seconds,
        min_volume_ramp_ratio=min_volume_ramp_ratio,
        min_volume_ramp_delta=min_volume_ramp_delta,
        min_volatility_ramp_delta=min_volatility_ramp_delta,
        min_pred_return_delta=min_pred_return_delta,
    )
    flow = _flow_metrics(
        anchor_time=anchor.timestamp,
        flow_events=flow_events,
        flow_window_seconds=flow_window_seconds,
    )
    path = _path_report(
        anchor_time=anchor.timestamp,
        price_path=price_path,
        horizon_seconds=horizon_seconds,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )

    take_time = path.get("time_to_take_profit_seconds")
    stop_time = path.get("time_to_stop_loss_seconds")
    profit_before_stop = _before_stop(take_time, stop_time)
    stop_before_profit = stop_time is not None and (take_time is None or float(stop_time) < float(take_time))
    buy_pressure_ok = flow["pre_buy_pressure"] >= float(min_pre_buy_pressure)
    ramping_signal = bool(trajectory["ramping_signal"])

    if path.get("missing_path"):
        classification = "missing_path"
        accepted = False
        recommended_policy = "skip_missing_path"
        reason = "no_post_anchor_price_path"
    elif anchor.near_threshold_rescue_used and not profit_before_stop and (not buy_pressure_ok or not ramping_signal):
        classification = "dead_flow_rescue"
        accepted = False
        recommended_policy = "skip_near_rescue_without_flow"
        reason = "near_threshold_rescue_without_new_flow_or_profit"
    elif ramping_signal and not buy_pressure_ok and stop_before_profit:
        classification = "sell_pressure_fakeout"
        accepted = False
        recommended_policy = "skip_or_tight_exit"
        reason = "volume_ramp_met_seller_pressure_and_stop_first"
    elif ramping_signal and buy_pressure_ok and profit_before_stop:
        classification = "flow_activation_clean_profit"
        accepted = True
        recommended_policy = "allow_flow_activation"
        reason = "ramping_signal_buy_pressure_and_profit_first"
    else:
        classification = "flow_activation_uncertain"
        accepted = False
        recommended_policy = "skip"
        reason = "activation_evidence_incomplete"

    return {
        "token": _event_token(anchor),
        "symbol": anchor.symbol,
        "signal_time": anchor.timestamp,
        "decision": anchor.decision,
        "buy_probability": anchor.buy_probability,
        "pred_return": anchor.pred_return,
        "volume_30s": anchor.volume_30s,
        "price_volatility": anchor.price_volatility,
        "age_seconds": anchor.age_seconds,
        "near_threshold_rescue_used": anchor.near_threshold_rescue_used,
        "classification": classification,
        "accepted_by_probe": accepted,
        "accepted": accepted,
        "classification_basis": "retrospective_post_anchor_path",
        "live_gate_safe": False,
        "recommended_policy": recommended_policy,
        "recommended_policy_scope": "offline_probe_only",
        "trajectory": trajectory,
        "flow": flow,
        "path": path,
        "reason": reason,
    }


def flow_events_from_lifecycle(lifecycle: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not lifecycle:
        return []
    events: list[dict[str, Any]] = []
    for side, field_name in (("buy", "buys"), ("sell", "sells")):
        for row in lifecycle.get(field_name) or []:
            if not isinstance(row, Mapping):
                continue
            event = dict(row)
            event.setdefault("type", side)
            events.append(event)
    return events


def _row_key(row: Mapping[str, Any], *, side: str = "") -> tuple[Any, ...]:
    timestamp = _first_non_empty(row.get("timestamp"), row.get("time"))
    try:
        timestamp = reentry_probe.parse_time(timestamp).isoformat(sep=" ") if timestamp is not None else None
    except (TypeError, ValueError):
        pass
    return (
        side,
        row.get("type"),
        timestamp,
        _first_non_empty(row.get("bnb_amount"), row.get("amount_bnb"), row.get("value_bnb"), row.get("amount")),
        row.get("price"),
        row.get("account"),
        row.get("token_amount"),
    )


def _append_unique_rows(existing: list[Any], incoming: Iterable[Any], *, side: str = "") -> list[Any]:
    merged = list(existing)
    seen = {
        _row_key(row, side=side)
        for row in merged
        if isinstance(row, Mapping)
    }
    for row in incoming or []:
        if not isinstance(row, Mapping):
            continue
        key = _row_key(row, side=side)
        if key in seen:
            continue
        seen.add(key)
        merged.append(dict(row))
    return merged


def _coerce_lifecycle_map(lifecycles: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    coerced: dict[str, dict[str, Any]] = {}
    for token, lifecycle in (lifecycles or {}).items():
        normalized = reentry_probe.normalize_token(token)
        if not normalized:
            continue
        if isinstance(lifecycle, Mapping):
            copied = dict(lifecycle)
            copied["token_address"] = reentry_probe.normalize_token(
                _first_non_empty(copied.get("token_address"), copied.get("token"), normalized)
            )
            copied["price_history"] = list(copied.get("price_history") or [])
            coerced[normalized] = copied
        elif isinstance(lifecycle, Sequence) and not isinstance(lifecycle, (str, bytes, bytearray)):
            rows = []
            for row in lifecycle:
                if isinstance(row, Mapping):
                    copied_row = dict(row)
                    copied_row.setdefault("token_address", normalized)
                    rows.append(copied_row)
            coerced.update(extract_lifecycles_from_rows_for_flow(rows))
    return coerced


def extract_lifecycles_from_rows_for_flow(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    lifecycle_maps: list[dict[str, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        token = reentry_probe.normalize_token(_first_non_empty(row.get("token_address"), row.get("token")))
        if not token:
            continue
        copied = dict(row)
        copied["token_address"] = token
        copied["price_history"] = list(copied.get("price_history") or [])
        copied["buys"] = list(copied.get("buys") or [])
        copied["sells"] = list(copied.get("sells") or [])
        lifecycle_maps.append({token: copied})
    return _merge_lifecycle_maps_for_flow(*lifecycle_maps)


def _merge_lifecycle_maps_for_flow(*maps: Mapping[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for lifecycle_map in maps:
        for token, lifecycle in (lifecycle_map or {}).items():
            normalized = reentry_probe.normalize_token(token)
            if not normalized:
                continue
            existing = merged.get(normalized)
            if existing is None:
                copied = dict(lifecycle)
                copied["token_address"] = reentry_probe.normalize_token(
                    _first_non_empty(copied.get("token_address"), copied.get("token"), normalized)
                )
                copied["price_history"] = _append_unique_rows([], copied.get("price_history") or [])
                copied["buys"] = _append_unique_rows([], copied.get("buys") or [], side="buy")
                copied["sells"] = _append_unique_rows([], copied.get("sells") or [], side="sell")
                merged[normalized] = copied
                continue
            existing["price_history"] = _append_unique_rows(
                list(existing.get("price_history") or []),
                lifecycle.get("price_history") or [],
            )
            existing["buys"] = _append_unique_rows(
                list(existing.get("buys") or []),
                lifecycle.get("buys") or [],
                side="buy",
            )
            existing["sells"] = _append_unique_rows(
                list(existing.get("sells") or []),
                lifecycle.get("sells") or [],
                side="sell",
            )
            if lifecycle.get("symbol") and not existing.get("symbol"):
                existing["symbol"] = lifecycle.get("symbol")
    return merged


def merge_lifecycle_maps_for_flow(*maps: Mapping[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return _merge_lifecycle_maps_for_flow(*maps)


def _anchor_rank(event: SignalEvent) -> tuple[int, dt.datetime, float, float]:
    decision_rank = 1 if event.decision == "queued" else 0
    return (decision_rank, event.timestamp, event.buy_probability, event.pred_return)


def _classification_counts(candidates: Sequence[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(candidate.get("classification") for candidate in candidates)
    for name in (
        "flow_activation_clean_profit",
        "sell_pressure_fakeout",
        "dead_flow_rescue",
        "flow_activation_uncertain",
        "missing_path",
    ):
        counts.setdefault(name, 0)
    return dict(sorted(counts.items()))


def build_flow_activation_report(
    *,
    signal_events: Sequence[SignalEvent],
    lifecycle_by_token: Mapping[str, Any],
    collector_lifecycles: Mapping[str, Any] | None = None,
    since: dt.datetime | None = None,
    max_candidates: int | None = None,
    generated_at: dt.datetime | None = None,
    **thresholds: Any,
) -> dict[str, Any]:
    normalized_events_all = [
        event
        for event in signal_events
        if _event_token(event) and str(event.decision or "").lower() in {"queued", "rejected"}
    ]
    normalized_events_all = sorted(normalized_events_all, key=lambda event: event.timestamp)
    normalized_events = list(normalized_events_all)
    if since is not None:
        since_time = reentry_probe.parse_time(since)
        normalized_events = [event for event in normalized_events if event.timestamp >= since_time]

    events_by_token: dict[str, list[SignalEvent]] = {}
    for event in normalized_events_all:
        events_by_token.setdefault(_event_token(event), []).append(event)

    anchor_events_by_token: dict[str, list[SignalEvent]] = {}
    for event in normalized_events:
        anchor_events_by_token.setdefault(_event_token(event), []).append(event)
    anchors = [max(events, key=_anchor_rank) for events in anchor_events_by_token.values()]
    anchors = sorted(anchors, key=lambda event: event.timestamp)
    if max_candidates is not None:
        anchors = anchors[: max(0, int(max_candidates))]

    lifecycles = _merge_lifecycle_maps_for_flow(
        _coerce_lifecycle_map(collector_lifecycles),
        _coerce_lifecycle_map(lifecycle_by_token),
    )
    candidates = []
    diagnostics = {
        "missing_lifecycle_path": 0,
        "dropped_duplicate_signal_events": max(0, len(normalized_events) - len(anchors)),
    }
    for anchor in anchors:
        token = _event_token(anchor)
        lifecycle = lifecycles.get(token) or {}
        price_path = reentry_probe.price_path_from_lifecycle(lifecycle) if lifecycle else []
        if not price_path:
            diagnostics["missing_lifecycle_path"] += 1
        history = [event for event in events_by_token.get(token, []) if event.timestamp < anchor.timestamp]
        candidates.append(
            classify_flow_activation_candidate(
                anchor=anchor,
                signal_history=history,
                price_path=price_path,
                flow_events=flow_events_from_lifecycle(lifecycle),
                **thresholds,
            )
        )

    class_counts = _classification_counts(candidates)
    policy_counts = dict(sorted(Counter(candidate["recommended_policy"] for candidate in candidates).items()))
    accepted_count = sum(1 for candidate in candidates if candidate["accepted_by_probe"])
    queued_count = sum(1 for event in normalized_events if event.decision == "queued")
    rejected_count = sum(1 for event in normalized_events if event.decision == "rejected")

    return {
        "generated_at": generated_at
        or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "post_anchor_path_labels_are_retrospective": True,
            "safe_for_live_gate": False,
        },
        "parameters": {
            "since": reentry_probe.parse_time(since) if since is not None else None,
            "max_candidates": max_candidates,
            **thresholds,
        },
        "candidate_counts": {
            "signal_events": len(normalized_events),
            "queued_signal_events": queued_count,
            "rejected_signal_events": rejected_count,
            "flow_activation_candidates": len(candidates),
            "accepted_by_probe": accepted_count,
            "dropped_duplicate_signal_events": diagnostics["dropped_duplicate_signal_events"],
        },
        "summary": {
            "total_candidates": len(candidates),
            "accepted_by_probe": accepted_count,
            "classification_counts": class_counts,
            "policy_counts": policy_counts,
        },
        "diagnostics": diagnostics,
        "candidates": candidates,
        "signal_event_sample": [_event_report(event) for event in normalized_events[:50]],
    }


__all__ = [
    "SignalEvent",
    "build_flow_activation_report",
    "classify_flow_activation_candidate",
    "extract_lifecycles_from_rows_for_flow",
    "flow_events_from_lifecycle",
    "iter_signal_events",
    "merge_lifecycle_maps_for_flow",
    "to_json_text",
]
