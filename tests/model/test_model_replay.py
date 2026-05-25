import json
import importlib
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pipeline import model_replay as m


QUICK_PROFIT_OVERLAY_KEYS = (
    "buy_quick_profit_overlay_min_prob",
    "buy_quick_profit_overlay_min_pred_return",
    "buy_quick_profit_overlay_max_pred_return",
    "buy_quick_profit_overlay_min_entry_volume_30s",
    "buy_quick_profit_overlay_min_entry_price_volatility",
    "buy_quick_profit_overlay_max_age_seconds",
    "buy_quick_profit_overlay_take_profit_pct",
    "buy_quick_profit_overlay_max_hold_seconds",
    "buy_quick_profit_overlay_min_total_buys",
)


FLOW_ACTIVATION_KEYS = (
    "buy_flow_activation_min_prob",
    "buy_flow_activation_min_pred_return",
    "buy_flow_activation_max_age_seconds",
    "buy_flow_activation_lookback_seconds",
    "buy_flow_activation_min_volume_ramp_ratio",
    "buy_flow_activation_min_volume_ramp_delta",
    "buy_flow_activation_min_pred_return_delta",
    "buy_flow_activation_min_price_volatility_delta",
    "buy_flow_activation_min_current_volume_30s",
    "buy_dead_flow_exit_min_hold_seconds",
    "buy_dead_flow_exit_max_mfe_pct",
)


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


def _load_replay_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "replay_model.py"
    spec = importlib.util.spec_from_file_location("replay_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


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

    def test_selected_runtime_params_override_stale_evaluation_values(self):
        manifest = {
            "artifacts": {"buy_model": {"target_label_column": "live_delay_robust_return_pct"}},
            "evaluation": {
                "fixed_stake_bnb": 0.1,
                "position_fraction": 0.25,
                "max_position_fraction": 0.25,
                "min_policy_hold_seconds": 45,
                "min_entry_score": 35.0,
                "buy_primary_score_rescue_min_prob": 0.99,
                "buy_primary_score_rescue_min_pred_return": 30.0,
            },
            "selected_runtime_params": {
                "fixed_stake_bnb": None,
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
                "min_policy_hold_seconds": 60,
                "min_entry_score": 65.0,
                "buy_primary_score_rescue_min_prob": 0.985,
                "buy_primary_score_rescue_min_pred_return": 25.0,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertIsNone(config["fixed_stake_bnb"])
        self.assertEqual(config["position_fraction"], 0.1)
        self.assertEqual(config["max_position_fraction"], 0.1)
        self.assertEqual(config["min_policy_hold_seconds"], 60)
        self.assertEqual(config["min_entry_score"], 65.0)
        self.assertEqual(config["buy_primary_score_rescue_min_prob"], 0.985)
        self.assertEqual(config["buy_primary_score_rescue_min_pred_return"], 25.0)

    def test_live_replay_config_ignores_manifest_path_state_gate_by_default(self):
        manifest = {
            "selected_runtime_params": {
                "buy_path_state_meta_gate_min_score": 0.7,
                "path_state_scores_by_episode": [{0: 0.9}],
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertIsNone(config["buy_path_state_meta_gate_min_score"])
        self.assertIsNone(config["path_state_scores_by_episode"])

    def test_live_replay_config_ignores_manifest_dead_bounce_veto_by_default(self):
        manifest = {
            "evaluation": {
                "buy_dead_bounce_veto_max_age_seconds": 30.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
            },
            "selected_runtime_params": {
                "buy_dead_bounce_veto_max_age_seconds": 30.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
            },
        }

        config = m.live_replay_config_from_manifest(manifest)

        self.assertIsNone(config["buy_dead_bounce_veto_max_age_seconds"])
        self.assertIsNone(config["buy_dead_bounce_veto_min_peak_drawdown_pct"])

    def test_live_replay_config_allows_explicit_dead_bounce_veto_overrides(self):
        config = m.live_replay_config_from_manifest(
            {},
            overrides={
                "buy_dead_bounce_veto_max_age_seconds": 30.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
            },
        )

        self.assertEqual(config["buy_dead_bounce_veto_max_age_seconds"], 30.0)
        self.assertEqual(config["buy_dead_bounce_veto_min_peak_drawdown_pct"], 0.55)

    def test_selected_runtime_params_omitted_keys_do_not_fallback_to_evaluation_values(self):
        manifest = {
            "evaluation": {
                "fixed_stake_bnb": 0.1,
                "buy_primary_score_rescue_min_prob": 0.99,
                "buy_primary_score_rescue_min_pred_return": 30.0,
                "buy_primary_score_rescue_min_entry_volume_30s": 4.0,
                "buy_primary_score_rescue_min_entry_price_volatility": 0.35,
                "buy_primary_score_rescue_min_age_seconds": 10.0,
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
            },
        }

        config = m.live_replay_config_from_manifest(manifest)

        self.assertIsNone(config["fixed_stake_bnb"])
        self.assertIsNone(config["buy_primary_score_rescue_min_prob"])
        self.assertIsNone(config["buy_primary_score_rescue_min_pred_return"])
        self.assertIsNone(config["buy_primary_score_rescue_min_entry_volume_30s"])
        self.assertIsNone(config["buy_primary_score_rescue_min_entry_price_volatility"])
        self.assertIsNone(config["buy_primary_score_rescue_min_age_seconds"])

    def test_live_replay_config_uses_selected_max_open_positions_by_default(self):
        manifest = {
            "evaluation": {"max_open_positions": 99},
            "selected_runtime_params": {"max_open_positions": 4},
        }

        config = m.live_replay_config_from_manifest(manifest)
        overridden = m.live_replay_config_from_manifest(manifest, max_open_positions=6)

        self.assertEqual(config["max_open_positions"], 4)
        self.assertEqual(overridden["max_open_positions"], 6)

    def test_live_replay_config_keeps_safe_cap_for_selected_null_max_open_positions(self):
        manifest = {
            "evaluation": {"max_open_positions": 99},
            "selected_runtime_params": {"max_open_positions": None},
        }

        config = m.live_replay_config_from_manifest(manifest)
        overridden = m.live_replay_config_from_manifest(manifest, max_open_positions=6)

        self.assertEqual(config["max_open_positions"], 8)
        self.assertEqual(overridden["max_open_positions"], 6)

    def test_live_replay_config_keeps_safe_cap_for_selected_zero_max_open_positions(self):
        manifest = {
            "evaluation": {"max_open_positions": 99},
            "selected_runtime_params": {"max_open_positions": 0},
        }

        config = m.live_replay_config_from_manifest(manifest)
        overridden = m.live_replay_config_from_manifest(manifest, max_open_positions=6)

        self.assertEqual(config["max_open_positions"], 8)
        self.assertEqual(overridden["max_open_positions"], 6)

    def test_live_replay_config_includes_near_threshold_runtime_params(self):
        manifest = {
            "evaluation": {
                "buy_near_threshold_min_prob": 0.95,
                "buy_near_min_pred_return": 40.0,
                "buy_near_min_entry_volume_30s": 2.0,
                "buy_near_min_entry_price_volatility": 0.12,
                "buy_near_min_age_seconds": 5.0,
            },
            "selected_runtime_params": {
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertEqual(config["buy_near_threshold_min_prob"], 0.94)
        self.assertEqual(config["buy_near_min_pred_return"], 32.0)
        self.assertEqual(config["buy_near_min_entry_volume_30s"], 1.25)
        self.assertEqual(config["buy_near_min_entry_price_volatility"], 0.08)
        self.assertEqual(config["buy_near_min_age_seconds"], 0.0)

    def test_live_replay_config_includes_primary_score_rescue_runtime_params(self):
        manifest = {
            "evaluation": {
                "buy_primary_score_rescue_min_prob": 0.99,
                "buy_primary_score_rescue_min_pred_return": 30.0,
                "buy_primary_score_rescue_min_entry_volume_30s": 4.0,
                "buy_primary_score_rescue_min_entry_price_volatility": 0.35,
                "buy_primary_score_rescue_min_age_seconds": 10.0,
            },
            "selected_runtime_params": {
                "buy_primary_score_rescue_min_prob": 0.985,
                "buy_primary_score_rescue_min_pred_return": 25.0,
                "buy_primary_score_rescue_min_entry_volume_30s": 3.0,
                "buy_primary_score_rescue_min_entry_price_volatility": 0.30,
                "buy_primary_score_rescue_min_age_seconds": 0.0,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertEqual(config["buy_primary_score_rescue_min_prob"], 0.985)
        self.assertEqual(config["buy_primary_score_rescue_min_pred_return"], 25.0)
        self.assertEqual(config["buy_primary_score_rescue_min_entry_volume_30s"], 3.0)
        self.assertEqual(config["buy_primary_score_rescue_min_entry_price_volatility"], 0.30)
        self.assertEqual(config["buy_primary_score_rescue_min_age_seconds"], 0.0)

    def test_live_replay_config_excludes_evaluation_low_volume_rescue_params(self):
        manifest = {
            "evaluation": {
                "buy_low_volume_rescue_min_prob": 0.99,
                "buy_low_volume_rescue_min_entry_volume_30s": 1.0,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.6,
                "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
                "buy_low_volume_rescue_max_age_seconds": 60.0,
                "buy_low_volume_rescue_take_profit_pct": 0.25,
                "buy_low_volume_rescue_min_action_score": 0.5,
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertNotIn("buy_low_volume_rescue_min_prob", manifest["selected_runtime_params"])
        self.assertNotIn("buy_low_volume_rescue_take_profit_pct", manifest["selected_runtime_params"])
        self.assertIsNone(config["buy_low_volume_rescue_min_prob"])
        self.assertIsNone(config["buy_low_volume_rescue_min_entry_volume_30s"])
        self.assertIsNone(config["buy_low_volume_rescue_max_entry_volume_30s"])
        self.assertIsNone(config["buy_low_volume_rescue_min_entry_price_volatility"])
        self.assertIsNone(config["buy_low_volume_rescue_max_age_seconds"])
        self.assertIsNone(config["buy_low_volume_rescue_take_profit_pct"])
        self.assertIsNone(config["buy_low_volume_rescue_min_action_score"])
        self.assertIsNone(config["low_volume_rescue_scores_by_episode"])

    def test_live_replay_config_excludes_manifest_quick_profit_overlay_params(self):
        manifest = {
            "evaluation": {
                key: 0.99 for key in QUICK_PROFIT_OVERLAY_KEYS
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
                **{key: 0.988 for key in QUICK_PROFIT_OVERLAY_KEYS},
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        for key in QUICK_PROFIT_OVERLAY_KEYS:
            self.assertIsNone(config[key])

    def test_live_replay_config_allows_explicit_quick_profit_overlay_overrides(self):
        overrides = {
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.5,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.10,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            "buy_quick_profit_overlay_min_total_buys": 10.0,
        }
        manifest = {
            "evaluation": {
                key: 0.99 for key in QUICK_PROFIT_OVERLAY_KEYS
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
            },
        }

        config = m.live_replay_config_from_manifest(
            manifest,
            overrides=overrides,
        )

        for key, value in overrides.items():
            self.assertEqual(config[key], value)

    def test_live_replay_config_excludes_manifest_flow_activation_params(self):
        manifest = {
            "evaluation": {
                key: 0.99 for key in FLOW_ACTIVATION_KEYS
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
                **{key: 0.988 for key in FLOW_ACTIVATION_KEYS},
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        for key in FLOW_ACTIVATION_KEYS:
            self.assertIsNone(config[key])

    def test_live_replay_config_allows_explicit_flow_activation_overrides(self):
        overrides = {
            "buy_flow_activation_min_prob": 0.98,
            "buy_flow_activation_min_pred_return": 35.0,
            "buy_flow_activation_max_age_seconds": 60.0,
            "buy_flow_activation_lookback_seconds": 30.0,
            "buy_flow_activation_min_volume_ramp_ratio": 2.0,
            "buy_flow_activation_min_volume_ramp_delta": 1.0,
            "buy_flow_activation_min_pred_return_delta": 5.0,
            "buy_flow_activation_min_price_volatility_delta": 0.04,
            "buy_flow_activation_min_current_volume_30s": 1.5,
            "buy_dead_flow_exit_min_hold_seconds": 60.0,
            "buy_dead_flow_exit_max_mfe_pct": 0.05,
        }
        manifest = {
            "evaluation": {
                key: 0.99 for key in FLOW_ACTIVATION_KEYS
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
            },
        }

        config = m.live_replay_config_from_manifest(
            manifest,
            overrides=overrides,
        )

        for key, value in overrides.items():
            self.assertEqual(config[key], value)

    def test_live_replay_config_defaults_profit_lock_overrides_to_none(self):
        manifest = {
            "evaluation": {
                "profit_lock_take_profit_pct": 0.25,
                "profit_lock_max_hold_seconds": 60.0,
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
                "profit_lock_take_profit_pct": 0.35,
                "profit_lock_max_hold_seconds": 90.0,
            },
        }

        config = m.live_replay_config_from_manifest(manifest, max_open_positions=8)

        self.assertIsNone(config["profit_lock_take_profit_pct"])
        self.assertIsNone(config["profit_lock_max_hold_seconds"])

    def test_live_replay_config_allows_explicit_profit_lock_overrides(self):
        manifest = {
            "evaluation": {
                "profit_lock_take_profit_pct": 0.25,
                "profit_lock_max_hold_seconds": 60.0,
            },
            "selected_runtime_params": {
                "position_fraction": 0.1,
                "max_position_fraction": 0.1,
            },
        }

        config = m.live_replay_config_from_manifest(
            manifest,
            max_open_positions=8,
            overrides={
                "profit_lock_take_profit_pct": 0.35,
                "profit_lock_max_hold_seconds": 90.0,
            },
        )

        self.assertEqual(config["profit_lock_take_profit_pct"], 0.35)
        self.assertEqual(config["profit_lock_max_hold_seconds"], 90.0)

    def test_replay_cli_can_load_execution_calibration_overrides(self):
        cli = _load_replay_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "execution_calibration.json"
            calibration_path.write_text(
                json.dumps(
                    {
                        "replay_overrides": {
                            "entry_delay_seconds": 6,
                            "entry_max_fill_wait_seconds": 12,
                            "exit_delay_seconds": 4,
                            "exit_max_fill_wait_seconds": 7,
                            "entry_execution_failure_rate": 0.03,
                            "exit_execution_failure_rate": 0.02,
                        }
                    }
                ),
                encoding="utf-8",
            )
            args = cli.parse_args(
                [
                    "--model-dir",
                    str(Path(tmpdir) / "model"),
                    "--execution-calibration-file",
                    str(calibration_path),
                ]
            )
            overrides = cli._overrides_from_args(args)

        self.assertEqual(overrides["entry_delay_seconds"], 6)
        self.assertEqual(overrides["entry_max_fill_wait_seconds"], 12)
        self.assertEqual(overrides["exit_delay_seconds"], 4)
        self.assertEqual(overrides["exit_max_fill_wait_seconds"], 7)
        self.assertEqual(overrides["entry_execution_failure_rate"], 0.03)
        self.assertEqual(overrides["exit_execution_failure_rate"], 0.02)

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

    def test_load_model_artifacts_loads_optional_entry_value_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir)
            (model_dir / "buy_model.cbm").write_text("buy", encoding="utf-8")
            (model_dir / "entry_value_model.cbm").write_text("entry-value", encoding="utf-8")
            (model_dir / "buy_threshold.json").write_text('{"threshold": 0.825}', encoding="utf-8")
            (model_dir / "feature_schema.json").write_text('{"feature_names": ["current_price"]}', encoding="utf-8")
            fake_buy = MagicMock()
            fake_value = MagicMock()

            with patch.object(m, "CatBoostClassifier", return_value=fake_buy), \
                 patch.object(m, "CatBoostRegressor", return_value=fake_value):
                artifacts = m.load_model_artifacts(model_dir)

        fake_value.load_model.assert_called_once_with(str(model_dir / "entry_value_model.cbm"))
        self.assertIs(artifacts.buy_artifact["entry_value_model"]["model"], fake_value)
        self.assertEqual(
            artifacts.buy_artifact["entry_value_model"]["model_path"],
            str(model_dir / "entry_value_model.cbm"),
        )

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

    def test_module_import_does_not_attempt_stable_baselines3_import(self):
        original_module = sys.modules.pop("src.pipeline.model_replay", None)
        original_attr = getattr(sys.modules["src.pipeline"], "model_replay", None)
        real_import = __import__
        attempted = []

        def _tracking_import(name, *args, **kwargs):
            attempted.append(name)
            if name == "stable_baselines3":
                raise AssertionError("stable_baselines3 should be imported lazily")
            return real_import(name, *args, **kwargs)

        try:
            with patch("builtins.__import__", side_effect=_tracking_import):
                imported = importlib.import_module("src.pipeline.model_replay")
        finally:
            sys.modules.pop("src.pipeline.model_replay", None)
            if original_module is not None:
                sys.modules["src.pipeline.model_replay"] = original_module
            if original_attr is not None:
                sys.modules["src.pipeline"].model_replay = original_attr

        self.assertIsNone(imported.PPO)
        self.assertNotIn("stable_baselines3", attempted)

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

    def test_load_or_build_samples_rebuilds_when_optional_flow_features_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            base_config = {"sample_mode": "trade_event", "future_windows": [300], "include_flow_features": False}
            flow_config = {"sample_mode": "trade_event", "future_windows": [300], "include_flow_features": True}
            base_samples = [{"meta": {"token_address": "0x1"}, "features": {"current_price": 1.0}}]
            flow_samples = [{"meta": {"token_address": "0x1"}, "features": {"sell_pressure_10s": 0.8}}]
            fake_module = _fake_train_hybrid(
                _load_samples=MagicMock(side_effect=[
                    base_samples,
                    flow_samples,
                ])
            )

            with patch.object(m.train_hybrid, "_load", return_value=fake_module):
                loaded_base = m.load_or_build_samples(base_config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(base_config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_flow = m.load_or_build_samples(flow_config, [lifecycle], set(), cache_dir=cache_dir)

        self.assertEqual(loaded_base, base_samples)
        self.assertEqual(loaded_cached, base_samples)
        self.assertEqual(loaded_flow, flow_samples)
        self.assertEqual(fake_module._load_samples.call_count, 2)

    def test_load_or_build_samples_reuses_cache_when_only_runtime_replay_knobs_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            lifecycle = Path(tmpdir) / "lifecycle_incremental_001.jsonl"
            lifecycle.write_text('{"token_address":"0x1"}\n', encoding="utf-8")
            base_config = {
                "sample_mode": "trade_event",
                "future_windows": [300],
                "max_sample_age_seconds": 300,
                "max_samples_per_token": 80,
                "buy_threshold": 0.972,
                "stop_loss": -0.3,
                "trailing_start_pct": 0.35,
                "trailing_stop_pct": 0.18,
                "min_policy_hold_seconds": 10,
                "stress_replay": True,
                "walk_forward_segments": 3,
            }
            runtime_changed_config = {
                **base_config,
                "buy_threshold": 0.973,
                "stop_loss": -0.25,
                "trailing_start_pct": 0.30,
                "trailing_stop_pct": 0.15,
                "min_policy_hold_seconds": 5,
                "stress_replay": False,
                "walk_forward_segments": 0,
            }
            first_samples = [{"meta": {"token_address": "0x1"}, "features": {"current_price": 1.0}}]
            fake_module = _fake_train_hybrid(_load_samples=MagicMock(return_value=first_samples))

            with patch.object(m.train_hybrid, "_load", return_value=fake_module):
                loaded_first = m.load_or_build_samples(base_config, [lifecycle], set(), cache_dir=cache_dir)
                loaded_cached = m.load_or_build_samples(runtime_changed_config, [lifecycle], set(), cache_dir=cache_dir)

        self.assertEqual(loaded_first, first_samples)
        self.assertEqual(loaded_cached, first_samples)
        self.assertEqual(fake_module._load_samples.call_count, 1)

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

    def test_live_score_uses_worst_harsh_stress_profit(self):
        report = {
            "evaluation": {
                "net_profit_bnb": 2.0,
                "stress_replay": [
                    {"name": "harsh_friction", "net_profit_bnb": 0.2},
                    {"name": "harsh_execution", "net_profit_bnb": -0.4},
                ],
            }
        }

        scored = m.live_score(report)

        self.assertEqual(scored["harsh_profit_bnb"], -0.4)
        self.assertGreater(scored["penalties"]["harsh_friction_loss"], 0.0)

    def test_live_score_penalizes_harsh_stress_percentage_collapse(self):
        stable = {
            "evaluation": {
                "net_profit_bnb": 1.0,
                "max_drawdown_pct": -15.0,
                "walk_forward_worst_net_return_pct": 20.0,
                "stress_replay": [
                    {
                        "name": "harsh_friction",
                        "net_profit_bnb": -0.01,
                        "net_return_pct": -5.0,
                        "max_drawdown_pct": -12.0,
                    }
                ],
            }
        }
        collapse = {
            "evaluation": {
                "net_profit_bnb": 1.1,
                "max_drawdown_pct": -15.0,
                "walk_forward_worst_net_return_pct": 20.0,
                "stress_replay": [
                    {
                        "name": "harsh_friction",
                        "net_profit_bnb": -0.01,
                        "net_return_pct": -99.0,
                        "max_drawdown_pct": -99.0,
                    }
                ],
            }
        }

        scored_stable = m.live_score(stable)
        scored_collapse = m.live_score(collapse)

        self.assertGreater(scored_stable["score"], scored_collapse["score"])
        self.assertGreater(scored_collapse["penalties"]["harsh_friction_return_loss"], 0.0)
        self.assertGreater(scored_collapse["penalties"]["harsh_friction_drawdown"], 0.0)

    def test_live_score_penalizes_top_trade_concentration(self):
        diversified = {
            "evaluation": {
                "net_profit_bnb": 2.0,
                "top_trade_profit_concentration": {"top_10_profit_share": 0.2},
            }
        }
        concentrated = {
            "evaluation": {
                "net_profit_bnb": 2.0,
                "top_trade_profit_concentration": {"top_10_profit_share": 0.8},
            }
        }

        scored_diversified = m.live_score(diversified)
        scored_concentrated = m.live_score(concentrated)

        self.assertGreater(scored_diversified["score"], scored_concentrated["score"])
        self.assertGreater(scored_concentrated["penalties"]["concentration"], 0.0)

    def test_run_parameter_search_selects_on_validation_and_reports_final(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            output_path = Path(tmpdir) / "search.json"
            calls = []

            def fake_replay(model_dir, *, split, overrides, output_path=None, **kwargs):
                calls.append({
                    "split": split,
                    "overrides": dict(overrides or {}),
                    "include_trade_log": kwargs.get("include_trade_log"),
                })
                threshold = float((overrides or {}).get("buy_threshold", 0.8))
                if split == "validation":
                    profit = 2.0 if threshold == 0.85 else 1.0
                    return {
                        "evaluation": {
                            "net_profit_bnb": profit,
                            "max_drawdown_pct": -10.0,
                            "walk_forward_worst_net_return_pct": 5.0,
                            "top_trade_profit_concentration": {"top_10_profit_share": 0.1},
                            "trade_log": [{"token": "0xraw", "net_profit_bnb": profit}],
                        }
                    }
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
        self.assertEqual([call["include_trade_log"] for call in calls], [True, True, False])
        self.assertNotIn("trade_log", result["selected_candidate"]["evaluation"])
        self.assertNotIn("trade_log", written["candidates"][0]["evaluation"])

    def test_run_parameter_search_applies_base_overrides_to_validation_and_final(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            calls = []

            def fake_replay(model_dir, *, split, overrides, output_path=None, **kwargs):
                calls.append({"split": split, "overrides": dict(overrides or {})})
                return {
                    "evaluation": {
                        "net_profit_bnb": 1.0,
                        "max_drawdown_pct": -10.0,
                        "walk_forward_worst_net_return_pct": 5.0,
                    }
                }

            with patch.object(m, "run_model_replay", side_effect=fake_replay):
                result = m.run_parameter_search(
                    model_dir,
                    candidates=[{"buy_threshold": 0.8, "entry_delay_seconds": 2}],
                    base_overrides={
                        "entry_delay_seconds": 1,
                        "entry_max_fill_wait_seconds": 4,
                        "exit_delay_seconds": 4,
                    },
                    write_report=False,
                )

        self.assertEqual(calls, [
            {
                "split": "validation",
                "overrides": {
                    "entry_delay_seconds": 2,
                    "entry_max_fill_wait_seconds": 4,
                    "exit_delay_seconds": 4,
                    "buy_threshold": 0.8,
                },
            },
            {
                "split": "final",
                "overrides": {
                    "entry_delay_seconds": 2,
                    "entry_max_fill_wait_seconds": 4,
                    "exit_delay_seconds": 4,
                    "buy_threshold": 0.8,
                },
            },
        ])
        self.assertEqual(result["base_overrides"], {
            "entry_delay_seconds": 1,
            "entry_max_fill_wait_seconds": 4,
            "exit_delay_seconds": 4,
        })

    def test_run_parameter_search_preserves_explicit_zero_max_open_positions_as_unlimited(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            calls = []

            def fake_replay(model_dir, *, split, overrides, max_open_positions=None, output_path=None, **kwargs):
                calls.append({
                    "split": split,
                    "max_open_positions": max_open_positions,
                    "overrides": dict(overrides or {}),
                })
                return {
                    "evaluation": {
                        "net_profit_bnb": 1.0,
                        "max_drawdown_pct": -10.0,
                        "walk_forward_worst_net_return_pct": 5.0,
                    }
                }

            with patch.object(m, "run_model_replay", side_effect=fake_replay):
                result = m.run_parameter_search(
                    model_dir,
                    candidates=[{"buy_threshold": 0.8, "max_open_positions": 0}],
                    write_report=False,
                )

        self.assertEqual([call["max_open_positions"] for call in calls], [0, 0])
        self.assertEqual(result["selected_candidate"]["overrides"]["max_open_positions"], 0)
        self.assertNotIn("max_open_positions", calls[0]["overrides"])
        self.assertNotIn("max_open_positions", calls[1]["overrides"])

    def test_run_parameter_search_preserves_explicit_variable_stake_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            calls = []

            def fake_replay(model_dir, *, split, overrides, output_path=None, **kwargs):
                calls.append({"split": split, "overrides": dict(overrides or {})})
                return {
                    "evaluation": {
                        "net_profit_bnb": 1.0,
                        "max_drawdown_pct": -10.0,
                        "walk_forward_worst_net_return_pct": 5.0,
                    }
                }

            with patch.object(m, "run_model_replay", side_effect=fake_replay):
                result = m.run_parameter_search(
                    model_dir,
                    candidates=[{"buy_threshold": 0.8}],
                    base_overrides={
                        "initial_equity_bnb": 0.0102,
                        "position_fraction": 0.1,
                        "max_position_fraction": 0.1,
                        "fixed_stake_bnb": None,
                    },
                    write_report=False,
                )

        expected = {
            "initial_equity_bnb": 0.0102,
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "fixed_stake_bnb": None,
            "buy_threshold": 0.8,
        }
        self.assertEqual(calls[0]["overrides"], expected)
        self.assertEqual(calls[1]["overrides"], expected)
        self.assertEqual(result["base_overrides"], {
            "initial_equity_bnb": 0.0102,
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "fixed_stake_bnb": None,
        })

    def test_run_parameter_search_rejects_position_fraction_above_ten_percent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")

            with patch.object(m, "run_model_replay") as mock_replay:
                with self.assertRaisesRegex(ValueError, "position_fraction.*0.10"):
                    m.run_parameter_search(
                        model_dir,
                        candidates=[{"buy_threshold": 0.8}],
                        base_overrides={"position_fraction": 0.11, "max_position_fraction": 0.11},
                        write_report=False,
                    )

        mock_replay.assert_not_called()

    def test_run_parameter_search_rejects_candidate_max_position_fraction_above_ten_percent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")

            with patch.object(m, "run_model_replay") as mock_replay:
                with self.assertRaisesRegex(ValueError, "max_position_fraction.*0.10"):
                    m.run_parameter_search(
                        model_dir,
                        candidates=[{"buy_threshold": 0.8, "max_position_fraction": 0.15}],
                        base_overrides={"position_fraction": 0.1, "max_position_fraction": 0.1},
                        write_report=False,
                    )

        mock_replay.assert_not_called()

    def test_run_parameter_search_can_use_fast_validation_selection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(json.dumps({"evaluation": {}, "artifacts": {"buy_model": {"threshold": 0.8}}}), encoding="utf-8")
            calls = []

            def fake_replay(model_dir, *, split, overrides, output_path=None, **kwargs):
                calls.append({
                    "split": split,
                    "overrides": dict(overrides or {}),
                    "include_trade_log": kwargs.get("include_trade_log"),
                })
                return {
                    "evaluation": {
                        "net_profit_bnb": 1.0,
                        "max_drawdown_pct": -10.0,
                        "walk_forward_worst_net_return_pct": 5.0,
                    }
                }

            with patch.object(m, "run_model_replay", side_effect=fake_replay):
                m.run_parameter_search(
                    model_dir,
                    candidates=[{"buy_threshold": 0.8}],
                    fast_selection=True,
                    write_report=False,
                )

        self.assertEqual(calls[0]["split"], "validation")
        self.assertFalse(calls[0]["include_trade_log"])
        self.assertEqual(calls[0]["overrides"]["stress_replay"], False)
        self.assertEqual(calls[0]["overrides"]["walk_forward_segments"], 0)
        self.assertEqual(calls[1]["split"], "final")
        self.assertFalse(calls[1]["include_trade_log"])
        self.assertNotIn("stress_replay", calls[1]["overrides"])
        self.assertNotIn("walk_forward_segments", calls[1]["overrides"])

    def test_run_parameter_search_rejects_empty_candidates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()

            with self.assertRaises(ValueError):
                m.run_parameter_search(model_dir, candidates=[], write_report=False)


    def test_write_trade_log_sidecar_skips_falsy_trade_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            sidecar_path = output_path.with_suffix(".trade_log.jsonl")

            without_trade_log = m._write_trade_log_sidecar(output_path, {"total_trades": 0})
            with_empty_trade_log = m._write_trade_log_sidecar(output_path, {"total_trades": 0, "trade_log": []})

            self.assertEqual(without_trade_log, {"total_trades": 0})
            self.assertEqual(with_empty_trade_log, {"total_trades": 0, "trade_log": []})
            self.assertNotIn("trade_log_path", without_trade_log)
            self.assertNotIn("trade_log_count", without_trade_log)
            self.assertNotIn("trade_log_path", with_empty_trade_log)
            self.assertNotIn("trade_log_count", with_empty_trade_log)
            self.assertFalse(sidecar_path.exists())

    def test_run_model_replay_rejects_validation_without_explicit_validation_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": False}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain"},
                raw_final_overlap_token_count=0,
            )

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[]) as mock_samples, \
                 patch.object(m, "load_model_artifacts") as mock_artifacts:
                with self.assertRaisesRegex(ValueError, "validation.*explicit validation files"):
                    m.run_model_replay(model_dir, split="validation", write_report=False)

        mock_samples.assert_not_called()
        mock_artifacts.assert_not_called()

    def test_run_model_replay_rejects_final_without_eval_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=0,
            )

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[]) as mock_samples, \
                 patch.object(m, "load_model_artifacts") as mock_artifacts:
                with self.assertRaisesRegex(ValueError, "final.*eval files"):
                    m.run_model_replay(model_dir, split="final", write_report=False)

        mock_samples.assert_not_called()
        mock_artifacts.assert_not_called()

    def test_run_model_replay_can_use_train_split_for_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=2,
            )
            fake_artifacts = types.SimpleNamespace(buy_artifact={}, ppo_artifact={}, bc_artifact={})

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[{"token": "0xA"}]) as mock_samples, \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m.train_hybrid, "run_ab_evaluation", return_value={"total_trades": 0}):
                report = m.run_model_replay(model_dir, split="train", write_report=False)

        mock_samples.assert_called_once()
        self.assertEqual(mock_samples.call_args.args[1], [Path("train.jsonl")])
        self.assertEqual(mock_samples.call_args.args[2], set())
        self.assertEqual(report["split"], "train")
        self.assertEqual(report["selection_role"], "diagnostic_train")
        self.assertEqual(report["replay_config"]["evaluation_split"], "train")
        self.assertEqual(report["replay_config"]["selected_lifecycle_file_count"], 1)
        self.assertEqual(report["replay_config"]["excluded_token_count"], 0)
        self.assertEqual(report["replay_config"]["raw_overlap_token_count"], 0)

    def test_run_model_replay_enables_flow_features_when_model_schema_requires_them(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            (model_dir / "feature_schema.json").write_text(
                json.dumps({"feature_names": ["current_price", "sell_pressure_10s"]}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=0,
            )
            fake_artifacts = types.SimpleNamespace(buy_artifact={}, ppo_artifact={}, bc_artifact={})

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[{"token": "0xA"}]) as mock_samples, \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m.train_hybrid, "run_ab_evaluation", return_value={"total_trades": 0}):
                m.run_model_replay(model_dir, split="final", write_report=False)

        self.assertTrue(mock_samples.call_args.args[0]["include_flow_features"])

    def test_live_replay_config_for_model_enables_flow_features_from_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"selected_runtime_params": {"position_fraction": 0.1}}),
                encoding="utf-8",
            )
            (model_dir / "feature_schema.json").write_text(
                json.dumps({"feature_names": ["current_price", "sell_pressure_10s"]}),
                encoding="utf-8",
            )

            manifest, config = m.live_replay_config_for_model(model_dir)

        self.assertEqual(manifest["selected_runtime_params"]["position_fraction"], 0.1)
        self.assertTrue(config["include_flow_features"])

    def test_run_model_replay_rejects_train_without_explicit_train_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens=set(),
                excluded_final_tokens=set(),
                raw_final_overlap_token_count=0,
            )

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[]) as mock_samples, \
                 patch.object(m, "load_model_artifacts") as mock_artifacts:
                with self.assertRaisesRegex(ValueError, "train.*explicit train files"):
                    m.run_model_replay(model_dir, split="train", write_report=False)

        mock_samples.assert_not_called()
        mock_artifacts.assert_not_called()

    def test_run_model_replay_train_diagnostic_lifecycle_paths_use_subset_without_exclusions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train_a.jsonl"), Path("train_b.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=2,
            )
            fake_artifacts = types.SimpleNamespace(buy_artifact={}, ppo_artifact={}, bc_artifact={})

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[{"token": "0xA"}]) as mock_samples, \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m.train_hybrid, "run_ab_evaluation", return_value={"total_trades": 0}):
                report = m.run_model_replay(
                    model_dir,
                    split="train",
                    diagnostic_lifecycle_paths=[Path("train_b.jsonl")],
                    write_report=False,
                )

        mock_samples.assert_called_once()
        self.assertEqual(mock_samples.call_args.args[1], [Path("train_b.jsonl")])
        self.assertEqual(mock_samples.call_args.args[2], set())
        self.assertEqual(report["lifecycle_paths"], ["train_b.jsonl"])
        self.assertTrue(report["replay_config"]["diagnostic_lifecycle_paths_override"])
        self.assertEqual(report["replay_config"]["selected_lifecycle_file_count"], 1)
        self.assertEqual(report["replay_config"]["excluded_token_count"], 0)

    def test_run_model_replay_rejects_diagnostic_lifecycle_paths_outside_train_split(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "diagnostic_lifecycle_paths.*train"):
                m.run_model_replay(
                    model_dir,
                    split="validation",
                    diagnostic_lifecycle_paths=[Path("validation.jsonl")],
                    write_report=False,
                )

    def test_run_model_replay_rejects_train_diagnostic_paths_outside_train_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({"three_way_split": {"enabled": True}, "artifacts": {"buy_model": {"threshold": 0.8}}}),
                encoding="utf-8",
            )
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens=set(),
                excluded_final_tokens=set(),
                raw_final_overlap_token_count=0,
            )

            with patch.object(m, "resolve_replay_split", return_value=replay_split):
                with self.assertRaisesRegex(ValueError, "diagnostic_lifecycle_paths.*train files"):
                    m.run_model_replay(
                        model_dir,
                        split="train",
                        diagnostic_lifecycle_paths=[Path("final.jsonl")],
                        write_report=False,
                    )

    def test_run_model_replay_rejects_protected_model_artifact_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            manifest_path = model_dir / "hybrid_manifest.json"
            original_manifest = {
                "three_way_split": {"enabled": True},
                "artifacts": {"buy_model": {"threshold": 0.8}},
                "evaluation": {"fixed_stake_bnb": 0.1},
            }
            manifest_path.write_text(json.dumps(original_manifest), encoding="utf-8")
            replay_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens={"0xtrain"},
                excluded_final_tokens={"0xtrain", "0xval"},
                raw_final_overlap_token_count=0,
            )

            with patch.object(m, "resolve_replay_split", return_value=replay_split), \
                 patch.object(m, "load_or_build_samples", return_value=[]) as mock_samples, \
                 patch.object(m, "load_model_artifacts") as mock_artifacts:
                with self.assertRaisesRegex(ValueError, "protected model artifact"):
                    m.run_model_replay(model_dir, output_path=manifest_path, split="final")

            manifest_after = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest_after, original_manifest)
        mock_samples.assert_not_called()
        mock_artifacts.assert_not_called()

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
            fake_train_hybrid = MagicMock()
            fake_train_hybrid.run_ab_evaluation.return_value = fake_eval
            fake_train_hybrid._summarize_trade_log_by_exit_reason.return_value = {"SELL100": {"count": 1}}
            fake_train_hybrid._trade_profit_concentration.return_value = {"top_10_profit_share": 1.0}

            with patch.object(m, "resolve_replay_split", return_value=fake_split), \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m, "load_or_build_samples", return_value=[{"features": {}, "meta": {}}]) as mock_samples, \
                 patch.object(m.train_hybrid, "_load", return_value=fake_train_hybrid), \
                 patch.object(m, "git_metadata", return_value={"commit": "abc", "branch": "main", "dirty": False}):
                report = m.run_model_replay(model_dir, output_path=output_path, cache_dir=Path(tmpdir) / "cache", split="final", include_trade_log=True)

            manifest_after = json.loads((model_dir / "hybrid_manifest.json").read_text(encoding="utf-8"))
            written = json.loads(output_path.read_text(encoding="utf-8"))
            trade_log_path = Path(written["evaluation"]["trade_log_path"])
            trade_log_exists = trade_log_path.exists()
            trade_log_rows = [
                json.loads(line)
                for line in trade_log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(manifest_after, original_manifest)
        self.assertEqual(report["evaluation"]["total_trades"], 1)
        self.assertEqual(written["evaluation"]["trade_log_count"], 1)
        self.assertEqual(written["replay_config"]["evaluation_split"], "final_test")
        self.assertEqual(trade_log_path, output_path.with_suffix(".trade_log.jsonl"))
        self.assertTrue(trade_log_exists)
        self.assertEqual(len(trade_log_rows), 1)
        self.assertEqual(trade_log_rows[0]["token"], "0x1")
        mock_samples.assert_called_once()

    def test_run_model_replay_uses_preloaded_eval_samples_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({
                    "artifacts": {"buy_model": {"threshold": 0.8}},
                    "three_way_split": {"enabled": True},
                    "evaluation": {"fixed_stake_bnb": 0.1},
                }),
                encoding="utf-8",
            )
            fake_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens=set(),
                excluded_final_tokens=set(),
                raw_final_overlap_token_count=0,
            )
            fake_artifacts = m.LoadedReplayArtifacts(
                buy_artifact={"model": MagicMock(), "threshold": 0.8},
                ppo_artifact={"model": MagicMock(), "total_timesteps": 10},
                bc_artifact={"bc_samples": 5},
            )
            preloaded_samples = [
                {"features": {}, "meta": {"token_address": "0xpreloaded", "sample_time": 1}},
                {"features": {}, "meta": {"token_address": "0xpreloaded", "sample_time": 2}},
            ]
            seen_eval_sample_ids = []

            def fake_evaluation(config, *_args):
                seen_eval_sample_ids.append(id(config["eval_samples"]))
                return {"total_trades": 0, "net_profit_bnb": 0.0, "max_drawdown_pct": 0.0}

            fake_train_hybrid = MagicMock()
            fake_train_hybrid.run_ab_evaluation.side_effect = fake_evaluation

            with patch.object(m, "resolve_replay_split", return_value=fake_split), \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m, "load_or_build_samples", return_value=[{"features": {}, "meta": {}}]) as mock_samples, \
                 patch.object(m.train_hybrid, "_load", return_value=fake_train_hybrid), \
                 patch.object(m, "git_metadata", return_value={"commit": "abc", "branch": "main", "dirty": False}):
                report = m.run_model_replay(
                    model_dir,
                    split="final",
                    write_report=False,
                    overrides={"eval_samples": preloaded_samples},
                )

        mock_samples.assert_not_called()
        self.assertEqual(report["sample_count"], 2)
        self.assertNotIn("eval_samples", report["replay_config"])
        self.assertEqual(seen_eval_sample_ids, [id(preloaded_samples)])

    def test_run_model_replay_filters_excluded_tokens_from_preloaded_eval_samples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({
                    "artifacts": {"buy_model": {"threshold": 0.8}},
                    "three_way_split": {"enabled": True},
                    "evaluation": {"fixed_stake_bnb": 0.1},
                }),
                encoding="utf-8",
            )
            fake_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens=set(),
                excluded_final_tokens={"0xtrain"},
                raw_final_overlap_token_count=0,
            )
            fake_artifacts = m.LoadedReplayArtifacts(
                buy_artifact={"model": MagicMock(), "threshold": 0.8},
                ppo_artifact={"model": MagicMock(), "total_timesteps": 10},
                bc_artifact={"bc_samples": 5},
            )
            preloaded_samples = [
                {"features": {}, "meta": {"token_address": "0xtrain", "sample_time": 1}},
                {"features": {}, "meta": {"token_address": "0xfinal", "sample_time": 2}},
            ]
            seen_eval_samples = []

            def fake_evaluation(config, *_args):
                seen_eval_samples.extend(config["eval_samples"])
                return {"total_trades": 0, "net_profit_bnb": 0.0, "max_drawdown_pct": 0.0}

            fake_train_hybrid = MagicMock()
            fake_train_hybrid.run_ab_evaluation.side_effect = fake_evaluation

            with patch.object(m, "resolve_replay_split", return_value=fake_split), \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m, "load_or_build_samples", return_value=[{"features": {}, "meta": {}}]) as mock_samples, \
                 patch.object(m.train_hybrid, "_load", return_value=fake_train_hybrid), \
                 patch.object(m, "git_metadata", return_value={"commit": "abc", "branch": "main", "dirty": False}):
                report = m.run_model_replay(
                    model_dir,
                    split="final",
                    write_report=False,
                    overrides={"eval_samples": preloaded_samples},
                )

        mock_samples.assert_not_called()
        self.assertEqual(report["sample_count"], 1)
        self.assertEqual(report["replay_config"]["preloaded_eval_samples"], True)
        self.assertEqual(report["replay_config"]["preloaded_eval_sample_count"], 2)
        self.assertEqual([sample["meta"]["token_address"] for sample in seen_eval_samples], ["0xfinal"])

    def test_run_model_replay_compacts_path_state_score_maps_in_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            output_path = Path(tmpdir) / "report.json"
            model_dir.mkdir()
            (model_dir / "hybrid_manifest.json").write_text(
                json.dumps({
                    "artifacts": {"buy_model": {"threshold": 0.8}},
                    "three_way_split": {"enabled": True},
                    "evaluation": {"fixed_stake_bnb": 0.1},
                }),
                encoding="utf-8",
            )
            fake_split = m.ReplaySplit(
                train_files=[Path("train.jsonl")],
                validation_files=[Path("validation.jsonl")],
                eval_files=[Path("final.jsonl")],
                excluded_validation_tokens=set(),
                excluded_final_tokens=set(),
                raw_final_overlap_token_count=0,
            )
            fake_artifacts = m.LoadedReplayArtifacts(
                buy_artifact={"model": MagicMock(), "threshold": 0.8},
                ppo_artifact={"model": MagicMock(), "total_timesteps": 10},
                bc_artifact={"bc_samples": 5},
            )
            fake_train_hybrid = MagicMock()
            fake_train_hybrid.run_ab_evaluation.return_value = {
                "total_trades": 1,
                "net_profit_bnb": 0.1,
                "max_drawdown_pct": -1.0,
                "win_rate": 1.0,
                "walk_forward_worst_net_return_pct": 1.0,
                "walk_forward_worst_max_drawdown_pct": -1.0,
                "stress_replay": [{
                    "name": "harsh_friction",
                    "net_return_pct": 1.0,
                    "net_profit_bnb": 0.01,
                    "max_drawdown_pct": -1.0,
                }],
            }

            with patch.object(m, "resolve_replay_split", return_value=fake_split), \
                 patch.object(m, "load_model_artifacts", return_value=fake_artifacts), \
                 patch.object(m, "load_or_build_samples", return_value=[{"features": {}, "meta": {}}]) as mock_samples, \
                 patch.object(m.train_hybrid, "_load", return_value=fake_train_hybrid), \
                 patch.object(m, "git_metadata", return_value={"commit": "abc", "branch": "main", "dirty": False}):
                report = m.run_model_replay(
                    model_dir,
                    output_path=output_path,
                    cache_dir=Path(tmpdir) / "cache",
                    split="final",
                    overrides={"path_state_scores_by_episode": [{0: 0.75}], "buy_path_state_meta_gate_min_score": 0.5},
                )

            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["replay_config"]["path_state_scores_by_episode_summary"], {
            "episode_count": 1,
            "non_empty_episode_count": 1,
            "scored_sample_count": 1,
            "max_episode_score_count": 1,
        })
        self.assertNotIn("path_state_scores_by_episode", report["replay_config"])
        self.assertEqual(written["replay_config"]["path_state_scores_by_episode_summary"]["episode_count"], 1)
        self.assertNotIn("path_state_scores_by_episode", written["replay_config"])
        mock_samples.assert_called_once()
