#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo


LOCAL_RUNTIME_TZ = ZoneInfo("Asia/Shanghai")


def _parse_time(value):
    if value is None:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LOCAL_RUNTIME_TZ)
    return parsed.astimezone(timezone.utc)


def _read_jsonl(path):
    if path is None:
        return []
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _filter_rows_by_time(rows, *, since=None, until=None):
    since_ts = _parse_time(since)
    until_ts = _parse_time(until)
    if since_ts is None and until_ts is None:
        return rows

    filtered = []
    for row in rows:
        row_ts = _parse_time(row.get("time"))
        if row_ts is None:
            continue
        if since_ts is not None and row_ts < since_ts:
            continue
        if until_ts is not None and row_ts > until_ts:
            continue
        filtered.append(row)
    return filtered


def _percentile(values, pct):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * float(pct)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def _nonnegative_int(value):
    if value is None:
        return None
    numeric = float(value)
    if numeric <= 0.0:
        return 0
    return int(math.ceil(numeric))


def _ratio(numerator, denominator):
    denominator = int(denominator or 0)
    return float(numerator / denominator) if denominator > 0 else 0.0


def _slippage_pct(row):
    signal_price = float(row.get("signal_price", 0.0) or 0.0)
    entry_price = float(row.get("entry_price", 0.0) or 0.0)
    if signal_price <= 0.0 or entry_price <= 0.0:
        return None
    return (entry_price / signal_price) - 1.0


def _exit_return_pct(row):
    entry_price = float(row.get("entry_price", 0.0) or 0.0)
    exit_price = float(row.get("exit_price", 0.0) or 0.0)
    if entry_price <= 0.0 or exit_price <= 0.0:
        return None
    return (exit_price / entry_price) - 1.0


def _entry_signal_to_open_seconds(row, *, signal_ts=None):
    value = row.get("signal_to_open_seconds")
    if value is not None:
        return max(0.0, float(value))
    if signal_ts is None:
        signal_ts = _parse_time(row.get("signal_time"))
    open_ts = _parse_time(row.get("time"))
    if signal_ts is None or open_ts is None:
        return None
    return max(0.0, (open_ts - signal_ts).total_seconds())


def _entry_submit_seconds(row, *, signal_ts=None, signal_to_open_seconds=None, fill_lag_seconds=None):
    value = row.get("entry_submit_seconds")
    if value is not None:
        return max(0.0, float(value))
    if signal_to_open_seconds is not None and fill_lag_seconds is not None:
        return max(0.0, signal_to_open_seconds - fill_lag_seconds)
    if signal_to_open_seconds is None:
        signal_to_open_seconds = _entry_signal_to_open_seconds(row, signal_ts=signal_ts)
    if signal_to_open_seconds is not None and fill_lag_seconds is not None:
        return max(0.0, signal_to_open_seconds - fill_lag_seconds)
    return signal_to_open_seconds


def _entry_fill_lag_seconds(row, *, signal_ts=None, signal_to_open_seconds=None, submit_seconds=None):
    value = row.get("entry_fill_lag_seconds")
    if value is not None:
        return max(0.0, float(value))
    if signal_to_open_seconds is None:
        signal_to_open_seconds = _entry_signal_to_open_seconds(row, signal_ts=signal_ts)
    if signal_to_open_seconds is not None and submit_seconds is not None:
        return max(0.0, signal_to_open_seconds - float(submit_seconds))
    return None


def _exit_execution_seconds(row):
    value = row.get("sell_execution_seconds")
    if value is not None:
        return max(0.0, float(value))
    started_at = _parse_time(row.get("sell_started_at"))
    closed_at = _parse_time(row.get("time"))
    if started_at is None or closed_at is None:
        return None
    return max(0.0, (closed_at - started_at).total_seconds())


def _nonnegative_float_field(row, name):
    value = row.get(name)
    if value is None:
        return None
    return max(0.0, float(value))


def _truthy_field(row, name):
    value = row.get(name)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def estimate_execution_costs(*, signal_audit_path=None, trade_log_path=None, since=None, until=None):
    audit_rows = _filter_rows_by_time(_read_jsonl(signal_audit_path), since=since, until=until)
    trade_rows = _filter_rows_by_time(_read_jsonl(trade_log_path), since=since, until=until)

    signal_rows = [row for row in audit_rows if row.get("action") == "SIGNAL_DECISION"]
    queued_signals = [row for row in signal_rows if row.get("decision") in {"queued", "replaced"}]
    opened_rows = [row for row in audit_rows if row.get("action") == "POSITION_OPENED"]
    if not opened_rows:
        opened_rows = [row for row in trade_rows if row.get("action") == "OPEN"]
    closed_rows = [row for row in audit_rows if row.get("action") in {"POSITION_CLOSED", "POSITION_PARTIAL_CLOSED"}]
    if not closed_rows:
        closed_rows = [row for row in trade_rows if row.get("action") in {"CLOSE", "PARTIAL_SELL"}]

    terminal_buy_failure_actions = {"BUY_EXECUTION_FAILED", "BUY_RECEIPT_REVERT"}
    transient_buy_retry_actions = {"BUY_NOT_READY", "BUY_ALREADY_SENT"}
    sell_failure_actions = {"SELL_EXECUTION_FAILED"}
    buy_failure_rows = [row for row in audit_rows if row.get("action") in terminal_buy_failure_actions]
    transient_buy_retry_rows = [row for row in audit_rows if row.get("action") in transient_buy_retry_actions]
    sell_failure_rows = [row for row in audit_rows if row.get("action") in sell_failure_actions]
    post_fill_protection_rows = [
        row for row in audit_rows
        if row.get("action") == "ENTRY_PRICE_PROTECTION_POST_FILL_EXIT"
    ]
    post_fill_protection_tokens = {
        str(row.get("token", "")).strip().lower()
        for row in post_fill_protection_rows
        if str(row.get("token", "")).strip()
    }
    protection_skip_rows = [
        row for row in audit_rows
        if row.get("action") in {"ENTRY_PRICE_PROTECTION_SKIP", "ENTRY_PRICE_PROTECTION_POST_FILL_EXIT"}
    ]
    queue_replace_rows = [row for row in audit_rows if row.get("action") == "QUEUE_REPLACE" and row.get("replaced_token")]
    replacement_drop_count = len(queue_replace_rows)

    latest_signal_by_token = {}
    for row in sorted(signal_rows, key=lambda item: str(item.get("time", ""))):
        token = row.get("token")
        if token:
            latest_signal_by_token[token] = row

    signal_to_open_seconds = []
    entry_submit_seconds = []
    entry_fill_lag_seconds = []
    for row in opened_rows:
        token = row.get("token")
        signal = latest_signal_by_token.get(token)
        if not signal:
            continue
        signal_ts = _parse_time(signal.get("time"))
        signal_to_open = _entry_signal_to_open_seconds(row, signal_ts=signal_ts)
        fill_lag_seconds = _entry_fill_lag_seconds(row, signal_ts=signal_ts, signal_to_open_seconds=signal_to_open)
        submit_seconds = _entry_submit_seconds(
            row,
            signal_ts=signal_ts,
            signal_to_open_seconds=signal_to_open,
            fill_lag_seconds=fill_lag_seconds,
        )
        if signal_to_open is not None:
            signal_to_open_seconds.append(signal_to_open)
        if submit_seconds is not None:
            entry_submit_seconds.append(submit_seconds)
        if fill_lag_seconds is not None:
            entry_fill_lag_seconds.append(fill_lag_seconds)

    slippage_rows = [
        row for row in opened_rows
        if str(row.get("token", "")).strip().lower() not in post_fill_protection_tokens
    ]
    entry_slippages = [value for value in (_slippage_pct(row) for row in slippage_rows) if value is not None]
    positive_entry_slippages = [max(0.0, value) for value in entry_slippages]
    buy_tx_submit_rpc_seconds = [
        value for value in (_nonnegative_float_field(row, "buy_tx_submit_rpc_seconds") for row in opened_rows)
        if value is not None
    ]
    buy_preflight_seconds = [
        value for value in (_nonnegative_float_field(row, "buy_preflight_seconds") for row in opened_rows)
        if value is not None
    ]
    token_status_check_seconds = [
        value for value in (_nonnegative_float_field(row, "token_status_check_seconds") for row in opened_rows)
        if value is not None
    ]
    buy_token_detect_seconds = [
        value for value in (_nonnegative_float_field(row, "buy_token_detect_seconds") for row in opened_rows)
        if value is not None
    ]
    buy_confirm_poll_intervals = [
        value for value in (_nonnegative_float_field(row, "buy_confirm_poll_interval_seconds") for row in opened_rows)
        if value is not None
    ]
    buy_post_detect_sync_seconds = [
        value for value in (_nonnegative_float_field(row, "buy_post_detect_sync_seconds") for row in opened_rows)
        if value is not None
    ]
    fast_status_rows = [
        row for row in opened_rows
        if _truthy_field(row, "buy_fast_status_used")
        or str(row.get("token_status_source", "")).strip().lower() == "lifecycle"
    ]
    helper_status_rows = [
        row for row in opened_rows
        if str(row.get("token_status_source", "")).strip().lower() == "helper"
    ]
    status_source_observation_count = len(fast_status_rows) + len(helper_status_rows)
    lifecycle_status_staleness_seconds = [
        value for value in (_nonnegative_float_field(row, "lifecycle_status_staleness_seconds") for row in opened_rows)
        if value is not None
    ]
    lifecycle_status_chain_lag_seconds = [
        value for value in (_nonnegative_float_field(row, "lifecycle_status_chain_lag_seconds") for row in opened_rows)
        if value is not None
    ]
    exit_returns = [value for value in (_exit_return_pct(row) for row in closed_rows) if value is not None]
    exit_execution_seconds = [value for value in (_exit_execution_seconds(row) for row in closed_rows) if value is not None]

    unresolved_signal_count = max(
        0,
        len(queued_signals)
        - len(opened_rows)
        - len(protection_skip_rows)
        - len(buy_failure_rows)
        - replacement_drop_count,
    )
    entry_failure_count = len(buy_failure_rows) + unresolved_signal_count
    entry_attempts = len(opened_rows) + entry_failure_count

    exit_attempts = len(closed_rows) + len(sell_failure_rows)
    exit_failure_count = len(sell_failure_rows)

    p95_signal_to_open = _percentile(signal_to_open_seconds, 0.95)
    p95_entry_slippage = _percentile(positive_entry_slippages, 0.95)
    recommended_protection = None
    if p95_entry_slippage is not None:
        recommended_protection = max(0.0, min(0.5, float(p95_entry_slippage) + 0.02))

    entry = {
        "signal_count": int(len(signal_rows)),
        "queued_signal_count": int(len(queued_signals)),
        "open_count": int(len(opened_rows)),
        "failure_count": int(entry_failure_count),
        "terminal_failure_count": int(len(buy_failure_rows)),
        "transient_retry_count": int(len(transient_buy_retry_rows)),
        "replacement_drop_count": int(replacement_drop_count),
        "unresolved_signal_count": int(unresolved_signal_count),
        "protection_skip_count": int(len(protection_skip_rows)),
        "post_fill_protection_exit_count": int(len(post_fill_protection_rows)),
        "avg_signal_to_open_seconds": float(mean(signal_to_open_seconds)) if signal_to_open_seconds else None,
        "p95_signal_to_open_seconds": p95_signal_to_open,
        "avg_entry_delay_seconds": float(mean(entry_submit_seconds)) if entry_submit_seconds else None,
        "p95_entry_delay_seconds": _percentile(entry_submit_seconds, 0.95),
        "avg_entry_fill_lag_seconds": float(mean(entry_fill_lag_seconds)) if entry_fill_lag_seconds else None,
        "p95_entry_fill_lag_seconds": _percentile(entry_fill_lag_seconds, 0.95),
        "avg_buy_preflight_seconds": float(mean(buy_preflight_seconds)) if buy_preflight_seconds else None,
        "avg_token_status_check_seconds": float(mean(token_status_check_seconds)) if token_status_check_seconds else None,
        "avg_buy_tx_submit_rpc_seconds": float(mean(buy_tx_submit_rpc_seconds)) if buy_tx_submit_rpc_seconds else None,
        "avg_buy_token_detect_seconds": float(mean(buy_token_detect_seconds)) if buy_token_detect_seconds else None,
        "avg_buy_confirm_poll_interval_seconds": float(mean(buy_confirm_poll_intervals)) if buy_confirm_poll_intervals else None,
        "avg_buy_post_detect_sync_seconds": float(mean(buy_post_detect_sync_seconds)) if buy_post_detect_sync_seconds else None,
        "fast_status_count": int(len(fast_status_rows)),
        "helper_status_count": int(len(helper_status_rows)),
        "status_source_observation_count": int(status_source_observation_count),
        "fast_status_rate": _ratio(len(fast_status_rows), status_source_observation_count),
        "avg_lifecycle_status_staleness_seconds": (
            float(mean(lifecycle_status_staleness_seconds)) if lifecycle_status_staleness_seconds else None
        ),
        "p95_lifecycle_status_staleness_seconds": _percentile(lifecycle_status_staleness_seconds, 0.95),
        "avg_lifecycle_status_chain_lag_seconds": (
            float(mean(lifecycle_status_chain_lag_seconds)) if lifecycle_status_chain_lag_seconds else None
        ),
        "p95_lifecycle_status_chain_lag_seconds": _percentile(lifecycle_status_chain_lag_seconds, 0.95),
        "max_lifecycle_status_chain_lag_seconds": (
            max(lifecycle_status_chain_lag_seconds) if lifecycle_status_chain_lag_seconds else None
        ),
        "avg_entry_slippage_pct": float(mean(entry_slippages)) if entry_slippages else None,
        "p95_positive_entry_slippage_pct": p95_entry_slippage,
        "observed_entry_execution_failure_rate": _ratio(entry_failure_count, entry_attempts),
    }
    exit_stats = {
        "close_count": int(len(closed_rows)),
        "failure_count": int(exit_failure_count),
        "avg_exit_return_pct": float(mean(exit_returns)) if exit_returns else None,
        "avg_sell_execution_seconds": float(mean(exit_execution_seconds)) if exit_execution_seconds else None,
        "p95_sell_execution_seconds": _percentile(exit_execution_seconds, 0.95),
        "observed_exit_execution_failure_rate": _ratio(exit_failure_count, exit_attempts),
    }

    replay_overrides = {
        "entry_delay_seconds": _nonnegative_int(entry["avg_entry_delay_seconds"] if entry["avg_entry_delay_seconds"] is not None else entry["avg_signal_to_open_seconds"]),
        "entry_max_fill_wait_seconds": _nonnegative_int(entry["p95_entry_fill_lag_seconds"] if entry["p95_entry_fill_lag_seconds"] is not None else p95_signal_to_open),
        "entry_price_protection_pct": recommended_protection,
        "entry_execution_failure_rate": entry["observed_entry_execution_failure_rate"],
        "exit_delay_seconds": _nonnegative_int(exit_stats["avg_sell_execution_seconds"]),
        "exit_max_fill_wait_seconds": _nonnegative_int(exit_stats["p95_sell_execution_seconds"]),
        "exit_execution_failure_rate": exit_stats["observed_exit_execution_failure_rate"],
    }

    return {
        "source": {
            "signal_audit_path": None if signal_audit_path is None else str(signal_audit_path),
            "trade_log_path": None if trade_log_path is None else str(trade_log_path),
            "since": since,
            "until": until,
        },
        "entry": entry,
        "exit": exit_stats,
        "replay_overrides": replay_overrides,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Estimate replay execution controls from live bot audit/trade logs")
    parser.add_argument("--signal-audit", default="data/signal_audit.jsonl", help="Bot signal audit JSONL path")
    parser.add_argument("--trade-log", default="data/paper_trades.jsonl", help="Bot trade JSONL path")
    parser.add_argument("--since", default=None, help="Only include rows at or after this ISO timestamp")
    parser.add_argument("--until", default=None, help="Only include rows at or before this ISO timestamp")
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = estimate_execution_costs(
        signal_audit_path=args.signal_audit,
        trade_log_path=args.trade_log,
        since=args.since,
        until=args.until,
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
