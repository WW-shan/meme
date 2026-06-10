from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

from src.pipeline import moonshot_local_runner_baseline as baseline


TOP_K_DEFAULTS = (10, 25, 50, 100)
VALID_DEDUPE_POLICIES = {"max_events", "max_multiple", "min_multiple"}


def _normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def _event_count(row: Dict) -> int:
    try:
        return int(row.get("_event_count", row.get("event_count", 0)) or 0)
    except (TypeError, ValueError):
        return 0


def _launch_time(row: Dict) -> int:
    try:
        return int(float(row.get("launch_time", 0) or 0))
    except (TypeError, ValueError):
        return 0


def _row_sort_key(row: Dict) -> Tuple[str, str, int, float, int]:
    return (
        str(row.get("chain") or "bsc").lower(),
        _normalize_address(row.get("token_address")),
        _launch_time(row),
        _float_value(row.get("max_multiple")),
        _event_count(row),
    )


def _dedupe_key(row: Dict) -> Tuple[str, str]:
    return (str(row.get("chain") or "bsc").lower(), _normalize_address(row.get("token_address")))


def _choose(rows: Sequence[Dict], policy: str) -> Dict:
    if policy == "max_events":
        return sorted(rows, key=lambda row: (_event_count(row), _float_value(row.get("max_multiple")), _launch_time(row)))[-1]
    if policy == "max_multiple":
        return sorted(rows, key=lambda row: (_float_value(row.get("max_multiple")), _event_count(row), _launch_time(row)))[-1]
    if policy == "min_multiple":
        return sorted(rows, key=lambda row: (_float_value(row.get("max_multiple")), -_event_count(row), _launch_time(row)))[0]
    raise ValueError(f"unknown dedupe policy: {policy}")


def dedupe_label_rows(rows: Iterable[Dict], policy: str = "max_events") -> Tuple[List[Dict], Dict]:
    if policy not in VALID_DEDUPE_POLICIES:
        raise ValueError(f"unknown dedupe policy: {policy}")
    groups: Dict[Tuple[str, str], List[Dict]] = {}
    for row in rows or []:
        key = _dedupe_key(row)
        if not key[1]:
            continue
        groups.setdefault(key, []).append(dict(row))
    selected = [_choose(group, policy) for group in groups.values()]
    duplicate_groups = [group for group in groups.values() if len(group) > 1]
    conflicts = [
        group
        for group in duplicate_groups
        if min(_float_value(row.get("max_multiple")) for row in group) > 0
        and (
            max(_float_value(row.get("max_multiple")) for row in group)
            - min(_float_value(row.get("max_multiple")) for row in group)
        )
        / min(_float_value(row.get("max_multiple")) for row in group)
        > 0.20
    ]
    summary = {
        "policy": policy,
        "input_row_count": sum(len(group) for group in groups.values()),
        "output_token_count": len(selected),
        "duplicate_token_count": len(duplicate_groups),
        "conflict_token_count": len(conflicts),
    }
    return sorted([dict(row) for row in selected], key=_row_sort_key), summary


def dedupe_sensitivity(rows: Iterable[Dict]) -> Dict[str, Dict[str, int]]:
    row_list = [dict(row) for row in rows or []]
    result = {}
    for policy in sorted(VALID_DEDUPE_POLICIES):
        selected, _ = dedupe_label_rows(row_list, policy=policy)
        result[policy] = {
            ">=10x": sum(1 for row in selected if _float_value(row.get("max_multiple")) >= 10.0),
            "token_count": len(selected),
        }
    return result


def _score_row(row: Dict, score_key: str | None = None) -> float:
    if score_key and score_key in row:
        return _float_value(row.get(score_key))
    return _float_value(baseline.score_snapshot(row).get("score"))


def _row_hit_10x(row: Dict) -> bool:
    return bool((row.get("label") or {}).get("hit_10x"))


def collapse_snapshots_to_tokens(rows: Iterable[Dict], *, score_key: str | None = None) -> List[Dict]:
    best: Dict[Tuple[str, str], Dict] = {}
    for row in rows or []:
        key = _dedupe_key(row)
        if not key[1]:
            continue
        score = _score_row(row, score_key=score_key)
        candidate = dict(row)
        candidate["token_score"] = score
        candidate["chosen_snapshot_time"] = candidate.get("snapshot_time")
        existing = best.get(key)
        snapshot_time = int(candidate.get("snapshot_time", 0) or 0)
        existing_time = int((existing or {}).get("chosen_snapshot_time", 0) or 0)
        if existing is None or (score, -snapshot_time) > (_float_value(existing.get("token_score")), -existing_time):
            best[key] = candidate
    return sorted(best.values(), key=lambda row: (_launch_time(row.get("label") or {}), str(row.get("token_address"))))


def group_time_split(rows: Iterable[Dict], validation_ratio: float = 0.2) -> Tuple[List[Dict], List[Dict], Dict]:
    row_list = sorted(list(rows or []), key=lambda row: (_launch_time(row.get("label") or row), str(row.get("token_address"))))
    if not row_list:
        return [], [], {"token_overlap": 0, "train_tokens": 0, "validation_tokens": 0}
    ratio = max(0.0, min(1.0, float(validation_ratio)))
    validation_count = max(1, int(math.ceil(len(row_list) * ratio))) if ratio > 0 else 0
    split_at = max(0, len(row_list) - validation_count)
    train = row_list[:split_at]
    validation = row_list[split_at:]
    train_tokens = {str(row.get("token_address")) for row in train}
    validation_tokens = {str(row.get("token_address")) for row in validation}
    split = {
        "token_overlap": len(train_tokens & validation_tokens),
        "train_tokens": len(train_tokens),
        "validation_tokens": len(validation_tokens),
    }
    return train, validation, split


def evaluate_token_level(rows: Iterable[Dict], top_k_values: Sequence[int] = TOP_K_DEFAULTS) -> Dict:
    token_rows = list(rows or [])
    if not token_rows:
        return {"decision": "invalid_input", "token_count": 0, "positive_count": 0, "metrics": {}}
    positives = sum(1 for row in token_rows if _row_hit_10x(row))
    base_rate = positives / float(len(token_rows)) if token_rows else 0.0
    train, validation, split = group_time_split(token_rows)
    eval_rows = validation or token_rows
    scores = [row.get("token_score", 0.0) for row in eval_rows]
    metrics = {}
    for k in top_k_values:
        metrics[f"precision_at_{int(k)}"] = baseline.precision_at_k(eval_rows, scores, int(k))
        metrics[f"lift_at_{int(k)}"] = baseline.lift_at_k(eval_rows, scores, int(k))
    return {
        "decision": "research_baseline_only" if positives else "insufficient_positive_support",
        "token_count": len(token_rows),
        "positive_count": positives,
        "base_positive_rate": base_rate,
        "split": split,
        "validation_token_count": len(eval_rows),
        "validation_positive_count": sum(1 for row in eval_rows if _row_hit_10x(row)),
        "metrics": metrics,
    }
