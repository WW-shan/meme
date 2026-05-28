from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from src.pipeline import added_trade_boundary_policy_probe as boundary_probe
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


_RESCUE_FLOW_FLOORS = (
    ("buy_runner_retention_rescue_min_entry_volume_30s", "volume_30s"),
    ("buy_runner_retention_rescue_min_flow_total_volume_30s", "flow_total_volume_30s"),
    ("buy_runner_retention_rescue_min_flow_total_volume_60s", "flow_total_volume_60s"),
    ("buy_runner_retention_rescue_min_flow_buy_volume_10s", "flow_buy_volume_10s"),
    ("buy_runner_retention_rescue_min_flow_buy_volume_30s", "flow_buy_volume_30s"),
    ("buy_runner_retention_rescue_min_flow_event_count_30s", "flow_event_count_30s"),
    ("buy_runner_retention_rescue_min_flow_signed_imbalance_30s", "flow_signed_imbalance_30s"),
    ("buy_runner_retention_rescue_min_flow_buy_sell_ratio_30s", "flow_buy_sell_ratio_30s"),
)

_RESCUE_FLOW_CEILINGS = (
    ("buy_runner_retention_rescue_max_flow_sell_pressure_10s", "flow_sell_pressure_10s"),
    ("buy_runner_retention_rescue_max_flow_sell_pressure_30s", "flow_sell_pressure_30s"),
    ("buy_runner_retention_rescue_max_entry_volume_30s", "volume_30s"),
    ("buy_runner_retention_rescue_max_entry_price_volatility", "price_volatility"),
    ("buy_runner_retention_rescue_max_price_momentum", "price_momentum"),
    ("buy_runner_retention_rescue_max_price_change_pct", "price_change_pct"),
    ("buy_runner_retention_rescue_max_trade_frequency", "trade_frequency"),
    ("buy_runner_retention_rescue_max_total_buy_volume", "total_buy_volume"),
    ("buy_runner_retention_rescue_max_early_buy_volume", "early_buy_volume"),
)

_RESCUE_FLOW_FEATURE_ALIASES = {
    "flow_buy_volume_10s": ("volume_10s",),
    "flow_buy_volume_30s": ("volume_30s",),
    "flow_buy_volume_60s": ("volume_60s",),
    "flow_sell_volume_10s": ("sell_volume_10s",),
    "flow_sell_volume_30s": ("sell_volume_30s",),
    "flow_sell_volume_60s": ("sell_volume_60s",),
    "flow_total_volume_10s": ("total_flow_volume_10s",),
    "flow_total_volume_30s": ("total_flow_volume_30s",),
    "flow_total_volume_60s": ("total_flow_volume_60s",),
    "flow_sell_pressure_10s": ("sell_pressure_10s",),
    "flow_sell_pressure_30s": ("sell_pressure_30s",),
    "flow_sell_pressure_60s": ("sell_pressure_60s",),
    "flow_signed_imbalance_10s": ("signed_imbalance_10s",),
    "flow_signed_imbalance_30s": ("signed_imbalance_30s",),
    "flow_signed_imbalance_60s": ("signed_imbalance_60s",),
}

_RESCUE_FLOW_META_ALIASES = {
    "flow_event_count_10s": ("flow_event_count_10s",),
    "flow_event_count_30s": ("flow_event_count_30s",),
    "flow_event_count_60s": ("flow_event_count_60s",),
}


def _has_rescue_flow_filter(runtime_params: Mapping[str, Any]) -> bool:
    params = runtime_params or {}
    return any(
        ranker_probe._as_optional_float(params.get(key)) is not None
        for key, _feature_name in (*_RESCUE_FLOW_FLOORS, *_RESCUE_FLOW_CEILINGS)
    )


def _direct_numeric(sample: Mapping[str, Any], feature_name: str) -> float | None:
    features = sample.get("features", {}) if isinstance(sample, Mapping) else {}
    meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
    for key in (feature_name, *_RESCUE_FLOW_FEATURE_ALIASES.get(feature_name, ())):
        value = ranker_probe._as_optional_float(features.get(key))
        if value is not None:
            return value
    for key in _RESCUE_FLOW_META_ALIASES.get(feature_name, ()):
        value = ranker_probe._as_optional_float(meta.get(key))
        if value is not None:
            return value
    return None


def _flow_feature_value(sample: Mapping[str, Any], feature_name: str) -> float | None:
    value = _direct_numeric(sample, feature_name)
    if value is not None:
        return value

    prefix = "flow_"
    for suffix in ("10s", "30s", "60s"):
        if not feature_name.endswith(f"_{suffix}"):
            continue
        buy_volume = _direct_numeric(sample, f"{prefix}buy_volume_{suffix}")
        sell_volume = _direct_numeric(sample, f"{prefix}sell_volume_{suffix}")
        if feature_name == f"{prefix}total_volume_{suffix}":
            if buy_volume is not None and sell_volume is not None:
                return float(buy_volume + sell_volume)
            return None
        total_volume = _flow_feature_value(sample, f"{prefix}total_volume_{suffix}")
        if total_volume is None or total_volume <= 0.0:
            return None
        if feature_name == f"{prefix}sell_pressure_{suffix}":
            if sell_volume is None:
                return None
            return float(sell_volume / total_volume)
        if feature_name == f"{prefix}signed_imbalance_{suffix}":
            if buy_volume is None or sell_volume is None:
                return None
            return float((buy_volume - sell_volume) / total_volume)
        if feature_name == f"{prefix}buy_sell_ratio_{suffix}":
            if buy_volume is None or sell_volume is None or sell_volume <= 0.0:
                return None
            return float(buy_volume / sell_volume)
    return None


def _passes_rescue_flow_compatibility(
    sample: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> bool:
    params = runtime_params or {}
    if not _has_rescue_flow_filter(params):
        return True
    for param_key, feature_name in _RESCUE_FLOW_FLOORS:
        floor = ranker_probe._as_optional_float(params.get(param_key))
        if floor is None:
            continue
        value = _flow_feature_value(sample, feature_name)
        if value is None or value < floor:
            return False
    for param_key, feature_name in _RESCUE_FLOW_CEILINGS:
        ceiling = ranker_probe._as_optional_float(params.get(param_key))
        if ceiling is None:
            continue
        value = _flow_feature_value(sample, feature_name)
        if value is None or value > ceiling:
            return False
    return True


def _passes_runtime_entry_stack(
    sample: Mapping[str, Any],
    *,
    buy_prob: float,
    entry_score: float,
    runtime_params: Mapping[str, Any] | None,
) -> bool:
    params = runtime_params or {}
    threshold = ranker_probe._as_optional_float(params.get("buy_threshold"))
    probability = ranker_probe._as_optional_float(buy_prob)
    if threshold is None or probability is None:
        return False
    if _current_price(sample) <= 0.0:
        return False
    if probability >= threshold:
        return ranker_probe._primary_reject_kind(sample, entry_score, params) is None
    near_threshold = ranker_probe._as_optional_float(params.get("buy_near_threshold_min_prob"))
    if near_threshold is not None and near_threshold <= probability < threshold:
        return ranker_probe._near_reject_kind(sample, entry_score, params) is None
    return False


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
        if not _passes_rescue_flow_compatibility(sample, runtime_params):
            continue
        row["features"] = dict(sample.get("features", {}) or {})
        row["source_family"] = "runner_retention_candidate_gate"
        rows.append(row)
    return rows


def _baseline_entry_pass_times_by_token(
    samples: Sequence[Mapping[str, Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
) -> dict[str, list[int]]:
    candidate_samples = ranker_probe.prefilter_candidate_samples(samples, runtime_params)
    if not candidate_samples:
        return {}
    buy_probabilities, entry_scores = ranker_probe._score_samples(candidate_samples, buy_artifact)
    pass_times_by_token: dict[str, list[int]] = defaultdict(list)
    for sample, buy_prob, entry_score in zip(candidate_samples, buy_probabilities, entry_scores):
        if not _passes_runtime_entry_stack(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=runtime_params,
        ):
            continue
        meta = sample.get("meta", {}) if isinstance(sample, Mapping) else {}
        token = str(meta.get("token_address") or "").strip().lower()
        if not token:
            continue
        sample_time = int(ranker_probe._as_float(meta.get("sample_time"), 0.0))
        pass_times_by_token[token].append(sample_time)
    for token in list(pass_times_by_token):
        pass_times_by_token[token] = sorted(set(pass_times_by_token[token]))
    return dict(pass_times_by_token)


def _next_baseline_entry_lead_seconds(
    row: Mapping[str, Any],
    baseline_pass_times_by_token: Mapping[str, Sequence[int]],
) -> int | None:
    token = str(row.get("token") or "").strip().lower()
    if not token:
        return None
    sample_time = int(ranker_probe._as_float(row.get("decision_sample_time", row.get("sample_time")), 0.0))
    for pass_time in baseline_pass_times_by_token.get(token, ()):
        lead = int(pass_time) - sample_time
        if lead >= 0:
            return lead
    return None


def _candidate_gate_rows_by_episode(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    base_runtime_params: Mapping[str, Any] | None = None,
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
        preserve_base_candidate = _passes_runtime_entry_stack(
            sample,
            buy_prob=float(buy_prob),
            entry_score=float(entry_score),
            runtime_params=base_runtime_params,
        )
        if not preserve_base_candidate and not _passes_rescue_flow_compatibility(sample, runtime_params):
            continue
        row["features"] = dict(sample.get("features", {}) or {})
        row["source_family"] = "runner_retention_candidate_gate"
        row["preserve_base_candidate"] = preserve_base_candidate
        rows_by_episode[episode_index].append(row)
    return rows_by_episode


def _train_rows_with_labels(
    train_samples: Sequence[Mapping[str, Any]],
    train_price_paths_by_token: Mapping[str, Sequence[Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    *,
    base_runtime_params: Mapping[str, Any] | None = None,
    early_replacement_max_lead_seconds: int | None = None,
) -> list[dict[str, Any]]:
    rows = _candidate_gate_rows_with_indices(
        train_samples,
        buy_artifact,
        runtime_params,
    )
    baseline_pass_times_by_token = {}
    if early_replacement_max_lead_seconds is not None:
        baseline_pass_times_by_token = _baseline_entry_pass_times_by_token(
            train_samples,
            buy_artifact,
            base_runtime_params or runtime_params,
        )
    scored_rows: list[dict[str, Any]] = []
    for row in rows:
        token = str(row.get("token") or "").strip().lower()
        path = train_price_paths_by_token.get(token, [])
        scored = retention_probe.score_runner_retention_candidate(row, path)
        decision_sample_time = int(ranker_probe._as_float(row.get("sample_time"), 0.0))
        tagged = dict(row)
        tagged.update(scored)
        tagged["decision_sample_time"] = decision_sample_time
        if early_replacement_max_lead_seconds is not None:
            lead_seconds = _next_baseline_entry_lead_seconds(tagged, baseline_pass_times_by_token)
            tagged["baseline_entry_lead_seconds"] = lead_seconds
            tagged["label_positive"] = (
                bool(scored.get("runner_retention_positive"))
                and lead_seconds is not None
                and 0 < int(lead_seconds) <= int(early_replacement_max_lead_seconds)
            )
        else:
            tagged["label_positive"] = bool(scored.get("runner_retention_positive"))
        tagged["source_family"] = "runner_retention_train"
        scored_rows.append(tagged)
    return scored_rows


def _eval_rows_by_episode(
    eval_episodes: Sequence[Sequence[Mapping[str, Any]]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    base_runtime_params: Mapping[str, Any] | None = None,
) -> list[list[dict[str, Any]]]:
    return _candidate_gate_rows_by_episode(
        eval_episodes,
        buy_artifact,
        runtime_params,
        base_runtime_params=base_runtime_params,
    )


def _score_rows(
    model,
    medians: Mapping[str, float],
    feature_names: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> list[float]:
    return replay_gate._predict_scores(model, medians, feature_names, rows)


def _passes_added_trade_boundary_rule(row: Mapping[str, Any], rule: Mapping[str, Any] | None) -> bool:
    if not isinstance(rule, Mapping):
        return True
    features = row.get("features") if isinstance(row, Mapping) else {}
    feature_view = {"features": dict(features) if isinstance(features, Mapping) else {}}
    return boundary_probe._rule_matches(feature_view, rule)


def _runtime_bool(params: Mapping[str, Any], key: str, default: bool = False) -> bool:
    value = (params or {}).get(key)
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _runtime_positive_int(params: Mapping[str, Any], key: str, default: int) -> int:
    value = ranker_probe._as_optional_float((params or {}).get(key))
    if value is None:
        return int(default)
    return max(1, int(value))


def _runtime_optional_positive_int(params: Mapping[str, Any], key: str) -> int | None:
    value = ranker_probe._as_optional_float((params or {}).get(key))
    if value is None:
        return None
    return max(1, int(value))


def _train_boundary_feature_enabled(runtime_params: Mapping[str, Any]) -> bool:
    return _runtime_bool(runtime_params, "buy_runner_retention_train_boundary_feature_enabled")


def _boundary_proxy_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    proxy_rows = []
    for row in rows:
        features = row.get("features") if isinstance(row, Mapping) else {}
        if not isinstance(features, Mapping):
            continue
        proxy_rows.append(
            {
                "features": dict(features),
                "trade": {"return_pct": 1.0 if row.get("label_positive") else -1.0},
            }
        )
    return proxy_rows


def _train_boundary_feature_report(
    rows: Sequence[Mapping[str, Any]],
    runtime_params: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _train_boundary_feature_enabled(runtime_params):
        return None
    max_rows = _runtime_optional_positive_int(
        runtime_params,
        "buy_runner_retention_train_boundary_max_rows",
    )
    source_row_count = len(rows)
    search_rows = (
        _evenly_spaced_rows(rows, max_rows)
        if max_rows is not None and source_row_count > max_rows
        else list(rows)
    )
    report_metadata = {
        "source_row_count": source_row_count,
        "search_row_count": len(search_rows),
        "max_rows": max_rows,
    }
    proxy_rows = _boundary_proxy_rows(search_rows)
    if not proxy_rows:
        return {
            "selected_rule": None,
            "support_reasons": ["no_train_boundary_proxy_rows"],
            "intended_use": "train_only_soft_feature",
            **report_metadata,
        }
    loss_cost = ranker_probe._as_optional_float(
        runtime_params.get("buy_runner_retention_train_boundary_loss_cost")
    )
    report = boundary_probe.build_added_trade_boundary_policy_report(
        validation_rows=proxy_rows,
        final_rows=[],
        loss_cost=3.0 if loss_cost is None else float(loss_cost),
        min_keep_count=_runtime_positive_int(
            runtime_params,
            "buy_runner_retention_train_boundary_min_keep_count",
            20,
        ),
        min_reject_count=_runtime_positive_int(
            runtime_params,
            "buy_runner_retention_train_boundary_min_reject_count",
            20,
        ),
        max_conditions=_runtime_positive_int(
            runtime_params,
            "buy_runner_retention_train_boundary_max_conditions",
            2,
        ),
        beam_width=_runtime_positive_int(
            runtime_params,
            "buy_runner_retention_train_boundary_beam_width",
            80,
        ),
    )
    report["intended_use"] = "train_only_soft_feature"
    report["selection_split"] = "train"
    report.update(report_metadata)
    return report


def _boundary_feature_values(row: Mapping[str, Any], rule: Mapping[str, Any]) -> tuple[float, float]:
    conditions = boundary_probe._rule_conditions(rule)
    if not conditions:
        return 0.0, 0.0
    features = row.get("features") if isinstance(row, Mapping) else {}
    feature_view = {"features": dict(features) if isinstance(features, Mapping) else {}}
    matched = sum(1 for condition in conditions if boundary_probe._condition_matches(feature_view, condition))
    fraction = float(matched) / float(len(conditions))
    return (1.0 if matched == len(conditions) else 0.0, fraction)


def _apply_train_boundary_features(
    rows: Sequence[Mapping[str, Any]],
    rule: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    if not isinstance(rule, Mapping):
        return list(rows)
    tagged_rows = []
    for row in rows:
        tagged = dict(row)
        match, fraction = _boundary_feature_values(tagged, rule)
        tagged["runner_retention_train_boundary_match"] = match
        tagged["runner_retention_train_boundary_condition_fraction"] = fraction
        tagged_rows.append(tagged)
    return tagged_rows


def _apply_train_boundary_features_by_episode(
    rows_by_episode: Sequence[Sequence[Mapping[str, Any]]],
    rule: Mapping[str, Any] | None,
) -> list[list[Mapping[str, Any]]]:
    return [
        list(_apply_train_boundary_features(rows, rule))
        for rows in rows_by_episode
    ]


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
    base_runtime_params: Mapping[str, Any] | None = None,
    max_depth: int = 3,
    min_samples_leaf: int = 50,
    min_common_features: int = 2,
    max_train_negative_count: int | None = 1500,
    early_replacement_max_lead_seconds: int | None = None,
    added_trade_boundary_rule: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_train_rows = _train_rows_with_labels(
        train_samples,
        train_price_paths_by_token,
        buy_artifact,
        runtime_params,
        base_runtime_params=base_runtime_params,
        early_replacement_max_lead_seconds=early_replacement_max_lead_seconds,
    )
    raw_label_counts = replay_gate._label_counts(raw_train_rows)
    support_reasons: list[str] = []
    if raw_label_counts["positive"] == 0 or raw_label_counts["negative"] == 0:
        support_reasons.append("train_labels_missing_positive_or_negative")

    rows_by_episode = _episode_meta_score_maps(eval_episodes)
    eval_rows_by_episode = []
    train_boundary_report = None
    train_boundary_rule = None
    train_rows = list(raw_train_rows)
    if not support_reasons:
        train_rows = _balanced_training_rows(
            raw_train_rows,
            max_negative_count=max_train_negative_count,
        )
        train_boundary_report = _train_boundary_feature_report(train_rows, runtime_params)
        if isinstance(train_boundary_report, Mapping):
            selected_rule = train_boundary_report.get("selected_rule")
            if isinstance(selected_rule, Mapping):
                train_boundary_rule = selected_rule
                train_rows = _apply_train_boundary_features(train_rows, train_boundary_rule)
        rows_by_episode = _eval_rows_by_episode(
            eval_episodes,
            buy_artifact,
            runtime_params,
            base_runtime_params=base_runtime_params,
        )
        if isinstance(train_boundary_rule, Mapping):
            rows_by_episode = _apply_train_boundary_features_by_episode(
                rows_by_episode,
                train_boundary_rule,
            )
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
        "target_mode": (
            "runner_retention_early_replacement"
            if early_replacement_max_lead_seconds is not None
            else "runner_retention"
        ),
        "early_replacement_max_lead_seconds": early_replacement_max_lead_seconds,
        "live_switch_evidence": False,
        "rescue_flow_filter_active": _has_rescue_flow_filter(runtime_params),
        "added_trade_boundary_filter_active": isinstance(added_trade_boundary_rule, Mapping),
        "added_trade_boundary_rule": (
            dict(added_trade_boundary_rule) if isinstance(added_trade_boundary_rule, Mapping) else None
        ),
        "train_boundary_feature_enabled": _train_boundary_feature_enabled(runtime_params),
        "train_boundary_feature_active": isinstance(train_boundary_rule, Mapping),
        "train_boundary_feature_report": (
            dict(train_boundary_report) if isinstance(train_boundary_report, Mapping) else None
        ),
        "preserved_base_candidate_count": 0,
        "scored_rescue_candidate_count": 0,
        "boundary_rejected_rescue_candidate_count": 0,
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
    preserved_base_candidate_count = 0
    scored_rescue_candidate_count = 0
    boundary_rejected_rescue_candidate_count = 0
    for episode, rows in zip(eval_episodes, eval_rows_by_episode):
        score_map: dict[Any, Any] = {
            replay_gate.PATH_STATE_EPISODE_META_KEY: replay_gate._path_state_episode_metadata(episode),
        }
        scored_candidate_count += len(rows)
        if not rows:
            score_maps.append(score_map)
            continue
        scores = _score_rows(model, medians, feature_names, rows)
        for row, score in zip(rows, scores):
            if bool(row.get("preserve_base_candidate")):
                preserved_base_candidate_count += 1
                score_map[int(row["original_index"])] = 1.0
            elif not _passes_added_trade_boundary_rule(row, added_trade_boundary_rule):
                boundary_rejected_rescue_candidate_count += 1
            else:
                scored_rescue_candidate_count += 1
                score_map[int(row["original_index"])] = float(score)
        score_maps.append(score_map)
    metadata["scored_candidate_count"] = int(scored_candidate_count)
    metadata["preserved_base_candidate_count"] = int(preserved_base_candidate_count)
    metadata["scored_rescue_candidate_count"] = int(scored_rescue_candidate_count)
    metadata["boundary_rejected_rescue_candidate_count"] = int(boundary_rejected_rescue_candidate_count)
    metadata["scored_episode_count"] = int(len(eval_episodes))
    return score_maps, metadata


def load_train_price_paths_by_token(lifecycle_paths: Sequence[str | Path]) -> dict[str, list[Any]]:
    lifecycles = retention_probe._load_lifecycles_from_paths(lifecycle_paths)
    return retention_probe._price_paths_by_token(lifecycles)
