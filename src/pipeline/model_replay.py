from __future__ import annotations

import hashlib
import importlib
from datetime import datetime, timezone
import json
import logging
import os
import pickle
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CatBoostClassifier = None
CatBoostRegressor = None
PPO = None

logger = logging.getLogger(__name__)

MODEL_ARTIFACT_FILES = ("buy_model.cbm", "buy_threshold.json", "feature_schema.json", "entry_value_model.cbm", "sell_policy.zip")
PROTECTED_REPORT_OUTPUT_FILES = frozenset(("hybrid_manifest.json", "bc.pt", "trade_log.jsonl", *MODEL_ARTIFACT_FILES))
SAMPLE_CACHE_VERSION = 1
MAX_LIVE_POSITION_FRACTION = 0.10
REPLAY_SAMPLE_CACHE_CONFIG_KEYS = frozenset(
    (
        "sample_mode",
        "future_windows",
        "max_sample_age_seconds",
        "max_entry_age_seconds",
        "dataset_max_sample_age_seconds",
        "max_hold_seconds",
        "max_samples_per_token",
        "min_entry_unique_buyers",
        "min_entry_buy_count",
        "include_token_addresses",
    )
)


class _LazyTrainHybridProxy:
    def _load(self):
        return importlib.import_module("src.pipeline.train_hybrid")

    def __getattr__(self, name):
        return getattr(self._load(), name)


train_hybrid = _LazyTrainHybridProxy()


@dataclass
class LoadedReplayArtifacts:
    buy_artifact: dict
    ppo_artifact: dict
    bc_artifact: dict


@dataclass
class ReplaySplit:
    train_files: list
    validation_files: list
    eval_files: list
    excluded_validation_tokens: set
    excluded_final_tokens: set
    raw_final_overlap_token_count: int


def file_sha1(path: Path) -> str:
    path = Path(path)
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_checksums(model_dir) -> dict:
    base = Path(model_dir)
    checksums = {}
    for name in MODEL_ARTIFACT_FILES:
        path = base / name
        if path.exists():
            checksums[name] = file_sha1(path)
    return checksums


def load_manifest(model_dir) -> dict:
    path = Path(model_dir) / "hybrid_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"missing hybrid manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_replay_split(manifest, lifecycle_dir="data/training") -> ReplaySplit:
    manifest = manifest if isinstance(manifest, dict) else {}
    lifecycle_files = train_hybrid._discover_lifecycle_files(lifecycle_dir)
    split_config = manifest.get("three_way_split", {}) or {}

    if split_config.get("enabled"):
        split = train_hybrid._split_lifecycle_files_three_way(
            lifecycle_files,
            split_config.get("train_split_ratio", 0.8),
            split_config.get("validation_split_ratio", 0.1),
            split_config.get("min_validation_files", 1),
            split_config.get("min_eval_files", 1),
            enforce_no_overlap=False,
        )
        train_tokens = set(split.get("train_raw_tokens") or set())
        validation_tokens = set(split.get("validation_raw_tokens") or set())
        return ReplaySplit(
            train_files=list(split.get("train_files") or []),
            validation_files=list(split.get("validation_files") or []),
            eval_files=list(split.get("eval_files") or []),
            excluded_validation_tokens=train_tokens,
            excluded_final_tokens=train_tokens.union(validation_tokens),
            raw_final_overlap_token_count=int(split.get("raw_final_overlap_token_count", 0) or 0),
        )

    split_config = manifest.get("split", {}) or {}
    train_files, eval_files, overlap_count, train_tokens, _eval_tokens = train_hybrid._split_lifecycle_files(
        lifecycle_files,
        split_config.get("train_split_ratio", manifest.get("train_split_ratio", 0.8)),
        split_config.get("min_eval_files", manifest.get("min_eval_files", 1)),
        enforce_no_overlap=False,
        return_token_sets=True,
    )
    train_tokens = set(train_tokens or set())
    return ReplaySplit(
        train_files=list(train_files),
        validation_files=[],
        eval_files=list(eval_files),
        excluded_validation_tokens=train_tokens,
        excluded_final_tokens=train_tokens,
        raw_final_overlap_token_count=int(overlap_count or 0),
    )


def _lifecycle_metadata(paths: Iterable) -> list:
    metadata = []
    for path in paths or []:
        lifecycle_path = Path(path)
        stat = lifecycle_path.stat()
        metadata.append({
            "path": str(lifecycle_path),
            "size": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
        })
    return metadata


def _sample_cache_key(config: dict, lifecycle_paths: Iterable, exclude_tokens: Iterable) -> str:
    cache_config = {
        key: value
        for key, value in dict(config or {}).items()
        if key in REPLAY_SAMPLE_CACHE_CONFIG_KEYS
    }
    payload = {
        "version": SAMPLE_CACHE_VERSION,
        "config": cache_config,
        "lifecycle_metadata": _lifecycle_metadata(lifecycle_paths),
        "exclude_tokens": sorted(str(token).lower() for token in (exclude_tokens or []) if str(token).strip()),
    }
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()


def load_or_build_samples(
    config: dict,
    lifecycle_paths: Iterable,
    exclude_tokens: Iterable,
    *,
    cache_dir=None,
    use_cache: bool = True,
) -> list:
    paths = [Path(path) for path in (lifecycle_paths or [])]
    excluded = {str(token).strip().lower() for token in (exclude_tokens or []) if str(token).strip()}
    build_config = dict(config or {})
    build_config["lifecycle_paths"] = paths
    if excluded:
        build_config["exclude_token_addresses"] = excluded

    if not use_cache or cache_dir is None:
        return train_hybrid._load_samples(build_config)

    base = Path(cache_dir)
    base.mkdir(parents=True, exist_ok=True)
    cache_path = base / f"{_sample_cache_key(config or {}, paths, excluded)}.pkl"
    if cache_path.exists():
        try:
            with cache_path.open("rb") as handle:
                cached_samples = pickle.load(handle)
            if isinstance(cached_samples, list):
                return cached_samples
        except (pickle.UnpicklingError, EOFError, OSError, ValueError, TypeError):
            pass

    samples = train_hybrid._load_samples(build_config)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb",
            delete=False,
            dir=base,
            prefix=cache_path.name + ".",
            suffix=".tmp",
        ) as handle:
            tmp_path = Path(handle.name)
            pickle.dump(samples, handle, protocol=pickle.HIGHEST_PROTOCOL)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(cache_path)
    except Exception:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
    return samples


def _catboost_classifier():
    if CatBoostClassifier is not None:
        return CatBoostClassifier
    from catboost import CatBoostClassifier as _CatBoostClassifier
    return _CatBoostClassifier


def _catboost_regressor():
    if CatBoostRegressor is not None:
        return CatBoostRegressor
    from catboost import CatBoostRegressor as _CatBoostRegressor
    return _CatBoostRegressor


def _ppo_class():
    if PPO is not None:
        return PPO
    try:
        from stable_baselines3 import PPO as _PPO
    except Exception:  # pragma: no cover - optional runtime dependency
        return None
    return _PPO


def _assert_safe_report_output_path(model_dir: Path, output_path: Path) -> None:
    output_path = Path(output_path)
    if output_path.name not in PROTECTED_REPORT_OUTPUT_FILES:
        return

    try:
        resolved_model_dir = Path(model_dir).resolve()
        resolved_output_path = output_path.resolve(strict=False)
        resolved_output_path.relative_to(resolved_model_dir)
    except ValueError:
        return

    raise ValueError(
        f"refusing to write replay report to protected model artifact: {output_path}"
    )


def load_model_artifacts(model_dir) -> LoadedReplayArtifacts:
    base = Path(model_dir)
    buy_model_path = base / "buy_model.cbm"
    if not buy_model_path.exists():
        raise FileNotFoundError(f"missing buy model: {buy_model_path}")

    buy_model = _catboost_classifier()()
    buy_model.load_model(str(buy_model_path))

    threshold_path = base / "buy_threshold.json"
    threshold = 0.5
    if threshold_path.exists():
        threshold_payload = json.loads(threshold_path.read_text(encoding="utf-8"))
        threshold = float(threshold_payload.get("threshold", threshold))

    feature_schema_path = base / "feature_schema.json"
    feature_names = []
    dropped_features = []
    if feature_schema_path.exists():
        feature_schema = json.loads(feature_schema_path.read_text(encoding="utf-8"))
        feature_names = feature_schema.get("feature_names", [])
        dropped_features = feature_schema.get("dropped_features", [])

    entry_value_model = None
    entry_value_model_path = base / "entry_value_model.cbm"
    if entry_value_model_path.exists():
        entry_value_model = _catboost_regressor()()
        entry_value_model.load_model(str(entry_value_model_path))

    policy_path = base / "sell_policy.zip"
    sell_policy = None
    ppo_class = _ppo_class()
    if policy_path.exists() and ppo_class is not None:
        try:
            sell_policy = ppo_class.load(str(policy_path))
        except Exception as exc:
            logger.warning("failed to load optional sell policy from %s: %s", policy_path, exc)
            sell_policy = None

    manifest_path = base / "hybrid_manifest.json"
    bc_artifact = {}
    total_timesteps = 0
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = manifest.get("artifacts", {}) if isinstance(manifest, dict) else {}
        bc_artifact = artifacts.get("bc_warmstart") or {}
        sell_policy_artifact = artifacts.get("sell_policy", {}) or {}
        total_timesteps = int(sell_policy_artifact.get("total_timesteps", 0) or 0)

    return LoadedReplayArtifacts(
        buy_artifact={
            "model": buy_model,
            "threshold": threshold,
            "model_path": str(buy_model_path),
            "threshold_path": str(threshold_path),
            "feature_schema_path": str(feature_schema_path),
            "feature_names": feature_names,
            "dropped_features": dropped_features,
            "entry_value_model": None if entry_value_model is None else {
                "model": entry_value_model,
                "model_path": str(entry_value_model_path),
            },
        },
        ppo_artifact={
            "model": sell_policy,
            "policy_path": str(policy_path) if policy_path.exists() else None,
            "total_timesteps": total_timesteps,
        },
        bc_artifact=bc_artifact,
    )


def _evaluation_value(manifest: dict, key: str, default=None):
    selected_present = isinstance(manifest, dict) and "selected_runtime_params" in manifest
    selected = manifest.get("selected_runtime_params", {}) if selected_present else {}
    if selected_present:
        if isinstance(selected, dict) and key in selected:
            return selected[key]
        return default
    evaluation = manifest.get("evaluation", {}) if isinstance(manifest, dict) else {}
    if isinstance(evaluation, dict) and key in evaluation:
        return evaluation[key]
    return default


def live_replay_config_from_manifest(
    manifest: dict,
    *,
    max_open_positions: int | None = None,
    include_trade_log: bool = False,
    overrides: dict | None = None,
) -> dict:
    effective_max_open_positions = (
        _manifest_open_position_cap(_evaluation_value(manifest, "max_open_positions", 8))
        if max_open_positions is None
        else _open_position_cap(max_open_positions)
    )
    config = {
        "sample_mode": "trade_event",
        "future_windows": [300],
        "max_sample_age_seconds": int(_evaluation_value(manifest, "max_entry_age_seconds", 300) or 300),
        "max_entry_age_seconds": int(_evaluation_value(manifest, "max_entry_age_seconds", 300) or 300),
        "max_samples_per_token": 120,
        "target_label_column": manifest.get("artifacts", {}).get("buy_model", {}).get(
            "target_label_column", "live_risk_adjusted_return_pct"
        ),
        "target_threshold_value": manifest.get("artifacts", {}).get("buy_model", {}).get("target_threshold_value", 20),
        "min_entry_unique_buyers": int(_evaluation_value(manifest, "min_entry_unique_buyers", 3) or 3),
        "min_entry_buy_count": int(_evaluation_value(manifest, "min_entry_buy_count", 5) or 5),
        "stop_loss": float(_evaluation_value(manifest, "stop_loss", -0.25)),
        "position_fraction": float(_evaluation_value(manifest, "position_fraction", 0.1)),
        "max_position_fraction": _evaluation_value(manifest, "max_position_fraction", 0.1),
        "initial_equity_bnb": float(_evaluation_value(manifest, "initial_equity_bnb", 1.0)),
        "fixed_stake_bnb": _evaluation_value(manifest, "fixed_stake_bnb", None),
        "fee_bps": float(_evaluation_value(manifest, "fee_bps", 100.0)),
        "slippage_bps": float(_evaluation_value(manifest, "slippage_bps", 200.0)),
        "entry_fixed_cost_bnb": float(_evaluation_value(manifest, "entry_fixed_cost_bnb", 0.0) or 0.0),
        "exit_fixed_cost_bnb": float(_evaluation_value(manifest, "exit_fixed_cost_bnb", 0.0) or 0.0),
        "one_entry_per_token": bool(_evaluation_value(manifest, "one_entry_per_token", True)),
        "max_trades_per_token": _evaluation_value(manifest, "max_trades_per_token", 1),
        "max_hold_seconds": _evaluation_value(manifest, "max_hold_seconds", 420),
        "min_policy_hold_seconds": int(_evaluation_value(manifest, "min_policy_hold_seconds", 0) or 0),
        "allow_partial_exits": bool(_evaluation_value(manifest, "allow_partial_exits", False)),
        "entry_delay_seconds": int(_evaluation_value(manifest, "entry_delay_seconds", 3) or 0),
        "exit_delay_seconds": int(_evaluation_value(manifest, "exit_delay_seconds", 3) or 0),
        "max_open_positions": effective_max_open_positions,
        "entry_ranking_mode": str(_evaluation_value(manifest, "entry_ranking_mode", "chronological") or "chronological"),
        "min_entry_score": _evaluation_value(manifest, "min_entry_score", None),
        "min_entry_volume_30s": _evaluation_value(manifest, "min_entry_volume_30s", None),
        "min_entry_price_volatility": _evaluation_value(manifest, "min_entry_price_volatility", None),
        "buy_near_threshold_min_prob": _evaluation_value(manifest, "buy_near_threshold_min_prob", None),
        "buy_near_min_pred_return": _evaluation_value(manifest, "buy_near_min_pred_return", None),
        "buy_near_min_entry_volume_30s": _evaluation_value(manifest, "buy_near_min_entry_volume_30s", None),
        "buy_near_min_entry_price_volatility": _evaluation_value(manifest, "buy_near_min_entry_price_volatility", None),
        "buy_near_min_age_seconds": _evaluation_value(manifest, "buy_near_min_age_seconds", None),
        "buy_primary_score_rescue_min_prob": _evaluation_value(manifest, "buy_primary_score_rescue_min_prob", None),
        "buy_primary_score_rescue_min_pred_return": _evaluation_value(manifest, "buy_primary_score_rescue_min_pred_return", None),
        "buy_primary_score_rescue_min_entry_volume_30s": _evaluation_value(manifest, "buy_primary_score_rescue_min_entry_volume_30s", None),
        "buy_primary_score_rescue_min_entry_price_volatility": _evaluation_value(manifest, "buy_primary_score_rescue_min_entry_price_volatility", None),
        "buy_primary_score_rescue_min_age_seconds": _evaluation_value(manifest, "buy_primary_score_rescue_min_age_seconds", None),
        "buy_low_volume_rescue_min_prob": None,
        "buy_low_volume_rescue_min_entry_volume_30s": None,
        "buy_low_volume_rescue_max_entry_volume_30s": None,
        "buy_low_volume_rescue_min_entry_price_volatility": None,
        "buy_low_volume_rescue_max_age_seconds": None,
        "buy_low_volume_rescue_take_profit_pct": None,
        "buy_quick_profit_overlay_min_prob": None,
        "buy_quick_profit_overlay_min_pred_return": None,
        "buy_quick_profit_overlay_max_pred_return": None,
        "buy_quick_profit_overlay_min_entry_volume_30s": None,
        "buy_quick_profit_overlay_min_entry_price_volatility": None,
        "buy_quick_profit_overlay_max_age_seconds": None,
        "buy_quick_profit_overlay_take_profit_pct": None,
        "buy_quick_profit_overlay_max_hold_seconds": None,
        "buy_flow_activation_min_prob": None,
        "buy_flow_activation_min_pred_return": None,
        "buy_flow_activation_max_age_seconds": None,
        "buy_flow_activation_lookback_seconds": None,
        "buy_flow_activation_min_volume_ramp_ratio": None,
        "buy_flow_activation_min_volume_ramp_delta": None,
        "buy_flow_activation_min_pred_return_delta": None,
        "buy_flow_activation_min_price_volatility_delta": None,
        "buy_flow_activation_min_current_volume_30s": None,
        "buy_dead_flow_exit_min_hold_seconds": None,
        "buy_dead_flow_exit_max_mfe_pct": None,
        "entry_max_fill_wait_seconds": _evaluation_value(manifest, "entry_max_fill_wait_seconds", 3),
        "exit_max_fill_wait_seconds": _evaluation_value(manifest, "exit_max_fill_wait_seconds", 6),
        "entry_price_protection_pct": _evaluation_value(manifest, "entry_price_protection_pct", 0.4),
        "trailing_start_pct": _evaluation_value(manifest, "trailing_start_pct", 0.2),
        "trailing_stop_pct": _evaluation_value(manifest, "trailing_stop_pct", 0.1),
        "rug_sell_pressure": _evaluation_value(manifest, "rug_sell_pressure", 0.92),
        "walk_forward_segments": 3,
        "stress_replay": True,
        "include_trade_log": bool(include_trade_log),
        "label_entry_delay_seconds": int(_evaluation_value(manifest, "entry_delay_seconds", 3) or 0),
        "label_exit_delay_seconds": int(_evaluation_value(manifest, "exit_delay_seconds", 3) or 0),
        "label_fee_bps": float(_evaluation_value(manifest, "fee_bps", 100.0)),
        "label_slippage_bps": float(_evaluation_value(manifest, "slippage_bps", 200.0)),
        "label_fixed_stake_bnb": (
            _evaluation_value(manifest, "fixed_stake_bnb", None)
            if _evaluation_value(manifest, "fixed_stake_bnb", None) is not None
            else float(_evaluation_value(manifest, "initial_equity_bnb", 1.0) or 1.0)
            * float(_evaluation_value(manifest, "position_fraction", 0.1) or 0.1)
        ),
        "label_entry_fixed_cost_bnb": float(_evaluation_value(manifest, "entry_fixed_cost_bnb", 0.0) or 0.0),
        "label_exit_fixed_cost_bnb": float(_evaluation_value(manifest, "exit_fixed_cost_bnb", 0.0) or 0.0),
    }
    config.update(dict(overrides or {}))
    return config


def _stress_profit(evaluation: dict, names: set[str]) -> float:
    values = []
    for row in evaluation.get("stress_replay", []) or []:
        if str(row.get("name", "")) in names:
            values.append(float(row.get("net_profit_bnb", 0.0) or 0.0))
    return min(values) if values else 0.0


def _stress_min_metric(evaluation: dict, names: set[str], key: str, default: float = 0.0) -> float:
    values = []
    for row in evaluation.get("stress_replay", []) or []:
        if str(row.get("name", "")) not in names:
            continue
        try:
            values.append(float(row.get(key, default) or 0.0))
        except Exception:
            values.append(float(default))
    return min(values) if values else float(default)


def live_score(report_or_evaluation: dict, *, preferred_max_drawdown_pct=-30.0) -> dict:
    evaluation = report_or_evaluation.get("evaluation", report_or_evaluation) or {}
    base_profit = float(evaluation.get("net_profit_bnb", 0.0) or 0.0)
    max_drawdown = float(evaluation.get("max_drawdown_pct", 0.0) or 0.0)
    worst_walk_forward_return = float(evaluation.get("walk_forward_worst_net_return_pct", 0.0) or 0.0)
    harsh_names = {"harsh_friction", "harsh_execution"}
    harsh_profit = _stress_profit(evaluation, harsh_names)
    harsh_return_pct = _stress_min_metric(evaluation, harsh_names, "net_return_pct")
    harsh_drawdown_pct = _stress_min_metric(evaluation, harsh_names, "max_drawdown_pct")
    concentration = evaluation.get("top_trade_profit_concentration", {}) or {}
    top10_share = float(concentration.get("top_10_profit_share", 0.0) or 0.0)

    drawdown_excess = max(0.0, abs(min(0.0, max_drawdown)) - abs(float(preferred_max_drawdown_pct)))
    walk_forward_loss = max(0.0, -worst_walk_forward_return / 100.0)
    harsh_loss = max(0.0, -harsh_profit)
    harsh_return_loss = max(0.0, -harsh_return_pct / 100.0)
    harsh_drawdown_excess = max(0.0, abs(min(0.0, harsh_drawdown_pct)) - abs(float(preferred_max_drawdown_pct))) / 100.0
    concentration_excess = max(0.0, top10_share - 0.25)
    penalties = {
        "drawdown": drawdown_excess * 0.08,
        "walk_forward_loss": walk_forward_loss * 2.0,
        "harsh_friction_loss": harsh_loss * 1.5,
        "harsh_friction_return_loss": harsh_return_loss * 0.7,
        "harsh_friction_drawdown": harsh_drawdown_excess * 0.5,
        "concentration": concentration_excess * 2.0,
    }
    score = base_profit - sum(penalties.values())
    return {
        "score": float(score),
        "base_profit_bnb": base_profit,
        "penalties": penalties,
        "max_drawdown_pct": max_drawdown,
        "walk_forward_worst_net_return_pct": worst_walk_forward_return,
        "harsh_profit_bnb": harsh_profit,
        "harsh_return_pct": harsh_return_pct,
        "harsh_drawdown_pct": harsh_drawdown_pct,
    }


def default_candidate_grid() -> list[dict]:
    thresholds = [0.75, 0.8, 0.825, 0.85, 0.875, 0.9]
    stop_losses = [-0.2, -0.25, -0.3]
    trailing_pairs = [(0.2, 0.1), (0.2, 0.15), (0.25, 0.15)]
    candidates = []
    for threshold in thresholds:
        for stop_loss in stop_losses:
            for trailing_start, trailing_stop in trailing_pairs:
                candidates.append({
                    "buy_threshold": threshold,
                    "stop_loss": stop_loss,
                    "trailing_start_pct": trailing_start,
                    "trailing_stop_pct": trailing_stop,
                    "max_open_positions": 8,
                })
    return candidates


def _manifest_position_overrides(manifest: dict) -> dict:
    overrides = {}
    for key in ("initial_equity_bnb", "position_fraction", "max_position_fraction", "fixed_stake_bnb"):
        value = _evaluation_value(manifest, key, None)
        if value is not None:
            overrides[key] = value
    return overrides


def _validate_position_fraction_limit(overrides: dict, *, label: str, limit: float = MAX_LIVE_POSITION_FRACTION) -> None:
    for key in ("position_fraction", "max_position_fraction"):
        value = overrides.get(key)
        if value is None:
            continue
        if float(value) > float(limit) + 1e-12:
            raise ValueError(f"{label} {key}={float(value):.6g} exceeds live risk limit {float(limit):.2f}")

    fixed_stake = overrides.get("fixed_stake_bnb")
    initial_equity = overrides.get("initial_equity_bnb")
    if fixed_stake is None or initial_equity in (None, 0):
        return
    fixed_fraction = float(fixed_stake) / float(initial_equity)
    if fixed_fraction > float(limit) + 1e-12:
        raise ValueError(
            f"{label} fixed_stake_bnb={float(fixed_stake):.6g} exceeds live risk limit "
            f"{float(limit):.2f} for initial_equity_bnb={float(initial_equity):.6g}"
        )


def run_parameter_search(
    model_dir,
    *,
    lifecycle_dir="data/training",
    output_path=None,
    cache_dir=".cache/model_replay",
    candidates=None,
    max_open_positions=8,
    base_overrides=None,
    fast_selection=False,
    use_cache=True,
    write_report=True,
) -> dict:
    model_dir = Path(model_dir)
    candidates = default_candidate_grid() if candidates is None else list(candidates)
    if not candidates:
        raise ValueError("parameter search requires at least one candidate")
    if write_report and output_path is not None:
        _assert_safe_report_output_path(model_dir, Path(output_path))

    base_replay_overrides = {
        key: value
        for key, value in dict(base_overrides or {}).items()
        if value is not None or key == "fixed_stake_bnb"
    }
    manifest_position_overrides = _manifest_position_overrides(load_manifest(model_dir))
    effective_base_position = dict(manifest_position_overrides)
    effective_base_position.update(base_replay_overrides)
    _validate_position_fraction_limit(effective_base_position, label="base replay overrides")

    scored_candidates = []
    best = None
    best_score = None
    for index, overrides in enumerate(candidates):
        replay_overrides = dict(base_replay_overrides)
        replay_overrides.update(dict(overrides))
        effective_position = dict(effective_base_position)
        effective_position.update(replay_overrides)
        _validate_position_fraction_limit(effective_position, label=f"candidate[{index}]")
        replay_overrides.pop("max_open_positions", None)
        validation_overrides = dict(replay_overrides)
        if fast_selection:
            validation_overrides.update({
                "stress_replay": False,
                "walk_forward_segments": 0,
                "skip_all_in_replay": True,
            })
        validation_report = run_model_replay(
            model_dir,
            lifecycle_dir=lifecycle_dir,
            output_path=None,
            cache_dir=cache_dir,
            split="validation",
            max_open_positions=overrides.get("max_open_positions", max_open_positions),
            include_trade_log=not bool(fast_selection),
            overrides=validation_overrides,
            use_cache=use_cache,
            write_report=False,
        )
        scored = live_score(validation_report)
        row_evaluation = dict(validation_report.get("evaluation", {}) or {})
        row_evaluation.pop("trade_log", None)
        row = {
            "candidate_index": int(index),
            "selection_split": "validation",
            "overrides": dict(overrides),
            "score": scored,
            "evaluation": row_evaluation,
        }
        scored_candidates.append(row)
        score_key = (float(scored["score"]), float(scored.get("base_profit_bnb", 0.0)), -index)
        if best_score is None or score_key > best_score:
            best_score = score_key
            best = row

    selected_overrides = dict(base_replay_overrides)
    selected_overrides.update(dict(best["overrides"]))
    selected_max_open_positions = selected_overrides.pop("max_open_positions", max_open_positions)
    final_report = run_model_replay(
        model_dir,
        lifecycle_dir=lifecycle_dir,
        output_path=None,
        cache_dir=cache_dir,
        split="final",
        max_open_positions=selected_max_open_positions,
        include_trade_log=False,
        overrides=selected_overrides,
        use_cache=use_cache,
        write_report=False,
    )
    final_report["selection_role"] = "report_only"
    result = {
        "model_dir": str(model_dir),
        "base_overrides": base_replay_overrides,
        "fast_selection": bool(fast_selection),
        "selected_candidate": best,
        "candidate_count": int(len(scored_candidates)),
        "candidates": scored_candidates,
        "final_report": final_report,
    }
    if write_report:
        if output_path is None:
            report_dir = Path("data/replay_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            output_path = report_dir / f"{model_dir.name}_validation_search.json"
        output_path = Path(output_path)
        _assert_safe_report_output_path(model_dir, output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _write_trade_log_sidecar(output_path: Path, evaluation: dict) -> dict:
    output_path = Path(output_path)
    report_evaluation = dict(evaluation or {})
    trade_log = report_evaluation.get("trade_log")
    if not trade_log:
        return report_evaluation
    report_evaluation.pop("trade_log", None)
    trade_log_path = output_path.with_suffix(".trade_log.jsonl")
    trade_log_path.parent.mkdir(parents=True, exist_ok=True)
    with trade_log_path.open("w", encoding="utf-8") as handle:
        for row in trade_log:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")

    train_hybrid_module = train_hybrid._load()
    report_evaluation["trade_log_path"] = str(trade_log_path)
    report_evaluation["trade_log_count"] = len(trade_log)
    report_evaluation["exit_reason_summary"] = train_hybrid_module._summarize_trade_log_by_exit_reason(trade_log)
    report_evaluation["top_trade_profit_concentration"] = train_hybrid_module._trade_profit_concentration(trade_log)
    return report_evaluation


def _split_paths_for_role(replay_split: ReplaySplit, split: str) -> tuple[list[Path], set[str], int]:
    if split == "validation":
        return (
            [Path(path) for path in replay_split.validation_files],
            set(replay_split.excluded_validation_tokens or set()),
            0,
        )
    if split == "final":
        return (
            [Path(path) for path in replay_split.eval_files],
            set(replay_split.excluded_final_tokens or set()),
            int(replay_split.raw_final_overlap_token_count or 0),
        )
    raise ValueError(f"unsupported replay split: {split}")


def _assert_replay_split_has_explicit_files(split: str, lifecycle_paths: list[Path]) -> None:
    if lifecycle_paths:
        return
    if split == "validation":
        raise ValueError("validation replay requires explicit validation files")
    if split == "final":
        raise ValueError("final replay requires explicit eval files")


def _open_position_cap(value):
    if value is None:
        return None
    cap = int(value)
    return None if cap <= 0 else cap


def _manifest_open_position_cap(value):
    cap = _open_position_cap(value)
    return 8 if cap is None else cap


def _default_replay_report_path(model_dir: Path, split: str, max_open_positions: int | None) -> Path:
    cap_label = "unlimited" if max_open_positions is None else str(int(max_open_positions))
    return Path("data/replay_reports") / f"{model_dir.name}_{split}_cap{cap_label}.json"


def run_model_replay(
    model_dir,
    *,
    lifecycle_dir="data/training",
    output_path=None,
    cache_dir=".cache/model_replay",
    split="final",
    max_open_positions=None,
    include_trade_log=False,
    overrides=None,
    use_cache=True,
    write_report=True,
) -> dict:
    model_dir = Path(model_dir)
    if write_report and output_path is not None:
        _assert_safe_report_output_path(model_dir, Path(output_path))

    manifest = load_manifest(model_dir)
    replay_split = resolve_replay_split(manifest, lifecycle_dir)
    lifecycle_paths, excluded_tokens, raw_overlap_count = _split_paths_for_role(replay_split, split)
    _assert_replay_split_has_explicit_files(split, lifecycle_paths)

    config_overrides = dict(overrides or {})
    config_overrides.pop("buy_threshold", None)
    config = live_replay_config_from_manifest(
        manifest,
        max_open_positions=max_open_positions,
        include_trade_log=include_trade_log,
        overrides=config_overrides,
    )
    config.update({
        "lifecycle_dir": str(lifecycle_dir),
        "evaluation_split": "final_test" if split == "final" else "validation",
        "train_file_count": len(replay_split.train_files),
        "validation_file_count": len(replay_split.validation_files),
        "eval_file_count": len(replay_split.eval_files),
        "selected_lifecycle_file_count": len(lifecycle_paths),
        "excluded_validation_token_count": len(replay_split.excluded_validation_tokens or set()),
        "excluded_final_token_count": len(replay_split.excluded_final_tokens or set()),
        "excluded_token_count": len(excluded_tokens),
        "raw_final_overlap_token_count": int(replay_split.raw_final_overlap_token_count or 0),
        "raw_overlap_token_count": int(raw_overlap_count or 0),
    })

    samples = load_or_build_samples(
        config,
        lifecycle_paths,
        excluded_tokens,
        cache_dir=cache_dir,
        use_cache=use_cache,
    )
    config["eval_samples"] = samples

    artifacts = load_model_artifacts(model_dir)
    buy_artifact = dict(artifacts.buy_artifact or {})
    ppo_artifact = dict(artifacts.ppo_artifact or {})
    bc_artifact = dict(artifacts.bc_artifact or {})
    if overrides and "buy_threshold" in overrides:
        buy_artifact["threshold"] = float(overrides["buy_threshold"])

    evaluation = train_hybrid.run_ab_evaluation(config, buy_artifact, ppo_artifact, bc_artifact)
    evaluation = dict(evaluation or {})

    report_output_path = Path(output_path) if output_path is not None else _default_replay_report_path(
        model_dir,
        split,
        _open_position_cap(config.get("max_open_positions", 8)),
    )
    if write_report:
        report_evaluation = _write_trade_log_sidecar(report_output_path, evaluation) if include_trade_log else dict(evaluation)
    else:
        report_evaluation = dict(evaluation)

    replay_config = dict(config)
    replay_config.pop("eval_samples", None)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_dir": str(model_dir),
        "split": split,
        "selection_role": "validation_selection" if split == "validation" else "report_only",
        "git": git_metadata(),
        "model_checksums": model_checksums(model_dir),
        "replay_config": replay_config,
        "sample_count": len(samples),
        "lifecycle_paths": [str(path) for path in lifecycle_paths],
        "evaluation": report_evaluation,
    }

    if write_report:
        report_output_path.parent.mkdir(parents=True, exist_ok=True)
        report_output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return report


def git_metadata(repo_dir=".") -> dict:
    import subprocess

    root = Path(repo_dir)

    def _run(args):
        result = subprocess.run(
            args,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.stdout.strip()

    return {
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "branch": _run(["git", "branch", "--show-current"]),
        "dirty": bool(_run(["git", "status", "--short"])),
    }
