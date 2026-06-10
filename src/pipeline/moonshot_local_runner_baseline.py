from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple


def _features(row: Dict) -> Dict:
    if isinstance(row.get("features"), dict):
        return row["features"]
    return row


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def _positive_log(value: object) -> float:
    return math.log1p(max(0.0, _float_value(value)))


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def score_snapshot(row: Dict) -> Dict:
    features = _features(row)
    price_change = _clamp(_float_value(features.get("price_change_300s_pct")), -100.0, 1000.0)
    sell_pressure_60s = _clamp(_float_value(features.get("sell_pressure_60s")), 0.0, 1.0)
    sell_pressure_300s = _clamp(_float_value(features.get("sell_pressure_300s")), 0.0, 1.0)

    components = {
        "buy_volume_60s": 1.20 * _positive_log(features.get("buy_volume_60s")),
        "buy_volume_300s": 1.40 * _positive_log(features.get("buy_volume_300s")),
        "unique_buyers_60s": 1.50 * _positive_log(features.get("unique_buyers_60s")),
        "unique_buyers_300s": 1.80 * _positive_log(features.get("unique_buyers_300s")),
        "price_change_300s_pct": 0.85 * (price_change / 100.0),
        "sell_pressure_60s": -3.00 * sell_pressure_60s,
        "sell_pressure_300s": -2.25 * sell_pressure_300s,
    }

    if features.get("top_holder_concentration") is not None:
        concentration = _clamp(_float_value(features.get("top_holder_concentration")), 0.0, 1.0)
        components["top_holder_concentration"] = -2.50 * concentration

    score = sum(components.values())
    return {
        "score": score,
        "components": components,
    }


def _is_positive(row: Dict) -> bool:
    label = row.get("label") or {}
    return bool(label.get("hit_10x"))


def _score_value(value: object) -> float:
    if isinstance(value, dict):
        return _float_value(value.get("score"))
    return _float_value(value)


def _score_pairs(rows: Sequence[Dict], scores: object) -> List[Tuple[Dict, float]]:
    if isinstance(scores, dict):
        pairs = []
        for index, row in enumerate(rows):
            token_address = str(row.get("token_address", ""))
            score = scores.get(token_address, scores.get(index, 0.0))
            pairs.append((row, _score_value(score)))
        return pairs
    score_list = list(scores or [])
    return [(row, _score_value(score_list[index] if index < len(score_list) else 0.0)) for index, row in enumerate(rows)]


def precision_at_k(rows: Sequence[Dict], scores: object, k: int) -> float:
    row_list = list(rows or [])
    if not row_list or int(k) <= 0:
        return 0.0
    pairs = sorted(
        _score_pairs(row_list, scores),
        key=lambda item: (-item[1], str(item[0].get("token_address", ""))),
    )
    top = pairs[: min(int(k), len(pairs))]
    if not top:
        return 0.0
    return sum(1 for row, _ in top if _is_positive(row)) / float(len(top))


def lift_at_k(rows: Sequence[Dict], scores: object, k: int) -> float:
    row_list = list(rows or [])
    if not row_list:
        return 0.0
    base_rate = sum(1 for row in row_list if _is_positive(row)) / float(len(row_list))
    if base_rate <= 0:
        return 0.0
    return precision_at_k(row_list, scores, k) / base_rate


def _snapshot_sort_key(row: Dict) -> Tuple[int, str]:
    try:
        snapshot_time = int(row.get("snapshot_time", 0) or 0)
    except (TypeError, ValueError):
        snapshot_time = 0
    return (snapshot_time, str(row.get("token_address", "")))


def time_split_rows(rows: Iterable[Dict], validation_ratio: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
    row_list = sorted(list(rows or []), key=_snapshot_sort_key)
    if not row_list:
        return [], []
    ratio = _clamp(float(validation_ratio), 0.0, 1.0)
    validation_count = max(1, int(math.ceil(len(row_list) * ratio))) if ratio > 0 else 0
    if validation_count >= len(row_list):
        return [], row_list
    split_at = len(row_list) - validation_count
    return row_list[:split_at], row_list[split_at:]


def evaluate_baseline(rows: Iterable[Dict], top_k_values: Sequence[int] = (10, 25, 50, 100)) -> Dict:
    row_list = list(rows or [])
    if not row_list:
        return {
            "decision": "invalid_input",
            "row_count": 0,
            "positive_count": 0,
            "base_positive_rate": 0.0,
            "metrics": {},
        }

    positive_count = sum(1 for row in row_list if _is_positive(row))
    base_rate = positive_count / float(len(row_list))
    if positive_count <= 0:
        return {
            "decision": "insufficient_positive_support",
            "row_count": len(row_list),
            "positive_count": 0,
            "base_positive_rate": 0.0,
            "metrics": {},
        }

    train_rows, validation_rows = time_split_rows(row_list)
    eval_rows = validation_rows or row_list
    score_details = [score_snapshot(row) for row in eval_rows]
    scores = [detail["score"] for detail in score_details]
    metrics = {}
    for k in top_k_values:
        k_value = int(k)
        metrics[f"precision_at_{k_value}"] = precision_at_k(eval_rows, scores, k_value)
        metrics[f"lift_at_{k_value}"] = lift_at_k(eval_rows, scores, k_value)

    return {
        "decision": "research_baseline_only",
        "row_count": len(row_list),
        "positive_count": positive_count,
        "base_positive_rate": base_rate,
        "train_count": len(train_rows),
        "validation_count": len(eval_rows),
        "validation_positive_count": sum(1 for row in eval_rows if _is_positive(row)),
        "metrics": metrics,
        "top_validation_rows": [
            {
                "token_address": row.get("token_address"),
                "snapshot_time": row.get("snapshot_time"),
                "hit_10x": _is_positive(row),
                "score": detail["score"],
                "components": detail["components"],
            }
            for row, detail in sorted(
                zip(eval_rows, score_details),
                key=lambda item: (-item[1]["score"], str(item[0].get("token_address", ""))),
            )[:10]
        ],
    }
