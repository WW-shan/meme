from __future__ import annotations

import datetime as dt
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ANALYSIS_TZ = dt.timezone(dt.timedelta(hours=8))


@dataclass(frozen=True)
class PricePoint:
    time: dt.datetime
    price: float
    kind: str = ""


def parse_time(value: Any) -> dt.datetime:
    if isinstance(value, dt.datetime):
        if value.tzinfo:
            return value.astimezone(ANALYSIS_TZ).replace(tzinfo=None)
        return value
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, tz=ANALYSIS_TZ).replace(tzinfo=None)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty timestamp")
        try:
            return dt.datetime.fromtimestamp(float(text), tz=ANALYSIS_TZ).replace(tzinfo=None)
        except ValueError:
            pass
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed.astimezone(ANALYSIS_TZ).replace(tzinfo=None)
        return parsed
    raise TypeError(f"unsupported timestamp value: {value!r}")


def normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if math.isfinite(parsed) else float(default)


def iter_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                yield json.loads(text)


def latest_lifecycle_files(lifecycle_dir: str | Path, *, limit: int = 1) -> list[Path]:
    base = Path(lifecycle_dir)
    if not base.exists():
        return []
    limit = max(0, int(limit or 0))
    if limit == 0:
        return []
    files = sorted(base.glob("lifecycle_incremental_*.jsonl"), key=lambda path: path.stat().st_mtime_ns)
    if not files:
        files = sorted(
            [
                path
                for path in base.glob("lifecycle_*.jsonl")
                if not path.name.startswith("lifecycle_incremental_")
            ],
            key=lambda path: path.stat().st_mtime_ns,
        )
    return files[-limit:]


def path_status(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    exists = resolved.exists()
    return {
        "path": str(resolved),
        "exists": exists,
        "size_bytes": int(resolved.stat().st_size) if exists and resolved.is_file() else 0,
    }


def build_input_status(
    *,
    paper_trades: str | Path,
    signal_audit: str | Path,
    collector_state: str | Path,
    lifecycle_dir: str | Path,
    lifecycle_paths: Iterable[str | Path],
) -> dict[str, Any]:
    lifecycle_dir_path = Path(lifecycle_dir)
    lifecycle_path_statuses = [path_status(path) for path in lifecycle_paths]
    return {
        "paper_trades": path_status(paper_trades),
        "signal_audit": path_status(signal_audit),
        "collector_state": path_status(collector_state),
        "lifecycle_dir": {
            "path": str(lifecycle_dir_path),
            "exists": lifecycle_dir_path.exists(),
        },
        "lifecycle_paths": lifecycle_path_statuses,
        "existing_lifecycle_path_count": sum(1 for row in lifecycle_path_statuses if row["exists"]),
    }


def iter_signal_decisions(rows: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for row in rows:
        if row.get("action") != "SIGNAL_DECISION":
            continue
        if str(row.get("decision") or "").lower() != "rejected":
            continue
        parsed = dict(row)
        parsed["token"] = normalize_token(row.get("token") or row.get("token_address"))
        parsed["time"] = parse_time(row.get("time"))
        if row.get("create_timestamp") is not None and row.get("token_age_seconds") is not None:
            parsed["age_anchor_time"] = parse_time(float(row.get("create_timestamp") or 0.0) + float(row.get("token_age_seconds") or 0.0))
        yield parsed


def _trade_anchor_time(row: dict[str, Any]) -> dt.datetime:
    action = str(row.get("action") or "").upper()
    candidates = []
    if action == "OPEN":
        candidates = [row.get("entry_signal_time"), row.get("signal_time"), row.get("time")]
    elif action == "CLOSE":
        candidates = [row.get("time"), row.get("sell_started_at")]
    else:
        candidates = [row.get("time")]
    for candidate in candidates:
        if candidate is not None:
            return parse_time(candidate)
    raise ValueError(f"trade row has no parseable time: {row!r}")


def pair_live_trades(rows: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    open_by_token: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=_trade_anchor_time):
        action = str(row.get("action") or "").upper()
        token = normalize_token(row.get("token") or row.get("token_address"))
        if not token:
            continue
        parsed = dict(row)
        parsed["token"] = token
        parsed["time"] = _trade_anchor_time(row)
        if parsed.get("sell_started_at") is not None:
            parsed["sell_started_at"] = parse_time(parsed["sell_started_at"])
        if action == "OPEN":
            open_by_token.setdefault(token, []).append(parsed)
        elif action == "CLOSE":
            opens = open_by_token.get(token)
            if not opens:
                continue
            opened = opens.pop(0)
            yield {
                "token": token,
                "symbol": parsed.get("symbol") or opened.get("symbol"),
                "open": opened,
                "close": parsed,
            }


def path_metrics(
    path: Iterable[PricePoint],
    *,
    anchor_time: dt.datetime,
    anchor_price: float,
    horizon_seconds: float = 900,
) -> dict[str, Any]:
    anchor_time = parse_time(anchor_time)
    anchor_price = float(anchor_price)
    if anchor_price <= 0:
        raise ValueError("anchor_price must be positive")

    metrics: dict[str, Any] = {
        "mfe_pct": None,
        "mae_pct": None,
        "time_to_plus_25_seconds": None,
        "time_to_plus_60_seconds": None,
        "time_to_minus_18_seconds": None,
        "time_to_minus_25_seconds": None,
        "first_barrier": None,
    }
    barriers = {
        "+25": ("time_to_plus_25_seconds", 25.0),
        "+60": ("time_to_plus_60_seconds", 60.0),
        "-18": ("time_to_minus_18_seconds", -18.0),
        "-25": ("time_to_minus_25_seconds", -25.0),
    }
    barrier_hits: list[tuple[float, str]] = []
    changes: list[float] = []

    for point in sorted(path, key=lambda item: parse_time(item.time)):
        seconds = (parse_time(point.time) - anchor_time).total_seconds()
        if seconds < 0 or seconds > horizon_seconds:
            continue
        pct = ((float(point.price) / anchor_price) - 1.0) * 100.0
        changes.append(pct)
        for label, (field, threshold) in barriers.items():
            hit = pct >= threshold if threshold > 0 else pct <= threshold
            if hit and metrics[field] is None:
                metrics[field] = seconds
                barrier_hits.append((seconds, label))

    if changes:
        metrics["mfe_pct"] = max(changes)
        metrics["mae_pct"] = min(changes)
    if barrier_hits:
        metrics["first_barrier"] = sorted(barrier_hits, key=lambda item: item[0])[0][1]
    return metrics


def extract_lifecycles_from_runtime_state(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lifecycles: dict[str, dict[str, Any]] = {}
    for lifecycle in state.get("active_lifecycles") or []:
        token = normalize_token(lifecycle.get("token_address") or lifecycle.get("token"))
        if token:
            lifecycles[token] = lifecycle
    return lifecycles


def extract_lifecycles_from_rows(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lifecycles: dict[str, dict[str, Any]] = {}
    for row in rows:
        token = normalize_token(row.get("token_address") or row.get("token"))
        if not token:
            continue
        existing = lifecycles.get(token)
        if existing is None:
            merged = dict(row)
            merged["token_address"] = token
            merged["price_history"] = list(row.get("price_history") or [])
            lifecycles[token] = merged
            continue
        existing["price_history"] = list(existing.get("price_history") or []) + list(row.get("price_history") or [])
        if row.get("symbol") and not existing.get("symbol"):
            existing["symbol"] = row.get("symbol")
    return lifecycles


def merge_lifecycle_maps(*maps: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for lifecycle_map in maps:
        for token, lifecycle in (lifecycle_map or {}).items():
            token = normalize_token(token)
            if not token:
                continue
            existing = merged.get(token)
            if existing is None:
                copied = dict(lifecycle)
                copied["token_address"] = token
                copied["price_history"] = list(lifecycle.get("price_history") or [])
                merged[token] = copied
                continue
            existing["price_history"] = list(existing.get("price_history") or []) + list(lifecycle.get("price_history") or [])
            if lifecycle.get("symbol") and not existing.get("symbol"):
                existing["symbol"] = lifecycle.get("symbol")
    return merged


def load_lifecycles(
    *,
    collector_state_path: str | Path | None = None,
    lifecycle_paths: Iterable[str | Path] | None = None,
) -> dict[str, dict[str, Any]]:
    maps: list[dict[str, dict[str, Any]]] = []
    if collector_state_path is not None:
        path = Path(collector_state_path)
        if path.exists():
            maps.append(extract_lifecycles_from_runtime_state(json.loads(path.read_text(encoding="utf-8"))))
    for lifecycle_path in lifecycle_paths or []:
        path = Path(lifecycle_path)
        if path.exists():
            maps.append(extract_lifecycles_from_rows(iter_jsonl(path)))
    return merge_lifecycle_maps(*maps)


def price_path_from_lifecycle(lifecycle: dict[str, Any]) -> list[PricePoint]:
    points: list[PricePoint] = []
    seen = set()
    for row in lifecycle.get("price_history") or []:
        timestamp = row.get("timestamp", row.get("time"))
        price = row.get("price")
        if timestamp is None or price is None:
            continue
        point = PricePoint(parse_time(timestamp), float(price), str(row.get("type") or ""))
        key = (point.time, point.price, point.kind)
        if key in seen:
            continue
        seen.add(key)
        points.append(point)
    return sorted(points, key=lambda point: point.time)


def price_path_for_token(lifecycles: dict[str, dict[str, Any]], token: Any) -> list[PricePoint]:
    lifecycle = lifecycles.get(normalize_token(token))
    return price_path_from_lifecycle(lifecycle) if lifecycle else []


def _anchor_price_at_or_before(path: Iterable[PricePoint], anchor_time: dt.datetime) -> float | None:
    anchor_time = parse_time(anchor_time)
    ordered = sorted(path, key=lambda point: point.time)
    before = [point for point in ordered if point.time <= anchor_time and point.price > 0.0]
    if before:
        return float(before[-1].price)
    return None


def _probe_decision_fields(accepted: bool) -> dict[str, Any]:
    accepted = bool(accepted)
    return {
        "accepted_by_probe": accepted,
        "accepted": accepted,
        "decision": "accepted" if accepted else "rejected",
    }


def score_exit_reclaim_candidate(
    pair: dict[str, Any],
    path: Iterable[PricePoint],
    *,
    accepted_reasons: set[str] | None = None,
    reclaim_pct: float = 25.0,
    collapse_pct: float = -18.0,
    post_reclaim_collapse_pct: float = -25.0,
    post_reclaim_guard_seconds: float = 60,
    horizon_seconds: float = 300,
) -> dict[str, Any]:
    close = pair.get("close") or {}
    reason = str(close.get("reason") or "").upper()
    accepted_reasons = {str(value).upper() for value in (accepted_reasons or {"STOP_LOSS"})}
    anchor_time = parse_time(close.get("time"))
    anchor_price = safe_float(close.get("exit_price") or close.get("price"))
    candidate_type = "stoploss_reentry" if reason == "STOP_LOSS" else "runner_retention"
    base = {
        "token": normalize_token(pair.get("token")),
        "symbol": pair.get("symbol"),
        "reason": reason,
        "candidate_type": candidate_type,
    }
    if anchor_price <= 0.0:
        return {
            **base,
            **_probe_decision_fields(False),
            "missing_anchor_price": True,
        }
    metrics = path_metrics(path, anchor_time=anchor_time, anchor_price=anchor_price, horizon_seconds=horizon_seconds)

    reclaim_field = f"time_to_plus_{int(reclaim_pct)}_seconds"
    collapse_field = f"time_to_minus_{abs(int(collapse_pct))}_seconds"
    reclaim_time = metrics.get(reclaim_field)
    collapse_time = metrics.get(collapse_field)
    post_reclaim_collapse_field = f"time_to_minus_{abs(int(post_reclaim_collapse_pct))}_seconds"
    post_reclaim_collapse_time = metrics.get(post_reclaim_collapse_field)
    post_reclaim_failed = (
        reclaim_time is not None
        and post_reclaim_collapse_time is not None
        and post_reclaim_collapse_time > reclaim_time
        and post_reclaim_collapse_time <= reclaim_time + float(post_reclaim_guard_seconds)
    )
    accepted = reason in accepted_reasons and reclaim_time is not None and (
        collapse_time is None or reclaim_time < collapse_time
    ) and not post_reclaim_failed

    return {
        **base,
        **_probe_decision_fields(accepted),
        "post_reclaim_collapse_failed": post_reclaim_failed,
        **metrics,
    }


def score_stoploss_reentry_candidate(
    pair: dict[str, Any],
    path: Iterable[PricePoint],
    *,
    reclaim_pct: float = 25.0,
    collapse_pct: float = -18.0,
    post_reclaim_collapse_pct: float = -25.0,
    post_reclaim_guard_seconds: float = 60,
    horizon_seconds: float = 300,
) -> dict[str, Any]:
    return score_exit_reclaim_candidate(
        pair,
        path,
        accepted_reasons={"STOP_LOSS"},
        reclaim_pct=reclaim_pct,
        collapse_pct=collapse_pct,
        post_reclaim_collapse_pct=post_reclaim_collapse_pct,
        post_reclaim_guard_seconds=post_reclaim_guard_seconds,
        horizon_seconds=horizon_seconds,
    )


def score_signal_reclaim_candidate(
    signal: dict[str, Any],
    path: Iterable[PricePoint],
    *,
    min_prob: float = 0.94,
    min_pred_return: float = 20.0,
    reclaim_pct: float = 25.0,
    collapse_pct: float = -18.0,
    post_reclaim_collapse_pct: float = -25.0,
    post_reclaim_guard_seconds: float = 60,
    horizon_seconds: float = 300,
) -> dict[str, Any]:
    prob = signal.get("prob")
    pred_return = signal.get("pred_return")
    prob_value = safe_float(prob)
    pred_return_value = safe_float(pred_return)
    anchor_time = parse_time(signal.get("time"))
    path = list(path)
    anchor_price = _anchor_price_at_or_before(path, anchor_time)
    base = {
        "token": normalize_token(signal.get("token")),
        "symbol": signal.get("symbol"),
        "reason": signal.get("reason"),
        "prob": prob,
        "pred_return": pred_return,
        "candidate_type": "rejected_signal_reclaim",
    }
    if prob_value < float(min_prob) or pred_return_value < float(min_pred_return):
        return {
            **base,
            **_probe_decision_fields(False),
            "filtered_by_confidence": True,
        }
    if anchor_price is None or anchor_price <= 0.0:
        return {
            **base,
            **_probe_decision_fields(False),
            "missing_path": True,
        }
    metrics = path_metrics(path, anchor_time=anchor_time, anchor_price=anchor_price, horizon_seconds=horizon_seconds)
    reclaim_field = f"time_to_plus_{int(reclaim_pct)}_seconds"
    collapse_field = f"time_to_minus_{abs(int(collapse_pct))}_seconds"
    reclaim_time = metrics.get(reclaim_field)
    collapse_time = metrics.get(collapse_field)
    post_reclaim_collapse_field = f"time_to_minus_{abs(int(post_reclaim_collapse_pct))}_seconds"
    post_reclaim_collapse_time = metrics.get(post_reclaim_collapse_field)
    post_reclaim_failed = (
        reclaim_time is not None
        and post_reclaim_collapse_time is not None
        and post_reclaim_collapse_time > reclaim_time
        and post_reclaim_collapse_time <= reclaim_time + float(post_reclaim_guard_seconds)
    )
    accepted = reclaim_time is not None and (collapse_time is None or reclaim_time < collapse_time) and not post_reclaim_failed
    return {
        **base,
        **_probe_decision_fields(accepted),
        "post_reclaim_collapse_failed": post_reclaim_failed,
        **metrics,
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, indent=2, sort_keys=True) + "\n"


def build_probe_report(
    *,
    trade_rows: Iterable[dict[str, Any]],
    signal_rows: Iterable[dict[str, Any]],
    lifecycles: dict[str, dict[str, Any]],
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    parsed_signals = list(iter_signal_decisions(signal_rows))
    pairs = list(pair_live_trades(trade_rows))
    stoploss_candidates = []
    retention_candidates = []
    signal_candidates = []
    diagnostics = {
        "missing_lifecycle_path_stoploss": 0,
        "missing_lifecycle_path_runner_retention": 0,
        "missing_lifecycle_path_rejected_signal": 0,
        "dropped_rejected_signal_decisions_by_token_best": 0,
    }

    normalized_lifecycles = {
        normalize_token(token): lifecycle
        for token, lifecycle in lifecycles.items()
        if normalize_token(token)
    }
    for pair in pairs:
        close = pair.get("close") or {}
        if str(close.get("reason") or "").upper() != "STOP_LOSS":
            continue
        path = price_path_for_token(normalized_lifecycles, pair.get("token"))
        if not path:
            diagnostics["missing_lifecycle_path_stoploss"] += 1
            continue
        stoploss_candidates.append(score_stoploss_reentry_candidate(pair, path))
    for pair in pairs:
        close = pair.get("close") or {}
        if str(close.get("reason") or "").upper() != "PPO_SELL100":
            continue
        path = price_path_for_token(normalized_lifecycles, pair.get("token"))
        if not path:
            diagnostics["missing_lifecycle_path_runner_retention"] += 1
            continue
        retention_candidates.append(score_exit_reclaim_candidate(pair, path, accepted_reasons={"PPO_SELL100"}))
    signal_by_token: dict[str, dict[str, Any]] = {}
    for signal in parsed_signals:
        token = normalize_token(signal.get("token"))
        if not token:
            continue
        current = signal_by_token.get(token)
        candidate_key = (safe_float(signal.get("prob")), safe_float(signal.get("pred_return")))
        current_key = (
            safe_float(current.get("prob")),
            safe_float(current.get("pred_return")),
        ) if current else None
        if current is None or candidate_key > current_key:
            signal_by_token[token] = signal
    diagnostics["dropped_rejected_signal_decisions_by_token_best"] = max(0, len(parsed_signals) - len(signal_by_token))
    for signal in signal_by_token.values():
        path = price_path_for_token(normalized_lifecycles, signal.get("token"))
        if not path:
            diagnostics["missing_lifecycle_path_rejected_signal"] += 1
            continue
        signal_candidates.append(score_signal_reclaim_candidate(signal, path))

    accepted = [candidate for candidate in stoploss_candidates if candidate["accepted_by_probe"]]
    accepted_retention = [candidate for candidate in retention_candidates if candidate["accepted_by_probe"]]
    accepted_signals = [candidate for candidate in signal_candidates if candidate["accepted_by_probe"]]
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).astimezone(ANALYSIS_TZ).replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
        },
        "candidate_counts": {
            "signal_decisions": len(parsed_signals),
            "paired_live_trades": len(pairs),
            "stoploss_reentry": len(stoploss_candidates),
            "accepted_stoploss_reentry": len(accepted),
            "runner_retention": len(retention_candidates),
            "accepted_runner_retention": len(accepted_retention),
            "per_token_rejected_signal_reclaim": len(signal_candidates),
            "accepted_rejected_signal_reclaim": len(accepted_signals),
            "dropped_rejected_signal_decisions_by_token_best": diagnostics["dropped_rejected_signal_decisions_by_token_best"],
        },
        "diagnostics": diagnostics,
        "stoploss_reentry_candidates": stoploss_candidates,
        "runner_retention_candidates": retention_candidates,
        "rejected_signal_reclaim_candidates": signal_candidates[:100],
        "signal_decision_sample": parsed_signals[:50],
    }
