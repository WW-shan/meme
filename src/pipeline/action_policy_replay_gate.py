from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from src.pipeline import action_policy_reward_probe as reward_probe
from src.pipeline import action_policy_router_probe as router_probe
from src.pipeline import candidate_meta_label_probe as label_probe
from src.pipeline import candidate_ranker_probe as ranker_probe


DECISION_TIME_FIELDS = reward_probe.DECISION_TIME_FIELDS
PATH_STATE_EPISODE_META_KEY = "__episode_meta__"


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _source_family_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("source_family") or "") for row in rows)
    return dict(sorted(counts.items()))


def _label_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    positives = sum(1 for row in rows if row.get("label_positive"))
    total = len(rows)
    return {"total": total, "positive": positives, "negative": total - positives}


def _empty_score_maps(eval_episodes: Sequence[Sequence[Mapping[str, Any]]]) -> list[dict[int, float]]:
    return [{} for _episode in eval_episodes]


def _path_state_episode_metadata(episode: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = list(episode or [])
    if not ordered:
        return {"token": "", "sample_count": 0, "start_time": 0, "end_time": 0}
    first_meta = ordered[0].get("meta", {}) if isinstance(ordered[0], Mapping) else {}
    last_meta = ordered[-1].get("meta", {}) if isinstance(ordered[-1], Mapping) else {}
    return {
        "token": str(first_meta.get("token_address") or "").strip().lower(),
        "sample_count": int(len(ordered)),
        "start_time": int(_finite_float(first_meta.get("sample_time")) or 0),
        "end_time": int(_finite_float(last_meta.get("sample_time")) or 0),
    }


def _empty_path_state_score_maps(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    return [{PATH_STATE_EPISODE_META_KEY: _path_state_episode_metadata(episode)} for episode in eval_episodes]


def _fit_scorer(
    train_rows: Sequence[Mapping[str, Any]],
    feature_names: Sequence[str],
    *,
    max_depth: int,
    min_samples_leaf: int,
) -> tuple[label_probe._SmallDecisionTree, dict[str, float]]:
    x_train, medians = label_probe._feature_matrix(list(train_rows), list(feature_names))
    y_train = np.asarray([1 if row.get("label_positive") else 0 for row in train_rows], dtype=int)
    model = label_probe._SmallDecisionTree(max_depth=max_depth, min_samples_leaf=min_samples_leaf)
    model.fit(x_train, y_train)
    return model, medians


def _predict_scores(
    model: label_probe._SmallDecisionTree,
    medians: Mapping[str, float],
    feature_names: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> list[float]:
    if not rows:
        return []
    x_rows, _ = label_probe._feature_matrix(list(rows), list(feature_names), medians=dict(medians))
    return [float(value) for value in model.predict_positive_probability(x_rows).reshape(-1)]


def _runtime_float(runtime_params: Mapping[str, Any], key: str) -> float | None:
    return _finite_float((runtime_params or {}).get(key))


def _passes_floor(value: Any, floor: Any) -> bool:
    floor_value = _finite_float(floor)
    if floor_value is None:
        return True
    parsed = _finite_float(value)
    return parsed is not None and parsed >= floor_value


def _sample_age_seconds(sample: Mapping[str, Any]) -> float | None:
    age = ranker_probe._sample_age_seconds(sample)
    return float(age) if math.isfinite(float(age)) else None


def _token(sample: Mapping[str, Any]) -> str:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return str(meta.get("token_address") or meta.get("token") or "").strip().lower()


def _sample_time(sample: Mapping[str, Any]) -> int:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return int(ranker_probe._as_float(meta.get("sample_time"), 0.0))


def _current_price(sample: Mapping[str, Any]) -> float:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    return ranker_probe._as_float(features.get("current_price"), 0.0)


def _low_volume_candidate(
    sample: Mapping[str, Any],
    *,
    buy_prob: float,
    entry_score: float,
    runtime_params: Mapping[str, Any],
) -> bool:
    params = runtime_params or {}
    threshold = _runtime_float(params, "buy_threshold")
    min_prob = _runtime_float(params, "buy_low_volume_rescue_min_prob")
    base_volume_floor = _runtime_float(params, "min_entry_volume_30s")
    rescue_volume_floor = _runtime_float(params, "buy_low_volume_rescue_min_entry_volume_30s")
    rescue_volume_ceiling = _runtime_float(params, "buy_low_volume_rescue_max_entry_volume_30s")
    rescue_volatility_floor = _runtime_float(params, "buy_low_volume_rescue_min_entry_price_volatility")
    rescue_age_ceiling = _runtime_float(params, "buy_low_volume_rescue_max_age_seconds")
    if (
        threshold is None
        or min_prob is None
        or base_volume_floor is None
        or rescue_volume_floor is None
        or rescue_volume_ceiling is None
        or rescue_volatility_floor is None
        or rescue_age_ceiling is None
    ):
        return False
    if _current_price(sample) <= 0.0:
        return False
    probability = _finite_float(buy_prob)
    if probability is None or probability < threshold or probability < min_prob:
        return False
    if not _passes_floor(entry_score, params.get("min_entry_score")):
        return False

    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    volume = _finite_float(features.get("volume_30s"))
    if (
        volume is None
        or volume >= base_volume_floor
        or volume < rescue_volume_floor
        or volume > rescue_volume_ceiling
    ):
        return False
    volatility = _finite_float(features.get("price_volatility"))
    if volatility is None or volatility < rescue_volatility_floor:
        return False
    age_seconds = _sample_age_seconds(sample)
    if age_seconds is None or age_seconds > rescue_age_ceiling:
        return False
    return True


def _decision_row_from_sample(
    sample: Mapping[str, Any],
    *,
    buy_prob: float,
    entry_score: float,
    runtime_params: Mapping[str, Any],
    original_index: int,
) -> dict[str, Any]:
    features = dict(sample.get("features", {}) or {})
    row = {field: features.get(field) for field in DECISION_TIME_FIELDS if field in features}
    age_seconds = _sample_age_seconds(sample)
    row.update(
        {
            "token": _token(sample),
            "sample_time": _sample_time(sample),
            "prob": float(buy_prob),
            "pred_return": float(entry_score),
            "volume_30s": features.get("volume_30s"),
            "entry_volume_30s": features.get("volume_30s"),
            "price_volatility": features.get("price_volatility"),
            "entry_price_volatility": features.get("price_volatility"),
            "token_age_seconds": age_seconds,
            "age_seconds": age_seconds,
            "feature_count": len(features),
            "near_threshold_rescue_used": False,
            "use_pred_return_filter": runtime_params.get("min_entry_score") is not None,
            "min_pred_return": runtime_params.get("min_entry_score"),
            "min_entry_volume_30s": runtime_params.get("min_entry_volume_30s"),
            "min_entry_price_volatility": runtime_params.get("min_entry_price_volatility"),
            "buy_near_threshold_min_prob": runtime_params.get("buy_near_threshold_min_prob"),
            "buy_near_min_pred_return": runtime_params.get("buy_near_min_pred_return"),
            "buy_near_min_entry_volume_30s": runtime_params.get("buy_near_min_entry_volume_30s"),
            "buy_near_min_entry_price_volatility": runtime_params.get("buy_near_min_entry_price_volatility"),
            "buy_near_min_age_seconds": runtime_params.get("buy_near_min_age_seconds"),
            "flow_metrics_available": any(str(name).startswith("flow_") for name in features),
            "source_family": "replay_low_volume",
            "original_index": int(original_index),
        }
    )
    return row


def low_volume_action_policy_rows_with_indices(
    samples: Sequence[Mapping[str, Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not samples:
        return []
    buy_probabilities, entry_scores = ranker_probe._score_samples(samples, buy_artifact)
    rows = []
    for original_index, (sample, buy_prob, entry_score) in enumerate(
        zip(samples, buy_probabilities, entry_scores)
    ):
        if not _low_volume_candidate(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
        ):
            continue
        rows.append(
            _decision_row_from_sample(
                sample,
                buy_prob=float(buy_prob),
                entry_score=float(entry_score),
                runtime_params=runtime_params,
                original_index=original_index,
            )
        )
    return rows


def _candidate_gate_candidate(
    sample: Mapping[str, Any],
    *,
    buy_prob: float,
    runtime_params: Mapping[str, Any],
) -> bool:
    params = runtime_params or {}
    threshold = _runtime_float(params, "buy_threshold")
    near_threshold = _runtime_float(params, "buy_near_threshold_min_prob")
    if threshold is None:
        return False
    if _current_price(sample) <= 0.0:
        return False
    probability = _finite_float(buy_prob)
    if probability is None:
        return False
    floor = min(threshold, near_threshold) if near_threshold is not None else threshold
    return probability >= floor


def candidate_gate_action_policy_rows_with_indices(
    samples: Sequence[Mapping[str, Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not samples:
        return []
    buy_probabilities, entry_scores = ranker_probe._score_samples(samples, buy_artifact)
    rows = []
    for original_index, (sample, buy_prob, entry_score) in enumerate(
        zip(samples, buy_probabilities, entry_scores)
    ):
        if not _candidate_gate_candidate(
            sample,
            buy_prob=float(buy_prob),
            runtime_params=runtime_params,
        ):
            continue
        row = _decision_row_from_sample(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
            original_index=original_index,
        )
        row["source_family"] = "replay_candidate_gate"
        rows.append(row)
    return rows


def _candidate_gate_action_policy_rows_by_episode(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> list[list[dict[str, Any]]]:
    flat_samples: list[Mapping[str, Any]] = []
    sample_refs: list[tuple[int, int]] = []
    for episode_index, episode in enumerate(eval_episodes):
        for original_index, sample in enumerate(list(episode[:-1])):
            flat_samples.append(sample)
            sample_refs.append((episode_index, original_index))
    rows_by_episode: list[list[dict[str, Any]]] = [[] for _episode in eval_episodes]
    if not flat_samples:
        return rows_by_episode

    buy_probabilities, entry_scores = ranker_probe._score_samples(flat_samples, buy_artifact)
    for (episode_index, original_index), sample, buy_prob, entry_score in zip(
        sample_refs,
        flat_samples,
        buy_probabilities,
        entry_scores,
    ):
        if not _candidate_gate_candidate(
            sample,
            buy_prob=float(buy_prob),
            runtime_params=runtime_params,
        ):
            continue
        row = _decision_row_from_sample(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
            original_index=original_index,
        )
        row["source_family"] = "replay_candidate_gate"
        rows_by_episode[episode_index].append(row)
    return rows_by_episode


def fit_action_policy_model_and_score_episodes(
    *,
    train_rejected_reports: Iterable[Mapping[str, Any]],
    train_accepted_reports: Iterable[Mapping[str, Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    train_rejected_source_names: Iterable[str] | None = None,
    train_accepted_source_names: Iterable[str] | None = None,
    max_depth: int = 3,
    min_samples_leaf: int = 50,
    min_common_features: int = 2,
) -> tuple[list[dict[int, float]], dict[str, Any]]:
    train_rejected, train_rejected_names = reward_probe._normalize_rows(
        reports=train_rejected_reports,
        source_family="rejected",
        split="train",
        source_names=train_rejected_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_accepted, train_accepted_names = reward_probe._normalize_rows(
        reports=train_accepted_reports,
        source_family="accepted",
        split="train",
        source_names=train_accepted_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_rows = train_rejected + train_accepted
    feature_names = reward_probe._feature_names(train_rows, train_rows)
    label_counts = _label_counts(train_rows)
    support_reasons = []
    if label_counts["positive"] == 0 or label_counts["negative"] == 0:
        support_reasons.append("train_labels_missing_positive_or_negative")
    if len(feature_names) < int(min_common_features):
        support_reasons.append("common_decision_features_below_min")

    metadata: dict[str, Any] = {
        "trained": False,
        "train_candidate_count": len(train_rows),
        "train_source_family_counts": _source_family_counts(train_rows),
        "train_label_counts": label_counts,
        "feature_names": feature_names,
        "feature_importances": [],
        "source_groups": {
            "train_rejected": train_rejected_names,
            "train_accepted": train_accepted_names,
        },
        "support_reasons": support_reasons,
        "intended_use": "low_volume_rescue_score_map_for_replay_only",
        "live_switch_evidence": False,
    }
    if support_reasons:
        return _empty_path_state_score_maps(eval_episodes), metadata

    model, medians = _fit_scorer(
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

    score_maps = []
    scored_candidate_count = 0
    for episode in eval_episodes:
        enterable_episode = list(episode[:-1])
        rows = low_volume_action_policy_rows_with_indices(
            enterable_episode,
            buy_artifact,
            runtime_params,
        )
        scored_candidate_count += len(rows)
        if not rows:
            score_maps.append({})
            continue
        scores = _predict_scores(model, medians, feature_names, rows)
        score_maps.append({
            int(row["original_index"]): float(score)
            for row, score in zip(rows, scores)
        })
    metadata["scored_candidate_count"] = int(scored_candidate_count)
    metadata["scored_episode_count"] = int(len(eval_episodes))
    return score_maps, metadata


def fit_action_policy_candidate_gate_and_score_episodes(
    *,
    train_rejected_reports: Iterable[Mapping[str, Any]],
    train_accepted_reports: Iterable[Mapping[str, Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    train_rejected_source_names: Iterable[str] | None = None,
    train_accepted_source_names: Iterable[str] | None = None,
    max_depth: int = 3,
    min_samples_leaf: int = 50,
    min_common_features: int = 2,
) -> tuple[list[dict[int, float]], dict[str, Any]]:
    train_rejected, train_rejected_names = reward_probe._normalize_rows(
        reports=train_rejected_reports,
        source_family="rejected",
        split="train",
        source_names=train_rejected_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_accepted, train_accepted_names = reward_probe._normalize_rows(
        reports=train_accepted_reports,
        source_family="accepted",
        split="train",
        source_names=train_accepted_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_rows = train_rejected + train_accepted
    label_counts = _label_counts(train_rows)
    support_reasons = []
    if label_counts["positive"] == 0 or label_counts["negative"] == 0:
        support_reasons.append("train_labels_missing_positive_or_negative")
    if support_reasons:
        feature_names = reward_probe._feature_names(train_rows, train_rows)
        rows_by_episode: list[list[dict[str, Any]]] = [[] for _episode in eval_episodes]
    else:
        rows_by_episode = _candidate_gate_action_policy_rows_by_episode(
            eval_episodes,
            buy_artifact,
            runtime_params,
        )
        eval_rows = [row for rows in rows_by_episode for row in rows]
        feature_names = reward_probe._feature_names(train_rows, eval_rows)
        if len(feature_names) < int(min_common_features):
            support_reasons.append("common_decision_features_below_min")

    metadata: dict[str, Any] = {
        "trained": False,
        "train_candidate_count": len(train_rows),
        "train_source_family_counts": _source_family_counts(train_rows),
        "train_label_counts": label_counts,
        "feature_names": feature_names,
        "feature_importances": [],
        "source_groups": {
            "train_rejected": train_rejected_names,
            "train_accepted": train_accepted_names,
        },
        "support_reasons": support_reasons,
        "intended_use": "path_state_candidate_gate_score_map_for_replay_only",
        "live_switch_evidence": False,
    }
    if support_reasons:
        return _empty_path_state_score_maps(eval_episodes), metadata

    model, medians = _fit_scorer(
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

    score_maps = []
    scored_candidate_count = 0
    for episode, rows in zip(eval_episodes, rows_by_episode):
        score_map: dict[Any, Any] = {
            PATH_STATE_EPISODE_META_KEY: _path_state_episode_metadata(episode),
        }
        scored_candidate_count += len(rows)
        if not rows:
            score_maps.append(score_map)
            continue
        scores = _predict_scores(model, medians, feature_names, rows)
        score_map.update({
            int(row["original_index"]): float(score)
            for row, score in zip(rows, scores)
        })
        score_maps.append(score_map)
    metadata["scored_candidate_count"] = int(scored_candidate_count)
    metadata["scored_episode_count"] = int(len(eval_episodes))
    return score_maps, metadata


def fit_action_policy_router_and_route_episodes(
    *,
    train_rejected_reports: Iterable[Mapping[str, Any]],
    train_accepted_reports: Iterable[Mapping[str, Any]],
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    train_rejected_source_names: Iterable[str] | None = None,
    train_accepted_source_names: Iterable[str] | None = None,
    max_depth: int = 3,
    min_samples_leaf: int = 10,
    min_common_features: int = 2,
) -> tuple[list[dict[Any, Any]], dict[str, Any]]:
    train_rejected, train_rejected_names = router_probe._normalize_rows(
        reports=train_rejected_reports,
        source_family="rejected",
        split="train",
        source_names=train_rejected_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_accepted, train_accepted_names = router_probe._normalize_rows(
        reports=train_accepted_reports,
        source_family="accepted",
        split="train",
        source_names=train_accepted_source_names,
        quick_take_profit_pct=25.0,
        stop_loss_pct=-18.0,
        post_target_window_seconds=60.0,
    )
    train_rows = train_rejected + train_accepted
    route_counts = router_probe._route_counts(train_rows)
    route_names = router_probe._route_names(train_rows)
    support_reasons = []
    if len(route_counts) < 2:
        support_reasons.append("train_route_labels_below_two_classes")
    if sum(count for route, count in route_counts.items() if route != router_probe.SKIP_ROUTE) <= 0:
        support_reasons.append("train_positive_route_labels_missing")
    if support_reasons:
        feature_names = reward_probe._feature_names(train_rows, train_rows)
        rows_by_episode: list[list[dict[str, Any]]] = [[] for _episode in eval_episodes]
    else:
        rows_by_episode = _candidate_gate_action_policy_rows_by_episode(
            eval_episodes,
            buy_artifact,
            runtime_params,
        )
        eval_rows = [row for rows in rows_by_episode for row in rows]
        feature_names = reward_probe._feature_names(train_rows, eval_rows)
        if len(feature_names) < int(min_common_features):
            support_reasons.append("common_decision_features_below_min")

    metadata: dict[str, Any] = {
        "trained": False,
        "train_candidate_count": len(train_rows),
        "train_source_family_counts": _source_family_counts(train_rows),
        "train_route_counts": route_counts,
        "route_names": route_names,
        "feature_names": feature_names,
        "feature_importances": [],
        "feature_importances_by_route": {},
        "source_groups": {
            "train_rejected": train_rejected_names,
            "train_accepted": train_accepted_names,
        },
        "support_reasons": support_reasons,
        "intended_use": "action_policy_router_route_map_for_replay_only",
        "live_switch_evidence": False,
    }
    if support_reasons:
        return _empty_path_state_score_maps(eval_episodes), metadata

    models, medians, priors = router_probe._fit_route_models(
        train_rows,
        feature_names,
        route_names,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
    )
    by_route = router_probe._feature_importances_by_route(models, feature_names)
    metadata.update(
        {
            "trained": True,
            "route_priors": priors,
            "imputed_feature_medians": medians,
            "feature_importances": router_probe._aggregate_feature_importances(by_route),
            "feature_importances_by_route": by_route,
        }
    )

    route_maps = []
    scored_candidate_count = 0
    for episode, rows in zip(eval_episodes, rows_by_episode):
        route_map: dict[Any, Any] = {
            PATH_STATE_EPISODE_META_KEY: _path_state_episode_metadata(episode),
        }
        scored_candidate_count += len(rows)
        if rows:
            probabilities = router_probe._predict_route_probabilities(
                models,
                medians,
                feature_names,
                route_names,
                rows,
            )
            for row, probability_row in zip(rows, probabilities):
                best_index = int(np.argmax(probability_row)) if len(probability_row) else 0
                route = route_names[best_index] if route_names else router_probe.SKIP_ROUTE
                confidence = float(probability_row[best_index]) if len(probability_row) else 0.0
                route_map[int(row["original_index"])] = {
                    "route": route,
                    "confidence": confidence,
                }
        route_maps.append(route_map)
    metadata["scored_candidate_count"] = int(scored_candidate_count)
    metadata["scored_episode_count"] = int(len(eval_episodes))
    return route_maps, metadata
