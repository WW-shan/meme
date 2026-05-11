import json
import importlib
import sys
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
