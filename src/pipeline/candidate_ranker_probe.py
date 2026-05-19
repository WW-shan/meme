from __future__ import annotations

import json
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np


def _as_float(value, default=0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(number):
        return float(default)
    return float(number)


def _as_optional_float(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return float(number)


def _sample_age_seconds(sample: Mapping) -> float:
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    if features.get("token_age_seconds") is not None:
        return max(0.0, _as_float(features.get("token_age_seconds"), 0.0))
    sample_time = _as_optional_float(meta.get("sample_time"))
    create_timestamp = _as_optional_float(meta.get("create_timestamp"))
    if sample_time is None or create_timestamp is None:
        return 0.0
    return max(0.0, sample_time - create_timestamp)


def _sample_tokens(samples: Sequence[Mapping]) -> set[str]:
    tokens = set()
    for sample in samples or []:
        meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
        token = str(meta.get("token_address") or "").strip().lower()
        if token:
            tokens.add(token)
    return tokens


def _file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_fingerprints(paths: Sequence[Path]) -> list[dict]:
    records = []
    for path in paths:
        p = Path(path)
        records.append(
            {
                "path": str(p),
                "name": p.name,
                "exists": bool(p.exists()),
                "size_bytes": int(p.stat().st_size) if p.exists() and p.is_file() else None,
                "sha256": _file_sha256(p),
            }
        )
    return records


def candidate_relevance(
    labels: Mapping,
    *,
    target_return_pct: float = 60.0,
    medium_return_pct: float = 25.0,
) -> float:
    risk_adjusted_return = _as_float(labels.get("live_risk_adjusted_return_pct"), 0.0)
    hit_before_stop = int(_as_float(labels.get("live_target_hit_before_stop"), 0.0)) == 1

    if risk_adjusted_return >= float(target_return_pct):
        return 3.0
    if risk_adjusted_return >= float(medium_return_pct):
        return 2.0
    if hit_before_stop and risk_adjusted_return > 0.0:
        return 1.0
    return 0.0


def _passes_floor(value, floor) -> bool:
    floor_value = _as_optional_float(floor)
    if floor_value is None:
        return True
    return _as_float(value, 0.0) >= floor_value


def _passes_age(age_seconds: float, runtime_params: Mapping) -> bool:
    max_age = _as_optional_float(runtime_params.get("max_entry_age_seconds"))
    if max_age is not None and age_seconds > max_age:
        return False
    return True


def _runtime_bool(runtime_params: Mapping, key: str, default: bool = False) -> bool:
    value = runtime_params.get(key, default)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _primary_reject_kind(sample: Mapping, entry_score, runtime_params: Mapping) -> str | None:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    if not _passes_floor(entry_score, runtime_params.get("min_entry_score")):
        return "score"
    if not _passes_floor(features.get("volume_30s"), runtime_params.get("min_entry_volume_30s")):
        return "quality"
    if not _passes_floor(
        features.get("price_volatility"),
        runtime_params.get("min_entry_price_volatility"),
    ):
        return "quality"
    if not _passes_age(_sample_age_seconds(sample), runtime_params):
        return "quality"
    return None


def _near_reject_kind(sample: Mapping, entry_score, runtime_params: Mapping) -> str | None:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    if not _passes_floor(entry_score, runtime_params.get("buy_near_min_pred_return")):
        return "score"
    if not _passes_floor(features.get("volume_30s"), runtime_params.get("buy_near_min_entry_volume_30s")):
        return "quality"
    if not _passes_floor(
        features.get("price_volatility"),
        runtime_params.get("buy_near_min_entry_price_volatility"),
    ):
        return "quality"
    age_seconds = _sample_age_seconds(sample)
    if not _passes_age(age_seconds, runtime_params):
        return "quality"
    min_age = _as_optional_float(runtime_params.get("buy_near_min_age_seconds"))
    if min_age is not None and age_seconds < min_age:
        return "quality"
    return None


def _shadow_floor(runtime_params: Mapping, shadow_key: str, fallback_key: str):
    value = _as_optional_float(runtime_params.get(shadow_key))
    if value is not None:
        return value
    return _as_optional_float(runtime_params.get(fallback_key))


def _shadow_probability_floor(runtime_params: Mapping) -> float:
    value = _shadow_floor(runtime_params, "shadow_min_prob", "buy_threshold")
    if value is None:
        return _as_float(runtime_params.get("buy_threshold"), 1.0)
    return float(value)


def _shadow_score_reject_kind(
    sample: Mapping,
    *,
    buy_prob,
    entry_score,
    runtime_params: Mapping,
) -> str | None:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    if _as_float(buy_prob, -1.0) < _shadow_probability_floor(runtime_params):
        return "probability"

    min_entry_score = _as_optional_float(runtime_params.get("min_entry_score"))
    score = _as_float(entry_score, 0.0)
    if min_entry_score is None or score >= min_entry_score:
        return "score"
    max_shadow_score = _shadow_floor(runtime_params, "shadow_max_entry_score", "min_entry_score")
    if max_shadow_score is not None and score > max_shadow_score:
        return "score"

    volume_floor = _shadow_floor(runtime_params, "shadow_min_entry_volume_30s", "min_entry_volume_30s")
    if volume_floor is not None and _as_float(features.get("volume_30s"), 0.0) < volume_floor:
        return "quality"
    volatility_floor = _shadow_floor(
        runtime_params,
        "shadow_min_entry_price_volatility",
        "min_entry_price_volatility",
    )
    if volatility_floor is not None and _as_float(features.get("price_volatility"), 0.0) < volatility_floor:
        return "quality"
    max_age = _shadow_floor(runtime_params, "shadow_max_age_seconds", "max_entry_age_seconds")
    if max_age is not None and _sample_age_seconds(sample) > max_age:
        return "quality"
    return None


def assign_group_ids(rows: Sequence[Mapping], *, bucket_seconds: int = 30) -> list[str]:
    if not rows:
        return []
    bucket = max(1, int(bucket_seconds or 1))
    sample_times = [int(_as_float(row.get("sample_time"), 0.0)) for row in rows]
    anchor = min(sample_times)
    group_ids = []
    for sample_time in sample_times:
        group_start = anchor + ((sample_time - anchor) // bucket) * bucket
        group_ids.append(str(int(group_start)))
    return group_ids


def build_candidate_rows(
    samples: Sequence[Mapping],
    *,
    buy_probabilities: Sequence[float],
    entry_scores: Sequence[float],
    runtime_params: Mapping,
    group_bucket_seconds: int = 30,
) -> list[dict]:
    if len(samples) != len(buy_probabilities):
        raise ValueError("buy_probabilities length must match samples length")
    if len(samples) != len(entry_scores):
        raise ValueError("entry_scores length must match samples length")

    threshold = _as_float(runtime_params.get("buy_threshold"), 1.0)
    near_threshold = _as_optional_float(runtime_params.get("buy_near_threshold_min_prob"))
    rows = []

    for sample, buy_prob, entry_score in zip(samples, buy_probabilities, entry_scores):
        features = dict(sample.get("features", {}) or {})
        meta = dict(sample.get("meta", {}) or {})
        price = _as_float(features.get("current_price"), 0.0)
        if price <= 0.0:
            continue

        probability = _as_float(buy_prob, -1.0)
        source = None
        if probability >= threshold:
            if _primary_reject_kind(sample, entry_score, runtime_params) is not None:
                source = None
            else:
                source = "primary"
        elif near_threshold is not None and near_threshold <= probability < threshold:
            if _near_reject_kind(sample, entry_score, runtime_params) is not None:
                source = None
            else:
                source = "near"

        if source is None and _runtime_bool(runtime_params, "include_shadow_score_rejects", False):
            if (
                _shadow_score_reject_kind(
                    sample,
                    buy_prob=probability,
                    entry_score=entry_score,
                    runtime_params=runtime_params,
                )
                is None
            ):
                source = "shadow_score_reject"

        if source is None:
            continue

        labels = dict(sample.get("label", {}) or {})
        rows.append(
            {
                "token": str(meta.get("token_address") or "").strip().lower(),
                "sample_time": int(_as_float(meta.get("sample_time"), 0.0)),
                "create_timestamp": int(_as_float(meta.get("create_timestamp"), 0.0)),
                "age_seconds": float(_sample_age_seconds(sample)),
                "buy_prob": float(probability),
                "entry_score": float(_as_float(entry_score, 0.0)),
                "entry_volume_30s": float(_as_float(features.get("volume_30s"), 0.0)),
                "entry_price_volatility": float(_as_float(features.get("price_volatility"), 0.0)),
                "candidate_source": source,
                "relevance": float(candidate_relevance(labels)),
                "features": features,
                "labels": labels,
            }
        )

    for row, group_id in zip(rows, assign_group_ids(rows, bucket_seconds=group_bucket_seconds)):
        row["group_id"] = group_id

    return rows


def _quality_union_floor(runtime_params: Mapping, primary_key: str, near_key: str):
    values = [
        value
        for value in (
            _as_optional_float(runtime_params.get(primary_key)),
            _as_optional_float(runtime_params.get(near_key)),
        )
        if value is not None and value > 0.0
    ]
    if not values:
        return None
    return min(values)


def _quality_union_floor_with_optional_shadow(
    runtime_params: Mapping,
    primary_key: str,
    near_key: str,
    shadow_key: str,
):
    values = [
        value
        for value in (
            _as_optional_float(runtime_params.get(primary_key)),
            _as_optional_float(runtime_params.get(near_key)),
        )
        if value is not None and value > 0.0
    ]
    if _runtime_bool(runtime_params, "include_shadow_score_rejects", False):
        shadow_value = _shadow_floor(runtime_params, shadow_key, primary_key)
        if shadow_value is not None and shadow_value >= 0.0:
            values.append(shadow_value)
    if not values:
        return None
    return min(values)


def prefilter_candidate_samples(samples: Sequence[Mapping], runtime_params: Mapping) -> list[Mapping]:
    volume_floor = _quality_union_floor_with_optional_shadow(
        runtime_params,
        "min_entry_volume_30s",
        "buy_near_min_entry_volume_30s",
        "shadow_min_entry_volume_30s",
    )
    volatility_floor = _quality_union_floor_with_optional_shadow(
        runtime_params,
        "min_entry_price_volatility",
        "buy_near_min_entry_price_volatility",
        "shadow_min_entry_price_volatility",
    )
    max_age = _as_optional_float(runtime_params.get("max_entry_age_seconds"))
    if _runtime_bool(runtime_params, "include_shadow_score_rejects", False):
        shadow_max_age = _shadow_floor(runtime_params, "shadow_max_age_seconds", "max_entry_age_seconds")
        if shadow_max_age is not None:
            max_age = max(max_age, shadow_max_age) if max_age is not None else shadow_max_age

    filtered = []
    for sample in samples:
        features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
        if _as_float(features.get("current_price"), 0.0) <= 0.0:
            continue
        if volume_floor is not None and _as_float(features.get("volume_30s"), 0.0) < volume_floor:
            continue
        if volatility_floor is not None and _as_float(features.get("price_volatility"), 0.0) < volatility_floor:
            continue
        if max_age is not None and _sample_age_seconds(sample) > max_age:
            continue
        filtered.append(sample)
    return filtered


def summarize_candidates(rows: Sequence[Mapping]) -> dict:
    source_counts = defaultdict(int)
    relevance_counts = defaultdict(int)
    for row in rows:
        source_counts[str(row.get("candidate_source") or "unknown")] += 1
        relevance_counts[str(float(_as_float(row.get("relevance"), 0.0)))] += 1

    probabilities = [_as_float(row.get("buy_prob"), 0.0) for row in rows]
    entry_scores = [_as_float(row.get("entry_score"), 0.0) for row in rows]

    return {
        "candidate_count": int(len(rows)),
        "group_count": int(len({str(row.get("group_id")) for row in rows})),
        "source_counts": dict(sorted(source_counts.items())),
        "relevance_counts": dict(sorted(relevance_counts.items())),
        "buy_prob_min": float(min(probabilities)) if probabilities else None,
        "buy_prob_max": float(max(probabilities)) if probabilities else None,
        "entry_score_min": float(min(entry_scores)) if entry_scores else None,
        "entry_score_max": float(max(entry_scores)) if entry_scores else None,
    }


def _top_k(rows_with_scores: list[tuple[Mapping, float]], top_k: int) -> list[Mapping]:
    limit = max(1, int(top_k or 1))
    ordered = sorted(
        rows_with_scores,
        key=lambda item: (
            -float(item[1]),
            int(_as_float(item[0].get("sample_time"), 0.0)),
            str(item[0].get("token") or ""),
        ),
    )
    return [row for row, _score in ordered[:limit]]


def evaluate_ranker_predictions(
    rows: Sequence[Mapping],
    *,
    predictions: Sequence[float],
    top_k_per_group: int = 1,
) -> dict:
    if len(rows) != len(predictions):
        raise ValueError("predictions length must match rows length")

    by_group: dict[str, list[tuple[Mapping, float]]] = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        by_group[str(row.get("group_id") or "")].append((row, _as_float(prediction, 0.0)))

    ranker_top = []
    entry_value_top = []
    for group_rows in by_group.values():
        ranker_top.extend(_top_k(group_rows, top_k_per_group))
        entry_value_top.extend(
            _top_k(
                [(row, _as_float(row.get("entry_score"), 0.0)) for row, _prediction in group_rows],
                top_k_per_group,
            )
        )

    def _relevance_sum(selected: Iterable[Mapping]) -> float:
        return float(sum(_as_float(row.get("relevance"), 0.0) for row in selected))

    def _clean_runner_count(selected: Iterable[Mapping]) -> int:
        return int(sum(1 for row in selected if _as_float(row.get("relevance"), 0.0) >= 3.0))

    def _collapse_count(selected: Iterable[Mapping]) -> int:
        return int(sum(1 for row in selected if _as_float(row.get("relevance"), 0.0) <= 0.0))

    return {
        "group_count": int(len(by_group)),
        "candidate_count": int(len(rows)),
        "top_k_per_group": int(max(1, int(top_k_per_group or 1))),
        "ranker_selected_count": int(len(ranker_top)),
        "entry_value_selected_count": int(len(entry_value_top)),
        "ranker_top_relevance_sum": _relevance_sum(ranker_top),
        "entry_value_top_relevance_sum": _relevance_sum(entry_value_top),
        "ranker_clean_runner_top_count": _clean_runner_count(ranker_top),
        "entry_value_clean_runner_top_count": _clean_runner_count(entry_value_top),
        "ranker_collapse_top_count": _collapse_count(ranker_top),
        "entry_value_collapse_top_count": _collapse_count(entry_value_top),
        "ranker_top_tokens": [str(row.get("token") or "") for row in ranker_top],
        "entry_value_top_tokens": [str(row.get("token") or "") for row in entry_value_top],
    }


def _positive_probabilities(probabilities) -> np.ndarray:
    arr = np.asarray(probabilities, dtype=float)
    if arr.ndim == 2:
        return arr[:, 1]
    return arr.reshape(-1)


def _runtime_config(model_dir: Path) -> tuple[dict, dict]:
    from src.pipeline.model_replay import live_replay_config_from_manifest

    manifest_path = model_dir / "hybrid_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing hybrid manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"invalid hybrid manifest: {manifest_path}")
    return manifest, live_replay_config_from_manifest(manifest, overrides={"skip_all_in_replay": True})


def runtime_params_with_buy_threshold(runtime_params: Mapping, buy_artifact: Mapping) -> dict:
    params = dict(runtime_params)
    threshold = _as_optional_float(params.get("buy_threshold"))
    if threshold is None:
        threshold = _as_optional_float(buy_artifact.get("threshold"))
    if threshold is not None:
        params["buy_threshold"] = float(threshold)
    return params


def runtime_params_for_report(runtime_params: Mapping) -> dict:
    keys = (
        "buy_threshold",
        "min_entry_score",
        "min_entry_volume_30s",
        "min_entry_price_volatility",
        "buy_near_threshold_min_prob",
        "buy_near_min_pred_return",
        "buy_near_min_entry_volume_30s",
        "buy_near_min_entry_price_volatility",
        "buy_near_min_age_seconds",
        "max_entry_age_seconds",
        "include_shadow_score_rejects",
        "shadow_min_prob",
        "shadow_max_entry_score",
        "shadow_min_entry_volume_30s",
        "shadow_min_entry_price_volatility",
        "shadow_max_age_seconds",
        "position_fraction",
        "max_position_fraction",
    )
    return {key: runtime_params.get(key) for key in keys}


def _load_split_samples(
    *,
    lifecycle_dir: str,
    runtime_params: Mapping,
    train_split_ratio: float,
    validation_split_ratio: float,
    min_validation_files: int,
    min_eval_files: int,
    max_samples_per_token: int,
    sample_cache_dir: str | None,
    max_lifecycle_files: int | None = None,
    lifecycle_files: Sequence[str | Path] | None = None,
) -> tuple[dict, dict]:
    from src.pipeline.train_hybrid import _discover_lifecycle_files, _load_samples, _split_lifecycle_files_three_way
    from src.pipeline.model_replay import load_or_build_samples

    files = [Path(path) for path in lifecycle_files] if lifecycle_files else list(_discover_lifecycle_files(lifecycle_dir))
    if max_lifecycle_files is not None:
        max_files = max(3, int(max_lifecycle_files))
        files = files[-max_files:]
    split = _split_lifecycle_files_three_way(
        files,
        train_split_ratio=train_split_ratio,
        validation_split_ratio=validation_split_ratio,
        min_validation_files=min_validation_files,
        min_eval_files=min_eval_files,
        enforce_no_overlap=False,
    )
    train_tokens = set(split.get("train_raw_tokens") or set())
    validation_tokens = set(split.get("validation_raw_tokens") or set())

    samples_by_split = {}
    for split_name, key in (
        ("train", "train_files"),
        ("validation", "validation_files"),
        ("final", "eval_files"),
    ):
        cache_dir = str(Path(sample_cache_dir)) if sample_cache_dir else None
        cfg = dict(runtime_params)
        cfg.update(
            {
                "lifecycle_dir": lifecycle_dir,
                "sample_cache_dir": None,
                "max_samples_per_token": int(max_samples_per_token),
            }
        )
        excluded_tokens = set()
        if split_name == "validation" and train_tokens:
            excluded_tokens = set(train_tokens)
        elif split_name == "final":
            excluded_tokens = train_tokens.union(validation_tokens)
        if cache_dir is None:
            build_config = dict(cfg)
            build_config["lifecycle_paths"] = split[key]
            if excluded_tokens:
                build_config["exclude_token_addresses"] = excluded_tokens
            samples_by_split[split_name] = _load_samples(build_config)
        else:
            samples_by_split[split_name] = load_or_build_samples(
                cfg,
                split[key],
                excluded_tokens,
                cache_dir=cache_dir,
                use_cache=True,
            )

    train_sample_tokens = _sample_tokens(samples_by_split.get("train", []))
    validation_sample_tokens = _sample_tokens(samples_by_split.get("validation", []))
    final_sample_tokens = _sample_tokens(samples_by_split.get("final", []))
    sample_train_validation_overlap = train_sample_tokens.intersection(validation_sample_tokens)
    sample_train_final_overlap = train_sample_tokens.intersection(final_sample_tokens)
    sample_validation_final_overlap = validation_sample_tokens.intersection(final_sample_tokens)
    if sample_train_validation_overlap or sample_train_final_overlap or sample_validation_final_overlap:
        raise ValueError(
            "sample leakage detected: "
            f"train_validation={len(sample_train_validation_overlap)}, "
            f"train_final={len(sample_train_final_overlap)}, "
            f"validation_final={len(sample_validation_final_overlap)}"
        )

    split_meta = {
        "train_file_count": len(split["train_files"]),
        "validation_file_count": len(split["validation_files"]),
        "final_file_count": len(split["eval_files"]),
        "train_files": [str(path) for path in split["train_files"]],
        "validation_files": [str(path) for path in split["validation_files"]],
        "final_files": [str(path) for path in split["eval_files"]],
        "train_file_fingerprints": _file_fingerprints(split["train_files"]),
        "validation_file_fingerprints": _file_fingerprints(split["validation_files"]),
        "final_file_fingerprints": _file_fingerprints(split["eval_files"]),
        "raw_train_validation_overlap_count": split["raw_train_validation_overlap_count"],
        "raw_train_eval_overlap_count": split["raw_train_eval_overlap_count"],
        "raw_validation_eval_overlap_count": split["raw_validation_eval_overlap_count"],
        "excluded_validation_token_count": len(train_tokens),
        "excluded_final_token_count": len(train_tokens.union(validation_tokens)),
        "sample_train_validation_overlap_count": len(sample_train_validation_overlap),
        "sample_train_final_overlap_count": len(sample_train_final_overlap),
        "sample_validation_final_overlap_count": len(sample_validation_final_overlap),
    }
    return samples_by_split, split_meta


def _feature_contract(buy_artifact: Mapping) -> tuple[list[str] | None, object]:
    feature_names = buy_artifact.get("feature_names")
    if feature_names is not None:
        feature_names = list(feature_names)
    return feature_names, buy_artifact.get("dropped_features", {})


def _score_samples(samples: Sequence[Mapping], buy_artifact: Mapping) -> tuple[list[float], list[float]]:
    from src.pipeline.train_hybrid import build_feature_frame_many

    buy_model = buy_artifact.get("model")
    if buy_model is None:
        raise ValueError("buy artifact missing model")
    entry_value_artifact = buy_artifact.get("entry_value_model")
    entry_value_model = entry_value_artifact.get("model") if isinstance(entry_value_artifact, Mapping) else None
    if entry_value_model is None:
        raise ValueError("candidate ranker probe requires an entry_value_model artifact")

    feature_names, dropped_features = _feature_contract(buy_artifact)
    rows = [dict(sample.get("features", {}) or {}) for sample in samples]
    X = build_feature_frame_many(rows, feature_names, dropped_features)
    buy_probabilities = _positive_probabilities(buy_model.predict_proba(X)).reshape(-1)
    entry_scores = np.asarray(entry_value_model.predict(X), dtype=float).reshape(-1)
    return [float(value) for value in buy_probabilities], [float(value) for value in entry_scores]


def _candidate_rows_for_split(
    samples: Sequence[Mapping],
    buy_artifact: Mapping,
    runtime_params: Mapping,
    *,
    group_bucket_seconds: int,
) -> list[dict]:
    candidate_samples = prefilter_candidate_samples(samples, runtime_params)
    buy_probabilities, entry_scores = _score_samples(candidate_samples, buy_artifact)
    return build_candidate_rows(
        candidate_samples,
        buy_probabilities=buy_probabilities,
        entry_scores=entry_scores,
        runtime_params=runtime_params,
        group_bucket_seconds=group_bucket_seconds,
    )


def _rows_to_frame(rows: Sequence[Mapping], buy_artifact: Mapping):
    from src.pipeline.train_hybrid import build_feature_frame_many

    feature_names, dropped_features = _feature_contract(buy_artifact)
    feature_rows = [dict(row.get("features", {}) or {}) for row in rows]
    return build_feature_frame_many(feature_rows, feature_names, dropped_features)


def _ordered_rows(rows: Sequence[Mapping]) -> list[Mapping]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("group_id") or ""),
            int(_as_float(row.get("sample_time"), 0.0)),
            str(row.get("token") or ""),
        ),
    )


def _train_ranker(train_rows: Sequence[Mapping], buy_artifact: Mapping):
    from src.model.buy_catboost import CandidateRankCatBoostModel

    ordered = _ordered_rows(train_rows)
    X = _rows_to_frame(ordered, buy_artifact)
    y = [_as_float(row.get("relevance"), 0.0) for row in ordered]
    group_id = [str(row.get("group_id") or "") for row in ordered]
    model = CandidateRankCatBoostModel(catboost_params={"iterations": 120, "od_wait": 20})
    model.fit(X, y, group_id=group_id)
    return model


def _predict_ranker(model, rows: Sequence[Mapping], buy_artifact: Mapping) -> list[float]:
    if not rows:
        return []
    indexed_rows = list(enumerate(rows))
    ordered_pairs = sorted(
        indexed_rows,
        key=lambda item: (
            str(item[1].get("group_id") or ""),
            int(_as_float(item[1].get("sample_time"), 0.0)),
            str(item[1].get("token") or ""),
            int(item[0]),
        ),
    )
    ordered = [row for _index, row in ordered_pairs]
    X = _rows_to_frame(ordered, buy_artifact)
    predictions = np.asarray(model.predict(X), dtype=float).reshape(-1)
    by_index = {
        int(index): float(prediction)
        for (index, _row), prediction in zip(ordered_pairs, predictions)
    }
    return [by_index[index] for index in range(len(rows))]


def _evaluate_split(model, rows: Sequence[Mapping], buy_artifact: Mapping, *, top_k_per_group: int) -> dict:
    predictions = _predict_ranker(model, rows, buy_artifact)
    out = evaluate_ranker_predictions(rows, predictions=predictions, top_k_per_group=top_k_per_group)
    out["candidate_summary"] = summarize_candidates(rows)
    return out


def _incumbent_metrics(manifest: Mapping) -> dict:
    evaluation = manifest.get("evaluation", {}) if isinstance(manifest, Mapping) else {}
    return {
        "model": "v95_incumbent",
        "net_profit_bnb": _as_float(evaluation.get("net_profit_bnb"), 0.0),
        "net_return_pct": _as_float(evaluation.get("net_return_pct"), 0.0),
        "total_trades": int(_as_float(evaluation.get("total_trades"), 0.0)),
        "win_rate": _as_float(evaluation.get("win_rate"), 0.0),
        "max_drawdown_pct": _as_float(evaluation.get("max_drawdown_pct"), 0.0),
        "walk_forward_worst_net_return_pct": _as_float(
            evaluation.get("walk_forward_worst_net_return_pct"),
            0.0,
        ),
        "walk_forward_worst_max_drawdown_pct": _as_float(
            evaluation.get("walk_forward_worst_max_drawdown_pct"),
            0.0,
        ),
    }


def _decision(validation: Mapping, final: Mapping) -> str:
    validation_gain = _as_float(validation.get("ranker_top_relevance_sum"), 0.0) - _as_float(
        validation.get("entry_value_top_relevance_sum"),
        0.0,
    )
    final_gain = _as_float(final.get("ranker_top_relevance_sum"), 0.0) - _as_float(
        final.get("entry_value_top_relevance_sum"),
        0.0,
    )
    validation_collapse_delta = int(validation.get("ranker_collapse_top_count", 0)) - int(
        validation.get("entry_value_collapse_top_count", 0)
    )
    final_collapse_delta = int(final.get("ranker_collapse_top_count", 0)) - int(
        final.get("entry_value_collapse_top_count", 0)
    )
    if validation_gain > 0.0 and final_gain > 0.0 and validation_collapse_delta <= 0 and final_collapse_delta <= 0:
        return "supports_followup_replay_integration"
    return "reject_probe"


def run_candidate_ranker_probe(
    *,
    model_dir: str,
    lifecycle_dir: str = "data/training",
    output_path: str = "data/replay_reports/v96_candidate_ranker_probe_20260519.json",
    train_split_ratio: float = 0.60,
    validation_split_ratio: float = 0.20,
    min_validation_files: int = 1,
    min_eval_files: int = 1,
    max_samples_per_token: int = 120,
    sample_cache_dir: str | None = ".cache/model_replay",
    top_k_per_group: int = 1,
    group_bucket_seconds: int = 30,
    max_lifecycle_files: int | None = None,
    lifecycle_files: Sequence[str | Path] | None = None,
    include_shadow_score_rejects: bool = False,
    shadow_min_prob: float | None = None,
    shadow_max_entry_score: float | None = None,
    shadow_min_entry_volume_30s: float | None = None,
    shadow_min_entry_price_volatility: float | None = None,
    shadow_max_age_seconds: float | None = None,
) -> dict:
    from src.pipeline.model_replay import load_model_artifacts

    model_path = Path(model_dir)
    manifest, runtime_params = _runtime_config(model_path)
    runtime_params = dict(runtime_params)
    runtime_params["max_samples_per_token"] = int(max_samples_per_token)
    runtime_params["include_shadow_score_rejects"] = bool(include_shadow_score_rejects)
    runtime_params["shadow_min_prob"] = shadow_min_prob
    runtime_params["shadow_max_entry_score"] = shadow_max_entry_score
    runtime_params["shadow_min_entry_volume_30s"] = shadow_min_entry_volume_30s
    runtime_params["shadow_min_entry_price_volatility"] = shadow_min_entry_price_volatility
    runtime_params["shadow_max_age_seconds"] = shadow_max_age_seconds

    artifacts = load_model_artifacts(model_path)
    buy_artifact = artifacts.buy_artifact
    runtime_params = runtime_params_with_buy_threshold(runtime_params, buy_artifact)
    samples_by_split, split_meta = _load_split_samples(
        lifecycle_dir=lifecycle_dir,
        runtime_params=runtime_params,
        train_split_ratio=train_split_ratio,
        validation_split_ratio=validation_split_ratio,
        min_validation_files=min_validation_files,
        min_eval_files=min_eval_files,
        max_samples_per_token=max_samples_per_token,
        sample_cache_dir=sample_cache_dir,
        max_lifecycle_files=max_lifecycle_files,
        lifecycle_files=lifecycle_files,
    )

    rows_by_split = {
        split_name: _candidate_rows_for_split(
            samples,
            buy_artifact,
            runtime_params,
            group_bucket_seconds=group_bucket_seconds,
        )
        for split_name, samples in samples_by_split.items()
    }

    train_rows = rows_by_split["train"]
    relevance_values = {_as_float(row.get("relevance"), 0.0) for row in train_rows}
    if len(train_rows) < 2 or len(relevance_values) < 2:
        report = {
            "decision": "insufficient_training_candidates",
            "model_dir": str(model_path),
            "incumbent": _incumbent_metrics(manifest),
            "split": split_meta,
            "max_lifecycle_files": max_lifecycle_files,
            "explicit_lifecycle_files": [str(path) for path in lifecycle_files] if lifecycle_files else None,
            "runtime_params": runtime_params_for_report(runtime_params),
            "candidate_summaries": {
                split_name: summarize_candidates(rows)
                for split_name, rows in rows_by_split.items()
            },
        }
    else:
        ranker = _train_ranker(train_rows, buy_artifact)
        validation_eval = _evaluate_split(
            ranker,
            rows_by_split["validation"],
            buy_artifact,
            top_k_per_group=top_k_per_group,
        )
        final_eval = _evaluate_split(
            ranker,
            rows_by_split["final"],
            buy_artifact,
            top_k_per_group=top_k_per_group,
        )
        report = {
            "decision": _decision(validation_eval, final_eval),
            "model_dir": str(model_path),
            "incumbent": _incumbent_metrics(manifest),
            "split": split_meta,
            "max_lifecycle_files": max_lifecycle_files,
            "explicit_lifecycle_files": [str(path) for path in lifecycle_files] if lifecycle_files else None,
            "runtime_params": runtime_params_for_report(runtime_params),
            "candidate_summaries": {
                split_name: summarize_candidates(rows)
                for split_name, rows in rows_by_split.items()
            },
            "validation": validation_eval,
            "final": final_eval,
        }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return report
