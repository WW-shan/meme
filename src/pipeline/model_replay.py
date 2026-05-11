from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
import pickle
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CatBoostClassifier = None

try:
    from stable_baselines3 import PPO
except Exception:  # pragma: no cover - optional runtime dependency
    PPO = None

logger = logging.getLogger(__name__)

MODEL_ARTIFACT_FILES = ("buy_model.cbm", "buy_threshold.json", "feature_schema.json", "sell_policy.zip")
SAMPLE_CACHE_VERSION = 1


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
    cache_config = dict(config or {})
    cache_config.pop("eval_samples", None)
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

    policy_path = base / "sell_policy.zip"
    sell_policy = None
    if policy_path.exists() and PPO is not None:
        try:
            sell_policy = PPO.load(str(policy_path))
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
        },
        ppo_artifact={
            "model": sell_policy,
            "policy_path": str(policy_path) if policy_path.exists() else None,
            "total_timesteps": total_timesteps,
        },
        bc_artifact=bc_artifact,
    )


def _evaluation_value(manifest: dict, key: str, default=None):
    evaluation = manifest.get("evaluation", {}) if isinstance(manifest, dict) else {}
    if key in evaluation:
        return evaluation[key]
    selected = manifest.get("selected_runtime_params", {}) if isinstance(manifest, dict) else {}
    return selected.get(key, default)


def live_replay_config_from_manifest(
    manifest: dict,
    *,
    max_open_positions: int = 8,
    include_trade_log: bool = False,
    overrides: dict | None = None,
) -> dict:
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
        "fixed_stake_bnb": _evaluation_value(manifest, "fixed_stake_bnb", 0.1),
        "fee_bps": float(_evaluation_value(manifest, "fee_bps", 100.0)),
        "slippage_bps": float(_evaluation_value(manifest, "slippage_bps", 200.0)),
        "one_entry_per_token": bool(_evaluation_value(manifest, "one_entry_per_token", True)),
        "max_trades_per_token": _evaluation_value(manifest, "max_trades_per_token", 1),
        "max_hold_seconds": _evaluation_value(manifest, "max_hold_seconds", 420),
        "min_policy_hold_seconds": int(_evaluation_value(manifest, "min_policy_hold_seconds", 0) or 0),
        "allow_partial_exits": bool(_evaluation_value(manifest, "allow_partial_exits", False)),
        "entry_delay_seconds": int(_evaluation_value(manifest, "entry_delay_seconds", 3) or 0),
        "exit_delay_seconds": int(_evaluation_value(manifest, "exit_delay_seconds", 3) or 0),
        "max_open_positions": int(max_open_positions),
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
    }
    config.update(dict(overrides or {}))
    return config


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
