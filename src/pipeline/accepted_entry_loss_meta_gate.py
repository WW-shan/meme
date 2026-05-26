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


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    keep_count = sum(1 for row in rows if row.get("label_keep"))
    total = len(rows)
    return {"total": total, "keep": keep_count, "skip": total - keep_count}


def _sorted_training_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    def sort_key(row: Mapping[str, Any]) -> tuple[float, str]:
        return (
            _finite_float(row.get("entry_signal_time")) or _finite_float(row.get("sample_time")) or 0.0,
            str(row.get("token") or ""),
        )

    return sorted(rows, key=sort_key)


def _window_training_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    window_count: int,
    min_samples_leaf: int,
) -> list[tuple[str, list[Mapping[str, Any]]]]:
    ordered = _sorted_training_rows(rows)
    windows: list[tuple[str, list[Mapping[str, Any]]]] = [("full", list(ordered))]
    count = max(1, int(window_count))
    if count <= 1 or not ordered:
        return windows

    min_rows = max(2, int(min_samples_leaf) * 2)
    total = len(ordered)
    for index in range(count):
        start = int(total * index / count)
        end = int(total * (index + 1) / count)
        window = list(ordered[start:end])
        labels = _label_counts(window)
        if labels["total"] < min_rows or labels["keep"] <= 0 or labels["skip"] <= 0:
            continue
        windows.append((f"window_{index + 1}_of_{count}", window))
    return windows


def _lower_quantile(values: Sequence[float], quantile: float) -> float:
    if not values:
        return 0.0
    bounded = min(1.0, max(0.0, float(quantile)))
    ordered = sorted(float(value) for value in values)
    index = int(math.floor((len(ordered) - 1) * bounded))
    return float(ordered[index])


def _fit_window_model(
    rows: Sequence[Mapping[str, Any]],
    *,
    max_depth: int,
    min_samples_leaf: int,
    min_common_features: int,
) -> dict[str, Any] | None:
    labels = _label_counts(rows)
    if labels["keep"] <= 0 or labels["skip"] <= 0:
        return None
    feature_names = _feature_names(rows, min_common_features=min_common_features)
    if not feature_names:
        return None
    x_train, medians = label_probe._feature_matrix(rows, feature_names)
    y_train = np.asarray([1 if row.get("label_keep") else 0 for row in rows], dtype=int)
    model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    model.fit(x_train, y_train)
    return {
        "model": model,
        "feature_names": list(feature_names),
        "medians": dict(medians),
        "label_counts": labels,
        "feature_importances": _feature_importance(model, feature_names),
    }


def _score_episode_with_lcb_models(
    episode: Sequence[Mapping[str, Any]],
    model_rows: Sequence[Mapping[str, Any]],
    *,
    lcb_quantile: float,
) -> dict[Any, Any]:
    episode_map: dict[Any, Any] = {PATH_STATE_EPISODE_META_KEY: _episode_metadata(episode)}
    for sample_index, sample in enumerate(episode):
        sample_features = contrast._sample_feature_values(sample)
        scores = []
        for row in model_rows:
            feature_names = list(row["feature_names"])
            x_sample, _ = label_probe._feature_matrix(
                [{name: sample_features.get(name) for name in feature_names}],
                feature_names,
                medians=dict(row["medians"]),
            )
            scores.append(float(row["model"].predict_positive_probability(x_sample).reshape(-1)[0]))
        episode_map[int(sample_index)] = _lower_quantile(scores, lcb_quantile)
    return episode_map


def _combined_feature_importance(model_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for row in model_rows:
        for item in row.get("feature_importances", []) or []:
            feature = str(item.get("feature") or "")
            if not feature:
                continue
            totals[feature] = totals.get(feature, 0.0) + float(item.get("importance") or 0.0)
            counts[feature] = counts.get(feature, 0) + 1
    combined = [
        {
            "feature": feature,
            "mean_importance": totals[feature] / max(1, counts[feature]),
            "model_count": counts[feature],
        }
        for feature in totals
    ]
    return sorted(combined, key=lambda row: (row["mean_importance"], row["model_count"]), reverse=True)


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


def fit_keep_lcb_scorer_and_score_episodes(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    train_samples: Sequence[Mapping[str, Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    max_depth: int = 2,
    min_samples_leaf: int = 8,
    min_common_features: int = 10,
    window_count: int = 4,
    lcb_quantile: float = 0.25,
) -> tuple[list[dict[Any, Any]], dict[str, Any]]:
    rows, match_summary = _training_rows(trade_rows=trade_rows, train_samples=train_samples)
    label_counts = _label_counts(rows)
    if label_counts["keep"] <= 0 or label_counts["skip"] <= 0:
        raise ValueError("accepted-entry loss scorer requires both keep and skip training examples")

    model_rows = []
    window_metadata = []
    for window_name, window_rows in _window_training_rows(
        rows,
        window_count=window_count,
        min_samples_leaf=min_samples_leaf,
    ):
        fitted = _fit_window_model(
            window_rows,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            min_common_features=min_common_features,
        )
        if fitted is None:
            continue
        fitted["window_name"] = window_name
        model_rows.append(fitted)
        window_metadata.append(
            {
                "window_name": window_name,
                "row_count": int(len(window_rows)),
                "label_counts": dict(fitted["label_counts"]),
                "feature_names": list(fitted["feature_names"]),
                "feature_importances": list(fitted["feature_importances"]),
            }
        )
    if not model_rows:
        raise ValueError("accepted-entry LCB scorer found no stable train windows")

    score_maps = [
        _score_episode_with_lcb_models(episode, model_rows, lcb_quantile=lcb_quantile)
        for episode in eval_episodes
    ]
    metadata = {
        "model": {
            "type": "SmallDecisionTreeEnsemble",
            "target": "lower_confidence_keep_probability_from_accepted_entry_outcome",
            "score_aggregation": "lower_quantile",
            "lcb_quantile": float(lcb_quantile),
            "max_depth": int(max_depth),
            "min_samples_leaf": int(min_samples_leaf),
            "min_common_features": int(min_common_features),
            "window_count": int(window_count),
            "ensemble_model_count": int(len(model_rows)),
            "windows": window_metadata,
            "feature_importances": _combined_feature_importance(model_rows),
        },
        "train_match_summary": match_summary,
        "train_label_counts": {
            "total": int(label_counts["total"]),
            "keep": int(label_counts["keep"]),
            "skip": int(label_counts["skip"]),
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
