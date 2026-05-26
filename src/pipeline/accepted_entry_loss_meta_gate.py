from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from src.pipeline import accepted_entry_feature_contrast as contrast
from src.pipeline import candidate_meta_label_probe as label_probe


PATH_STATE_EPISODE_META_KEY = "__episode_meta__"


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _sample_token(sample: Mapping[str, Any]) -> str:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return str(meta.get("token_address") or meta.get("token") or "").strip().lower()


def _sample_time(sample: Mapping[str, Any]) -> int:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return int(_finite_float(meta.get("sample_time")) or 0)


def _episode_metadata(episode: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = list(episode or [])
    if not ordered:
        return {"token": "", "sample_count": 0, "start_time": 0, "end_time": 0}
    return {
        "token": _sample_token(ordered[0]),
        "sample_count": int(len(ordered)),
        "start_time": _sample_time(ordered[0]),
        "end_time": _sample_time(ordered[-1]),
    }


def _feature_names(rows: Sequence[Mapping[str, Any]], *, min_common_features: int) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        for name, value in row.items():
            if name in {"label_keep", "token", "entry_signal_time", "return_pct", "exit_reason"}:
                continue
            if _finite_float(value) is None:
                continue
            counts[name] = counts.get(name, 0) + 1
    min_count = max(1, int(min_common_features))
    return sorted(name for name, count in counts.items() if count >= min_count)


def _training_rows(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    train_samples: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sample_index, indexed_sample_count = contrast._build_sample_index(train_samples)
    matched, unmatched = contrast._matched_trade_rows(
        trade_rows=trade_rows,
        sample_index=sample_index,
    )
    rows = []
    for row in matched:
        keep = not bool(row.get("labels", {}).get("bad_loss"))
        rows.append(
            {
                **dict(row.get("features", {}) or {}),
                "label_keep": keep,
                "token": str(row.get("trade", {}).get("token") or "").strip().lower(),
                "entry_signal_time": row.get("trade", {}).get("entry_signal_time"),
                "return_pct": row.get("trade", {}).get("return_pct"),
                "exit_reason": row.get("trade", {}).get("exit_reason"),
            }
        )
    return rows, {
        "trade_count": len(trade_rows),
        "sample_count": len(train_samples),
        "indexed_sample_count": indexed_sample_count,
        "matched_trade_count": len(matched),
        "unmatched_trade_count": len(unmatched),
    }


def _feature_importance(model: Any, feature_names: Sequence[str]) -> list[dict[str, Any]]:
    importances = getattr(model, "feature_importances_", None) or []
    rows = [
        {"feature": feature, "importance": float(importance)}
        for feature, importance in zip(feature_names, importances)
        if float(importance) > 0.0
    ]
    return sorted(rows, key=lambda row: row["importance"], reverse=True)


def fit_keep_scorer_and_score_episodes(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    train_samples: Sequence[Mapping[str, Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    max_depth: int = 2,
    min_samples_leaf: int = 8,
    min_common_features: int = 10,
) -> tuple[list[dict[Any, Any]], dict[str, Any]]:
    rows, match_summary = _training_rows(trade_rows=trade_rows, train_samples=train_samples)
    keep_count = sum(1 for row in rows if row.get("label_keep"))
    skip_count = len(rows) - keep_count
    if keep_count <= 0 or skip_count <= 0:
        raise ValueError("accepted-entry loss scorer requires both keep and skip training examples")

    feature_names = _feature_names(rows, min_common_features=min_common_features)
    if not feature_names:
        raise ValueError("accepted-entry loss scorer found no finite decision-time features")

    x_train, medians = label_probe._feature_matrix(rows, feature_names)
    y_train = np.asarray([1 if row.get("label_keep") else 0 for row in rows], dtype=int)
    model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    model.fit(x_train, y_train)

    score_maps: list[dict[Any, Any]] = []
    for episode in eval_episodes:
        episode_map: dict[Any, Any] = {PATH_STATE_EPISODE_META_KEY: _episode_metadata(episode)}
        feature_rows = []
        for sample in episode:
            sample_features = contrast._sample_feature_values(sample)
            feature_rows.append({name: sample_features.get(name) for name in feature_names})
        if feature_rows:
            x_episode, _ = label_probe._feature_matrix(
                feature_rows,
                list(feature_names),
                medians=dict(medians),
            )
            scores = model.predict_positive_probability(x_episode).reshape(-1)
            for sample_index, score in enumerate(scores):
                episode_map[int(sample_index)] = float(score)
        score_maps.append(episode_map)

    metadata = {
        "model": {
            "type": "SmallDecisionTree",
            "target": "keep_probability_from_accepted_entry_outcome",
            "feature_names": list(feature_names),
            "imputed_feature_medians": dict(medians),
            "feature_importances": _feature_importance(model, feature_names),
            "max_depth": int(max_depth),
            "min_samples_leaf": int(min_samples_leaf),
        },
        "train_match_summary": match_summary,
        "train_label_counts": {
            "total": len(rows),
            "keep": keep_count,
            "skip": skip_count,
        },
        "score_maps_summary": {
            "episode_count": len(score_maps),
            "scored_sample_count": sum(
                1
                for score_map in score_maps
                for key in score_map
                if isinstance(key, int)
            ),
            "non_empty_episode_count": sum(
                1
                for score_map in score_maps
                if any(isinstance(key, int) for key in score_map)
            ),
        },
    }
    return score_maps, metadata
