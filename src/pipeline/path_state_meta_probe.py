from __future__ import annotations

import math
import sys
from typing import Mapping, Sequence

import numpy as np

PATH_STATE_EPISODE_META_KEY = "__episode_meta__"


def _as_float(value, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _as_optional_float(value):
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def _token(sample: Mapping) -> str:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return str(meta.get("token_address") or meta.get("token") or "").strip().lower()


def _sample_time(sample: Mapping) -> float:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    return _as_float(meta.get("sample_time"), 0.0)


def _features(sample: Mapping) -> dict:
    return dict(sample.get("features", {}) or {})


def _current_price(sample: Mapping) -> float:
    return _as_float(_features(sample).get("current_price"), 0.0)


def _sample_age_seconds(sample: Mapping) -> float:
    features = _features(sample)
    age = _as_optional_float(features.get("token_age_seconds"))
    if age is not None:
        return float(age)
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    interval = _as_optional_float(meta.get("sample_interval"))
    if interval is not None:
        return max(0.0, float(interval))
    sample_time = _as_optional_float(meta.get("sample_time"))
    create_timestamp = _as_optional_float(meta.get("create_timestamp"))
    if sample_time is None or create_timestamp is None:
        return 0.0
    return max(0.0, float(sample_time) - float(create_timestamp))


def _prior_samples_for_token(sample: Mapping, prior_samples: Sequence[Mapping]) -> list[Mapping]:
    token = _token(sample)
    current_time = _sample_time(sample)
    out = []
    for prior in prior_samples:
        if token and _token(prior) != token:
            continue
        prior_time = _sample_time(prior)
        if prior_time < current_time:
            out.append(prior)
    return sorted(out, key=_sample_time)


def _pct_change(new_value: float, old_value: float) -> float:
    if old_value <= 0.0:
        return 0.0
    return ((float(new_value) / float(old_value)) - 1.0) * 100.0


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return 0.0
    return float(numerator) / float(denominator)


def _prior_model_value(sample: Mapping, *names: str) -> float | None:
    features = _features(sample)
    for name in names:
        value = _as_optional_float(features.get(name))
        if value is not None:
            return float(value)
    return None


def build_path_state_features(
    sample,
    prior_samples,
    *,
    buy_prob,
    entry_score,
    prior_samples_are_causal: bool = False,
) -> dict:
    """Build causal pre-entry path-state features for one candidate sample."""
    features = _features(sample)
    token_prior = (
        list(prior_samples or [])
        if prior_samples_are_causal
        else _prior_samples_for_token(sample, list(prior_samples or []))
    )
    current_price = _current_price(sample)
    prior_prices = [_current_price(prior) for prior in token_prior if _current_price(prior) > 0.0]
    path_prices = [*prior_prices, current_price] if current_price > 0.0 else prior_prices
    pre_entry_peak = max(path_prices) if path_prices else 0.0
    first_price = prior_prices[0] if prior_prices else current_price
    latest_prior_price = prior_prices[-1] if prior_prices else current_price

    prior_volumes = [_as_float(_features(prior).get("volume_30s"), 0.0) for prior in token_prior]
    prior_volatility = [_as_float(_features(prior).get("price_volatility"), 0.0) for prior in token_prior]
    avg_prior_volume = float(np.mean(prior_volumes)) if prior_volumes else 0.0
    avg_prior_volatility = float(np.mean(prior_volatility)) if prior_volatility else 0.0

    prior_buy_prob = token_prior[-1] if token_prior else None
    previous_buy_prob = (
        _prior_model_value(prior_buy_prob, "path_state_buy_prob", "buy_prob", "model_buy_prob")
        if prior_buy_prob is not None
        else None
    )
    previous_entry_score = (
        _prior_model_value(prior_buy_prob, "path_state_entry_score", "entry_score", "predicted_return", "pred_return")
        if prior_buy_prob is not None
        else None
    )

    volume_30s = _as_float(features.get("volume_30s"), 0.0)
    price_volatility = _as_float(features.get("price_volatility"), 0.0)
    probability = _as_float(buy_prob, 0.0)
    score = _as_float(entry_score, 0.0)

    return {
        "buy_prob": float(probability),
        "entry_score": float(score),
        "age_seconds": float(_sample_age_seconds(sample)),
        "volume_30s": float(volume_30s),
        "price_volatility": float(price_volatility),
        "pre_entry_peak_price": float(pre_entry_peak),
        "pre_entry_peak_drawdown_pct": float(_pct_change(current_price, pre_entry_peak)),
        "pre_entry_price_extension_pct": float(_pct_change(current_price, first_price)),
        "recent_price_return_pct": float(_pct_change(current_price, latest_prior_price)),
        "volume_ramp_ratio": float(_safe_ratio(volume_30s, avg_prior_volume)),
        "volatility_ramp_delta": float(price_volatility - avg_prior_volatility),
        "buy_prob_delta": float(probability - previous_buy_prob) if previous_buy_prob is not None else 0.0,
        "entry_score_delta": float(score - previous_entry_score) if previous_entry_score is not None else 0.0,
        "prior_sample_count": int(len(token_prior)),
    }


def path_state_meta_label(labels) -> int:
    from src.pipeline.candidate_ranker_probe import candidate_relevance

    row = dict(labels or {})
    hit_before_stop = int(_as_float(row.get("live_target_hit_before_stop"), 0.0)) == 1
    stop_before_target = int(_as_float(row.get("live_stop_hit_before_target"), 0.0)) == 1
    risk_adjusted = _as_optional_float(row.get("live_risk_adjusted_return_pct"))
    if hit_before_stop:
        return 1
    if stop_before_target:
        return 0
    if risk_adjusted is not None:
        return 1 if risk_adjusted > 0.0 else 0
    return 1 if float(candidate_relevance(row)) > 0.0 else 0


def _passes_floor(value, floor) -> bool:
    floor_value = _as_optional_float(floor)
    if floor_value is None:
        return True
    return _as_float(value, -float("inf")) >= float(floor_value)


def _passes_age(sample: Mapping, max_age_value) -> bool:
    max_age = _as_optional_float(max_age_value)
    if max_age is None:
        return True
    return _sample_age_seconds(sample) <= float(max_age)


def _is_candidate(sample: Mapping, buy_prob: float, entry_score: float, runtime_params: Mapping) -> bool:
    params = runtime_params or {}
    features = _features(sample)
    if _current_price(sample) <= 0.0:
        return False
    probability = _as_float(buy_prob, -1.0)
    threshold = _as_float(params.get("buy_threshold"), 1.0)
    near_threshold = _as_optional_float(params.get("buy_near_threshold_min_prob"))
    if probability >= threshold:
        return (
            _passes_floor(entry_score, params.get("min_entry_score"))
            and _passes_floor(features.get("volume_30s"), params.get("min_entry_volume_30s"))
            and _passes_floor(features.get("price_volatility"), params.get("min_entry_price_volatility"))
            and _passes_age(sample, params.get("max_entry_age_seconds"))
        )
    if near_threshold is not None and near_threshold <= probability < threshold:
        return (
            _passes_floor(entry_score, params.get("buy_near_min_pred_return"))
            and _passes_floor(features.get("volume_30s"), params.get("buy_near_min_entry_volume_30s"))
            and _passes_floor(features.get("price_volatility"), params.get("buy_near_min_entry_price_volatility"))
            and _passes_floor(_sample_age_seconds(sample), params.get("buy_near_min_age_seconds"))
            and _passes_age(sample, params.get("max_entry_age_seconds"))
        )
    return False


def build_path_state_rows_with_indices(samples, buy_probabilities, entry_scores, runtime_params) -> list[dict]:
    if len(samples) != len(buy_probabilities):
        raise ValueError("buy_probabilities length must match samples length")
    if len(samples) != len(entry_scores):
        raise ValueError("entry_scores length must match samples length")

    rows = []
    scored_samples = [
        _sample_with_path_state_scores(sample, buy_prob, entry_score)
        for sample, buy_prob, entry_score in zip(samples, buy_probabilities, entry_scores)
    ]
    prior_samples_by_index = _same_token_prior_samples_by_original_index(scored_samples)
    for original_index, (sample, scored_sample, buy_prob, entry_score) in enumerate(
        zip(samples, scored_samples, buy_probabilities, entry_scores)
    ):
        token = _token(sample)
        if _is_candidate(sample, buy_prob, entry_score, runtime_params):
            labels = dict(sample.get("label", {}) or {})
            rows.append(
                {
                    "token": token,
                    "sample_time": int(_sample_time(sample)),
                    "features": build_path_state_features(
                        scored_sample,
                        prior_samples_by_index[original_index],
                        buy_prob=buy_prob,
                        entry_score=entry_score,
                        prior_samples_are_causal=True,
                    ),
                    "label": path_state_meta_label(labels),
                    "labels": labels,
                    "original_index": int(original_index),
                }
            )
    return rows


def _sample_with_path_state_scores(sample: Mapping, buy_prob: float, entry_score: float) -> dict:
    scored = dict(sample or {})
    scored["features"] = dict(scored.get("features", {}) or {})
    scored["features"]["path_state_buy_prob"] = float(_as_float(buy_prob, 0.0))
    scored["features"]["path_state_entry_score"] = float(_as_float(entry_score, 0.0))
    return scored


def _same_token_prior_samples_by_original_index(samples: Sequence[Mapping]) -> list[list[Mapping]]:
    indexed_samples = list(enumerate(samples or []))
    prior_by_index: list[list[Mapping]] = [[] for _sample in indexed_samples]
    histories: dict[str, list[Mapping]] = {}
    sorted_indices = sorted(indexed_samples, key=lambda item: (_sample_time(item[1]), item[0]))

    cursor = 0
    while cursor < len(sorted_indices):
        sample_time = _sample_time(sorted_indices[cursor][1])
        end = cursor + 1
        while end < len(sorted_indices) and _sample_time(sorted_indices[end][1]) == sample_time:
            end += 1

        same_time_batch = sorted_indices[cursor:end]
        for original_index, sample in same_time_batch:
            token = _token(sample)
            prior_by_index[original_index] = list(histories.get(token, [])) if token else []

        for _original_index, sample in same_time_batch:
            token = _token(sample)
            if token:
                histories.setdefault(token, []).append(sample)

        cursor = end

    return prior_by_index


def _enterable_samples_from_flat_lifecycles(samples: Sequence[Mapping]) -> list[Mapping]:
    samples_by_token: dict[str, list[Mapping]] = {}
    for sample in samples or []:
        token = _token(sample)
        if token:
            samples_by_token.setdefault(token, []).append(sample)

    enterable = []
    for token_samples in samples_by_token.values():
        ordered = sorted(token_samples, key=_sample_time)
        if len(ordered) >= 2:
            enterable.extend(ordered[:-1])
    return enterable


def _episode_metadata(episode: Sequence[Mapping]) -> dict:
    ordered = list(episode or [])
    if not ordered:
        return {"token": "", "sample_count": 0, "start_time": 0, "end_time": 0}
    return {
        "token": _token(ordered[0]),
        "sample_count": int(len(ordered)),
        "start_time": int(_sample_time(ordered[0])),
        "end_time": int(_sample_time(ordered[-1])),
    }


def _feature_frame(rows: Sequence[Mapping]):
    from src.pipeline.train_hybrid import build_feature_frame_many

    feature_rows = [dict(row.get("features", {}) or {}) for row in rows]
    feature_names = sorted({name for row in feature_rows for name in row})
    return build_feature_frame_many(feature_rows, feature_names, [])


def _positive_probabilities(probabilities) -> np.ndarray:
    arr = np.asarray(probabilities, dtype=float)
    if arr.ndim == 2 and arr.shape[1] >= 2:
        return arr[:, 1]
    return arr.reshape(-1)


def _score_samples(samples: Sequence[Mapping], buy_artifact: Mapping) -> tuple[list[float], list[float]]:
    from src.pipeline.train_hybrid import build_feature_frame_many

    artifact = buy_artifact or {}
    buy_model = artifact.get("buy_model") or artifact.get("model")
    entry_value_model = artifact.get("entry_value_model") or artifact.get("entry_model")
    if isinstance(entry_value_model, Mapping):
        entry_value_model = entry_value_model.get("model")
    if buy_model is None or entry_value_model is None:
        raise ValueError("buy_artifact must provide buy and entry value models")

    feature_names = artifact.get("feature_names")
    ignored_feature_names = artifact.get("ignored_feature_names") or artifact.get("dropped_features") or []
    feature_rows = [dict(sample.get("features", {}) or {}) for sample in samples]
    X = build_feature_frame_many(feature_rows, feature_names, ignored_feature_names)
    buy_probabilities = _positive_probabilities(buy_model.predict_proba(X)).reshape(-1)
    entry_scores = np.asarray(entry_value_model.predict(X), dtype=float).reshape(-1)
    return [float(value) for value in buy_probabilities], [float(value) for value in entry_scores]


def _train_path_state_model(train_rows: Sequence[Mapping]):
    from src.model.buy_catboost import BuyCatBoostModel

    X = _feature_frame(train_rows)
    y = [int(row.get("label", 0)) for row in train_rows]
    model = BuyCatBoostModel(catboost_params={"iterations": 120, "od_wait": 20})
    model.fit(X, y)
    return model


def _predict_path_state_scores(model, rows: Sequence[Mapping]) -> list[float]:
    if not rows:
        return []
    X = _feature_frame(rows)
    return [float(value) for value in _positive_probabilities(model.predict_proba(X)).reshape(-1)]


def _path_state_training_runtime_params(runtime_params: Mapping) -> dict:
    params = dict(runtime_params or {})
    train_min_prob = _as_optional_float(
        params.get("path_state_train_min_prob", params.get("buy_path_state_train_min_prob"))
    )
    if train_min_prob is None:
        train_min_prob = min(
            value
            for value in (
                _as_optional_float(params.get("buy_threshold")),
                _as_optional_float(params.get("buy_near_threshold_min_prob")),
                0.75,
            )
            if value is not None
        )
    params["buy_threshold"] = float(train_min_prob)
    params["buy_near_threshold_min_prob"] = None
    params["min_entry_score"] = None
    params["min_entry_volume_30s"] = None
    params["min_entry_price_volatility"] = None
    params["max_entry_age_seconds"] = None

    return params


def fit_path_state_model_and_score_episodes(train_samples, eval_episodes, buy_artifact, runtime_params) -> list[dict[int, float]]:
    train_enterable_samples = _enterable_samples_from_flat_lifecycles(train_samples)
    if train_enterable_samples:
        buy_probabilities, entry_scores = _score_samples(train_enterable_samples, buy_artifact)
    else:
        buy_probabilities, entry_scores = [], []
    training_runtime_params = _path_state_training_runtime_params(runtime_params)
    quality_count = 0
    for sample in train_enterable_samples:
        if _current_price(sample) <= 0.0:
            continue
        features = _features(sample)
        if not _passes_floor(features.get("volume_30s"), training_runtime_params.get("min_entry_volume_30s")):
            continue
        if not _passes_floor(features.get("price_volatility"), training_runtime_params.get("min_entry_price_volatility")):
            continue
        if not _passes_age(sample, training_runtime_params.get("max_entry_age_seconds")):
            continue
        quality_count += 1
    prob_counts = {
        threshold: sum(1 for probability in buy_probabilities if _as_float(probability, -1.0) >= threshold)
        for threshold in (0.50, 0.75, 0.90, 0.94, 0.98)
    }
    max_probability = max((_as_float(probability, -1.0) for probability in buy_probabilities), default=-1.0)
    print(
        "stage=path_state_probe train_prefilter "
        f"quality_count={quality_count} "
        f"max_probability={max_probability:.6f} "
        f"prob_ge_050={prob_counts[0.50]} "
        f"prob_ge_075={prob_counts[0.75]} "
        f"prob_ge_090={prob_counts[0.90]} "
        f"prob_ge_094={prob_counts[0.94]} "
        f"prob_ge_098={prob_counts[0.98]}",
        file=sys.stderr,
        flush=True,
    )
    train_rows = build_path_state_rows_with_indices(
        train_enterable_samples,
        buy_probabilities,
        entry_scores,
        training_runtime_params,
    )
    empty_maps = [{PATH_STATE_EPISODE_META_KEY: _episode_metadata(episode)} for episode in eval_episodes]
    labels = {int(row.get("label", 0)) for row in train_rows}
    positive_count = sum(1 for row in train_rows if int(row.get("label", 0)) == 1)
    negative_count = len(train_rows) - positive_count
    print(
        "stage=path_state_probe train_rows "
        f"count={len(train_rows)} label_positive={positive_count} label_negative={negative_count}",
        file=sys.stderr,
        flush=True,
    )
    if len(train_rows) < 2 or labels != {0, 1}:
        print(
            "stage=path_state_probe empty_score_maps "
            f"reason=insufficient_label_diversity label_set={sorted(labels)}",
            file=sys.stderr,
            flush=True,
        )
        return empty_maps

    model = _train_path_state_model(train_rows)
    score_maps = []
    eval_candidate_count = 0
    eval_quality_count = 0
    eval_prob_counts = {threshold: 0 for threshold in (0.50, 0.75, 0.90, 0.94, 0.98)}
    eval_max_probability = -1.0
    for episode in eval_episodes:
        enterable_episode = list(episode[:-1])
        score_map = {PATH_STATE_EPISODE_META_KEY: _episode_metadata(episode)}
        if enterable_episode:
            episode_probabilities, episode_entry_scores = _score_samples(enterable_episode, buy_artifact)
        else:
            episode_probabilities, episode_entry_scores = [], []
        for sample, probability in zip(enterable_episode, episode_probabilities):
            eval_max_probability = max(eval_max_probability, _as_float(probability, -1.0))
            for threshold in eval_prob_counts:
                if _as_float(probability, -1.0) >= threshold:
                    eval_prob_counts[threshold] += 1
            if _current_price(sample) <= 0.0:
                continue
            features = _features(sample)
            if not _passes_floor(features.get("volume_30s"), runtime_params.get("min_entry_volume_30s")):
                continue
            if not _passes_floor(features.get("price_volatility"), runtime_params.get("min_entry_price_volatility")):
                continue
            if not _passes_age(sample, runtime_params.get("max_entry_age_seconds")):
                continue
            eval_quality_count += 1
        rows = build_path_state_rows_with_indices(
            enterable_episode,
            episode_probabilities,
            episode_entry_scores,
            runtime_params,
        )
        eval_candidate_count += len(rows)
        if not rows:
            score_maps.append(score_map)
            continue
        scores = _predict_path_state_scores(model, rows)
        score_map.update({
            int(row["original_index"]): float(score)
            for row, score in zip(rows, scores)
        })
        score_maps.append(score_map)
    print(
        "stage=path_state_probe eval_rows "
        f"count={eval_candidate_count} "
        f"quality_count={eval_quality_count} "
        f"max_probability={eval_max_probability:.6f} "
        f"prob_ge_050={eval_prob_counts[0.50]} "
        f"prob_ge_075={eval_prob_counts[0.75]} "
        f"prob_ge_090={eval_prob_counts[0.90]} "
        f"prob_ge_094={eval_prob_counts[0.94]} "
        f"prob_ge_098={eval_prob_counts[0.98]}",
        file=sys.stderr,
        flush=True,
    )
    return score_maps
