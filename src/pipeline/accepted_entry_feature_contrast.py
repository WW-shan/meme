from __future__ import annotations

import datetime as dt
import json
import math
import pickle
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


LEAKY_FEATURE_FRAGMENTS = (
    "future",
    "label_",
    "target_",
    "time_to_target",
    "time_to_stop",
)


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


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
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _token_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _time_key(value: Any) -> int | None:
    parsed = _finite_float(value)
    if parsed is None:
        return None
    return int(round(parsed))


def _trade_times(trade: Mapping[str, Any]) -> list[int]:
    times: list[int] = []
    signal_time = _time_key(trade.get("entry_signal_time"))
    if signal_time is not None:
        times.append(signal_time)
    entry_time = _time_key(trade.get("entry_time"))
    if entry_time is not None:
        times.extend([entry_time - 1, entry_time])
    return list(dict.fromkeys(times))


def _sample_token(sample: Mapping[str, Any]) -> str:
    meta = sample.get("meta") if isinstance(sample.get("meta"), Mapping) else {}
    return _token_key(meta.get("token_address") or meta.get("token") or sample.get("token"))


def _sample_time(sample: Mapping[str, Any]) -> int | None:
    meta = sample.get("meta") if isinstance(sample.get("meta"), Mapping) else {}
    return _time_key(meta["sample_time"] if "sample_time" in meta else sample.get("sample_time"))


def _is_allowed_feature(name: str, value: Any) -> bool:
    lower_name = name.lower()
    if any(fragment in lower_name for fragment in LEAKY_FEATURE_FRAGMENTS):
        return False
    return _finite_float(value) is not None


def _sample_feature_values(sample: Mapping[str, Any]) -> dict[str, float]:
    features = sample.get("features")
    if not isinstance(features, Mapping):
        return {}
    values: dict[str, float] = {}
    for key, raw_value in features.items():
        name = str(key)
        if not _is_allowed_feature(name, raw_value):
            continue
        value = _finite_float(raw_value)
        if value is not None:
            values[name] = value
    return values


def _return_pct(trade: Mapping[str, Any]) -> float:
    raw_value = trade["return_pct"] if "return_pct" in trade else trade.get("net_return_pct")
    return _finite_float(raw_value) or 0.0


def _exit_reason(trade: Mapping[str, Any]) -> str:
    return str(trade.get("exit_reason") or trade.get("close_reason") or "").upper()


def _label_values(trade: Mapping[str, Any]) -> dict[str, bool]:
    return_pct = _return_pct(trade)
    reason = _exit_reason(trade)
    is_loss = return_pct < 0.0
    return {
        "bad_loss": is_loss,
        "time_exit_loss": is_loss and reason == "TIME_EXIT",
        "stop_loss_any": reason == "STOP_LOSS",
    }


def _mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _sample_std(values: Sequence[float], mean: float) -> float:
    if len(values) <= 1:
        return 0.0
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _auc(pos_values: Sequence[float], neg_values: Sequence[float]) -> float | None:
    if not pos_values or not neg_values:
        return None
    ranked = sorted([(value, 1) for value in pos_values] + [(value, 0) for value in neg_values])
    rank_sum = 0.0
    index = 0
    while index < len(ranked):
        value = ranked[index][0]
        end = index + 1
        while end < len(ranked) and ranked[end][0] == value:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        positives_in_tie = sum(label for _, label in ranked[index:end])
        rank_sum += positives_in_tie * average_rank
        index = end
    n_pos = len(pos_values)
    n_neg = len(neg_values)
    return float((rank_sum - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg))


def _feature_contrast(
    rows: Sequence[Mapping[str, Any]],
    *,
    label_name: str,
    feature_names: Sequence[str],
    top_n: int,
) -> dict[str, Any]:
    positive_rows = [row for row in rows if row["labels"].get(label_name)]
    negative_rows = [row for row in rows if not row["labels"].get(label_name)]
    top_features = []
    for feature_name in feature_names:
        pos_values = [row["features"][feature_name] for row in positive_rows if feature_name in row["features"]]
        neg_values = [row["features"][feature_name] for row in negative_rows if feature_name in row["features"]]
        if not pos_values or not neg_values:
            continue
        pos_mean = _mean(pos_values)
        neg_mean = _mean(neg_values)
        pos_std = _sample_std(pos_values, pos_mean)
        neg_std = _sample_std(neg_values, neg_mean)
        pooled_var = ((pos_std**2) + (neg_std**2)) / 2.0
        smd = (pos_mean - neg_mean) / math.sqrt(pooled_var) if pooled_var > 0.0 else 0.0
        top_features.append(
            {
                "feature": feature_name,
                "positive_mean": pos_mean,
                "negative_mean": neg_mean,
                "positive_min": min(pos_values),
                "positive_max": max(pos_values),
                "negative_min": min(neg_values),
                "negative_max": max(neg_values),
                "positive_count": len(pos_values),
                "negative_count": len(neg_values),
                "smd": float(smd),
                "auc": _auc(pos_values, neg_values),
            }
        )

    top_features.sort(
        key=lambda row: (
            abs(_finite_float(row.get("smd")) or 0.0),
            abs((_finite_float(row.get("auc")) or 0.5) - 0.5),
        ),
        reverse=True,
    )
    return {
        "positive_count": len(positive_rows),
        "negative_count": len(negative_rows),
        "top_features": top_features[: int(top_n)],
    }


def _build_sample_index(sample_rows: Iterable[Mapping[str, Any]]) -> tuple[dict[tuple[str, int], Mapping[str, Any]], int]:
    index: dict[tuple[str, int], Mapping[str, Any]] = {}
    seen = 0
    for sample in sample_rows:
        if not isinstance(sample, Mapping):
            continue
        token = _sample_token(sample)
        sample_time = _sample_time(sample)
        if not token or sample_time is None:
            continue
        index.setdefault((token, sample_time), sample)
        seen += 1
    return index, seen


def _matched_trade_rows(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_index: Mapping[tuple[str, int], Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for trade in trade_rows:
        token = _token_key(trade.get("token") or trade.get("token_address"))
        match = None
        matched_time = None
        for trade_time in _trade_times(trade):
            match = sample_index.get((token, trade_time))
            if match is not None:
                matched_time = trade_time
                break
        if match is None:
            unmatched.append(
                {
                    "token": trade.get("token") or trade.get("token_address"),
                    "entry_signal_time": trade.get("entry_signal_time"),
                    "entry_time": trade.get("entry_time"),
                    "return_pct": trade.get("return_pct"),
                    "exit_reason": trade.get("exit_reason") or trade.get("close_reason"),
                }
            )
            continue
        matched.append(
            {
                "trade": trade,
                "matched_sample_time": matched_time,
                "features": _sample_feature_values(match),
                "labels": _label_values(trade),
            }
        )
    return matched, unmatched


def build_contrast_report(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
    trade_log_sources: Sequence[str],
    sample_sources: Sequence[str],
    top_n: int = 25,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    sample_index, indexed_sample_count = _build_sample_index(sample_rows)
    matched_rows, unmatched_trades = _matched_trade_rows(
        trade_rows=trade_rows,
        sample_index=sample_index,
    )
    feature_names = sorted({name for row in matched_rows for name in row["features"]})
    labels = {
        label_name: _feature_contrast(
            matched_rows,
            label_name=label_name,
            feature_names=feature_names,
            top_n=top_n,
        )
        for label_name in ("bad_loss", "time_exit_loss", "stop_loss_any")
    }
    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "diagnostic_only_not_live_switch_evidence",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "uses_decision_time_features_only": True,
        },
        "inputs": {
            "trade_logs": list(trade_log_sources),
            "sample_caches": list(sample_sources),
        },
        "match_summary": {
            "trade_count": len(trade_rows),
            "sample_count": len(sample_rows),
            "indexed_sample_count": indexed_sample_count,
            "matched_trade_count": len(matched_rows),
            "unmatched_trade_count": len(unmatched_trades),
        },
        "feature_summary": {
            "scanned_feature_count": len(feature_names),
            "scanned_features": feature_names,
            "excluded_feature_fragments": list(LEAKY_FEATURE_FRAGMENTS),
        },
        "labels": labels,
        "unmatched_trades": unmatched_trades,
    }


def load_trade_logs(paths: Sequence[Path]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                if isinstance(row, Mapping):
                    rows.append(row)
    return rows


def _rows_from_pickle_object(obj: Any) -> list[Mapping[str, Any]]:
    if isinstance(obj, list):
        return [row for row in obj if isinstance(row, Mapping)]
    if isinstance(obj, Mapping):
        for key in ("samples", "rows", "records", "data"):
            value = obj.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, Mapping)]
    return []


def load_sample_caches(paths: Sequence[Path]) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for path in paths:
        with path.open("rb") as handle:
            rows.extend(_rows_from_pickle_object(pickle.load(handle)))
    return rows
