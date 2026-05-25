from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from src.pipeline import reentry_probe, time_to_barrier_probe


DEFAULT_ACTIVE_MODEL = None
DEFAULT_NEAR_MIN_PROB = 0.94
DEFAULT_PRIMARY_MIN_PROB = 0.98
DEFAULT_BARRIER_HORIZON_SECONDS = 600.0
DEFAULT_QUICK_PROFIT_SECONDS = 120.0
DEFAULT_MINIMUM_SAME_SHAPE_TRADES = 7


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


def _go_no_go(trades: list[dict[str, Any]], *, minimum_same_shape_trades: int = DEFAULT_MINIMUM_SAME_SHAPE_TRADES) -> dict[str, Any]:
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
            "Read-only live attribution is diagnostic evidence only; same-shape count can "
            "trigger a future replay, but live runtime/model changes still require causal, "
            "replay-equivalent support."
        ),
        "minimum_same_shape_trades_for_next_replay": int(minimum_same_shape_trades),
        "max_bucket_count": int(max_bucket),
        "max_near_bucket_count": int(max_near_bucket),
        "next_action": (
            "Keep live config unchanged; only a future replay task may test a conditional "
            "dead-flow exit or candidate-level meta gate if causal support improves."
        ),
    }


def _direction_id_for_failure_label(label: str) -> tuple[str, str]:
    mapping = {
        "dead_flow_timeout": ("live_dead_flow_exit_or_abstention_replay", "conditional_dead_flow_exit_or_entry_abstention"),
        "entry_slippage_failure": ("live_entry_slippage_risk_replay", "entry_slippage_risk_filter"),
        "mfe_then_giveback": ("live_mfe_giveback_exit_replay", "profit_lock_or_trailing_exit"),
        "stop_first_after_entry": ("live_stop_first_risk_replay", "pre_entry_stop_risk_filter"),
        "unprofitable_other": ("live_unprofitable_other_replay", "diagnostic_replay"),
    }
    return mapping.get(label, (f"live_{label}_replay", "diagnostic_replay"))


def _policy_hint_for_barrier_class(barrier_class: str) -> str:
    if barrier_class in {"fast_profit", "fast_profit_then_collapse"}:
        return "quick_take_profit"
    if barrier_class == "slow_runner":
        return "conditional_slow_hold"
    return "skip"


def _ranked_directions(
    *,
    trades: list[dict[str, Any]],
    rejected_signal_paths: Mapping[str, Any] | None,
    minimum_same_shape_trades: int,
) -> list[dict[str, Any]]:
    minimum_same_shape_trades = max(1, int(minimum_same_shape_trades))
    directions: list[dict[str, Any]] = []

    trades_by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        label = str(trade.get("failure_label") or "")
        if label and label != "profitable_exit":
            trades_by_label[label].append(trade)
    for label, bucket_trades in sorted(trades_by_label.items()):
        loss_bnb = sum(
            abs(float(trade.get("net_profit_bnb") or 0.0))
            for trade in bucket_trades
            if float(trade.get("net_profit_bnb") or 0.0) < 0.0
        )
        direction_id, policy_hint = _direction_id_for_failure_label(label)
        count = len(bucket_trades)
        directions.append(
            {
                "direction_id": direction_id,
                "source": "live_trade_failure",
                "bucket": label,
                "count": count,
                "sort_loss_bnb": float(loss_bnb),
                "sort_opportunity_count": count,
                "meets_minimum_same_shape_count": count >= minimum_same_shape_trades,
                "evidence_value": float(loss_bnb),
                "evidence_unit": "bnb_loss",
                "policy_hint": policy_hint,
            }
        )

    for barrier_class, count in sorted((rejected_signal_paths or {}).get("class_counts", {}).items()):
        count = int(count)
        policy_hint = _policy_hint_for_barrier_class(str(barrier_class))
        actionable_policy = policy_hint != "skip"
        opportunity_count = count if actionable_policy else 0
        directions.append(
            {
                "direction_id": f"rejected_{barrier_class}_{policy_hint}_replay",
                "source": "rejected_signal_path",
                "bucket": str(barrier_class),
                "count": count,
                "sort_loss_bnb": 0.0,
                "sort_opportunity_count": opportunity_count,
                "meets_minimum_same_shape_count": actionable_policy and count >= minimum_same_shape_trades,
                "evidence_value": float(opportunity_count),
                "evidence_unit": "candidate_count",
                "policy_hint": policy_hint,
            }
        )

    ordered = sorted(
        directions,
        key=lambda row: (
            -float(row.get("sort_loss_bnb") or 0.0),
            -int(row.get("sort_opportunity_count") or 0),
            -int(row.get("count") or 0),
            str(row.get("source") or ""),
            str(row.get("bucket") or ""),
        ),
    )
    for index, row in enumerate(ordered, start=1):
        row["rank"] = index
    return ordered


def _filter_signal_rows_by_window(
    signal_rows: Iterable[dict[str, Any]],
    *,
    since_time: dt.datetime | None,
    until_time: dt.datetime | None,
) -> list[dict[str, Any]]:
    filtered = []
    for row in signal_rows:
        if row.get("time") is None:
            continue
        try:
            if not _time_in_window(row.get("time"), since_time=since_time, until_time=until_time):
                continue
        except (TypeError, ValueError):
            continue
        filtered.append(dict(row))
    return filtered


def build_attribution_report(
    *,
    trade_rows: Iterable[dict[str, Any]],
    lifecycles: Mapping[str, dict[str, Any]],
    signal_rows: Iterable[dict[str, Any]] | None = None,
    generated_at: dt.datetime | None = None,
    active_model: str | None = DEFAULT_ACTIVE_MODEL,
    restart_anchor: Any = None,
    since: Any = None,
    until: Any = None,
    near_min_prob: float = DEFAULT_NEAR_MIN_PROB,
    primary_min_prob: float = DEFAULT_PRIMARY_MIN_PROB,
    barrier_horizon_seconds: float = DEFAULT_BARRIER_HORIZON_SECONDS,
    quick_profit_seconds: float = DEFAULT_QUICK_PROFIT_SECONDS,
    minimum_same_shape_trades: int = DEFAULT_MINIMUM_SAME_SHAPE_TRADES,
    max_trade_sample: int = 0,
    max_candidate_sample: int = 100,
) -> dict[str, Any]:
    normalized_lifecycles = {
        reentry_probe.normalize_token(token): lifecycle
        for token, lifecycle in (lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }
    generated_at_value = generated_at or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None)
    restart_time = _optional_time(restart_anchor)
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    pairs = []
    for pair in pair_real_trades(trade_rows):
        opened = pair.get("open") or {}
        open_time = reentry_probe.parse_time(opened.get("time"))
        if restart_time is not None and open_time < restart_time:
            continue
        if since_time is not None and open_time < since_time:
            continue
        if until_time is not None and open_time > until_time:
            continue
        pairs.append(pair)
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
    rejected_signal_paths = None
    if signal_rows is not None:
        filtered_signal_rows = _filter_signal_rows_by_window(
            signal_rows,
            since_time=since_time,
            until_time=until_time,
        )
        rejected_signal_paths = time_to_barrier_probe.build_probe_report(
            signal_rows=filtered_signal_rows,
            lifecycles=normalized_lifecycles,
            generated_at=generated_at_value,
            horizon_seconds=float(barrier_horizon_seconds),
            quick_profit_seconds=float(quick_profit_seconds),
            since=since_time,
            until=until_time,
            max_candidate_sample=max_candidate_sample,
        )

    return {
        "generated_at": generated_at_value,
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
            "restart_anchor": restart_time,
            "restart_anchor_applied": restart_time is not None,
            "since": since_time,
            "until": until_time,
            "barrier_horizon_seconds": float(barrier_horizon_seconds),
            "quick_profit_seconds": float(quick_profit_seconds),
            "minimum_same_shape_trades": int(minimum_same_shape_trades),
            "ranked_direction_evidence_units": {
                "live_trade_failure": "bnb_loss",
                "rejected_signal_path": "candidate_count",
            },
            "max_trade_sample": trade_sample_limit,
            "max_candidate_sample": int(max_candidate_sample),
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
        "rejected_signal_paths": rejected_signal_paths,
        "ranked_directions": _ranked_directions(
            trades=trades,
            rejected_signal_paths=rejected_signal_paths,
            minimum_same_shape_trades=int(minimum_same_shape_trades),
        ),
        "go_no_go": _go_no_go(trades, minimum_same_shape_trades=int(minimum_same_shape_trades)),
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
    rejected_signal_paths = report.get("rejected_signal_paths")
    ranked_directions = _json_sanitize(report.get("ranked_directions") or [])
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
        "## Rejected Signal Paths",
        "",
    ]
    if rejected_signal_paths is None:
        lines.extend(["- Signal audit input: `not_supplied`", ""])
    else:
        candidate_counts = rejected_signal_paths.get("candidate_counts") or {}
        class_counts = _json_sanitize(rejected_signal_paths.get("class_counts") or {})
        policy_counts = _json_sanitize(rejected_signal_paths.get("policy_counts") or {})
        lines.extend(
            [
                f"- Signal decisions: `{candidate_counts.get('signal_decisions')}`; per-token candidates: `{candidate_counts.get('per_token_candidates')}`",
                f"- Barrier classes: `{json.dumps(class_counts, ensure_ascii=False, sort_keys=True)}`",
                f"- Recommended policies: `{json.dumps(policy_counts, ensure_ascii=False, sort_keys=True)}`",
                f"- Missing/unemitted candidates: `{candidate_counts.get('unemitted_candidate_count')}`",
                "",
            ]
        )
    lines.extend(
        [
        "## Ranked Directions",
        "",
            f"- Ranked directions total: `{len(ranked_directions)}`",
            "",
            "```json",
            json.dumps(ranked_directions[:10], ensure_ascii=False, sort_keys=True, indent=2),
            "```",
            "",
        ]
    )
    lines.extend(
        [
            "## Decision",
            "",
            f"`{go_no_go.get('status')}`: {go_no_go.get('reason')}",
            "",
            f"Next action: {go_no_go.get('next_action')}",
            "",
        ]
    )
    return "\n".join(lines)
