import json
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pipeline import model_replay as m


def _fake_train_hybrid(**overrides):
    fake = types.SimpleNamespace(
        _discover_lifecycle_files=MagicMock(),
        _split_lifecycle_files_three_way=MagicMock(),
        _split_lifecycle_files=MagicMock(),
        _load_samples=MagicMock(),
    )
    for name, value in overrides.items():
        setattr(fake, name, value)
    return fake


class TestModelReplay(unittest.TestCase):
    def tearDown(self):
        import src.pipeline

        sys.modules.pop("src.pipeline.train_hybrid", None)
        if hasattr(src.pipeline, "train_hybrid"):
            delattr(src.pipeline, "train_hybrid")

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
        self.assertEqual(checksums["buy_model.cbm"], checksums["buy_model.cbm"])

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

    def test_module_import_does_not_require_catboost(self):
        original_module = sys.modules.pop("src.pipeline.model_replay", None)
        original_attr = getattr(sys.modules["src.pipeline"], "model_replay", None)
        real_import = __import__

        def _import_without_catboost(name, *args, **kwargs):
            if name == "catboost":
                raise ModuleNotFoundError("No module named 'catboost'")
            return real_import(name, *args, **kwargs)

        try:
            with patch("builtins.__import__", side_effect=_import_without_catboost):
                imported = importlib.import_module("src.pipeline.model_replay")
        finally:
            sys.modules.pop("src.pipeline.model_replay", None)
            if original_module is not None:
                sys.modules["src.pipeline.model_replay"] = original_module
            if original_attr is not None:
                sys.modules["src.pipeline"].model_replay = original_attr

        self.assertIsNone(imported.CatBoostClassifier)

    def test_module_import_does_not_import_train_hybrid(self):
        import src.pipeline

        original_module = sys.modules.pop("src.pipeline.model_replay", None)
        original_attr = getattr(sys.modules["src.pipeline"], "model_replay", None)
        original_train_hybrid = sys.modules.pop("src.pipeline.train_hybrid", None)
        original_train_hybrid_attr = getattr(src.pipeline, "train_hybrid", None)
        if hasattr(src.pipeline, "train_hybrid"):
            delattr(src.pipeline, "train_hybrid")

        try:
            importlib.import_module("src.pipeline.model_replay")
            self.assertNotIn("src.pipeline.train_hybrid", sys.modules)
        finally:
            sys.modules.pop("src.pipeline.model_replay", None)
            if original_module is not None:
                sys.modules["src.pipeline.model_replay"] = original_module
            if original_attr is not None:
                sys.modules["src.pipeline"].model_replay = original_attr
            if original_train_hybrid is not None:
                sys.modules["src.pipeline.train_hybrid"] = original_train_hybrid
            if original_train_hybrid_attr is not None:
                src.pipeline.train_hybrid = original_train_hybrid_attr

    def test_load_model_artifacts_keeps_policy_path_when_policy_load_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir)
            (model_dir / "buy_model.cbm").write_text("buy", encoding="utf-8")
            (model_dir / "buy_threshold.json").write_text('{"threshold": 0.5}', encoding="utf-8")
            (model_dir / "feature_schema.json").write_text('{"feature_names": ["current_price"]}', encoding="utf-8")
            (model_dir / "sell_policy.zip").write_text("ppo", encoding="utf-8")

            with patch.object(m, "CatBoostClassifier", return_value=MagicMock()), \
                 patch.object(m, "PPO", MagicMock(load=MagicMock(side_effect=RuntimeError("bad policy")))), \
                 self.assertLogs(m.logger, level="WARNING") as logs:
                artifacts = m.load_model_artifacts(model_dir)

        self.assertIsNone(artifacts.ppo_artifact["model"])
        self.assertEqual(artifacts.ppo_artifact["policy_path"], str(model_dir / "sell_policy.zip"))
        self.assertIn("failed to load optional sell policy", "\n".join(logs.output))

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

        fake_module = _fake_train_hybrid(
            _discover_lifecycle_files=MagicMock(return_value=fake_files),
            _split_lifecycle_files_three_way=MagicMock(return_value=split_result),
        )
        with patch.object(m.train_hybrid, "_load", return_value=fake_module):
            replay_split = m.resolve_replay_split(manifest, "data/training")

        fake_module._discover_lifecycle_files.assert_called_once_with("data/training")
        fake_module._split_lifecycle_files_three_way.assert_called_once_with(
            fake_files,
            0.6,
            0.2,
            1,
            1,
            enforce_no_overlap=False,
        )
        self.assertEqual(replay_split.train_files, fake_files[:3])
        self.assertEqual(replay_split.validation_files, fake_files[3:4])
        self.assertEqual(replay_split.eval_files, fake_files[4:])
        self.assertEqual(replay_split.excluded_final_tokens, {"0xtrain", "0xval"})
        self.assertEqual(replay_split.raw_final_overlap_token_count, 2)

    def test_resolve_replay_split_uses_two_way_manifest_when_three_way_disabled(self):
        fake_files = [Path(f"lifecycle_incremental_{idx:03d}.jsonl") for idx in range(1, 5)]
        manifest = {
            "three_way_split": {"enabled": False},
            "split": {
                "train_split_ratio": 0.75,
                "min_eval_files": 1,
            },
        }
        train_files = fake_files[:3]
        eval_files = fake_files[3:]
        train_tokens = {"0xtrain-a", "0xtrain-b"}
        eval_tokens = {"0xeval"}

        fake_module = _fake_train_hybrid(
            _discover_lifecycle_files=MagicMock(return_value=fake_files),
            _split_lifecycle_files=MagicMock(return_value=(
                train_files,
                eval_files,
                1,
                train_tokens,
                eval_tokens,
            )),
        )
        with patch.object(m.train_hybrid, "_load", return_value=fake_module):
            replay_split = m.resolve_replay_split(manifest, "data/training")

        fake_module._discover_lifecycle_files.assert_called_once_with("data/training")
        fake_module._split_lifecycle_files.assert_called_once_with(
            fake_files,
            0.75,
            1,
            enforce_no_overlap=False,
            return_token_sets=True,
        )
        self.assertEqual(replay_split.train_files, train_files)
        self.assertEqual(replay_split.validation_files, [])
        self.assertEqual(replay_split.eval_files, eval_files)
        self.assertEqual(replay_split.excluded_final_tokens, train_tokens)
        self.assertEqual(replay_split.raw_final_overlap_token_count, 1)

    def test_load_or_build_samples_uses_cache_until_lifecycle_metadata_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            config = {"sample_mode": "trade_event", "max_sample_age_seconds": 300, "future_windows": [300]}
            first_samples = [{"meta": {"token_address": "0x1"}, "features": {"current_price": 1.0}}]
            second_samples = [{"meta": {"token_address": "0x2"}, "features": {"current_price": 2.0}}]

            first_module = _fake_train_hybrid(_load_samples=MagicMock(return_value=first_samples))
            with patch.object(m.train_hybrid, "_load", return_value=first_module):
                loaded_first = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)

            lifecycle.write_text('{"token_address":"0x1"}\n{"token_address":"0x2"}\n', encoding="utf-8")
            second_module = _fake_train_hybrid(_load_samples=MagicMock(return_value=second_samples))
            with patch.object(m.train_hybrid, "_load", return_value=second_module):
                loaded_second = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)

        self.assertEqual(loaded_first, first_samples)
        self.assertEqual(loaded_cached, first_samples)
        self.assertEqual(loaded_second, second_samples)
        self.assertEqual(first_module._load_samples.call_count, 1)
        self.assertEqual(second_module._load_samples.call_count, 1)

    def test_load_or_build_samples_rebuilds_when_config_or_exclude_tokens_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            base_config = {"sample_mode": "trade_event", "future_windows": [300]}
            changed_config = {"sample_mode": "trade_event", "future_windows": [600]}
            first_samples = [{"meta": {"token_address": "0x1"}, "features": {"window": 300}}]
            config_changed_samples = [{"meta": {"token_address": "0x1"}, "features": {"window": 600}}]
            exclude_changed_samples = [{"meta": {"token_address": "0x2"}, "features": {"window": 600}}]
            fake_module = _fake_train_hybrid(
                _load_samples=MagicMock(side_effect=[
                    first_samples,
                    config_changed_samples,
                    exclude_changed_samples,
                ])
            )

            with patch.object(m.train_hybrid, "_load", return_value=fake_module):
                loaded_first = m.load_or_build_samples(base_config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(base_config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_config_changed = m.load_or_build_samples(
                    changed_config,
                    [lifecycle],
                    set(),
                    cache_dir=cache_dir,
                )
                loaded_exclude_changed = m.load_or_build_samples(
                    changed_config,
                    [lifecycle],
                    {"0xtrain"},
                    cache_dir=cache_dir,
                )

        self.assertEqual(loaded_first, first_samples)
        self.assertEqual(loaded_cached, first_samples)
        self.assertEqual(loaded_config_changed, config_changed_samples)
        self.assertEqual(loaded_exclude_changed, exclude_changed_samples)
        self.assertEqual(fake_module._load_samples.call_count, 3)

    def test_load_or_build_samples_ignores_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir()
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            config = {"sample_mode": "trade_event", "future_windows": [300]}
            rebuilt_samples = [{"meta": {"token_address": "0x1"}, "features": {"current_price": 1.0}}]
            cache_path = cache_dir / f"{m._sample_cache_key(config, [lifecycle], set())}.pkl"
            cache_path.write_bytes(b"not a pickle")

            fake_module = _fake_train_hybrid(_load_samples=MagicMock(return_value=rebuilt_samples))
            with patch.object(m.train_hybrid, "_load", return_value=fake_module):
                loaded = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(config, [lifecycle], set(), cache_dir=cache_dir)

        self.assertEqual(loaded, rebuilt_samples)
        self.assertEqual(loaded_cached, rebuilt_samples)
        self.assertEqual(fake_module._load_samples.call_count, 1)
