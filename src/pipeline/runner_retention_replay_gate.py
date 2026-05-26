from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from src.pipeline import action_policy_replay_gate as replay_gate
from src.pipeline import candidate_meta_label_probe as label_probe
from src.pipeline import candidate_ranker_probe as ranker_probe
from src.pipeline import runner_retention_label_probe as retention_probe


def _episode_meta_score_maps(eval_episodes: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[str, Any]]:
    return replay_gate._empty_path_state_score_maps(eval_episodes)


def _feature_names(train_rows: Sequence[Mapping[str, Any]], eval_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    rows = list(train_rows) + list(eval_rows)
    return label_probe._feature_names(rows)


def _current_price(sample: Mapping[str, Any]) -> float:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    return ranker_probe._as_float(features.get("current_price"), 0.0)


def _candidate_gate_candidate(
    sample: Mapping[str, Any],
    *,
    buy_prob: float,
    runtime_params: Mapping[str, Any],
) -> bool:
    params = runtime_params or {}
    threshold = ranker_probe._as_optional_float(params.get("buy_threshold"))
    near_threshold = ranker_probe._as_optional_float(params.get("buy_near_threshold_min_prob"))
    if threshold is None:
        return False
    if _current_price(sample) <= 0.0:
        return False
    probability = ranker_probe._as_optional_float(buy_prob)
    if probability is None:
        return False
    floor = min(threshold, near_threshold) if near_threshold is not None else threshold
    return probability >= floor


def _candidate_gate_rows_with_indices(
    samples: Sequence[Mapping[str, Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not samples:
        return []
    candidate_samples = ranker_probe.prefilter_candidate_samples(samples, runtime_params)
    buy_probabilities, entry_scores = ranker_probe._score_samples(candidate_samples, buy_artifact)
    rows = []
    for original_index, (sample, buy_prob, entry_score) in enumerate(
        zip(candidate_samples, buy_probabilities, entry_scores)
    ):
        if not _candidate_gate_candidate(
            sample,
            buy_prob=float(buy_prob),
            runtime_params=runtime_params,
        ):
            continue
        row = replay_gate._decision_row_from_sample(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
            original_index=original_index,
        )
        row["features"] = dict(sample.get("features", {}) or {})
        row["source_family"] = "runner_retention_candidate_gate"
        rows.append(row)
    return rows


def _candidate_gate_rows_by_episode(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[list[dict[str, Any]]]:
    sample_triples: list[tuple[int, int, Mapping[str, Any]]] = []
    for episode_index, episode in enumerate(eval_episodes):
        for original_index, sample in enumerate(list(episode[:-1])):
            sample_triples.append((episode_index, original_index, sample))
    rows_by_episode: list[list[dict[str, Any]]] = [[] for _episode in eval_episodes]
    prefiltered = ranker_probe.prefilter_candidate_samples(
        [sample for _episode_index, _original_index, sample in sample_triples],
        runtime_params,
    )
    prefiltered_ids = {id(sample) for sample in prefiltered}
    filtered_triples = [
        (episode_index, original_index, sample)
        for episode_index, original_index, sample in sample_triples
        if id(sample) in prefiltered_ids
    ]
    flat_samples = [sample for _episode_index, _original_index, sample in filtered_triples]
    if not flat_samples:
        return rows_by_episode

    buy_probabilities, entry_scores = ranker_probe._score_samples(flat_samples, buy_artifact)
    for (episode_index, original_index, sample), buy_prob, entry_score in zip(
        filtered_triples,
        buy_probabilities,
        entry_scores,
    ):
        if not _candidate_gate_candidate(
            sample,
            buy_prob=float(buy_prob),
            runtime_params=runtime_params,
        ):
            continue
        row = replay_gate._decision_row_from_sample(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
            original_index=original_index,
        )
        row["features"] = dict(sample.get("features", {}) or {})
        row["source_family"] = "runner_retention_candidate_gate"
        rows_by_episode[episode_index].append(row)
    return rows_by_episode


def _train_rows_with_labels(
    train_samples: Sequence[Mapping[str, Any]],
    train_price_paths_by_token: Mapping[str, Sequence[Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = _candidate_gate_rows_with_indices(
        train_samples,
        buy_artifact,
        runtime_params,
    )
    scored_rows: list[dict[str, Any]] = []
    for row in rows:
        token = str(row.get("token") or "").strip().lower()
        path = train_price_paths_by_token.get(token, [])
        scored = retention_probe.score_runner_retention_candidate(row, path)
        tagged = dict(row)
        tagged.update(scored)
        tagged["label_positive"] = bool(scored.get("runner_retention_positive"))
        tagged["source_family"] = "runner_retention_train"
        scored_rows.append(tagged)
    return scored_rows


def _eval_rows_by_episode(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[list[dict[str, Any]]]:
    return _candidate_gate_rows_by_episode(
        eval_episodes,
        buy_artifact,
        runtime_params,
    )


def _score_rows(
    model,
    medians: Mapping[str, float],
    feature_names: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> list[float]:
    return replay_gate._predict_scores(model, medians, feature_names, rows)


def _row_sort_key(row: Mapping[str, Any]) -> tuple[int, str, float]:
    return (
        int(ranker_probe._as_float(row.get("sample_time"), 0.0)),
        str(row.get("token") or ""),
        float(ranker_probe._as_float(row.get("prob"), 0.0)),
    )


def _evenly_spaced_rows(rows: Sequence[Mapping[str, Any]], limit: int) -> list[Mapping[str, Any]]:
    ordered = sorted(list(rows), key=_row_sort_key)
    if len(ordered) <= int(limit):
        return ordered
    limit = max(0, int(limit))
    if limit <= 0:
        return []
    if limit == 1:
        return [ordered[0]]
    step = (len(ordered) - 1) / float(limit - 1)
    return [ordered[round(index * step)] for index in range(limit)]


def _balanced_training_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    max_negative_count: int | None,
) -> list[Mapping[str, Any]]:
    positives = [row for row in rows if row.get("label_positive")]
    negatives = [row for row in rows if not row.get("label_positive")]
    if max_negative_count is None or len(negatives) <= int(max_negative_count):
        return list(rows)

    limit = max(0, int(max_negative_count))
    by_label: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in negatives:
        by_label[str(row.get("retention_label") or "negative")].append(row)

    selected: list[Mapping[str, Any]] = []
    labels = sorted(by_label)
    per_label = max(1, limit // max(1, len(labels)))
    for label in labels:
        selected.extend(_evenly_spaced_rows(by_label[label], per_label))
    if len(selected) < limit:
        selected_ids = {id(row) for row in selected}
        remaining = [row for row in negatives if id(row) not in selected_ids]
        selected.extend(_evenly_spaced_rows(remaining, limit - len(selected)))
    elif len(selected) > limit:
        selected = _evenly_spaced_rows(selected, limit)
    return sorted(positives + selected, key=_row_sort_key)


def fit_runner_retention_candidate_gate_and_score_episodes(
    *,
    train_samples: Sequence[Mapping[str, Any]],
    train_price_paths_by_token: Mapping[str, Sequence[Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    max_depth: int = 3,
    min_samples_leaf: int = 50,
    min_common_features: int = 2,
    max_train_negative_count: int | None = 1500,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_train_rows = _train_rows_with_labels(
        train_samples,
        train_price_paths_by_token,
        buy_artifact,
        runtime_params,
    )
    raw_label_counts = replay_gate._label_counts(raw_train_rows)
    support_reasons: list[str] = []
    if raw_label_counts["positive"] == 0 or raw_label_counts["negative"] == 0:
        support_reasons.append("train_labels_missing_positive_or_negative")

    rows_by_episode = _episode_meta_score_maps(eval_episodes)
    eval_rows_by_episode = []
    train_rows = list(raw_train_rows)
    if not support_reasons:
        train_rows = _balanced_training_rows(
            raw_train_rows,
            max_negative_count=max_train_negative_count,
        )
        rows_by_episode = _eval_rows_by_episode(eval_episodes, buy_artifact, runtime_params)
        eval_rows = [row for rows in rows_by_episode for row in rows]
        feature_names = _feature_names(train_rows, eval_rows)
        eval_rows_by_episode = rows_by_episode
        if len(feature_names) < int(min_common_features):
            support_reasons.append("common_decision_features_below_min")
    else:
        feature_names = _feature_names(train_rows, [])

    metadata: dict[str, Any] = {
        "trained": False,
        "train_candidate_count": len(train_rows),
        "raw_train_candidate_count": len(raw_train_rows),
        "used_train_candidate_count": len(train_rows),
        "max_train_negative_count": max_train_negative_count,
        "train_source_family_counts": replay_gate._source_family_counts(train_rows),
        "train_label_counts": replay_gate._label_counts(train_rows),
        "raw_train_label_counts": raw_label_counts,
        "feature_names": feature_names,
        "feature_importances": [],
        "support_reasons": support_reasons,
        "intended_use": "runner_retention_path_state_candidate_gate_score_map",
        "live_switch_evidence": False,
    }
    if support_reasons:
        return rows_by_episode, metadata

    model, medians = replay_gate._fit_scorer(
        train_rows,
        feature_names,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
    )
    metadata.update(
        {
            "trained": True,
            "imputed_feature_medians": medians,
            "feature_importances": label_probe._feature_importance_block(model, list(feature_names)),
        }
    )

    score_maps: list[dict[str, Any]] = []
    scored_candidate_count = 0
    for episode, rows in zip(eval_episodes, eval_rows_by_episode):
        score_map: dict[Any, Any] = {
            replay_gate.PATH_STATE_EPISODE_META_KEY: replay_gate._path_state_episode_metadata(episode),
        }
        scored_candidate_count += len(rows)
        if not rows:
            score_maps.append(score_map)
            continue
        scores = _score_rows(model, medians, feature_names, rows)
        score_map.update({
            int(row["original_index"]): float(score)
            for row, score in zip(rows, scores)
        })
        score_maps.append(score_map)
    metadata["scored_candidate_count"] = int(scored_candidate_count)
    metadata["scored_episode_count"] = int(len(eval_episodes))
    return score_maps, metadata


def load_train_price_paths_by_token(lifecycle_paths: Sequence[str | Path]) -> dict[str, list[Any]]:
    lifecycles = retention_probe._load_lifecycles_from_paths(lifecycle_paths)
    return retention_probe._price_paths_by_token(lifecycles)
