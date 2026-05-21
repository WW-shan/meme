from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from typing import Any, Iterable

from src.pipeline import reentry_probe


DECISION_TIME_FIELDS = (
    "volume_30s",
    "price_volatility",
    "token_age_seconds",
    "feature_count",
    "features_hash",
    "entry_ranking_mode",
    "near_threshold_rescue_used",
    "use_pred_return_filter",
    "min_pred_return",
    "min_entry_volume_30s",
    "min_entry_price_volatility",
    "buy_near_threshold_min_prob",
    "buy_near_min_pred_return",
    "buy_near_min_entry_volume_30s",
    "buy_near_min_entry_price_volatility",
    "buy_near_min_age_seconds",
)

DECISION_TIME_ALIASES = {
    "entry_volume_30s": "volume_30s",
    "entry_price_volatility": "price_volatility",
    "age_seconds": "token_age_seconds",
}


def _first_present(*values: float | None) -> float | None:
    present = [float(value) for value in values if value is not None]
    return min(present) if present else None


def _decision_time_fields(signal: dict[str, Any]) -> dict[str, Any]:
    copied = {key: signal[key] for key in DECISION_TIME_FIELDS if key in signal}
    for alias, canonical in DECISION_TIME_ALIASES.items():
        if alias in signal:
            copied[alias] = signal[alias]
        if canonical in signal:
            copied[canonical] = signal[canonical]
        if canonical in copied:
            copied.setdefault(alias, copied[canonical])
        if alias in copied:
            copied.setdefault(canonical, copied[alias])
    return copied


def _before_stop(hit_time: float | None, stop_time: float | None) -> bool:
    return hit_time is not None and (stop_time is None or float(hit_time) < float(stop_time))


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def score_signal_time_to_barrier(
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
        "signal_time": anchor_time,
        "candidate_type": "rejected_signal_time_to_barrier",
        **_decision_time_fields(signal),
    }
    if not path or anchor_price is None or anchor_price <= 0.0:
        return {
            **base,
            "barrier_class": "missing_path",
            "recommended_policy": "skip",
            "quick_take_profit_candidate": False,
            "slow_runner_candidate": False,
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
        barrier_class = "stop_first"
    elif (
        plus_25 is not None
        and float(plus_25) <= float(quick_profit_seconds)
        and _before_stop(plus_25, stop_time)
        and stop_time is not None
        and float(stop_time) > float(plus_25)
    ):
        barrier_class = "fast_profit_then_collapse"
    elif plus_25 is not None and float(plus_25) <= float(quick_profit_seconds) and _before_stop(plus_25, stop_time):
        barrier_class = "fast_profit"
    elif (
        (plus_25 is not None and float(plus_25) > float(quick_profit_seconds) and _before_stop(plus_25, stop_time))
        or _before_stop(plus_60, stop_time)
    ):
        barrier_class = "slow_runner"
    else:
        barrier_class = "flat_timeout"

    recommended_policy = "skip"
    if barrier_class in {"fast_profit_then_collapse", "fast_profit"}:
        recommended_policy = "quick_take_profit"
    elif barrier_class == "slow_runner":
        recommended_policy = "conditional_slow_hold"

    return {
        **base,
        "barrier_class": barrier_class,
        "recommended_policy": recommended_policy,
        "quick_take_profit_candidate": recommended_policy == "quick_take_profit",
        "slow_runner_candidate": recommended_policy == "conditional_slow_hold",
        "missing_path": False,
        **metrics,
    }


def _signal_rank_key(signal: dict[str, Any]) -> tuple[float, float, dt.datetime]:
    return (
        reentry_probe.safe_float(signal.get("pred_return")),
        reentry_probe.safe_float(signal.get("prob")),
        reentry_probe.parse_time(signal.get("time")),
    )


def build_probe_report(
    *,
    signal_rows: Iterable[dict[str, Any]],
    lifecycles: dict[str, dict[str, Any]],
    generated_at: dt.datetime | None = None,
    horizon_seconds: float = 600,
    quick_profit_seconds: float = 120,
    since: Any = None,
) -> dict[str, Any]:
    parsed_signals = list(reentry_probe.iter_signal_decisions(signal_rows))
    if since is not None:
        since_time = reentry_probe.parse_time(since)
        parsed_signals = [signal for signal in parsed_signals if reentry_probe.parse_time(signal.get("time")) >= since_time]
    signal_by_token: dict[str, dict[str, Any]] = {}
    for signal in parsed_signals:
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
        score_signal_time_to_barrier(
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
            "horizon_seconds": horizon_seconds,
            "quick_profit_seconds": quick_profit_seconds,
            "since": reentry_probe.parse_time(since) if since is not None else None,
        },
        "candidate_counts": {
            "signal_decisions": len(parsed_signals),
            "per_token_candidates": len(candidates),
            "dropped_duplicate_signal_decisions": max(0, len(parsed_signals) - len(candidates)),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "policy_counts": dict(sorted(policy_counts.items())),
        "candidate_sample": candidates[:100],
    }
