from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from typing import Any, Iterable

from src.pipeline import reentry_probe


LOW_VOLUME_REASON = "entry_volume_30s_below_min"


def _first_present(*values: float | None) -> float | None:
    present = [float(value) for value in values if value is not None]
    return min(present) if present else None


def _before_stop(hit_time: float | None, stop_time: float | None) -> bool:
    return hit_time is not None and (stop_time is None or float(hit_time) < float(stop_time))


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def score_low_volume_signal(
    signal: dict[str, Any],
    path: Iterable[reentry_probe.PricePoint],
    *,
    horizon_seconds: float = 600,
    quick_profit_seconds: float = 120,
) -> dict[str, Any]:
    anchor_time = reentry_probe.parse_time(signal.get("time"))
    path = list(path)
    anchor_price = reentry_probe._anchor_price_at_or_before(path, anchor_time)
    base = {
        "token": reentry_probe.normalize_token(signal.get("token") or signal.get("token_address")),
        "symbol": signal.get("symbol"),
        "reason": signal.get("reason"),
        "prob": signal.get("prob"),
        "pred_return": signal.get("pred_return"),
        "volume_30s": signal.get("volume_30s"),
        "price_volatility": signal.get("price_volatility"),
        "token_age_seconds": signal.get("token_age_seconds"),
        "signal_time": anchor_time,
        "candidate_type": "rejected_low_volume_breakout",
    }
    if not path or anchor_price is None or anchor_price <= 0.0:
        return {
            **base,
            "barrier_class": "missing_path",
            "recommended_policy": "skip",
            "missing_path": True,
        }

    metrics = reentry_probe.path_metrics(
        path,
        anchor_time=anchor_time,
        anchor_price=anchor_price,
        horizon_seconds=horizon_seconds,
    )
    plus_25 = metrics.get("time_to_plus_25_seconds")
    plus_60 = metrics.get("time_to_plus_60_seconds")
    minus_18 = metrics.get("time_to_minus_18_seconds")
    minus_25 = metrics.get("time_to_minus_25_seconds")
    stop_time = _first_present(minus_18, minus_25)

    if metrics.get("first_barrier") in {"-18", "-25"}:
        barrier_class = "low_volume_fakeout"
    elif plus_25 is not None and stop_time is not None and float(plus_25) < float(stop_time):
        barrier_class = "low_volume_fast_profit_then_stop"
    elif (_before_stop(plus_60, stop_time) or _before_stop(plus_25, stop_time)) and stop_time is None:
        barrier_class = "low_volume_runner"
    else:
        barrier_class = "low_volume_flat"

    recommended_policy = "skip"
    if barrier_class == "low_volume_runner":
        recommended_policy = "conditional_rescue_probe"
    elif barrier_class == "low_volume_fast_profit_then_stop":
        recommended_policy = "quick_take_profit_probe"

    return {
        **base,
        "barrier_class": barrier_class,
        "recommended_policy": recommended_policy,
        "missing_path": False,
        "quick_profit_seconds": quick_profit_seconds,
        **metrics,
    }


def _signal_rank_key(signal: dict[str, Any]) -> tuple[float, float, dt.datetime]:
    return (
        reentry_probe.safe_float(signal.get("prob")),
        reentry_probe.safe_float(signal.get("pred_return")),
        reentry_probe.parse_time(signal.get("time")),
    )


def _is_low_volume_candidate(
    signal: dict[str, Any],
    *,
    min_prob: float,
    min_volume_30s: float,
    max_volume_30s: float,
    min_price_volatility: float,
    max_token_age_seconds: float,
) -> bool:
    token_age_seconds = signal.get("token_age_seconds")
    if token_age_seconds is None:
        return False
    return (
        signal.get("reason") == LOW_VOLUME_REASON
        and reentry_probe.safe_float(signal.get("prob")) >= float(min_prob)
        and reentry_probe.safe_float(signal.get("volume_30s")) >= float(min_volume_30s)
        and reentry_probe.safe_float(signal.get("volume_30s")) <= float(max_volume_30s)
        and reentry_probe.safe_float(signal.get("price_volatility")) >= float(min_price_volatility)
        and reentry_probe.safe_float(token_age_seconds, default=float("inf")) <= float(max_token_age_seconds)
    )


def build_probe_report(
    *,
    signal_rows: Iterable[dict[str, Any]],
    lifecycles: dict[str, dict[str, Any]],
    generated_at: dt.datetime | None = None,
    since: Any = None,
    min_prob: float = 0.98,
    min_volume_30s: float = 0.75,
    max_volume_30s: float = 1.5,
    min_price_volatility: float = 0.05,
    max_token_age_seconds: float = 60,
    horizon_seconds: float = 600,
    quick_profit_seconds: float = 120,
) -> dict[str, Any]:
    parsed_signals = list(reentry_probe.iter_signal_decisions(signal_rows))
    if since is not None:
        since_time = reentry_probe.parse_time(since)
        parsed_signals = [signal for signal in parsed_signals if reentry_probe.parse_time(signal.get("time")) >= since_time]

    low_volume_signals = [
        signal
        for signal in parsed_signals
        if _is_low_volume_candidate(
            signal,
            min_prob=min_prob,
            min_volume_30s=min_volume_30s,
            max_volume_30s=max_volume_30s,
            min_price_volatility=min_price_volatility,
            max_token_age_seconds=max_token_age_seconds,
        )
    ]

    signal_by_token: dict[str, dict[str, Any]] = {}
    for signal in low_volume_signals:
        token = reentry_probe.normalize_token(signal.get("token"))
        if not token:
            continue
        current = signal_by_token.get(token)
        if current is None or _signal_rank_key(signal) > _signal_rank_key(current):
            signal_by_token[token] = signal

    normalized_lifecycles = {
        reentry_probe.normalize_token(token): lifecycle
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    candidates = [
        score_low_volume_signal(
            signal,
            reentry_probe.price_path_for_token(normalized_lifecycles, signal.get("token")),
            horizon_seconds=horizon_seconds,
            quick_profit_seconds=quick_profit_seconds,
        )
        for signal in signal_by_token.values()
    ]
    class_counts = Counter(candidate["barrier_class"] for candidate in candidates)
    policy_counts = Counter(candidate["recommended_policy"] for candidate in candidates)

    return {
        "generated_at": generated_at
        or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
        },
        "parameters": {
            "min_prob": min_prob,
            "min_volume_30s": min_volume_30s,
            "max_volume_30s": max_volume_30s,
            "min_price_volatility": min_price_volatility,
            "max_token_age_seconds": max_token_age_seconds,
            "horizon_seconds": horizon_seconds,
            "quick_profit_seconds": quick_profit_seconds,
            "since": reentry_probe.parse_time(since) if since is not None else None,
        },
        "candidate_counts": {
            "raw_rejected_signal_decisions": len(parsed_signals),
            "filtered_low_volume_signal_decisions": len(low_volume_signals),
            "per_token_candidates": len(candidates),
            "dropped_duplicate_low_volume_signals": max(0, len(low_volume_signals) - len(candidates)),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "policy_counts": dict(sorted(policy_counts.items())),
        "candidate_sample": candidates[:100],
    }
