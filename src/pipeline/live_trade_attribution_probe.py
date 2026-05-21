from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from src.pipeline import reentry_probe


DEFAULT_ACTIVE_MODEL = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_RESTART_ANCHOR = "2026-05-19 04:02:23"
DEFAULT_NEAR_MIN_PROB = 0.94
DEFAULT_PRIMARY_MIN_PROB = 0.98


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


def _is_real_trade(row: Mapping[str, Any]) -> bool:
    return bool(row.get("is_real_trade"))


def pair_real_trades(rows: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    real_rows = [dict(row) for row in rows if _is_real_trade(row)]
    yield from reentry_probe.pair_live_trades(real_rows)


def _safe_float_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _first_non_none(*values: float | None) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def _close_net_profit(close: Mapping[str, Any]) -> float:
    for key in ("net_profit_bnb", "net_profit", "profit_bnb"):
        parsed = _safe_float_or_none(close.get(key))
        if parsed is not None:
            return parsed
    return 0.0


def _profit_pct(opened: Mapping[str, Any], close: Mapping[str, Any]) -> float | None:
    explicit = _safe_float_or_none(close.get("profit_pct"))
    if explicit is not None:
        return explicit
    entry_price = _first_non_none(_safe_float_or_none(close.get("entry_price")), _safe_float_or_none(opened.get("entry_price")))
    exit_price = _first_non_none(_safe_float_or_none(close.get("exit_price")), _safe_float_or_none(close.get("price")))
    if entry_price is None or exit_price is None or entry_price <= 0.0:
        return None
    return ((exit_price / entry_price) - 1.0) * 100.0


def _near_threshold_like(prob: Any, *, near_min_prob: float, primary_min_prob: float) -> bool:
    parsed = _safe_float_or_none(prob)
    return parsed is not None and float(near_min_prob) <= parsed < float(primary_min_prob)


def _near_threshold_rule(*, near_min_prob: float, primary_min_prob: float) -> str:
    return f"{near_min_prob:g}<=prob<{primary_min_prob:g}"


def _hold_seconds(opened: Mapping[str, Any], close: Mapping[str, Any]) -> float | None:
    try:
        open_time = reentry_probe.parse_time(opened.get("time"))
        close_time = reentry_probe.parse_time(close.get("time"))
    except (TypeError, ValueError):
        return None
    return max(0.0, (close_time - open_time).total_seconds())


def _path_metrics_for_trade(pair: Mapping[str, Any], path: Iterable[reentry_probe.PricePoint]) -> dict[str, Any]:
    opened = dict(pair.get("open") or {})
    close = dict(pair.get("close") or {})
    path = list(path)
    entry_price = _first_non_none(_safe_float_or_none(opened.get("entry_price")), _safe_float_or_none(close.get("entry_price")))
    if not path or entry_price is None or entry_price <= 0.0:
        return {
            "mfe_pct": None,
            "mae_pct": None,
            "time_to_plus_25_seconds": None,
            "time_to_plus_60_seconds": None,
            "time_to_minus_18_seconds": None,
            "time_to_minus_25_seconds": None,
            "first_barrier": None,
            "horizon_seconds": None,
            "missing_hold_seconds": False,
        }
    hold_seconds = _hold_seconds(opened, close)
    if hold_seconds is None:
        return {
            "mfe_pct": None,
            "mae_pct": None,
            "time_to_plus_25_seconds": None,
            "time_to_plus_60_seconds": None,
            "time_to_minus_18_seconds": None,
            "time_to_minus_25_seconds": None,
            "first_barrier": None,
            "horizon_seconds": None,
            "missing_hold_seconds": True,
        }
    metrics = reentry_probe.path_metrics(
        path,
        anchor_time=reentry_probe.parse_time(opened.get("time")),
        anchor_price=entry_price,
        horizon_seconds=max(1.0, hold_seconds),
    )
    metrics["horizon_seconds"] = hold_seconds
    metrics["missing_hold_seconds"] = False
    return metrics


def _classify_failure(
    *,
    net_profit_bnb: float,
    reason: str,
    metrics: Mapping[str, Any],
) -> str:
    if net_profit_bnb > 0.0:
        return "profitable_exit"

    if reason == "ENTRY_SLIPPAGE_PROTECTION":
        return "entry_slippage_failure"

    plus_25 = metrics.get("time_to_plus_25_seconds")
    minus_18 = metrics.get("time_to_minus_18_seconds")
    minus_25 = metrics.get("time_to_minus_25_seconds")
    stop_times = [
        float(value)
        for value in (minus_18, minus_25)
        if value is not None
    ]
    first_stop = min(stop_times) if stop_times else None
    if metrics.get("first_barrier") in {"-18", "-25"}:
        return "stop_first_after_entry"
    if plus_25 is not None and (first_stop is None or float(plus_25) < first_stop):
        return "mfe_then_giveback"
    if reason == "STOP_LOSS":
        return "stop_first_after_entry"
    if reason == "TIME_EXIT" and plus_25 is None:
        return "dead_flow_timeout"
    return "unprofitable_other"


def score_trade_attribution(
    pair: Mapping[str, Any],
    path: Iterable[reentry_probe.PricePoint],
    *,
    near_min_prob: float = DEFAULT_NEAR_MIN_PROB,
    primary_min_prob: float = DEFAULT_PRIMARY_MIN_PROB,
) -> dict[str, Any]:
    path_points = list(path)
    opened = dict(pair.get("open") or {})
    close = dict(pair.get("close") or {})
    token = reentry_probe.normalize_token(pair.get("token") or opened.get("token") or close.get("token"))
    reason = str(close.get("reason") or "").upper()
    metrics = _path_metrics_for_trade(pair, path_points)
    net_profit_bnb = _close_net_profit(close)
    failure_label = _classify_failure(net_profit_bnb=net_profit_bnb, reason=reason, metrics=metrics)
    prob = opened.get("prob")
    entry_time = reentry_probe.parse_time(opened.get("time"))
    close_time = reentry_probe.parse_time(close.get("time"))
    hold_seconds = _hold_seconds(opened, close)

    return {
        "token": token,
        "symbol": pair.get("symbol") or close.get("symbol") or opened.get("symbol"),
        "open_time": entry_time,
        "close_time": close_time,
        "close_reason": reason,
        "net_profit_bnb": net_profit_bnb,
        "profit_pct": _profit_pct(opened, close),
        "failure_label": failure_label,
        "near_threshold_like": _near_threshold_like(
            prob,
            near_min_prob=near_min_prob,
            primary_min_prob=primary_min_prob,
        ),
        "near_threshold_rule": _near_threshold_rule(
            near_min_prob=near_min_prob,
            primary_min_prob=primary_min_prob,
        ),
        "prob": _safe_float_or_none(prob),
        "pred_return": _safe_float_or_none(opened.get("pred_return")),
        "entry_slippage_pct": _safe_float_or_none(opened.get("entry_slippage_pct")),
        "signal_to_open_seconds": _safe_float_or_none(opened.get("signal_to_open_seconds")),
        "hold_duration_seconds": _first_non_none(_safe_float_or_none(close.get("hold_duration")), hold_seconds),
        "entry_anchor": metrics,
        "path_point_count": len(path_points),
    }


def _counter(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key) or "") for row in rows if str(row.get(key) or ""))
    return dict(sorted(counts.items()))


def _bucket_net_profit(trades: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for trade in trades:
        label = str(trade.get("failure_label") or "")
        if label:
            totals[label] += float(trade.get("net_profit_bnb") or 0.0)
    return {key: totals[key] for key in sorted(totals)}


def _symbols_by_label(trades: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    symbols: dict[str, list[str]] = defaultdict(list)
    for trade in trades:
        label = str(trade.get("failure_label") or "")
        symbol = str(trade.get("symbol") or trade.get("token") or "")
        if label and symbol:
            symbols[label].append(symbol)
    return {key: symbols[key] for key in sorted(symbols)}


def _near_threshold_breakdown(trades: list[dict[str, Any]]) -> dict[str, Any]:
    near = [trade for trade in trades if bool(trade.get("near_threshold_like"))]
    primary = [trade for trade in trades if not bool(trade.get("near_threshold_like"))]
    return {
        "near_trade_count": len(near),
        "near_failure_labels": _counter(near, "failure_label"),
        "near_net_profit_bnb": sum(float(trade.get("net_profit_bnb") or 0.0) for trade in near),
        "primary_trade_count": len(primary),
        "primary_failure_labels": _counter(primary, "failure_label"),
        "primary_net_profit_bnb": sum(float(trade.get("net_profit_bnb") or 0.0) for trade in primary),
    }


def _go_no_go(trades: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(str(trade.get("failure_label") or "") for trade in trades)
    near_label_counts = Counter(
        str(trade.get("failure_label") or "")
        for trade in trades
        if bool(trade.get("near_threshold_like"))
    )
    max_bucket = max(label_counts.values(), default=0)
    max_near_bucket = max(near_label_counts.values(), default=0)
    return {
        "status": "NO_GO_FOR_LIVE_SWITCH",
        "safe_for_live_switch": False,
        "reason": (
            "Read-only live attribution is diagnostic evidence only; no bucket has enough "
            "causal, replay-equivalent support to change live runtime/model configuration."
        ),
        "minimum_same_shape_trades_for_next_replay": 7,
        "max_bucket_count": int(max_bucket),
        "max_near_bucket_count": int(max_near_bucket),
        "next_action": (
            "Keep live config unchanged; only a future replay task may test a conditional "
            "dead-flow exit or candidate-level meta gate if causal support improves."
        ),
    }


def build_attribution_report(
    *,
    trade_rows: Iterable[dict[str, Any]],
    lifecycles: Mapping[str, dict[str, Any]],
    generated_at: dt.datetime | None = None,
    active_model: str = DEFAULT_ACTIVE_MODEL,
    restart_anchor: str = DEFAULT_RESTART_ANCHOR,
    near_min_prob: float = DEFAULT_NEAR_MIN_PROB,
    primary_min_prob: float = DEFAULT_PRIMARY_MIN_PROB,
    max_trade_sample: int = 0,
) -> dict[str, Any]:
    normalized_lifecycles = {
        reentry_probe.normalize_token(token): lifecycle
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    restart_time = reentry_probe.parse_time(restart_anchor)
    pairs = [
        pair
        for pair in pair_real_trades(trade_rows)
        if reentry_probe.parse_time((pair.get("open") or {}).get("time")) >= restart_time
    ]
    trades = [
        score_trade_attribution(
            pair,
            reentry_probe.price_path_for_token(normalized_lifecycles, pair.get("token")),
            near_min_prob=near_min_prob,
            primary_min_prob=primary_min_prob,
        )
        for pair in pairs
    ]
    trade_sample_limit = int(max_trade_sample)
    emitted_trades = trades if trade_sample_limit == 0 else trades[: max(0, trade_sample_limit)]
    net_profit = sum(float(trade.get("net_profit_bnb") or 0.0) for trade in trades)
    win_count = sum(1 for trade in trades if float(trade.get("net_profit_bnb") or 0.0) > 0.0)
    missing_lifecycle_tokens = [
        trade["token"]
        for trade in trades
        if int(trade.get("path_point_count") or 0) == 0
    ]

    return {
        "generated_at": generated_at
        or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None),
        "timezone": "UTC+8",
        "active_model": active_model,
        "restart_anchor": restart_anchor,
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
        },
        "parameters": {
            "near_min_prob": float(near_min_prob),
            "primary_min_prob": float(primary_min_prob),
            "near_threshold_rule": _near_threshold_rule(
                near_min_prob=near_min_prob,
                primary_min_prob=primary_min_prob,
            ),
            "max_trade_sample": trade_sample_limit,
        },
        "trade_count": len(trades),
        "win_count": win_count,
        "loss_count": max(0, len(trades) - win_count),
        "net_profit_bnb": net_profit,
        "failure_label_counts": _counter(trades, "failure_label"),
        "reason_counts": _counter(trades, "close_reason"),
        "bucket_net_profit_bnb": _bucket_net_profit(trades),
        "near_threshold_breakdown": _near_threshold_breakdown(trades),
        "symbols_by_label": _symbols_by_label(trades),
        "lifecycle_coverage": {
            "trade_count": len(trades),
            "with_price_path_count": sum(1 for trade in trades if int(trade.get("path_point_count") or 0) > 0),
            "missing_price_path_count": len(missing_lifecycle_tokens),
            "missing_lifecycle_tokens": missing_lifecycle_tokens,
        },
        "go_no_go": _go_no_go(trades),
        "trade_sample": emitted_trades,
        "unemitted_trade_count": max(0, len(trades) - len(emitted_trades)),
    }


def to_markdown_text(report: Mapping[str, Any]) -> str:
    label_counts = _json_sanitize(report.get("failure_label_counts") or {})
    reason_counts = _json_sanitize(report.get("reason_counts") or {})
    near_breakdown = report.get("near_threshold_breakdown") or {}
    lifecycle_coverage = report.get("lifecycle_coverage") or {}
    bucket_net_profit = _json_sanitize(report.get("bucket_net_profit_bnb") or {})
    symbols_by_label = _json_sanitize(report.get("symbols_by_label") or {})
    go_no_go = report.get("go_no_go") or {}
    lines = [
        "# Live Trade Attribution Refresh",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.",
        "",
        "## Live Since Restart",
        "",
        f"- Active model: `{report.get('active_model')}`",
        f"- Restart anchor: `{report.get('restart_anchor')}`",
        f"- Closed trades: `{report.get('trade_count')}`; wins: `{report.get('win_count')}`; losses: `{report.get('loss_count')}`",
        f"- Net profit: `{report.get('net_profit_bnb')}` BNB",
        f"- Failure labels: `{json.dumps(label_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- Close reasons: `{json.dumps(reason_counts, ensure_ascii=False, sort_keys=True)}`",
        f"- Lifecycle price paths: `{lifecycle_coverage.get('with_price_path_count')}/{lifecycle_coverage.get('trade_count')}` with missing path count `{lifecycle_coverage.get('missing_price_path_count')}`",
        f"- Bucket net profit: `{json.dumps(bucket_net_profit, ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Near Threshold Split",
        "",
        f"- Near trades: `{near_breakdown.get('near_trade_count')}`; labels: `{json.dumps(near_breakdown.get('near_failure_labels') or {}, ensure_ascii=False, sort_keys=True)}`",
        f"- Near net profit: `{near_breakdown.get('near_net_profit_bnb')}` BNB",
        f"- Primary trades: `{near_breakdown.get('primary_trade_count')}`; labels: `{json.dumps(near_breakdown.get('primary_failure_labels') or {}, ensure_ascii=False, sort_keys=True)}`",
        f"- Primary net profit: `{near_breakdown.get('primary_net_profit_bnb')}` BNB",
        "",
        "## Symbols",
        "",
        f"- Symbols by label: `{json.dumps(symbols_by_label, ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Decision",
        "",
        f"`{go_no_go.get('status')}`: {go_no_go.get('reason')}",
        "",
        f"Next action: {go_no_go.get('next_action')}",
        "",
    ]
    return "\n".join(lines)
