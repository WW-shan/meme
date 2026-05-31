from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.model.action_policy_router_runtime import ActionPolicyRouterRuntime
from src.pipeline import reentry_probe


ANALYSIS_TZ = reentry_probe.ANALYSIS_TZ
SIGNAL_METADATA_KEYS = {
    "action",
    "decision",
    "reason",
    "symbol",
    "time",
    "token",
    "token_address",
    "features_hash",
    "entry_ranking_mode",
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    resolved = Path(path)
    if not resolved.exists():
        return rows
    with resolved.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _to_epoch_seconds(value: Any) -> float:
    parsed = reentry_probe.parse_time(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ANALYSIS_TZ)
    return float(parsed.timestamp())


def _optional_time(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    try:
        return reentry_probe.parse_time(value)
    except (TypeError, ValueError):
        return None


def _in_time_window(
    row: Mapping[str, Any],
    *,
    since_time: dt.datetime | None,
    until_time: dt.datetime | None,
) -> bool:
    parsed = _optional_time(row.get("time"))
    if parsed is None:
        return False
    if since_time is not None and parsed < since_time:
        return False
    if until_time is not None and parsed > until_time:
        return False
    return True


def _numeric_feature_map(row: Mapping[str, Any]) -> dict[str, Any]:
    features: dict[str, Any] = {}
    for key, value in row.items():
        if key in SIGNAL_METADATA_KEYS:
            continue
        if isinstance(value, bool):
            features[key] = value
            continue
        parsed = _finite_float(value)
        if parsed is not None:
            features[key] = parsed
    return features


def _runtime_param_from_rows(
    rows: Sequence[Mapping[str, Any]],
    key: str,
    *,
    fallback: Any = None,
) -> Any:
    for row in rows:
        value = row.get(key)
        if value is not None:
            return value
    return fallback


def runtime_params_from_signal_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    primary_min_prob: float = 0.98,
    router_min_prob: float | None = None,
    router_max_pred_return: float | None = None,
) -> dict[str, Any]:
    params = {
        "buy_threshold": float(primary_min_prob),
        "min_entry_score": _runtime_param_from_rows(rows, "min_pred_return", fallback=35.0),
        "min_entry_volume_30s": _runtime_param_from_rows(rows, "min_entry_volume_30s", fallback=1.5),
        "min_entry_price_volatility": _runtime_param_from_rows(
            rows,
            "min_entry_price_volatility",
            fallback=0.1,
        ),
        "buy_near_threshold_min_prob": _runtime_param_from_rows(
            rows,
            "buy_near_threshold_min_prob",
            fallback=0.94,
        ),
        "buy_near_min_pred_return": _runtime_param_from_rows(
            rows,
            "buy_near_min_pred_return",
            fallback=32.0,
        ),
        "buy_near_min_entry_volume_30s": _runtime_param_from_rows(
            rows,
            "buy_near_min_entry_volume_30s",
            fallback=1.25,
        ),
        "buy_near_min_entry_price_volatility": _runtime_param_from_rows(
            rows,
            "buy_near_min_entry_price_volatility",
            fallback=0.08,
        ),
        "buy_near_min_age_seconds": _runtime_param_from_rows(
            rows,
            "buy_near_min_age_seconds",
            fallback=0.0,
        ),
    }
    if router_min_prob is not None:
        params["buy_action_policy_router_min_prob"] = float(router_min_prob)
    if router_max_pred_return is not None:
        params["buy_action_policy_router_max_pred_return"] = float(router_max_pred_return)
    return params


def filter_signal_decisions(
    rows: Iterable[Mapping[str, Any]],
    *,
    since: str | None = None,
    until: str | None = None,
    decisions: Sequence[str] = ("queued", "rejected"),
) -> list[dict[str, Any]]:
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    allowed = {str(item).lower() for item in decisions}
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if row.get("action") != "SIGNAL_DECISION":
            continue
        decision = str(row.get("decision") or "").lower()
        if decision not in allowed:
            continue
        if not _in_time_window(row, since_time=since_time, until_time=until_time):
            continue
        filtered.append(dict(row))
    filtered.sort(key=lambda row: reentry_probe.parse_time(row.get("time")))
    return filtered


def _trade_anchor_epoch(opened: Mapping[str, Any]) -> float | None:
    for key in ("entry_signal_time", "signal_time", "time"):
        if opened.get(key) is not None:
            try:
                return _to_epoch_seconds(opened.get(key))
            except (TypeError, ValueError):
                continue
    return None


def _trade_sort_epoch(row: Mapping[str, Any]) -> float:
    candidates = [row.get("time"), row.get("entry_signal_time"), row.get("signal_time"), row.get("sell_started_at")]
    for value in candidates:
        if value is None:
            continue
        try:
            return _to_epoch_seconds(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _pair_real_trade_rows(trade_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    open_by_token: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pairs: list[dict[str, Any]] = []
    real_rows = [dict(row) for row in trade_rows if row.get("is_real_trade")]
    for row in sorted(real_rows, key=_trade_sort_epoch):
        action = str(row.get("action") or "").upper()
        token = reentry_probe.normalize_token(row.get("token") or row.get("token_address"))
        if not token:
            continue
        parsed = dict(row)
        parsed["token"] = token
        if action == "OPEN":
            open_by_token[token].append(parsed)
        elif action == "CLOSE":
            opens = open_by_token.get(token)
            if not opens:
                continue
            opened = opens.pop(0)
            pairs.append(
                {
                    "token": token,
                    "symbol": parsed.get("symbol") or opened.get("symbol"),
                    "open": opened,
                    "close": parsed,
                }
            )
    return pairs


def real_trade_outcomes(trade_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pairs = _pair_real_trade_rows(trade_rows)
    outcomes: list[dict[str, Any]] = []
    for pair in pairs:
        opened = dict(pair.get("open") or {})
        close = dict(pair.get("close") or {})
        token = reentry_probe.normalize_token(pair.get("token") or opened.get("token") or close.get("token"))
        anchor_epoch = _trade_anchor_epoch(opened)
        if not token or anchor_epoch is None:
            continue
        net_profit = _finite_float(close.get("net_profit_bnb"))
        if net_profit is None:
            net_profit = _finite_float(close.get("net_profit"))
        outcomes.append(
            {
                "token": token,
                "symbol": close.get("symbol") or opened.get("symbol") or pair.get("symbol"),
                "entry_signal_time": opened.get("entry_signal_time") or opened.get("signal_time") or opened.get("time"),
                "entry_signal_epoch": anchor_epoch,
                "entry_price": _finite_float(opened.get("entry_price") or close.get("entry_price")),
                "open_time": opened.get("time"),
                "close_time": close.get("time"),
                "close_reason": close.get("reason"),
                "hold_duration_seconds": _finite_float(close.get("hold_duration")),
                "net_profit_bnb": float(net_profit or 0.0),
                "is_win": float(net_profit or 0.0) > 0.0,
            }
        )
    return outcomes


def _match_trade_outcome(
    signal: Mapping[str, Any],
    outcomes_by_token: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    max_match_seconds: float,
) -> dict[str, Any] | None:
    token = reentry_probe.normalize_token(signal.get("token") or signal.get("token_address"))
    if not token:
        return None
    signal_epoch = _to_epoch_seconds(signal.get("time"))
    best: tuple[float, Mapping[str, Any]] | None = None
    for outcome in outcomes_by_token.get(token, ()):
        anchor_epoch = _finite_float(outcome.get("entry_signal_epoch"))
        if anchor_epoch is None:
            continue
        delta = abs(signal_epoch - anchor_epoch)
        if delta <= float(max_match_seconds) and (best is None or delta < best[0]):
            best = (delta, outcome)
    if best is None:
        return None
    matched = dict(best[1])
    matched["signal_match_delta_seconds"] = best[0]
    return matched


def _counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _route_probabilities(row: Mapping[str, Any]) -> dict[str, float]:
    probabilities = row.get("route_probabilities")
    if not isinstance(probabilities, Mapping):
        return {}
    parsed = {}
    for key, value in probabilities.items():
        finite = _finite_float(value)
        if finite is not None:
            parsed[str(key)] = finite
    return parsed


def _sample_row(row: Mapping[str, Any]) -> dict[str, Any]:
    sampled = {
        "time": row.get("time"),
        "token": row.get("token"),
        "symbol": row.get("symbol"),
        "decision": row.get("decision"),
        "reason": row.get("reason"),
        "prob": row.get("prob"),
        "pred_return": row.get("pred_return"),
        "volume_30s": row.get("volume_30s"),
        "price_volatility": row.get("price_volatility"),
        "token_age_seconds": row.get("token_age_seconds"),
        "shadow_used": row.get("shadow_used"),
        "shadow_route": row.get("shadow_route"),
        "shadow_confidence": row.get("shadow_confidence"),
        "shadow_reason": row.get("shadow_reason"),
        "shadow_live_feature_count": row.get("shadow_live_feature_count"),
        "route_probabilities": _route_probabilities(row),
    }
    if row.get("matched_trade"):
        sampled["matched_trade"] = row["matched_trade"]
    return sampled


def _matched_trade_key(row: Mapping[str, Any]) -> str | None:
    matched = row.get("matched_trade")
    if not isinstance(matched, Mapping):
        return None
    token = str(matched.get("token") or row.get("token") or "")
    entry_signal_time = str(matched.get("entry_signal_time") or "")
    if not token or not entry_signal_time:
        return None
    return f"{token}|{entry_signal_time}"


def _limited_samples(rows: Sequence[Mapping[str, Any]], max_sample_rows: int) -> list[dict[str, Any]]:
    limit = int(max_sample_rows)
    sample_rows = list(rows) if limit == 0 else list(rows[: max(0, limit)])
    return [_sample_row(row) for row in sample_rows]


def _first_threshold_seconds(
    path: Sequence[reentry_probe.PricePoint],
    *,
    anchor_time: dt.datetime,
    anchor_price: float,
    threshold_pct: float,
    horizon_seconds: float,
) -> float | None:
    threshold_pct = float(threshold_pct)
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        seconds = (reentry_probe.parse_time(point.time) - anchor_time).total_seconds()
        if seconds < 0.0 or seconds > float(horizon_seconds):
            continue
        pct = ((float(point.price) / float(anchor_price)) - 1.0) * 100.0
        if threshold_pct >= 0.0 and pct >= threshold_pct:
            return float(seconds)
        if threshold_pct < 0.0 and pct <= threshold_pct:
            return float(seconds)
    return None


def activation_path_outcome(
    *,
    matched_trade: Mapping[str, Any],
    lifecycles: Mapping[str, Mapping[str, Any]],
    activation_pct: float = 35.0,
    release_pct: float = 75.0,
    stop_loss_pct: float = -18.0,
    hard_stop_pct: float = -25.0,
) -> dict[str, Any]:
    token = reentry_probe.normalize_token(matched_trade.get("token"))
    lifecycle = lifecycles.get(token) or {}
    path = reentry_probe.price_path_from_lifecycle(dict(lifecycle)) if lifecycle else []
    anchor_price = _finite_float(matched_trade.get("entry_price"))
    anchor_time = _optional_time(matched_trade.get("open_time"))
    close_time = _optional_time(matched_trade.get("close_time"))
    hold_seconds = _finite_float(matched_trade.get("hold_duration_seconds"))
    if hold_seconds is None and anchor_time is not None and close_time is not None:
        hold_seconds = max(0.0, (close_time - anchor_time).total_seconds())
    base = {
        "token": token,
        "symbol": matched_trade.get("symbol"),
        "close_reason": matched_trade.get("close_reason"),
        "net_profit_bnb": _finite_float(matched_trade.get("net_profit_bnb")) or 0.0,
        "is_win": bool(matched_trade.get("is_win")),
        "entry_price": anchor_price,
        "open_time": matched_trade.get("open_time"),
        "close_time": matched_trade.get("close_time"),
        "hold_duration_seconds": hold_seconds,
        "path_point_count": len(path),
    }
    if not path or anchor_price is None or anchor_price <= 0.0 or anchor_time is None:
        return {
            **base,
            "outcome": "missing_path_or_anchor",
            "mfe_pct": None,
            "mae_pct": None,
            "time_to_activation_seconds": None,
            "time_to_release_seconds": None,
            "time_to_stop_seconds": None,
            "time_to_hard_stop_seconds": None,
        }

    horizon_seconds = max(1.0, float(hold_seconds or 0.0))
    changes: list[float] = []
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        seconds = (reentry_probe.parse_time(point.time) - anchor_time).total_seconds()
        if seconds < 0.0 or seconds > horizon_seconds:
            continue
        changes.append(((float(point.price) / float(anchor_price)) - 1.0) * 100.0)
    activation_time = _first_threshold_seconds(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        threshold_pct=float(activation_pct),
        horizon_seconds=horizon_seconds,
    )
    release_time = _first_threshold_seconds(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        threshold_pct=float(release_pct),
        horizon_seconds=horizon_seconds,
    )
    stop_time = _first_threshold_seconds(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        threshold_pct=float(stop_loss_pct),
        horizon_seconds=horizon_seconds,
    )
    hard_stop_time = _first_threshold_seconds(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        threshold_pct=float(hard_stop_pct),
        horizon_seconds=horizon_seconds,
    )

    if activation_time is None:
        outcome = "never_activated_win" if bool(matched_trade.get("is_win")) else "never_activated_loss"
    elif stop_time is not None and stop_time < activation_time:
        outcome = "stop_before_activation"
    elif release_time is not None and (stop_time is None or release_time <= stop_time):
        outcome = "activated_released"
    elif stop_time is not None:
        outcome = "activated_then_stop"
    elif bool(matched_trade.get("is_win")):
        outcome = "activated_profitable_no_release"
    else:
        outcome = "activated_no_release_giveback"

    return {
        **base,
        "outcome": outcome,
        "activation_pct": float(activation_pct),
        "release_pct": float(release_pct),
        "stop_loss_pct": float(stop_loss_pct),
        "hard_stop_pct": float(hard_stop_pct),
        "mfe_pct": max(changes) if changes else None,
        "mae_pct": min(changes) if changes else None,
        "time_to_activation_seconds": activation_time,
        "time_to_release_seconds": release_time,
        "time_to_stop_seconds": stop_time,
        "time_to_hard_stop_seconds": hard_stop_time,
    }


def build_activation_shadow_report(
    *,
    signal_rows: Sequence[Mapping[str, Any]],
    trade_rows: Sequence[Mapping[str, Any]],
    lifecycles: Mapping[str, Mapping[str, Any]],
    runtime: ActionPolicyRouterRuntime,
    since: str | None = None,
    until: str | None = None,
    active_model: str | None = None,
    primary_min_prob: float = 0.98,
    decisions: Sequence[str] = ("queued", "rejected"),
    max_match_seconds: float = 20.0,
    max_sample_rows: int = 100,
    activation_pct: float = 35.0,
    release_pct: float = 75.0,
    stop_loss_pct: float = -18.0,
    hard_stop_pct: float = -25.0,
) -> dict[str, Any]:
    base_report = build_live_shadow_report(
        signal_rows=signal_rows,
        trade_rows=trade_rows,
        runtime=runtime,
        since=since,
        until=until,
        active_model=active_model,
        primary_min_prob=primary_min_prob,
        decisions=decisions,
        max_match_seconds=max_match_seconds,
        max_sample_rows=0,
    )
    matched_rows = [
        row
        for row in base_report.get("queued_sample", [])
        if row.get("shadow_used") and isinstance(row.get("matched_trade"), Mapping)
    ]
    outcomes = [
        {
            "signal": {
                "time": row.get("time"),
                "token": row.get("token"),
                "symbol": row.get("symbol"),
                "prob": row.get("prob"),
                "pred_return": row.get("pred_return"),
                "shadow_confidence": row.get("shadow_confidence"),
            },
            "path": activation_path_outcome(
                matched_trade=row.get("matched_trade") or {},
                lifecycles=lifecycles,
                activation_pct=activation_pct,
                release_pct=release_pct,
                stop_loss_pct=stop_loss_pct,
                hard_stop_pct=hard_stop_pct,
            ),
        }
        for row in matched_rows
    ]
    outcome_counts = _counter_dict(outcome.get("path", {}).get("outcome") for outcome in outcomes)
    matched_net_profit = sum(float(outcome.get("path", {}).get("net_profit_bnb") or 0.0) for outcome in outcomes)
    release_count = sum(1 for outcome in outcomes if outcome.get("path", {}).get("time_to_release_seconds") is not None)
    activation_count = sum(1 for outcome in outcomes if outcome.get("path", {}).get("time_to_activation_seconds") is not None)
    activated_stop_count = sum(1 for outcome in outcomes if outcome.get("path", {}).get("outcome") == "activated_then_stop")
    stop_before_activation_count = sum(
        1 for outcome in outcomes if outcome.get("path", {}).get("outcome") == "stop_before_activation"
    )
    go_status = "insufficient_activation_shadow_support"
    if len(outcomes) >= 3:
        go_status = "activation_shadow_support"
    if activated_stop_count and release_count:
        go_status = "mixed_activation_shadow_support"

    sample_limit = int(max_sample_rows)
    emitted_outcomes = outcomes if sample_limit == 0 else outcomes[: max(0, sample_limit)]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "description": "Activation-aware counterfactual shadow attribution; no live config or runtime decisions changed.",
        },
        "active_model": active_model,
        "since": since,
        "until": until,
        "parameters": {
            "primary_min_prob": float(primary_min_prob),
            "decisions": list(decisions),
            "max_match_seconds": float(max_match_seconds),
            "max_sample_rows": int(max_sample_rows),
            "activation_pct": float(activation_pct),
            "release_pct": float(release_pct),
            "stop_loss_pct": float(stop_loss_pct),
            "hard_stop_pct": float(hard_stop_pct),
        },
        "base_shadow_summary": base_report.get("summary"),
        "base_shadow_parameters": base_report.get("parameters"),
        "router_runtime": base_report.get("router_runtime"),
        "summary": {
            "queued_shadow_used_matched_count": len(outcomes),
            "queued_shadow_used_matched_net_profit_bnb": matched_net_profit,
            "activation_hit_count": activation_count,
            "release_hit_count": release_count,
            "activated_then_stop_count": activated_stop_count,
            "stop_before_activation_count": stop_before_activation_count,
            "outcome_counts": outcome_counts,
            "unemitted_outcome_count": max(0, len(outcomes) - len(emitted_outcomes)),
        },
        "go_no_go": {
            "status": go_status,
            "reason": (
                "Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; "
                "runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review."
            ),
            "safe_for_live_switch": False,
        },
        "outcomes": emitted_outcomes,
    }


def build_live_shadow_report(
    *,
    signal_rows: Sequence[Mapping[str, Any]],
    trade_rows: Sequence[Mapping[str, Any]],
    runtime: ActionPolicyRouterRuntime,
    since: str | None = None,
    until: str | None = None,
    active_model: str | None = None,
    primary_min_prob: float = 0.98,
    decisions: Sequence[str] = ("queued", "rejected"),
    max_match_seconds: float = 20.0,
    max_sample_rows: int = 100,
) -> dict[str, Any]:
    signals = filter_signal_decisions(signal_rows, since=since, until=until, decisions=decisions)
    runtime_params = runtime_params_from_signal_rows(signals, primary_min_prob=primary_min_prob)
    runtime_params_for_shadow = dict(getattr(runtime, "runtime_params", {}) or runtime_params)
    outcomes = real_trade_outcomes(trade_rows)
    outcomes_by_token: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for outcome in outcomes:
        outcomes_by_token[str(outcome.get("token") or "")].append(outcome)

    rows: list[dict[str, Any]] = []
    for index, signal in enumerate(signals):
        token = reentry_probe.normalize_token(signal.get("token") or signal.get("token_address"))
        features = _numeric_feature_map(signal)
        age_seconds = _finite_float(signal.get("token_age_seconds")) or 0.0
        sample_epoch = _to_epoch_seconds(signal.get("time"))
        route_decision = runtime.predict(
            lifecycle={
                "token_address": token,
                "create_timestamp": sample_epoch - age_seconds,
                "last_update": sample_epoch,
            },
            features=features,
            prob=float(_finite_float(signal.get("prob")) or 0.0),
            pred_return=_finite_float(signal.get("pred_return")),
            token_address=token,
            sample_time=sample_epoch,
            create_timestamp=sample_epoch - age_seconds,
        )
        matched_trade = _match_trade_outcome(
            signal,
            outcomes_by_token,
            max_match_seconds=max_match_seconds,
        )
        row = {
            "index": int(index),
            "time": signal.get("time"),
            "token": token,
            "symbol": signal.get("symbol"),
            "decision": str(signal.get("decision") or ""),
            "reason": signal.get("reason"),
            "prob": _finite_float(signal.get("prob")),
            "pred_return": _finite_float(signal.get("pred_return")),
            "volume_30s": _finite_float(signal.get("volume_30s")),
            "price_volatility": _finite_float(signal.get("price_volatility")),
            "token_age_seconds": _finite_float(signal.get("token_age_seconds")),
            "feature_count": int(_finite_float(signal.get("feature_count")) or len(features)),
            "shadow_used": bool(route_decision.get("used")),
            "shadow_route": route_decision.get("route"),
            "shadow_confidence": _finite_float(route_decision.get("confidence")),
            "shadow_reason": route_decision.get("reason"),
            "shadow_live_feature_count": int(route_decision.get("live_feature_count") or 0),
            "route_probabilities": route_decision.get("route_probabilities") or {},
        }
        if matched_trade is not None:
            row["matched_trade"] = matched_trade
        rows.append(row)

    matched_rows = [row for row in rows if row.get("matched_trade")]
    queued_rows = [row for row in rows if str(row.get("decision")).lower() == "queued"]
    queued_matched_rows = [row for row in queued_rows if row.get("matched_trade")]
    used_rows = [row for row in rows if row.get("shadow_used")]
    queued_used_rows = [row for row in queued_rows if row.get("shadow_used")]
    queued_used_matched = [row for row in queued_matched_rows if row.get("shadow_used")]
    queued_not_used_matched = [row for row in queued_matched_rows if not row.get("shadow_used")]
    unique_matched_trade_keys = {key for key in (_matched_trade_key(row) for row in matched_rows) if key}

    def _profit_sum(sample: Sequence[Mapping[str, Any]]) -> float:
        return sum(float((row.get("matched_trade") or {}).get("net_profit_bnb") or 0.0) for row in sample)

    support_status = "insufficient_shadow_support"
    if queued_used_matched:
        support_status = "has_matched_shadow_route"
    if len(queued_used_matched) >= 3:
        support_status = "candidate_shadow_support"

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "description": "Counterfactual live shadow evaluator; no live config or runtime decisions changed.",
        },
        "active_model": active_model,
        "since": since,
        "until": until,
        "parameters": {
            "primary_min_prob": float(primary_min_prob),
            "decisions": list(decisions),
            "max_match_seconds": float(max_match_seconds),
            "max_sample_rows": int(max_sample_rows),
            "runtime_params_from_live_signals": runtime_params,
            "runtime_params_for_shadow": runtime_params_for_shadow,
        },
        "router_runtime": {
            "enabled": bool(runtime.enabled),
            "min_confidence": float(runtime.min_confidence),
            "min_live_features": int(runtime.min_live_features),
            "route_names": list(runtime.route_names),
            "feature_count": len(runtime.feature_names),
            "runtime_params": runtime_params_for_shadow,
            "metadata": runtime.metadata,
        },
        "summary": {
            "signal_count": len(rows),
            "queued_signal_count": len(queued_rows),
            "matched_trade_count": len(matched_rows),
            "unique_matched_trade_count": len(unique_matched_trade_keys),
            "queued_matched_trade_count": len(queued_matched_rows),
            "shadow_used_count": len(used_rows),
            "queued_shadow_used_count": len(queued_used_rows),
            "queued_shadow_used_matched_count": len(queued_used_matched),
            "queued_shadow_used_unmatched_count": len(queued_used_rows) - len(queued_used_matched),
            "queued_shadow_used_matched_net_profit_bnb": _profit_sum(queued_used_matched),
            "queued_shadow_not_used_matched_count": len(queued_not_used_matched),
            "queued_shadow_not_used_matched_net_profit_bnb": _profit_sum(queued_not_used_matched),
            "decision_counts": _counter_dict(row.get("decision") for row in rows),
            "signal_reason_counts": _counter_dict(row.get("reason") for row in rows),
            "shadow_route_counts": _counter_dict(row.get("shadow_route") for row in rows),
            "shadow_reason_counts": _counter_dict(row.get("shadow_reason") for row in rows),
            "matched_trade_reason_counts": _counter_dict(
                (row.get("matched_trade") or {}).get("close_reason") for row in matched_rows
            ),
        },
        "go_no_go": {
            "status": support_status,
            "reason": (
                "Read-only shadow evidence; promote only after enough matched live shadow routes "
                "and replay/stress evidence support the same route."
            ),
            "safe_for_live_switch": False,
        },
        "sample": _limited_samples(rows, int(max_sample_rows)),
        "queued_sample": _limited_samples(queued_rows, int(max_sample_rows)),
        "shadow_used_sample": _limited_samples(used_rows, int(max_sample_rows)),
    }
    return report


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"


def to_markdown_text(report: Mapping[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report, Mapping) else {}
    go_no_go = report.get("go_no_go", {}) if isinstance(report, Mapping) else {}
    runtime = report.get("router_runtime", {}) if isinstance(report, Mapping) else {}
    lines = [
        "# Action Policy Live Shadow Report",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.",
        "",
        "## Runtime",
        "",
        f"- Active model: `{report.get('active_model')}`",
        f"- Router enabled for scoring: `{runtime.get('enabled')}`",
        f"- Route names: `{runtime.get('route_names')}`",
        f"- Feature count: `{runtime.get('feature_count')}`",
        f"- Min confidence: `{runtime.get('min_confidence')}`",
        f"- Min live features: `{runtime.get('min_live_features')}`",
        f"- Runtime params: `{runtime.get('runtime_params')}`",
        "",
        "## Summary",
        "",
        f"- Signal count: `{summary.get('signal_count')}`",
        f"- Queued signal count: `{summary.get('queued_signal_count')}`",
        f"- Matched signal rows: `{summary.get('matched_trade_count')}`",
        f"- Unique matched live trades: `{summary.get('unique_matched_trade_count')}`",
        f"- Shadow-used signals: `{summary.get('shadow_used_count')}`",
        f"- Queued shadow-used signals: `{summary.get('queued_shadow_used_count')}`",
        f"- Queued shadow-used matched trades: `{summary.get('queued_shadow_used_matched_count')}`",
        f"- Queued shadow-used unmatched signals: `{summary.get('queued_shadow_used_unmatched_count')}`",
        f"- Queued shadow-used matched net profit BNB: `{summary.get('queued_shadow_used_matched_net_profit_bnb')}`",
        f"- Queued shadow-not-used matched net profit BNB: `{summary.get('queued_shadow_not_used_matched_net_profit_bnb')}`",
        "",
        "## Counts",
        "",
        f"- Decisions: `{summary.get('decision_counts')}`",
        f"- Signal reasons: `{summary.get('signal_reason_counts')}`",
        f"- Shadow routes: `{summary.get('shadow_route_counts')}`",
        f"- Shadow reasons: `{summary.get('shadow_reason_counts')}`",
        f"- Matched trade reasons: `{summary.get('matched_trade_reason_counts')}`",
        "",
        "## Decision",
        "",
        f"`{go_no_go.get('status')}`: {go_no_go.get('reason')}",
    ]
    return "\n".join(lines) + "\n"


def activation_to_markdown_text(report: Mapping[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report, Mapping) else {}
    go_no_go = report.get("go_no_go", {}) if isinstance(report, Mapping) else {}
    runtime = report.get("router_runtime", {}) if isinstance(report, Mapping) else {}
    lines = [
        "# Action Policy Activation Shadow Report",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.",
        "",
        "## Parameters",
        "",
        f"- Active model: `{report.get('active_model')}`",
        f"- Activation pct: `{(report.get('parameters') or {}).get('activation_pct')}`",
        f"- Release pct: `{(report.get('parameters') or {}).get('release_pct')}`",
        f"- Stop loss pct: `{(report.get('parameters') or {}).get('stop_loss_pct')}`",
        f"- Runtime params: `{runtime.get('runtime_params')}`",
        "",
        "## Summary",
        "",
        f"- Queued shadow-used matched trades: `{summary.get('queued_shadow_used_matched_count')}`",
        f"- Matched net profit BNB: `{summary.get('queued_shadow_used_matched_net_profit_bnb')}`",
        f"- Activation hits: `{summary.get('activation_hit_count')}`",
        f"- Release hits: `{summary.get('release_hit_count')}`",
        f"- Activated then stop: `{summary.get('activated_then_stop_count')}`",
        f"- Stop before activation: `{summary.get('stop_before_activation_count')}`",
        f"- Outcomes: `{summary.get('outcome_counts')}`",
        f"- Unemitted outcomes: `{summary.get('unemitted_outcome_count')}`",
        "",
        "## Decision",
        "",
        f"`{go_no_go.get('status')}`: {go_no_go.get('reason')}",
    ]
    return "\n".join(lines) + "\n"
