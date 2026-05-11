# Live Profit Robust Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a replay-only evaluation and validation-only parameter search path so existing FourMeme models can be optimized for fixed-stake, 8-slot live execution before deeper model retraining.

**Architecture:** Add a focused `src/pipeline/model_replay.py` module that wraps existing `train_hybrid` replay internals without modifying the training pipeline first. Add thin scripts under `scripts/` for replay and parameter search. Keep tests in `tests/model/` and use mocked models for fast unit coverage, then run real v31/v32/v33 reports as the final manual verification.

**Tech Stack:** Python 3.12, `unittest`, CatBoost model artifacts, Stable-Baselines3 PPO artifacts, existing `src.pipeline.train_hybrid` replay functions, JSON reports, optional pickle sample cache.

---

## File Map

- Create `src/pipeline/model_replay.py`: model artifact loading, replay config construction, split resolution, sample caching, report writing, live score, and validation-only parameter search.
- Create `scripts/replay_model.py`: thin CLI for replaying a trained model directory without retraining.
- Create `scripts/search_replay_params.py`: thin CLI for validation-only parameter search over existing model artifacts.
- Create `tests/model/test_model_replay.py`: unit tests for helpers, replay orchestration, live scoring, sample cache, and validation-only search.
- Create `tests/model/test_replay_model_cli.py`: unit tests for the replay CLI.
- Create `tests/model/test_search_replay_params_cli.py`: unit tests for the search CLI.
- Read but do not modify `src/pipeline/train_hybrid.py` unless a test exposes a replay bug that cannot be wrapped safely.
- Output generated reports under `data/replay_reports/`; these files remain untracked local artifacts.

## Task 1: Create Replay Metadata And Config Helpers

**Files:**
- Create: `tests/model/test_model_replay.py`
- Create: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing tests for metadata and live config defaults**

Add `tests/model/test_model_replay.py` with these tests:

```python
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pipeline import model_replay as m


class TestModelReplay(unittest.TestCase):
    def test_file_sha1_and_model_checksums_are_stable(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir)
            (model_dir / "buy_model.cbm").write_text("buy", encoding="utf-8")
            (model_dir / "buy_threshold.json").write_text('{"threshold": 0.8}', encoding="utf-8")
            (model_dir / "feature_schema.json").write_text('{"feature_names": ["current_price"]}', encoding="utf-8")
            (model_dir / "sell_policy.zip").write_text("ppo", encoding="utf-8")

            checksums = m.model_checksums(model_dir)

        self.assertEqual(set(checksums), {"buy_model.cbm", "buy_threshold.json", "feature_schema.json", "sell_policy.zip"})
        self.assertEqual(len(checksums["buy_model.cbm"]), 40)
        self.assertEqual(checksums["buy_model.cbm"], m.file_sha1(Path(tmpdir) / "buy_model.cbm") if Path(tmpdir, "buy_model.cbm").exists() else checksums["buy_model.cbm"])

    def test_live_replay_config_uses_manifest_values_and_forces_cap8(self):
        manifest = {
            "artifacts": {"buy_model": {"threshold": 0.825}},
            "evaluation": {
                "stop_loss": -0.25,
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
                "initial_equity_bnb": 1.0,
                "fixed_stake_bnb": 0.1,
                "fee_bps": 100.0,
                "slippage_bps": 200.0,
                "one_entry_per_token": True,
                "max_trades_per_token": 1,
                "max_entry_age_seconds": 300,
                "max_hold_seconds": 420,
                "min_policy_hold_seconds": 0,
                "allow_partial_exits": False,
                "entry_delay_seconds": 3,
                "exit_delay_seconds": 3,
                "entry_max_fill_wait_seconds": 3,
                "exit_max_fill_wait_seconds": 6,
                "entry_price_protection_pct": 0.4,
                "trailing_start_pct": 0.2,
                "trailing_stop_pct": 0.1,
                "rug_sell_pressure": 0.92,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8, include_trade_log=True)

        self.assertEqual(config["max_open_positions"], 8)
        self.assertEqual(config["fixed_stake_bnb"], 0.1)
        self.assertEqual(config["entry_delay_seconds"], 3)
        self.assertEqual(config["exit_delay_seconds"], 3)
        self.assertTrue(config["include_trade_log"])
        self.assertTrue(config["stress_replay"])
        self.assertEqual(config["walk_forward_segments"], 3)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_file_sha1_and_model_checksums_are_stable tests.model.test_model_replay.TestModelReplay.test_live_replay_config_uses_manifest_values_and_forces_cap8
```

Expected: FAIL because `src.pipeline.model_replay` does not exist.

- [ ] **Step 3: Add minimal metadata and config implementation**

Create `src/pipeline/model_replay.py` with this code:

```python
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

MODEL_ARTIFACT_FILES = ("buy_model.cbm", "buy_threshold.json", "feature_schema.json", "sell_policy.zip")


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
        "target_label_column": manifest.get("artifacts", {}).get("buy_model", {}).get("target_label_column", "live_risk_adjusted_return_pct"),
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
        result = subprocess.run(args, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        return result.stdout.strip()

    return {
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "branch": _run(["git", "branch", "--show-current"]),
        "dirty": bool(_run(["git", "status", "--short"])),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_file_sha1_and_model_checksums_are_stable tests.model.test_model_replay.TestModelReplay.test_live_replay_config_uses_manifest_values_and_forces_cap8
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Add model replay metadata helpers"
```

## Task 2: Load Existing Model Artifacts Without Retraining

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing tests for artifact loading**

Append these tests inside `TestModelReplay`:

```python
    def test_load_model_artifacts_loads_buy_threshold_schema_and_policy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir)
            (model_dir / "buy_model.cbm").write_text("buy", encoding="utf-8")
            (model_dir / "buy_threshold.json").write_text('{"threshold": 0.825}', encoding="utf-8")
            (model_dir / "feature_schema.json").write_text(json.dumps({
                "feature_names": ["current_price"],
                "dropped_features": {"constant": ["launch_fee"]},
            }), encoding="utf-8")
            (model_dir / "sell_policy.zip").write_text("ppo", encoding="utf-8")
            fake_buy = MagicMock()
            fake_policy = MagicMock()

            with patch.object(m, "CatBoostClassifier", return_value=fake_buy) as mock_cat, \
                 patch.object(m, "PPO", MagicMock(load=MagicMock(return_value=fake_policy))) as mock_ppo:
                artifacts = m.load_model_artifacts(model_dir)

        mock_cat.assert_called_once()
        fake_buy.load_model.assert_called_once()
        mock_ppo.load.assert_called_once()
        self.assertIs(artifacts.buy_artifact["model"], fake_buy)
        self.assertEqual(artifacts.buy_artifact["threshold"], 0.825)
        self.assertEqual(artifacts.buy_artifact["feature_names"], ["current_price"])
        self.assertEqual(artifacts.buy_artifact["dropped_features"], {"constant": ["launch_fee"]})
        self.assertIs(artifacts.ppo_artifact["model"], fake_policy)

    def test_load_model_artifacts_allows_missing_sell_policy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir)
            (model_dir / "buy_model.cbm").write_text("buy", encoding="utf-8")
            (model_dir / "buy_threshold.json").write_text('{"threshold": 0.5}', encoding="utf-8")
            (model_dir / "feature_schema.json").write_text('{"feature_names": ["current_price"]}', encoding="utf-8")

            with patch.object(m, "CatBoostClassifier", return_value=MagicMock()):
                artifacts = m.load_model_artifacts(model_dir)

        self.assertIsNone(artifacts.ppo_artifact["model"])
        self.assertIsNone(artifacts.ppo_artifact["policy_path"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_load_model_artifacts_loads_buy_threshold_schema_and_policy tests.model.test_model_replay.TestModelReplay.test_load_model_artifacts_allows_missing_sell_policy
```

Expected: FAIL because `load_model_artifacts` is not defined.

- [ ] **Step 3: Implement artifact loading**

Add these imports and definitions to `src/pipeline/model_replay.py`:

```python
from dataclasses import dataclass

from catboost import CatBoostClassifier
try:
    from stable_baselines3 import PPO
except Exception:  # pragma: no cover
    PPO = None
from src.model.hybrid_inference import load_feature_schema_from_file


@dataclass
class LoadedReplayArtifacts:
    buy_artifact: dict
    ppo_artifact: dict
    bc_artifact: dict


def load_model_artifacts(model_dir) -> LoadedReplayArtifacts:
    model_dir = Path(model_dir)
    buy_model_path = model_dir / "buy_model.cbm"
    if not buy_model_path.exists():
        raise FileNotFoundError(f"missing buy model: {buy_model_path}")

    buy_model = CatBoostClassifier()
    buy_model.load_model(str(buy_model_path))

    threshold_path = model_dir / "buy_threshold.json"
    threshold = 0.5
    if threshold_path.exists():
        threshold = float(json.loads(threshold_path.read_text(encoding="utf-8")).get("threshold", 0.5))

    schema_path = model_dir / "feature_schema.json"
    feature_names = None
    dropped_features = []
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        feature_names = schema.get("feature_names")
        dropped_features = schema.get("dropped_features", [])

    policy_path = model_dir / "sell_policy.zip"
    sell_policy = None
    if policy_path.exists() and PPO is not None:
        sell_policy = PPO.load(str(policy_path))

    manifest = load_manifest(model_dir) if (model_dir / "hybrid_manifest.json").exists() else {}
    bc_artifact = manifest.get("artifacts", {}).get("bc_warmstart", {}) or {}
    ppo_total_timesteps = manifest.get("artifacts", {}).get("sell_policy", {}).get("total_timesteps", 0)

    return LoadedReplayArtifacts(
        buy_artifact={
            "model": buy_model,
            "threshold": threshold,
            "model_path": str(buy_model_path),
            "threshold_path": str(threshold_path),
            "feature_schema_path": str(schema_path),
            "feature_names": feature_names,
            "dropped_features": dropped_features,
        },
        ppo_artifact={
            "model": sell_policy,
            "policy_path": str(policy_path) if policy_path.exists() else None,
            "total_timesteps": int(ppo_total_timesteps or 0),
        },
        bc_artifact=bc_artifact,
    )
```

- [ ] **Step 4: Run artifact loading tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_load_model_artifacts_loads_buy_threshold_schema_and_policy tests.model.test_model_replay.TestModelReplay.test_load_model_artifacts_allows_missing_sell_policy
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Load existing hybrid model artifacts"
```

## Task 3: Resolve Chronological Splits And Cache Eval Samples

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing tests for split resolution and cache invalidation**

Append these tests inside `TestModelReplay`:

```python
    def test_resolve_replay_split_uses_three_way_manifest(self):
        fake_files = [Path(f"lifecycle_incremental_{idx:03d}.jsonl") for idx in range(1, 6)]
        manifest = {
            "three_way_split": {
                "enabled": True,
                "train_split_ratio": 0.6,
                "validation_split_ratio": 0.2,
                "min_validation_files": 1,
                "min_eval_files": 1,
            }
        }
        split_result = {
            "train_files": fake_files[:3],
            "validation_files": fake_files[3:4],
            "eval_files": fake_files[4:],
            "train_raw_tokens": {"0xtrain"},
            "validation_raw_tokens": {"0xval"},
            "eval_raw_tokens": {"0xfinal"},
            "raw_final_overlap_token_count": 2,
        }

        with patch.object(m.train_hybrid, "_discover_lifecycle_files", return_value=fake_files), \
             patch.object(m.train_hybrid, "_split_lifecycle_files_three_way", return_value=split_result):
            replay_split = m.resolve_replay_split(manifest, "data/training")

        self.assertEqual(replay_split.train_files, fake_files[:3])
        self.assertEqual(replay_split.validation_files, fake_files[3:4])
        self.assertEqual(replay_split.eval_files, fake_files[4:])
        self.assertEqual(replay_split.excluded_final_tokens, {"0xtrain", "0xval"})
        self.assertEqual(replay_split.raw_final_overlap_token_count, 2)

    def test_load_or_build_samples_uses_cache_until_lifecycle_metadata_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            config = {"sample_mode": "trade_event", "max_sample_age_seconds": 300, "future_windows": [300]}
            first_samples = [{"meta": {"token_address": "0x1"}, "features": {"current_price": 1.0}}]
            second_samples = [{"meta": {"token_address": "0x2"}, "features": {"current_price": 2.0}}]

            with patch.object(m.train_hybrid, "_load_samples", return_value=first_samples) as mock_load:
                loaded_first = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)

            lifecycle.write_text('{"token_address":"0x1"}\n{"token_address":"0x2"}\n', encoding="utf-8")
            with patch.object(m.train_hybrid, "_load_samples", return_value=second_samples) as mock_load_after_change:
                loaded_second = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)

        self.assertEqual(loaded_first, first_samples)
        self.assertEqual(loaded_cached, first_samples)
        self.assertEqual(loaded_second, second_samples)
        self.assertEqual(mock_load.call_count, 1)
        self.assertEqual(mock_load_after_change.call_count, 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_resolve_replay_split_uses_three_way_manifest tests.model.test_model_replay.TestModelReplay.test_load_or_build_samples_uses_cache_until_lifecycle_metadata_changes
```

Expected: FAIL because split and cache helpers are not defined.

- [ ] **Step 3: Implement split resolution and sample cache**

Add these imports and code to `src/pipeline/model_replay.py`:

```python
import pickle
from dataclasses import dataclass
from typing import Iterable

from src.pipeline import train_hybrid


@dataclass
class ReplaySplit:
    train_files: list[Path]
    validation_files: list[Path]
    eval_files: list[Path]
    excluded_validation_tokens: set[str]
    excluded_final_tokens: set[str]
    raw_final_overlap_token_count: int


def resolve_replay_split(manifest: dict, lifecycle_dir="data/training") -> ReplaySplit:
    lifecycle_files = train_hybrid._discover_lifecycle_files(lifecycle_dir)
    split_meta = manifest.get("three_way_split", {}) or {}
    if bool(split_meta.get("enabled", False)):
        split = train_hybrid._split_lifecycle_files_three_way(
            lifecycle_files,
            train_split_ratio=split_meta.get("train_split_ratio", 0.6),
            validation_split_ratio=split_meta.get("validation_split_ratio", 0.2),
            min_validation_files=split_meta.get("min_validation_files", 1),
            min_eval_files=split_meta.get("min_eval_files", 1),
            enforce_no_overlap=False,
        )
        train_tokens = set(split.get("train_raw_tokens", set()))
        validation_tokens = set(split.get("validation_raw_tokens", set()))
        return ReplaySplit(
            train_files=[Path(path) for path in split["train_files"]],
            validation_files=[Path(path) for path in split["validation_files"]],
            eval_files=[Path(path) for path in split["eval_files"]],
            excluded_validation_tokens=train_tokens,
            excluded_final_tokens=train_tokens.union(validation_tokens),
            raw_final_overlap_token_count=int(split.get("raw_final_overlap_token_count", 0)),
        )

    train_files, eval_files, raw_overlap, train_tokens, _eval_tokens = train_hybrid._split_lifecycle_files(
        lifecycle_files,
        train_split_ratio=split_meta.get("train_split_ratio", 0.8),
        min_eval_files=split_meta.get("min_eval_files", 1),
        enforce_no_overlap=False,
        return_token_sets=True,
    )
    return ReplaySplit(
        train_files=[Path(path) for path in train_files],
        validation_files=[],
        eval_files=[Path(path) for path in eval_files],
        excluded_validation_tokens=set(),
        excluded_final_tokens=set(train_tokens or set()),
        raw_final_overlap_token_count=int(raw_overlap),
    )


def _lifecycle_metadata(paths: Iterable[Path]) -> list[dict]:
    rows = []
    for path in paths:
        path = Path(path)
        stat = path.stat()
        rows.append({"path": str(path), "size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)})
    return rows


def _sample_cache_key(config: dict, lifecycle_paths: Iterable[Path], exclude_tokens: Iterable[str]) -> str:
    payload = {
        "config": {key: config.get(key) for key in sorted(config.keys()) if key != "eval_samples"},
        "lifecycle": _lifecycle_metadata(lifecycle_paths),
        "exclude_tokens": sorted(str(token) for token in exclude_tokens),
    }
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def load_or_build_samples(config: dict, lifecycle_paths: Iterable[Path], exclude_tokens: Iterable[str], *, cache_dir=None, use_cache=True) -> list:
    lifecycle_paths = [Path(path) for path in lifecycle_paths]
    exclude_tokens = {str(token).lower() for token in (exclude_tokens or set()) if str(token).strip()}
    build_config = dict(config)
    build_config["lifecycle_paths"] = lifecycle_paths
    if exclude_tokens:
        build_config["exclude_token_addresses"] = exclude_tokens
    if not use_cache or cache_dir is None:
        return train_hybrid._load_samples(build_config)

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{_sample_cache_key(build_config, lifecycle_paths, exclude_tokens)}.pkl"
    if cache_path.exists():
        with cache_path.open("rb") as handle:
            return pickle.load(handle)
    samples = train_hybrid._load_samples(build_config)
    tmp_path = cache_path.with_suffix(".tmp")
    with tmp_path.open("wb") as handle:
        pickle.dump(samples, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tmp_path.replace(cache_path)
    return samples
```

- [ ] **Step 4: Run split/cache tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_resolve_replay_split_uses_three_way_manifest tests.model.test_model_replay.TestModelReplay.test_load_or_build_samples_uses_cache_until_lifecycle_metadata_changes
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Cache replay evaluation samples"
```

## Task 4: Run Replay And Write Reports Without Overwriting Model Artifacts

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing replay orchestration test**

Append this test inside `TestModelReplay`:

```python
    def test_run_model_replay_writes_report_without_overwriting_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            output_path = Path(tmpdir) / "report.json"
            model_dir.mkdir()
            original_manifest = {
                "artifacts": {"buy_model": {"threshold": 0.8}},
                "three_way_split": {"enabled": True, "train_split_ratio": 0.6, "validation_split_ratio": 0.2},
                "evaluation": {"max_entry_age_seconds": 300, "fixed_stake_bnb": 0.1},
            }
            (model_dir / "hybrid_manifest.json").write_text(json.dumps(original_manifest), encoding="utf-8")
            fake_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=2,
            )
            fake_artifacts = m.LoadedReplayArtifacts(
                buy_artifact={"model": MagicMock(), "threshold": 0.8},
                ppo_artifact={"model": MagicMock(), "total_timesteps": 10},
                bc_artifact={"bc_samples": 5},
            )
            fake_eval = {"total_trades": 1, "net_profit_bnb": 0.2, "max_drawdown_pct": -5.0, "trade_log": [{"token": "0x1", "return_pct": 20.0}]}

            with patch.object(m, "resolve_replay_split", return_value=fake_split), \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m, "load_or_build_samples", return_value=[{"features": {}, "meta": {}}]) as mock_samples, \
                 patch.object(m.train_hybrid, "run_ab_evaluation", return_value=fake_eval), \
                 patch.object(m, "git_metadata", return_value={"commit": "abc", "branch": "main", "dirty": False}):
                report = m.run_model_replay(model_dir, output_path=output_path, cache_dir=Path(tmpdir) / "cache", split="final", include_trade_log=True)

            manifest_after = json.loads((model_dir / "hybrid_manifest.json").read_text(encoding="utf-8"))
            written = json.loads(output_path.read_text(encoding="utf-8"))
            trade_log_path = Path(written["evaluation"]["trade_log_path"])

        self.assertEqual(manifest_after, original_manifest)
        self.assertEqual(report["evaluation"]["total_trades"], 1)
        self.assertEqual(written["evaluation"]["trade_log_count"], 1)
        self.assertTrue(trade_log_path.name.endswith(".trade_log.jsonl"))
        mock_samples.assert_called_once()
```

- [ ] **Step 2: Run the replay orchestration test to verify it fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_run_model_replay_writes_report_without_overwriting_manifest
```

Expected: FAIL because `run_model_replay` is not defined.

- [ ] **Step 3: Implement replay orchestration and report writing**

Add this code to `src/pipeline/model_replay.py`:

```python
from datetime import datetime, timezone


def _write_trade_log_sidecar(output_path: Path, evaluation: dict) -> dict:
    evaluation = dict(evaluation)
    trade_log = evaluation.pop("trade_log", None)
    if not trade_log:
        return evaluation
    trade_log_path = output_path.with_suffix(".trade_log.jsonl")
    with trade_log_path.open("w", encoding="utf-8") as handle:
        for row in trade_log:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    evaluation["trade_log_path"] = str(trade_log_path)
    evaluation["trade_log_count"] = int(len(trade_log))
    evaluation["exit_reason_summary"] = train_hybrid._summarize_trade_log_by_exit_reason(trade_log)
    evaluation["top_trade_profit_concentration"] = train_hybrid._trade_profit_concentration(trade_log)
    return evaluation


def _split_paths_for_role(replay_split: ReplaySplit, split: str) -> tuple[list[Path], set[str], int]:
    if split == "validation":
        return replay_split.validation_files, replay_split.excluded_validation_tokens, 0
    if split == "final":
        return replay_split.eval_files, replay_split.excluded_final_tokens, replay_split.raw_final_overlap_token_count
    raise ValueError("split must be 'validation' or 'final'")


def run_model_replay(
    model_dir,
    *,
    lifecycle_dir="data/training",
    output_path=None,
    cache_dir=".cache/model_replay",
    split="final",
    max_open_positions=8,
    include_trade_log=False,
    overrides=None,
    use_cache=True,
    write_report=True,
) -> dict:
    model_dir = Path(model_dir)
    manifest = load_manifest(model_dir)
    replay_split = resolve_replay_split(manifest, lifecycle_dir)
    lifecycle_paths, exclude_tokens, raw_overlap = _split_paths_for_role(replay_split, split)
    config = live_replay_config_from_manifest(
        manifest,
        max_open_positions=int(max_open_positions),
        include_trade_log=include_trade_log,
        overrides=overrides,
    )
    config["lifecycle_dir"] = lifecycle_dir
    config["evaluation_split"] = "validation" if split == "validation" else "final_test"
    config["train_file_count"] = len(replay_split.train_files)
    config["validation_file_count"] = len(replay_split.validation_files)
    config["eval_file_count"] = len(lifecycle_paths)
    config["raw_overlap_token_count"] = int(raw_overlap)
    config["excluded_eval_token_count"] = int(raw_overlap if split == "final" else 0)
    config["overlap_token_count"] = 0
    samples = load_or_build_samples(config, lifecycle_paths, exclude_tokens, cache_dir=cache_dir, use_cache=use_cache)
    config["eval_samples"] = samples

    artifacts = load_model_artifacts(model_dir)
    if overrides and overrides.get("buy_threshold") is not None:
        artifacts.buy_artifact = dict(artifacts.buy_artifact)
        artifacts.buy_artifact["threshold"] = float(overrides["buy_threshold"])
    evaluation = train_hybrid.run_ab_evaluation(
        config,
        artifacts.buy_artifact,
        artifacts.ppo_artifact,
        artifacts.bc_artifact,
    )

    if write_report:
        if output_path is None:
            report_dir = Path("data/replay_reports")
            report_dir.mkdir(parents=True, exist_ok=True)
            output_path = report_dir / f"{model_dir.name}_{split}_cap{max_open_positions}.json"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        evaluation = _write_trade_log_sidecar(output_path, evaluation)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_dir": str(model_dir),
        "split": split,
        "selection_role": "report_only" if split == "final" else "validation_selection",
        "git": git_metadata(Path.cwd()),
        "model_checksums": model_checksums(model_dir),
        "replay_config": {key: value for key, value in config.items() if key != "eval_samples"},
        "sample_count": int(len(samples)),
        "lifecycle_paths": [str(path) for path in lifecycle_paths],
        "evaluation": evaluation,
    }
    if write_report:
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report
```

- [ ] **Step 4: Run replay orchestration test**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_run_model_replay_writes_report_without_overwriting_manifest
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Replay existing models without retraining"
```

## Task 5: Add Replay CLI

**Files:**
- Create: `tests/model/test_replay_model_cli.py`
- Create: `scripts/replay_model.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/model/test_replay_model_cli.py`:

```python
import importlib.util
import json
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "replay_model.py"
    spec = importlib.util.spec_from_file_location("replay_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestReplayModelCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args(["--model-dir", "data/models/example"])
        self.assertEqual(args.model_dir, "data/models/example")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.split, "final")
        self.assertEqual(args.max_open_positions, 8)
        self.assertEqual(args.cache_dir, ".cache/model_replay")
        self.assertFalse(args.include_trade_log)
        self.assertTrue(args.use_cache)

    def test_main_calls_run_model_replay(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = lambda **kwargs: {"evaluation": {"net_profit_bnb": 1.2}}
        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            with patch.object(fake_module, "run_model_replay", return_value={"evaluation": {"net_profit_bnb": 1.2}}) as mock_run:
                result = cli.main([
                    "--model-dir", "data/models/example",
                    "--output", "data/replay_reports/out.json",
                    "--split", "validation",
                    "--max-open-positions", "8",
                    "--include-trade-log",
                    "--no-cache",
                ])

        mock_run.assert_called_once_with(
            model_dir="data/models/example",
            lifecycle_dir="data/training",
            output_path="data/replay_reports/out.json",
            cache_dir=".cache/model_replay",
            split="validation",
            max_open_positions=8,
            include_trade_log=True,
            use_cache=False,
            overrides={},
        )
        self.assertEqual(result["evaluation"]["net_profit_bnb"], 1.2)

    def test_help_lists_live_controls(self):
        result = subprocess.run(
            [sys.executable, "scripts/replay_model.py", "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--max-open-positions", result.stdout)
        self.assertIn("--threshold", result.stdout)
        self.assertIn("--stop-loss", result.stdout)
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_replay_model_cli
```

Expected: FAIL because `scripts/replay_model.py` does not exist.

- [ ] **Step 3: Implement thin replay CLI**

Create `scripts/replay_model.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Replay a trained hybrid model without retraining")
    parser.add_argument("--model-dir", required=True, help="Directory containing buy_model.cbm and hybrid_manifest.json")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=None, help="Replay report JSON path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for generated eval sample cache")
    parser.add_argument("--split", choices=["validation", "final"], default="final", help="Replay split to evaluate")
    parser.add_argument("--max-open-positions", type=int, default=8, help="Maximum open or pending positions in replay")
    parser.add_argument("--include-trade-log", action="store_true", help="Write trade log sidecar next to the report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild eval samples instead of using cache")
    parser.set_defaults(use_cache=True)
    parser.add_argument("--threshold", type=float, default=None, help="Override buy probability threshold")
    parser.add_argument("--stop-loss", type=float, default=None, help="Override stop loss")
    parser.add_argument("--trailing-start-pct", type=float, default=None, help="Override trailing start percent")
    parser.add_argument("--trailing-stop-pct", type=float, default=None, help="Override trailing stop percent")
    parser.add_argument("--entry-price-protection-pct", type=float, default=None, help="Override entry price protection")
    parser.add_argument("--max-pending-entries", type=int, default=None, help="Override pending entry cap")
    return parser.parse_args(argv)


def _overrides_from_args(args):
    mapping = {
        "threshold": "buy_threshold",
        "stop_loss": "stop_loss",
        "trailing_start_pct": "trailing_start_pct",
        "trailing_stop_pct": "trailing_stop_pct",
        "entry_price_protection_pct": "entry_price_protection_pct",
        "max_pending_entries": "max_pending_entries",
    }
    overrides = {}
    for attr, key in mapping.items():
        value = getattr(args, attr)
        if value is not None:
            overrides[key] = value
    return overrides


def main(argv=None):
    args = parse_args(argv)
    from src.pipeline.model_replay import run_model_replay

    report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        cache_dir=args.cache_dir,
        split=args.split,
        max_open_positions=args.max_open_positions,
        include_trade_log=args.include_trade_log,
        use_cache=args.use_cache,
        overrides=_overrides_from_args(args),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))
    return report


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_replay_model_cli
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/replay_model.py tests/model/test_replay_model_cli.py
git commit -m "Add replay model CLI"
```

## Task 6: Add Live Score Function

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing score tests**

Append these tests inside `TestModelReplay`:

```python
    def test_live_score_prefers_profit_when_risk_is_acceptable(self):
        low_profit = {"evaluation": {"net_profit_bnb": 1.0, "max_drawdown_pct": -10.0, "walk_forward_worst_net_return_pct": 20.0}}
        high_profit = {"evaluation": {"net_profit_bnb": 2.0, "max_drawdown_pct": -12.0, "walk_forward_worst_net_return_pct": 30.0}}

        self.assertGreater(m.live_score(high_profit)["score"], m.live_score(low_profit)["score"])

    def test_live_score_penalizes_drawdown_and_harsh_collapse(self):
        safe = {
            "evaluation": {
                "net_profit_bnb": 2.0,
                "max_drawdown_pct": -15.0,
                "walk_forward_worst_net_return_pct": 10.0,
                "stress_replay": [{"name": "harsh_friction", "net_profit_bnb": 0.1}],
            }
        }
        risky = {
            "evaluation": {
                "net_profit_bnb": 2.5,
                "max_drawdown_pct": -55.0,
                "walk_forward_worst_net_return_pct": -40.0,
                "stress_replay": [{"name": "harsh_friction", "net_profit_bnb": -1.0}],
            }
        }

        scored_safe = m.live_score(safe)
        scored_risky = m.live_score(risky)

        self.assertGreater(scored_safe["score"], scored_risky["score"])
        self.assertGreater(scored_risky["penalties"]["drawdown"], 0.0)
        self.assertGreater(scored_risky["penalties"]["walk_forward_loss"], 0.0)
        self.assertGreater(scored_risky["penalties"]["harsh_friction_loss"], 0.0)
```

- [ ] **Step 2: Run score tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_live_score_prefers_profit_when_risk_is_acceptable tests.model.test_model_replay.TestModelReplay.test_live_score_penalizes_drawdown_and_harsh_collapse
```

Expected: FAIL because `live_score` is not defined.

- [ ] **Step 3: Implement live score**

Add this code to `src/pipeline/model_replay.py`:

```python

def _stress_profit(evaluation: dict, names: set[str]) -> float:
    for row in evaluation.get("stress_replay", []) or []:
        if str(row.get("name", "")) in names:
            return float(row.get("net_profit_bnb", 0.0) or 0.0)
    return 0.0


def live_score(report_or_evaluation: dict, *, preferred_max_drawdown_pct=-30.0) -> dict:
    evaluation = report_or_evaluation.get("evaluation", report_or_evaluation)
    base_profit = float(evaluation.get("net_profit_bnb", 0.0) or 0.0)
    max_drawdown = float(evaluation.get("max_drawdown_pct", 0.0) or 0.0)
    worst_walk_forward_return = float(evaluation.get("walk_forward_worst_net_return_pct", 0.0) or 0.0)
    harsh_profit = _stress_profit(evaluation, {"harsh_friction", "harsh_execution"})
    concentration = evaluation.get("top_trade_profit_concentration", {}) or {}
    top10_share = float(concentration.get("top_10_profit_share", 0.0) or 0.0)

    drawdown_excess = max(0.0, abs(min(0.0, max_drawdown)) - abs(float(preferred_max_drawdown_pct)))
    walk_forward_loss = max(0.0, -worst_walk_forward_return / 100.0)
    harsh_loss = max(0.0, -harsh_profit)
    concentration_excess = max(0.0, top10_share - 0.25)
    penalties = {
        "drawdown": drawdown_excess * 0.08,
        "walk_forward_loss": walk_forward_loss * 2.0,
        "harsh_friction_loss": harsh_loss * 1.5,
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
    }
```

- [ ] **Step 4: Run score tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_live_score_prefers_profit_when_risk_is_acceptable tests.model.test_model_replay.TestModelReplay.test_live_score_penalizes_drawdown_and_harsh_collapse
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Score live replay robustness"
```

## Task 7: Add Validation-Only Parameter Search

**Files:**
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write failing search tests**

Append this test inside `TestModelReplay`:

```python
    def test_run_parameter_search_selects_on_validation_and_reports_final(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            output_path = Path(tmpdir) / "search.json"
            calls = []

            def fake_replay(model_dir, *, split, overrides, output_path=None, **kwargs):
                calls.append({"split": split, "overrides": dict(overrides or {})})
                threshold = float((overrides or {}).get("buy_threshold", 0.8))
                if split == "validation":
                    profit = 2.0 if threshold == 0.85 else 1.0
                    return {"evaluation": {"net_profit_bnb": profit, "max_drawdown_pct": -10.0, "walk_forward_worst_net_return_pct": 5.0}}
                return {"evaluation": {"net_profit_bnb": 3.0, "max_drawdown_pct": -12.0, "walk_forward_worst_net_return_pct": 6.0}}

            with patch.object(m, "run_model_replay", side_effect=fake_replay):
                result = m.run_parameter_search(
                    model_dir,
                    output_path=output_path,
                    candidates=[{"buy_threshold": 0.8}, {"buy_threshold": 0.85}],
                )

            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result["selected_candidate"]["overrides"], {"buy_threshold": 0.85})
        self.assertEqual(written["selected_candidate"]["selection_split"], "validation")
        self.assertEqual(written["final_report"]["selection_role"], "report_only")
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final"])
```

- [ ] **Step 2: Run search test to verify it fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_run_parameter_search_selects_on_validation_and_reports_final
```

Expected: FAIL because `run_parameter_search` is not defined.

- [ ] **Step 3: Implement candidate search**

Add this code to `src/pipeline/model_replay.py`:

```python

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


def run_parameter_search(
    model_dir,
    *,
    lifecycle_dir="data/training",
    output_path=None,
    cache_dir=".cache/model_replay",
    candidates=None,
    max_open_positions=8,
    use_cache=True,
    write_report=True,
) -> dict:
    model_dir = Path(model_dir)
    candidates = list(candidates or default_candidate_grid())
    scored_candidates = []
    best = None
    best_score = None
    for index, overrides in enumerate(candidates):
        replay_overrides = dict(overrides)
        replay_overrides.pop("max_open_positions", None)
        validation_report = run_model_replay(
            model_dir,
            lifecycle_dir=lifecycle_dir,
            output_path=None,
            cache_dir=cache_dir,
            split="validation",
            max_open_positions=int(overrides.get("max_open_positions", max_open_positions)),
            include_trade_log=False,
            overrides=replay_overrides,
            use_cache=use_cache,
            write_report=False,
        )
        scored = live_score(validation_report)
        row = {
            "candidate_index": int(index),
            "selection_split": "validation",
            "overrides": dict(overrides),
            "score": scored,
            "evaluation": validation_report.get("evaluation", {}),
        }
        scored_candidates.append(row)
        score_key = (float(scored["score"]), float(scored.get("base_profit_bnb", 0.0)), -index)
        if best_score is None or score_key > best_score:
            best_score = score_key
            best = row

    selected_overrides = dict(best["overrides"] if best else {})
    selected_max_open_positions = int(selected_overrides.pop("max_open_positions", max_open_positions))
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
        "selected_candidate": best,
        "candidate_count": int(len(scored_candidates)),
        "candidates": scored_candidates,
        "final_report": final_report,
    }
    if output_path is None:
        report_dir = Path("data/replay_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        output_path = report_dir / f"{model_dir.name}_validation_search.json"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
```

- [ ] **Step 4: Run search test**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay.TestModelReplay.test_run_parameter_search_selects_on_validation_and_reports_final
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/pipeline/model_replay.py tests/model/test_model_replay.py
git commit -m "Search replay parameters on validation split"
```

## Task 8: Add Parameter Search CLI

**Files:**
- Create: `tests/model/test_search_replay_params_cli.py`
- Create: `scripts/search_replay_params.py`

- [ ] **Step 1: Write failing search CLI tests**

Create `tests/model/test_search_replay_params_cli.py`:

```python
import importlib.util
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "search_replay_params.py"
    spec = importlib.util.spec_from_file_location("search_replay_params", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSearchReplayParamsCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args(["--model-dir", "data/models/example"])
        self.assertEqual(args.model_dir, "data/models/example")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.max_open_positions, 8)
        self.assertEqual(args.thresholds, "0.75,0.8,0.825,0.85,0.875,0.9")
        self.assertTrue(args.use_cache)

    def test_main_calls_run_parameter_search(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_parameter_search = lambda **kwargs: {"candidate_count": 1}
        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            with patch.object(fake_module, "run_parameter_search", return_value={"candidate_count": 1}) as mock_run:
                result = cli.main([
                    "--model-dir", "data/models/example",
                    "--output", "data/replay_reports/search.json",
                    "--thresholds", "0.8,0.85",
                    "--stop-losses", "-0.25",
                    "--trailing-pairs", "0.2:0.1",
                    "--no-cache",
                ])

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["model_dir"], "data/models/example")
        self.assertEqual(kwargs["output_path"], "data/replay_reports/search.json")
        self.assertEqual(kwargs["candidates"], [
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8},
            {"buy_threshold": 0.85, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8},
        ])
        self.assertFalse(kwargs["use_cache"])
        self.assertEqual(result["candidate_count"], 1)

    def test_help_lists_search_controls(self):
        result = subprocess.run(
            [sys.executable, "scripts/search_replay_params.py", "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--thresholds", result.stdout)
        self.assertIn("--trailing-pairs", result.stdout)
```

- [ ] **Step 2: Run search CLI tests to verify they fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_search_replay_params_cli
```

Expected: FAIL because `scripts/search_replay_params.py` does not exist.

- [ ] **Step 3: Implement search CLI**

Create `scripts/search_replay_params.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parse_float_list(raw):
    return [float(part.strip()) for part in str(raw).split(",") if part.strip()]


def _parse_trailing_pairs(raw):
    pairs = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        start, stop = part.split(":", 1)
        pairs.append((float(start), float(stop)))
    return pairs


def _candidate_grid(thresholds, stop_losses, trailing_pairs, max_open_positions):
    candidates = []
    for threshold in thresholds:
        for stop_loss in stop_losses:
            for trailing_start, trailing_stop in trailing_pairs:
                candidates.append({
                    "buy_threshold": float(threshold),
                    "stop_loss": float(stop_loss),
                    "trailing_start_pct": float(trailing_start),
                    "trailing_stop_pct": float(trailing_stop),
                    "max_open_positions": int(max_open_positions),
                })
    return candidates


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Search replay parameters on validation split and report sealed final replay")
    parser.add_argument("--model-dir", required=True, help="Directory containing trained hybrid model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=None, help="Search report JSON path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for generated eval sample cache")
    parser.add_argument("--max-open-positions", type=int, default=8, help="Live capacity for replay search")
    parser.add_argument("--thresholds", default="0.75,0.8,0.825,0.85,0.875,0.9", help="Comma-separated buy thresholds")
    parser.add_argument("--stop-losses", default="-0.2,-0.25,-0.3", help="Comma-separated stop-loss values")
    parser.add_argument("--trailing-pairs", default="0.2:0.1,0.2:0.15,0.25:0.15", help="Comma-separated trailing_start:trailing_stop pairs")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild eval samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from src.pipeline.model_replay import run_parameter_search

    candidates = _candidate_grid(
        _parse_float_list(args.thresholds),
        _parse_float_list(args.stop_losses),
        _parse_trailing_pairs(args.trailing_pairs),
        args.max_open_positions,
    )
    result = run_parameter_search(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        cache_dir=args.cache_dir,
        candidates=candidates,
        max_open_positions=args.max_open_positions,
        use_cache=args.use_cache,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run search CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_search_replay_params_cli
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/search_replay_params.py tests/model/test_search_replay_params_cli.py
git commit -m "Add replay parameter search CLI"
```

## Task 9: Run Focused And Full Test Verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run focused new test surface**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_replay_model_cli tests.model.test_search_replay_params_cli
```

Expected: all tests pass.

- [ ] **Step 2: Run related existing tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline tests.model.test_run_hybrid_training_cli
```

Expected: all tests pass.

- [ ] **Step 3: Run full suite**

Run:

```bash
venv/bin/python -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 4: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output.

## Task 10: Generate Real Replay Reports For v31, v32, And v33

**Files:**
- Creates local artifacts under `data/replay_reports/`.

- [ ] **Step 1: Replay v31 with live cap8**

Run:

```bash
venv/bin/python scripts/replay_model.py \
  --model-dir data/models/20260509_live_cash_v31 \
  --output data/replay_reports/20260509_live_cash_v31_current_cap8.json \
  --split final \
  --max-open-positions 8 \
  --include-trade-log
```

Expected: command completes and writes `data/replay_reports/20260509_live_cash_v31_current_cap8.json`.

- [ ] **Step 2: Replay v32 with live cap8**

Run:

```bash
venv/bin/python scripts/replay_model.py \
  --model-dir data/models/20260509_v32_live_3s_stable \
  --output data/replay_reports/20260509_v32_live_3s_stable_current_cap8.json \
  --split final \
  --max-open-positions 8 \
  --include-trade-log
```

Expected: command completes and writes `data/replay_reports/20260509_v32_live_3s_stable_current_cap8.json`.

- [ ] **Step 3: Replay v33 with live cap8**

Run:

```bash
venv/bin/python scripts/replay_model.py \
  --model-dir data/models/20260509_v33_live_3s_aggressive \
  --output data/replay_reports/20260509_v33_live_3s_aggressive_current_cap8.json \
  --split final \
  --max-open-positions 8 \
  --include-trade-log
```

Expected: command completes and writes `data/replay_reports/20260509_v33_live_3s_aggressive_current_cap8.json`.

- [ ] **Step 4: Extract comparison metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path('data/replay_reports').glob('*current_cap8.json')):
    report = json.loads(path.read_text(encoding='utf-8'))
    e = report['evaluation']
    print(json.dumps({
        'report': str(path),
        'model': report['model_dir'],
        'trades': e.get('total_trades'),
        'win_rate': e.get('win_rate'),
        'net_profit_bnb': e.get('net_profit_bnb'),
        'final_equity_bnb': e.get('final_equity_bnb'),
        'max_drawdown_pct': e.get('max_drawdown_pct'),
        'walk_forward_worst_net_return_pct': e.get('walk_forward_worst_net_return_pct'),
        'walk_forward_worst_max_drawdown_pct': e.get('walk_forward_worst_max_drawdown_pct'),
    }, ensure_ascii=False, sort_keys=True))
PY
```

Expected: prints one JSON metric row per model.

## Task 11: Run Validation-Only Search On The Latest Baseline

**Files:**
- Creates local artifact under `data/replay_reports/`.

- [ ] **Step 1: Run validation-only search on v33**

Run:

```bash
venv/bin/python scripts/search_replay_params.py \
  --model-dir data/models/20260509_v33_live_3s_aggressive \
  --output data/replay_reports/20260509_v33_live_3s_aggressive_validation_search.json \
  --thresholds 0.75,0.8,0.825,0.85,0.875,0.9 \
  --stop-losses -0.2,-0.25,-0.3 \
  --trailing-pairs 0.2:0.1,0.2:0.15,0.25:0.15 \
  --max-open-positions 8
```

Expected: command completes and writes `data/replay_reports/20260509_v33_live_3s_aggressive_validation_search.json`.

- [ ] **Step 2: Extract selected validation candidate and sealed final metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('data/replay_reports/20260509_v33_live_3s_aggressive_validation_search.json')
report = json.loads(p.read_text(encoding='utf-8'))
selected = report['selected_candidate']
final = report['final_report']['evaluation']
print(json.dumps({
    'selected_overrides': selected['overrides'],
    'validation_score': selected['score'],
    'final_trades': final.get('total_trades'),
    'final_win_rate': final.get('win_rate'),
    'final_net_profit_bnb': final.get('net_profit_bnb'),
    'final_max_drawdown_pct': final.get('max_drawdown_pct'),
    'final_walk_forward_worst_net_return_pct': final.get('walk_forward_worst_net_return_pct'),
    'final_walk_forward_worst_max_drawdown_pct': final.get('walk_forward_worst_max_drawdown_pct'),
}, ensure_ascii=False, indent=2, sort_keys=True))
PY
```

Expected: prints selected validation-only parameters and sealed final metrics for v33.

## Task 12: Final Review And Report

**Files:**
- No code changes expected unless Task 10 or Task 11 reveals a bug.

- [ ] **Step 1: Inspect git status**

Run:

```bash
git status --short
```

Expected: only intentional code/test/script files are tracked or committed; generated replay reports are untracked or ignored.

- [ ] **Step 2: Review changed code**

Run:

```bash
git diff HEAD~8..HEAD -- src/pipeline/model_replay.py scripts/replay_model.py scripts/search_replay_params.py tests/model/test_model_replay.py tests/model/test_replay_model_cli.py tests/model/test_search_replay_params_cli.py
```

Expected: code review confirms model artifacts are loaded without retraining, final reports are report-only, validation search selects on validation, and model manifests are not overwritten.

- [ ] **Step 3: Prepare final user report**

Report these items:

- Tests run and pass/fail status.
- v31/v32/v33 current-code cap8 replay comparison.
- Selected validation-only search candidate.
- Sealed final metrics for that candidate.
- Whether the result improves live-capacity profit, robustness, or both versus v33 saved baseline.
- Next recommendation: EV/risk entry ranking if parameter search does not materially improve both cap8 profit and stress robustness.
