from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.pipeline import reentry_probe


DEFAULT_HORIZON_SECONDS = 600.0
DEFAULT_QUICK_PROFIT_SECONDS = 120.0
DEFAULT_SLOW_MIN_PLUS25_SECONDS = 180.0


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        default=_json_default,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if math.isfinite(parsed) else float(default)


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _candidate_features(candidate: Mapping[str, Any]) -> dict[str, Any]:
    features = candidate.get("features")
    return dict(features) if isinstance(features, Mapping) else {}


def _candidate_anchor_time(candidate: Mapping[str, Any]) -> dt.datetime:
    meta = candidate.get("meta")
    meta = meta if isinstance(meta, Mapping) else {}
    for key in ("sample_time", "signal_time", "time"):
        if candidate.get(key) is not None:
            return reentry_probe.parse_time(candidate.get(key))
    if meta.get("sample_time") is not None:
        return reentry_probe.parse_time(meta.get("sample_time"))
    raise ValueError("candidate missing sample_time/time")


def _candidate_anchor_price(candidate: Mapping[str, Any]) -> float | None:
    features = _candidate_features(candidate)
    for key in ("current_price", "entry_price", "price"):
        value = features.get(key, candidate.get(key))
        parsed = _as_optional_float(value)
        if parsed is not None and parsed > 0.0:
            return parsed
    return None


def _first_present(*values: Any) -> float | None:
    present = [_as_optional_float(value) for value in values]
    present = [value for value in present if value is not None]
    return min(present) if present else None


def _before_stop(hit_time: Any, stop_time: float | None) -> bool:
    parsed = _as_optional_float(hit_time)
    return parsed is not None and (stop_time is None or parsed < stop_time)


def _base_candidate_fields(candidate: Mapping[str, Any], anchor_time: dt.datetime | None = None) -> dict[str, Any]:
    features = _candidate_features(candidate)
    return {
        "token": reentry_probe.normalize_token(candidate.get("token") or features.get("token")),
        "symbol": candidate.get("symbol") or features.get("symbol"),
        "sample_time": anchor_time,
        "candidate_source": candidate.get("candidate_source"),
        "buy_prob": _as_optional_float(candidate.get("buy_prob", candidate.get("prob"))),
        "entry_score": _as_optional_float(candidate.get("entry_score", candidate.get("pred_return"))),
        "entry_volume_30s": _as_optional_float(candidate.get("entry_volume_30s", features.get("volume_30s"))),
        "entry_price_volatility": _as_optional_float(
            candidate.get("entry_price_volatility", features.get("price_volatility"))
        ),
        "age_seconds": _as_optional_float(candidate.get("age_seconds", features.get("token_age_seconds"))),
    }


def score_runner_retention_candidate(
    candidate: Mapping[str, Any],
    path: Iterable[reentry_probe.PricePoint],
    *,
    horizon_seconds: float = DEFAULT_HORIZON_SECONDS,
    quick_profit_seconds: float = DEFAULT_QUICK_PROFIT_SECONDS,
    slow_min_plus25_seconds: float = DEFAULT_SLOW_MIN_PLUS25_SECONDS,
) -> dict[str, Any]:
    """Classify one decision-time candidate with replay-equivalent path labels."""
    try:
        anchor_time = _candidate_anchor_time(candidate)
    except (TypeError, ValueError):
        anchor_time = None
    anchor_price = _candidate_anchor_price(candidate)
    base = _base_candidate_fields(candidate, anchor_time)
    if anchor_time is None or anchor_price is None or anchor_price <= 0.0:
        return {
            **base,
            "retention_label": "missing_path",
            "competing_event": "missing_path",
            "runner_retention_positive": False,
            "missing_path": True,
            "reason": "invalid_anchor",
        }

    path_points = list(path)
    if not path_points:
        return {
            **base,
            "retention_label": "missing_path",
            "competing_event": "missing_path",
            "runner_retention_positive": False,
            "missing_path": True,
            "reason": "no_price_path",
        }

    metrics = reentry_probe.path_metrics(
        path_points,
        anchor_time=anchor_time,
        anchor_price=float(anchor_price),
        horizon_seconds=float(horizon_seconds),
    )
    plus_25 = metrics.get("time_to_plus_25_seconds")
    plus_60 = metrics.get("time_to_plus_60_seconds")
    minus_18 = metrics.get("time_to_minus_18_seconds")
    minus_25 = metrics.get("time_to_minus_25_seconds")
    stop_time = _first_present(minus_18, minus_25)

    plus25_before_stop = _before_stop(plus_25, stop_time)
    plus60_before_stop = _before_stop(plus_60, stop_time)
    plus25_time = _as_optional_float(plus_25)
    slow_plus25 = plus25_time is not None and plus25_time >= float(slow_min_plus25_seconds)

    if metrics.get("first_barrier") in {"-18", "-25"}:
        label = "stop_first_collapse"
        competing_event = "stop_first"
        positive = False
    elif plus60_before_stop and slow_plus25:
        label = "slow_runner_retention"
        competing_event = "runner_retention"
        positive = True
    elif plus60_before_stop:
        label = "fast_runner"
        competing_event = "fast_runner"
        positive = False
    elif plus25_before_stop and slow_plus25:
        label = "slow_target_unconfirmed"
        competing_event = "runner_retention_watch"
        positive = False
    elif plus25_before_stop:
        label = "fast_profit"
        competing_event = "fast_profit"
        positive = False
    else:
        label = "flat_timeout"
        competing_event = "flat_timeout"
        positive = False

    return {
        **base,
        "retention_label": label,
        "competing_event": competing_event,
        "runner_retention_positive": positive,
        "missing_path": False,
        "horizon_seconds": float(horizon_seconds),
        "quick_profit_seconds": float(quick_profit_seconds),
        "slow_min_plus25_seconds": float(slow_min_plus25_seconds),
        **metrics,
    }


def _split_summary(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(str(row.get("retention_label") or "") for row in candidates)
    event_counts = Counter(str(row.get("competing_event") or "") for row in candidates)
    source_counts = Counter(str(row.get("candidate_source") or "unknown") for row in candidates)
    positive_count = sum(1 for row in candidates if bool(row.get("runner_retention_positive")))
    candidate_count = len(candidates)
    candidate_tokens = {
        reentry_probe.normalize_token(row.get("token"))
        for row in candidates
        if reentry_probe.normalize_token(row.get("token"))
    }
    positive_tokens = {
        reentry_probe.normalize_token(row.get("token"))
        for row in candidates
        if bool(row.get("runner_retention_positive")) and reentry_probe.normalize_token(row.get("token"))
    }
    return {
        "candidate_count": int(candidate_count),
        "candidate_token_count": int(len(candidate_tokens)),
        "runner_retention_positive_count": int(positive_count),
        "runner_retention_positive_token_count": int(len(positive_tokens)),
        "runner_retention_positive_rate": (positive_count / candidate_count if candidate_count else 0.0),
        "runner_retention_positive_token_rate": (
            len(positive_tokens) / len(candidate_tokens) if candidate_tokens else 0.0
        ),
        "label_counts": dict(sorted(label_counts.items())),
        "competing_event_counts": dict(sorted(event_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "missing_path_count": int(label_counts.get("missing_path", 0)),
    }


def _class_counts(value: Mapping[str, Any]) -> dict[str, int]:
    return {
        str(key): _as_int(count)
        for key, count in dict(value or {}).items()
        if str(key)
    }


def _live_support(live_attribution: Mapping[str, Any] | None) -> dict[str, Any]:
    live_attribution = dict(live_attribution or {})
    rejected = live_attribution.get("rejected_signal_paths")
    rejected = dict(rejected) if isinstance(rejected, Mapping) else live_attribution
    class_counts = _class_counts(rejected.get("class_counts") or {})
    policy_counts = _class_counts(rejected.get("policy_counts") or {})
    candidate_counts = dict(rejected.get("candidate_counts") or {})
    return {
        "slow_runner_count": int(class_counts.get("slow_runner", 0)),
        "conditional_slow_hold_count": int(policy_counts.get("conditional_slow_hold", 0)),
        "class_counts": dict(sorted(class_counts.items())),
        "policy_counts": dict(sorted(policy_counts.items())),
        "candidate_counts": candidate_counts,
    }


def build_support_report(
    *,
    offline_candidates_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
    live_attribution: Mapping[str, Any] | None = None,
    generated_at: dt.datetime | None = None,
    min_train_positives: int = 5,
    min_validation_positives: int = 3,
    min_final_positives: int = 3,
    min_live_positives: int = 3,
) -> dict[str, Any]:
    split_summaries = {
        split: _split_summary(list(candidates or []))
        for split, candidates in sorted(dict(offline_candidates_by_split or {}).items())
    }
    train_pos = int(split_summaries.get("train", {}).get("runner_retention_positive_count", 0))
    validation_pos = int(split_summaries.get("validation", {}).get("runner_retention_positive_count", 0))
    final_pos = int(split_summaries.get("final", {}).get("runner_retention_positive_count", 0))
    train_tokens = int(split_summaries.get("train", {}).get("runner_retention_positive_token_count", 0))
    validation_tokens = int(split_summaries.get("validation", {}).get("runner_retention_positive_token_count", 0))
    final_tokens = int(split_summaries.get("final", {}).get("runner_retention_positive_token_count", 0))
    live = _live_support(live_attribution)
    live_pos = int(live.get("slow_runner_count") or 0)
    offline_sample_pass = (
        train_pos >= int(min_train_positives)
        and validation_pos >= int(min_validation_positives)
        and final_pos >= int(min_final_positives)
    )
    offline_token_pass = (
        train_tokens >= int(min_train_positives)
        and validation_tokens >= int(min_validation_positives)
        and final_tokens >= int(min_final_positives)
    )
    offline_pass = offline_sample_pass and offline_token_pass
    live_pass = live_pos >= int(min_live_positives)
    if offline_pass:
        offline_status = "PASS_OFFLINE_SUPPORT"
    else:
        offline_status = "NO_GO_OFFLINE_SUPPORT"

    if not offline_pass:
        reason = (
            "offline runner-retention support below gate: "
            f"sample train/validation/final={train_pos}/{validation_pos}/{final_pos}; "
            f"token train/validation/final={train_tokens}/{validation_tokens}/{final_tokens}; "
            f"required={min_train_positives}/{min_validation_positives}/{min_final_positives}"
        )
        next_action = "Do not train or replay-switch this label yet; adjust label universe or accumulate more support."
    elif not live_pass:
        reason = f"live slow-runner support {live_pos} < {int(min_live_positives)}; replay-equivalent live evidence is still too sparse."
        next_action = "Keep live unchanged; use the label only for shadow replay or wait for more same-shape live labels."
    else:
        reason = "offline and live support pass, but this read-only probe is not live-switch evidence."
        next_action = "A separate replay-integrated experiment must beat the current baseline before any live change."

    return {
        "generated_at": generated_at
        or dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).replace(tzinfo=None),
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
        },
        "label_definition": {
            "positive": "slow_runner_retention",
            "positive_rule": (
                "candidate reaches +25% no earlier than slow_min_plus25_seconds and later reaches +60%, "
                "both before a -18%/-25% stop barrier within horizon_seconds"
            ),
            "competing_events": ["stop_first", "flat_timeout", "fast_runner", "fast_profit", "runner_retention_watch"],
        },
        "support_gate": {
            "offline_status": offline_status,
            "offline_passes_support_gate": bool(offline_pass),
            "offline_sample_passes_support_gate": bool(offline_sample_pass),
            "offline_token_passes_support_gate": bool(offline_token_pass),
            "live_passes_support_gate": bool(live_pass),
            "min_train_positives": int(min_train_positives),
            "min_validation_positives": int(min_validation_positives),
            "min_final_positives": int(min_final_positives),
            "min_live_positives": int(min_live_positives),
            "train_positives": train_pos,
            "validation_positives": validation_pos,
            "final_positives": final_pos,
            "train_positive_tokens": train_tokens,
            "validation_positive_tokens": validation_tokens,
            "final_positive_tokens": final_tokens,
            "live_positives": live_pos,
        },
        "split_summaries": split_summaries,
        "live_support": live,
        "go_no_go": {
            "status": "NO_GO_FOR_LIVE_SWITCH",
            "reason": reason,
            "next_action": next_action,
        },
    }


def _load_lifecycles_from_paths(paths: Iterable[str | Path]) -> dict[str, dict[str, Any]]:
    maps = []
    for path in paths:
        resolved = Path(path)
        if resolved.exists():
            maps.append(reentry_probe.extract_lifecycles_from_rows(reentry_probe.iter_jsonl(resolved)))
    return reentry_probe.merge_lifecycle_maps(*maps)


def _price_paths_by_token(lifecycles: Mapping[str, Mapping[str, Any]]) -> dict[str, list[reentry_probe.PricePoint]]:
    return {
        reentry_probe.normalize_token(token): reentry_probe.price_path_from_lifecycle(dict(lifecycle or {}))
        for token, lifecycle in dict(lifecycles or {}).items()
        if reentry_probe.normalize_token(token)
    }


def _score_split_candidate_rows(
    *,
    samples: Sequence[Mapping[str, Any]],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    lifecycle_paths: Sequence[str | Path],
    group_bucket_seconds: int,
    horizon_seconds: float,
    quick_profit_seconds: float,
    slow_min_plus25_seconds: float,
) -> list[dict[str, Any]]:
    from src.pipeline.candidate_ranker_probe import _score_samples, build_candidate_rows, prefilter_candidate_samples

    candidate_samples = prefilter_candidate_samples(samples, runtime_params)
    buy_probabilities, entry_scores = _score_samples(candidate_samples, buy_artifact)
    rows = build_candidate_rows(
        candidate_samples,
        buy_probabilities=buy_probabilities,
        entry_scores=entry_scores,
        runtime_params=runtime_params,
        group_bucket_seconds=group_bucket_seconds,
    )
    price_paths = _price_paths_by_token(_load_lifecycles_from_paths(lifecycle_paths))
    scored = []
    for row in rows:
        token = reentry_probe.normalize_token(row.get("token"))
        scored.append(
            score_runner_retention_candidate(
                row,
                price_paths.get(token, []),
                horizon_seconds=horizon_seconds,
                quick_profit_seconds=quick_profit_seconds,
                slow_min_plus25_seconds=slow_min_plus25_seconds,
            )
        )
    return scored


def run_runner_retention_label_probe(
    *,
    model_dir: str,
    lifecycle_dir: str = "data/training",
    live_attribution_path: str | None = None,
    output_path: str = "data/replay_reports/runner_retention_label_probe.json",
    train_split_ratio: float = 0.60,
    validation_split_ratio: float = 0.20,
    min_validation_files: int = 1,
    min_eval_files: int = 1,
    max_samples_per_token: int = 80,
    sample_cache_dir: str | None = ".cache/model_replay",
    max_lifecycle_files: int | None = None,
    lifecycle_files: Sequence[str | Path] | None = None,
    include_shadow_score_rejects: bool = False,
    shadow_min_prob: float | None = None,
    shadow_max_entry_score: float | None = None,
    shadow_min_entry_volume_30s: float | None = None,
    shadow_min_entry_price_volatility: float | None = None,
    shadow_max_age_seconds: float | None = None,
    group_bucket_seconds: int = 30,
    horizon_seconds: float = DEFAULT_HORIZON_SECONDS,
    quick_profit_seconds: float = DEFAULT_QUICK_PROFIT_SECONDS,
    slow_min_plus25_seconds: float = DEFAULT_SLOW_MIN_PLUS25_SECONDS,
    min_train_positives: int = 5,
    min_validation_positives: int = 3,
    min_final_positives: int = 3,
    min_live_positives: int = 3,
) -> dict[str, Any]:
    from src.pipeline.candidate_ranker_probe import (
        _load_split_samples,
        _runtime_config,
        runtime_params_for_report,
        runtime_params_with_buy_threshold,
    )
    from src.pipeline.model_replay import load_model_artifacts

    model_path = Path(model_dir)
    manifest, runtime_params = _runtime_config(model_path)
    artifacts = load_model_artifacts(model_path)
    buy_artifact = artifacts.buy_artifact
    runtime_params = runtime_params_with_buy_threshold(runtime_params, buy_artifact)
    runtime_params = dict(runtime_params)
    runtime_params.update(
        {
            "max_samples_per_token": int(max_samples_per_token),
            "include_shadow_score_rejects": bool(include_shadow_score_rejects),
            "shadow_min_prob": shadow_min_prob,
            "shadow_max_entry_score": shadow_max_entry_score,
            "shadow_min_entry_volume_30s": shadow_min_entry_volume_30s,
            "shadow_min_entry_price_volatility": shadow_min_entry_price_volatility,
            "shadow_max_age_seconds": shadow_max_age_seconds,
        }
    )
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

    split_key_map = {
        "train": "train_files",
        "validation": "validation_files",
        "final": "final_files",
    }
    offline_candidates_by_split = {
        split: _score_split_candidate_rows(
            samples=samples,
            buy_artifact=buy_artifact,
            runtime_params=runtime_params,
            lifecycle_paths=split_meta.get(split_key_map[split], []),
            group_bucket_seconds=group_bucket_seconds,
            horizon_seconds=horizon_seconds,
            quick_profit_seconds=quick_profit_seconds,
            slow_min_plus25_seconds=slow_min_plus25_seconds,
        )
        for split, samples in samples_by_split.items()
    }
    live_attribution = {}
    if live_attribution_path and Path(live_attribution_path).exists():
        live_attribution = json.loads(Path(live_attribution_path).read_text(encoding="utf-8"))

    report = build_support_report(
        offline_candidates_by_split=offline_candidates_by_split,
        live_attribution=live_attribution,
        min_train_positives=min_train_positives,
        min_validation_positives=min_validation_positives,
        min_final_positives=min_final_positives,
        min_live_positives=min_live_positives,
    )
    report.update(
        {
            "model_dir": str(model_path),
            "incumbent_evaluation": dict((manifest or {}).get("evaluation") or {}),
            "split": split_meta,
            "runtime_params": runtime_params_for_report(runtime_params),
            "parameters": {
                "train_split_ratio": float(train_split_ratio),
                "validation_split_ratio": float(validation_split_ratio),
                "min_validation_files": int(min_validation_files),
                "min_eval_files": int(min_eval_files),
                "max_samples_per_token": int(max_samples_per_token),
                "max_lifecycle_files": max_lifecycle_files,
                "explicit_lifecycle_files": [str(path) for path in lifecycle_files] if lifecycle_files else None,
                "include_shadow_score_rejects": bool(include_shadow_score_rejects),
                "shadow_min_prob": shadow_min_prob,
                "shadow_max_entry_score": shadow_max_entry_score,
                "shadow_min_entry_volume_30s": shadow_min_entry_volume_30s,
                "shadow_min_entry_price_volatility": shadow_min_entry_price_volatility,
                "shadow_max_age_seconds": shadow_max_age_seconds,
                "group_bucket_seconds": int(group_bucket_seconds),
                "horizon_seconds": float(horizon_seconds),
                "quick_profit_seconds": float(quick_profit_seconds),
                "slow_min_plus25_seconds": float(slow_min_plus25_seconds),
                "live_attribution_path": live_attribution_path,
            },
            "candidate_samples": {
                split: list(candidates[:25])
                for split, candidates in offline_candidates_by_split.items()
            },
            "positive_candidate_samples": {
                split: [row for row in candidates if bool(row.get("runner_retention_positive"))][:25]
                for split, candidates in offline_candidates_by_split.items()
            },
        }
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(to_json_text(report), encoding="utf-8")
    return report
