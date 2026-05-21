from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = PROJECT_ROOT / "docs" / "research" / "20260521-conditional-exit-flow-state"
DEFAULT_TRAIN_REPORT = PROJECT_ROOT / "data" / "replay_reports" / "post_target_exit_state_probe_20260521_v95_train.json"
DEFAULT_VALIDATION_REPORT = PROJECT_ROOT / "data" / "replay_reports" / "post_target_exit_state_probe_20260521_v95_validation.json"
DEFAULT_FINAL_REPORT = PROJECT_ROOT / "data" / "replay_reports" / "post_target_exit_state_probe_20260521_v95_final.json"
DEFAULT_LIVE_ATTRIBUTION = RESEARCH_DIR / "live_attribution.json"

DEFAULT_MIN_HOLD_SECONDS = 540.0
DEFAULT_MAX_MFE_PCT = 5.0
DEFAULT_MIN_SELL_PRESSURE = 0.48
MIN_SUPPORT_POSITIVES = 3
MIN_LIVE_RECALL_MATCHES = 6


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
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


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _as_float(value)
        if parsed is not None:
            return parsed
    return None


def _candidate_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    for key in ("candidate_sample", "candidates", "trade_log", "trades"):
        rows = report.get(key)
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return [dict(row) for row in rows if isinstance(row, Mapping)]
    return []


def _entry_anchor(row: Mapping[str, Any]) -> dict[str, Any]:
    return _as_mapping(row.get("entry_anchor"))


def _path(row: Mapping[str, Any]) -> dict[str, Any]:
    return _as_mapping(row.get("path"))


def _flow(row: Mapping[str, Any]) -> dict[str, Any]:
    return _as_mapping(row.get("flow"))


def _pre_signal_10s_flow(row: Mapping[str, Any]) -> dict[str, Any]:
    return _as_mapping(row.get("pre_signal_10s_flow"))


def _mfe_pct(row: Mapping[str, Any]) -> float | None:
    anchor = _entry_anchor(row)
    path = _path(row)
    return _first_float(row.get("mfe_pct"), anchor.get("mfe_pct"), path.get("mfe_pct"))


def _time_to_plus_25(row: Mapping[str, Any]) -> float | None:
    anchor = _entry_anchor(row)
    path = _path(row)
    return _first_float(
        row.get("time_to_plus_25_seconds"),
        row.get("time_to_target_seconds") if row.get("target_hit") is True else None,
        anchor.get("time_to_plus_25_seconds"),
        path.get("time_to_plus_25_seconds"),
    )


def _target_hit(row: Mapping[str, Any]) -> bool:
    if row.get("target_hit") is not None:
        return bool(row.get("target_hit"))
    return _time_to_plus_25(row) is not None


def _hold_window_seconds(row: Mapping[str, Any], *, source: str) -> float | None:
    if source == "live":
        return _first_float(row.get("hold_duration_seconds"), row.get("hold_seconds"))
    return _first_float(row.get("hold_duration_seconds"), row.get("hold_seconds"), row.get("horizon_seconds"))


def _sell_pressure(row: Mapping[str, Any]) -> float | None:
    pre10 = _pre_signal_10s_flow(row)
    direct = _first_float(pre10.get("sell_pressure"), row.get("sell_pressure"))
    if direct is not None:
        return direct

    flow = _flow(row)
    buy_pressure = _as_float(flow.get("pre_buy_pressure"))
    if buy_pressure is not None:
        return max(0.0, min(1.0, 1.0 - buy_pressure))

    buy_volume = _as_float(flow.get("pre_buy_volume_bnb"))
    sell_volume = _as_float(flow.get("pre_sell_volume_bnb"))
    if buy_volume is not None and sell_volume is not None:
        total = buy_volume + sell_volume
        if total > 0.0:
            return sell_volume / total
    return None


def classify_dead_flow_timeout(
    row: Mapping[str, Any],
    *,
    source: str,
    min_hold_seconds: float = DEFAULT_MIN_HOLD_SECONDS,
    max_mfe_pct: float = DEFAULT_MAX_MFE_PCT,
    min_sell_pressure: float = DEFAULT_MIN_SELL_PRESSURE,
) -> dict[str, Any]:
    mfe_pct = _mfe_pct(row)
    hold_seconds = _hold_window_seconds(row, source=source)
    sell_pressure = _sell_pressure(row)
    time_to_plus_25 = _time_to_plus_25(row)
    target_hit = _target_hit(row)

    if bool(row.get("missing_path")):
        classification = "missing_path"
    elif target_hit or time_to_plus_25 is not None:
        classification = "target_hit_or_post_target"
    elif hold_seconds is None or hold_seconds < float(min_hold_seconds):
        classification = "insufficient_hold_window"
    elif mfe_pct is None:
        classification = "missing_mfe"
    elif mfe_pct > float(max_mfe_pct):
        classification = "mfe_above_dead_flow_floor"
    elif sell_pressure is None:
        classification = "missing_sell_pressure"
    elif sell_pressure < float(min_sell_pressure):
        classification = "sell_pressure_below_floor"
    else:
        classification = "replay_dead_flow_timeout"

    return {
        "symbol": row.get("symbol"),
        "token": row.get("token"),
        "source": source,
        "classification": classification,
        "is_dead_flow_timeout": classification == "replay_dead_flow_timeout",
        "mfe_pct": mfe_pct,
        "hold_window_seconds": hold_seconds,
        "sell_pressure": sell_pressure,
        "time_to_plus_25_seconds": time_to_plus_25,
        "target_hit": bool(target_hit),
        "near_threshold_like": bool(row.get("near_threshold_like")),
        "used_failure_label": False,
    }


def _build_split_report(
    report: Mapping[str, Any],
    *,
    split: str,
    source_path: str | None = None,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    rows = _candidate_rows(report)
    classified = [
        classify_dead_flow_timeout(row, source="replay")
        for row in rows
    ]
    class_counts = Counter(row["classification"] for row in classified)
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).astimezone(),
        "split": split,
        "source_path": source_path or str(report.get("_source_path") or ""),
        "source_scope": "existing_post_target_replay_reports_only",
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
        },
        "parameters": {
            "min_hold_seconds": DEFAULT_MIN_HOLD_SECONDS,
            "max_mfe_pct": DEFAULT_MAX_MFE_PCT,
            "min_sell_pressure": DEFAULT_MIN_SELL_PRESSURE,
        },
        "candidate_counts": {
            "input_rows": len(rows),
            "classified_rows": len(classified),
            "dead_flow_timeout_candidates": int(class_counts.get("replay_dead_flow_timeout", 0)),
        },
        "class_counts": dict(sorted(class_counts.items())),
        "candidate_sample": classified[:100],
    }


def _live_trades(live_attribution: Mapping[str, Any]) -> list[dict[str, Any]]:
    trades = live_attribution.get("trades") or []
    return [dict(row) for row in trades if isinstance(row, Mapping)]


def _live_recall(live_attribution: Mapping[str, Any]) -> dict[str, Any]:
    trades = _live_trades(live_attribution)
    classified = [classify_dead_flow_timeout(row, source="live") for row in trades]
    shape_matched = [
        row
        for row in classified
        if row["is_dead_flow_timeout"]
    ]
    dead_flow_indexes = [
        index
        for index, row in enumerate(trades)
        if row.get("failure_label") == "dead_flow_timeout"
    ]
    matched = [
        classified[index]
        for index in dead_flow_indexes
        if classified[index]["is_dead_flow_timeout"]
    ]
    return {
        "dead_flow_label_count": len(dead_flow_indexes),
        "shape_matched_live_count": len(shape_matched),
        "shape_matched_non_dead_flow_count": len(shape_matched) - len(matched),
        "matched_dead_flow_count": len(matched),
        "recall": (len(matched) / len(dead_flow_indexes)) if dead_flow_indexes else None,
        "min_required_matches": MIN_LIVE_RECALL_MATCHES,
        "passes_live_recall_gate": len(matched) >= MIN_LIVE_RECALL_MATCHES,
        "shape_matched_symbols": [str(row.get("symbol") or row.get("token") or "") for row in shape_matched],
        "matched_symbols": [str(row.get("symbol") or row.get("token") or "") for row in matched],
        "candidate_sample": classified[:100],
    }


def _dead_flow_count(split_report: Mapping[str, Any]) -> int:
    counts = _as_mapping(split_report.get("class_counts"))
    return int(counts.get("replay_dead_flow_timeout") or 0)


def build_support_report(
    *,
    train_report: Mapping[str, Any],
    validation_report: Mapping[str, Any],
    final_report: Mapping[str, Any],
    live_attribution: Mapping[str, Any],
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    generated = generated_at or dt.datetime.now(dt.timezone.utc).astimezone()
    split_counts = {
        "train": _build_split_report(train_report, split="train", generated_at=generated),
        "validation": _build_split_report(validation_report, split="validation", generated_at=generated),
        "final": _build_split_report(final_report, split="final", generated_at=generated),
    }
    live_recall = _live_recall(live_attribution)
    train_positives = _dead_flow_count(split_counts["train"])
    validation_positives = _dead_flow_count(split_counts["validation"])
    final_positives = _dead_flow_count(split_counts["final"])
    live_positives = int(live_recall["matched_dead_flow_count"])
    passes_support = (
        train_positives >= MIN_SUPPORT_POSITIVES
        and validation_positives >= MIN_SUPPORT_POSITIVES
        and final_positives >= MIN_SUPPORT_POSITIVES
        and live_positives >= MIN_SUPPORT_POSITIVES
        and bool(live_recall["passes_live_recall_gate"])
    )
    status = "PASS_DEAD_FLOW_SUPPORT_GATE" if passes_support else "NO_GO_FOR_DEAD_FLOW_RULE"
    return {
        "generated_at": generated,
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "position_fraction": 0.10,
            "max_open_positions": 8,
        },
        "support_scope": {
            "replay_input": "existing_post_target_replay_reports_only",
            "live_input": "live_attribution.json",
            "note": "This diagnostic probe does not reconstruct a new lifecycle replay surface.",
        },
        "input_paths": {
            "train": str(train_report.get("_source_path") or DEFAULT_TRAIN_REPORT),
            "validation": str(validation_report.get("_source_path") or DEFAULT_VALIDATION_REPORT),
            "final": str(final_report.get("_source_path") or DEFAULT_FINAL_REPORT),
            "live_attribution": str(live_attribution.get("_source_path") or DEFAULT_LIVE_ATTRIBUTION),
        },
        "bucket_definition": {
            "bucket": "dead_flow_timeout",
            "shared_label": "replay_dead_flow_timeout",
            "decision_scope": "read_only_path_label_not_live_decision",
            "min_hold_seconds": DEFAULT_MIN_HOLD_SECONDS,
            "max_mfe_pct": DEFAULT_MAX_MFE_PCT,
            "min_sell_pressure": DEFAULT_MIN_SELL_PRESSURE,
            "parity_caveat": "live sell pressure is read from pre_signal_10s_flow.sell_pressure; replay rows may derive sell pressure from flow.pre_buy_pressure or volume balance.",
            "forbidden_features": ["failure_label", "close_reason", "net_profit_bnb"],
        },
        "split_counts": split_counts,
        "live_recall": live_recall,
        "support_gate": {
            "status": status,
            "train_positives": train_positives,
            "validation_positives": validation_positives,
            "final_positives": final_positives,
            "live_positives": live_positives,
            "min_support_positives": MIN_SUPPORT_POSITIVES,
            "min_live_recall_matches": MIN_LIVE_RECALL_MATCHES,
            "passes_support_gate": passes_support,
            "reason": (
                "dead-flow support and live recall gates passed for a default-off replay follow-up; this is not live-switch evidence"
                if passes_support
                else "dead-flow support remains diagnostic only until train/validation/final/live support and live recall gates pass"
            ),
        },
    }


def to_markdown_text(report: Mapping[str, Any]) -> str:
    gate = _as_mapping(report.get("support_gate"))
    live_recall = _as_mapping(report.get("live_recall"))
    return "\n".join(
        [
            "# Dead-Flow Timeout Support",
            "",
            f"- Status: `{gate.get('status')}`",
            f"- Scope: `{report.get('support_scope', {}).get('replay_input')}`",
            f"- Train positives: `{gate.get('train_positives')}`",
            f"- Validation positives: `{gate.get('validation_positives')}`",
            f"- Final positives: `{gate.get('final_positives')}`",
            f"- Live matched positives: `{gate.get('live_positives')}`",
            f"- Live shape matches: `{live_recall.get('shape_matched_live_count')}`",
            f"- Live recall: `{live_recall.get('matched_dead_flow_count')}/{live_recall.get('dead_flow_label_count')}`",
            "",
            "No live switch is allowed from this diagnostic report alone.",
            "",
        ]
    )
