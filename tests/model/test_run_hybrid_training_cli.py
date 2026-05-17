import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import types


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_hybrid_training.py"
    spec = importlib.util.spec_from_file_location("run_hybrid_training", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestRunHybridTrainingCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.output_dir, "data/models")
        self.assertEqual(args.total_timesteps, 20000)
        self.assertEqual(args.initial_equity_bnb, 1.0)
        self.assertIsNone(args.fixed_stake_bnb)
        self.assertFalse(args.no_fixed_stake_bnb)
        self.assertEqual(args.label_live_downside_penalty_weight, 0.0)
        self.assertEqual(args.validation_split_ratio, 0.0)
        self.assertEqual(args.min_validation_files, 1)
        self.assertEqual(args.min_entry_unique_buyers, 3)
        self.assertEqual(args.min_entry_buy_count, 5)
        self.assertIsNone(args.entry_max_fill_wait_seconds)
        self.assertIsNone(args.exit_max_fill_wait_seconds)
        self.assertIsNone(args.entry_price_protection_pct)
        self.assertIsNone(getattr(args, "execution_calibration_file", None))
        self.assertEqual(args.risk_tune_probability_threshold_count, 0)
        self.assertIsNone(args.risk_tune_min_entry_rate)
        self.assertFalse(args.train_entry_value_model)
        self.assertEqual(args.entry_value_target_label_column, "live_risk_adjusted_return_pct")
        self.assertEqual(args.entry_ranking_mode, "chronological")
        self.assertIsNone(args.min_entry_score)
        self.assertEqual(args.entry_fixed_cost_bnb, 0.0)
        self.assertEqual(args.exit_fixed_cost_bnb, 0.0)
        self.assertIsNone(args.label_fixed_stake_bnb)
        self.assertIsNone(args.label_entry_fixed_cost_bnb)
        self.assertIsNone(args.label_exit_fixed_cost_bnb)
        self.assertIsNone(args.label_entry_price_protection_pct)
        self.assertEqual(args.bc_label_mode, "sell_pressure")
        self.assertEqual(args.bc_profit_path_min_hold_seconds, 0.0)
        self.assertEqual(args.bc_profit_path_trailing_start_pct, 0.25)
        self.assertEqual(args.bc_profit_path_trailing_stop_pct, 0.20)
        self.assertEqual(args.bc_profit_path_sell_margin_pct, 0.05)
        self.assertEqual(args.bc_profit_path_sell100_pct, 0.80)
        self.assertEqual(args.bc_profit_path_sell50_pct, 0.50)
        self.assertEqual(args.bc_profit_path_sell25_pct, 0.20)
        self.assertIsNone(args.label_target_return_pct)
        self.assertFalse(args.fit_artifacts_on_all_data)

    def test_parse_args_accepts_separate_label_target_return_pct(self):
        cli = _load_cli()
        args = cli.parse_args([
            "--target-label-column",
            "live_target_hit_before_stop",
            "--target-threshold-value",
            "1",
            "--label-target-return-pct",
            "25",
        ])

        self.assertEqual(args.target_label_column, "live_target_hit_before_stop")
        self.assertEqual(args.target_threshold_value, 1.0)
        self.assertEqual(args.label_target_return_pct, 25.0)

    def test_parse_args_accepts_profit_path_bc_options(self):
        cli = _load_cli()
        args = cli.parse_args([
            "--bc-label-mode", "profit_path",
            "--bc-profit-path-min-hold-seconds", "90",
            "--bc-profit-path-trailing-start-pct", "0.35",
            "--bc-profit-path-trailing-stop-pct", "0.12",
            "--bc-profit-path-sell-margin-pct", "0.08",
            "--bc-profit-path-sell100-pct", "1.2",
            "--bc-profit-path-sell50-pct", "0.65",
            "--bc-profit-path-sell25-pct", "0.3",
        ])

        self.assertEqual(args.bc_label_mode, "profit_path")
        self.assertEqual(args.bc_profit_path_min_hold_seconds, 90.0)
        self.assertEqual(args.bc_profit_path_trailing_start_pct, 0.35)
        self.assertEqual(args.bc_profit_path_trailing_stop_pct, 0.12)
        self.assertEqual(args.bc_profit_path_sell_margin_pct, 0.08)
        self.assertEqual(args.bc_profit_path_sell100_pct, 1.2)
        self.assertEqual(args.bc_profit_path_sell50_pct, 0.65)
        self.assertEqual(args.bc_profit_path_sell25_pct, 0.3)

    def test_parse_args_accepts_all_data_artifact_fit(self):
        cli = _load_cli()
        args = cli.parse_args(["--fit-artifacts-on-all-data"])

        self.assertTrue(args.fit_artifacts_on_all_data)

    def test_parse_args_does_not_import_pipeline_module(self):
        cli = _load_cli()
        self.assertNotIn("src.pipeline.train_hybrid", sys.modules)
        args = cli.parse_args(["--train-split-ratio", "0.7", "--min-eval-files", "2"])
        self.assertEqual(args.train_split_ratio, 0.7)
        self.assertEqual(args.min_eval_files, 2)
        self.assertNotIn("src.pipeline.train_hybrid", sys.modules)

        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_run = lambda config: {"artifacts": {}, "evaluation": {}}
        fake_pipeline.run_hybrid_training = fake_run

        with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
            with patch.object(cli, "parse_args", return_value=types.SimpleNamespace(
                output_dir="tmp/models",
                total_timesteps=512,
                lifecycle_dir="data/training",
                sample_mode="trade_event",
                max_sample_age_seconds=300,
                future_windows="300",
                max_hold_seconds=300,
                min_policy_hold_seconds=0,
                max_samples_per_token=120,
                target_label_column="executable_return_pct",
                target_threshold_value=80.0,
                label_target_return_pct=None,
                train_entry_value_model=False,
                entry_value_target_label_column="live_risk_adjusted_return_pct",
                entry_ranking_mode="chronological",
                min_entry_score=None,
                label_live_downside_penalty_weight=0.0,
                label_delay_robust_entry_delays=None,
                label_delay_robust_min_weight=1.0,
                bc_label_mode="profit_path",
                bc_profit_path_min_hold_seconds=90.0,
                bc_profit_path_trailing_start_pct=0.35,
                bc_profit_path_trailing_stop_pct=0.12,
                bc_profit_path_sell_margin_pct=0.08,
                bc_profit_path_sell100_pct=1.20,
                bc_profit_path_sell50_pct=0.65,
                bc_profit_path_sell25_pct=0.30,
                fit_artifacts_on_all_data=True,
                buy_min_precision=0.5,
                buy_min_threshold=0.5,
                buy_calibration_ratio=0.2,
                min_calibration_samples=20,
                buy_min_calibration_predictions=20,
                buy_sample_weighting="none",
                train_split_ratio=0.8,
                validation_split_ratio=0.0,
                min_validation_files=1,
                min_eval_files=1,
                min_entry_unique_buyers=3,
                min_entry_buy_count=5,
                min_entry_volume_30s=None,
                min_entry_price_volatility=None,
                stop_loss=-0.5,
                position_fraction=0.1,
                max_position_fraction=0.1,
                initial_equity_bnb=1.0,
                fixed_stake_bnb=None,
                no_fixed_stake_bnb=False,
                include_trade_log=False,
                allow_partial_exits=False,
                fee_bps=100.0,
                slippage_bps=200.0,
                one_entry_per_token=True,
                max_trades_per_token=1,
                trailing_start_pct=0.3,
                trailing_stop_pct=0.25,
                rug_sell_pressure=0.95,
                risk_tune_buy_threshold=True,
                risk_tune_min_trades=20,
                risk_tune_max_trades=200,
                risk_tune_min_threshold=0.5,
                risk_tune_target_entry_rate=0.15,
                risk_tune_entry_rate_penalty=0.25,
                risk_tune_min_entry_rate=None,
                risk_tune_max_entry_rate=None,
                risk_tune_candidate_entry_rates="0.05,0.10,0.15,0.25,0.40",
                risk_tune_thresholds=None,
                risk_tune_max_drawdown_pct=-40.0,
                risk_tune_min_win_rate=0.5,
                risk_tune_drawdown_penalty=1.0,
                risk_tune_turnover_penalty=0.001,
                risk_tune_probability_threshold_count=0,
                sell_drawdown_penalty_weight=0.0,
                sell_hold_penalty_per_step=0.0,
                sell_turnover_penalty=0.001,
                walk_forward_segments=3,
                stress_replay=False,
                live_replay_profile=False,
                entry_delay_seconds=None,
                exit_delay_seconds=None,
                max_open_positions=None,
                entry_max_fill_wait_seconds=None,
                exit_max_fill_wait_seconds=None,
                entry_price_protection_pct=None,
                entry_execution_failure_rate=0.0,
                exit_execution_failure_rate=0.0,
                max_pending_entries=None,
                entry_fixed_cost_bnb=0.0,
                exit_fixed_cost_bnb=0.0,
                label_fixed_stake_bnb=None,
                label_entry_fixed_cost_bnb=None,
                label_exit_fixed_cost_bnb=None,
                label_entry_price_protection_pct=None,
                catboost_iterations=500,
                catboost_learning_rate=0.05,
                catboost_depth=5,
                catboost_l2_leaf_reg=10.0,
                catboost_random_strength=1.0,
                catboost_bagging_temperature=1.0,
                catboost_rsm=0.8,
                catboost_od_wait=50,
            )):
                with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                    cli.main([])

        mock_run.assert_called_once_with({
            "output_dir": "tmp/models",
            "total_timesteps": 512,
            "lifecycle_dir": "data/training",
            "sample_mode": "trade_event",
            "max_sample_age_seconds": 300,
            "max_entry_age_seconds": 300,
            "future_windows": [300],
            "max_hold_seconds": 300,
            "min_policy_hold_seconds": 0,
            "max_samples_per_token": 120,
            "sample_cache_dir": ".cache/hybrid_samples",
            "target_label_column": "executable_return_pct",
            "target_threshold_value": 80.0,
            "label_target_return_pct": None,
            "train_entry_value_model": False,
            "entry_value_target_label_column": "live_risk_adjusted_return_pct",
            "entry_ranking_mode": "chronological",
            "min_entry_score": None,
            "label_live_downside_penalty_weight": 0.0,
            "label_delay_robust_entry_delay_seconds": None,
            "label_delay_robust_min_weight": 1.0,
            "bc_label_mode": "profit_path",
            "bc_profit_path_min_hold_seconds": 90.0,
            "bc_profit_path_trailing_start_pct": 0.35,
            "bc_profit_path_trailing_stop_pct": 0.12,
            "bc_profit_path_sell_margin_pct": 0.08,
            "bc_profit_path_sell100_pct": 1.20,
            "bc_profit_path_sell50_pct": 0.65,
            "bc_profit_path_sell25_pct": 0.30,
            "fit_artifacts_on_all_data": True,
            "buy_min_precision": 0.5,
            "buy_min_threshold": 0.5,
            "buy_calibration_ratio": 0.2,
            "min_calibration_samples": 20,
            "buy_min_calibration_predictions": 20,
            "buy_sample_weighting": "none",
            "train_split_ratio": 0.8,
            "validation_split_ratio": 0.0,
            "min_validation_files": 1,
            "min_eval_files": 1,
            "min_entry_unique_buyers": 3,
            "min_entry_buy_count": 5,
            "min_entry_volume_30s": None,
            "min_entry_price_volatility": None,
            "stop_loss": -0.5,
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "initial_equity_bnb": 1.0,
            "fixed_stake_bnb": None,
            "include_trade_log": False,
            "allow_partial_exits": False,
            "fee_bps": 100.0,
            "slippage_bps": 200.0,
            "one_entry_per_token": True,
            "max_trades_per_token": 1,
            "trailing_start_pct": 0.3,
            "trailing_stop_pct": 0.25,
            "rug_sell_pressure": 0.95,
            "risk_tune_buy_threshold": True,
            "risk_tune_min_trades": 20,
            "risk_tune_max_trades": 200,
            "risk_tune_min_threshold": 0.5,
            "risk_tune_target_entry_rate": 0.15,
            "risk_tune_entry_rate_penalty": 0.25,
            "risk_tune_min_entry_rate": None,
            "risk_tune_max_entry_rate": None,
            "risk_tune_candidate_entry_rates": [0.05, 0.10, 0.15, 0.25, 0.40],
            "risk_tune_thresholds": [],
            "risk_tune_max_drawdown_pct": -40.0,
            "risk_tune_min_win_rate": 0.5,
            "risk_tune_drawdown_penalty": 1.0,
            "risk_tune_turnover_penalty": 0.001,
            "risk_tune_probability_threshold_count": 0,
            "sell_drawdown_penalty_weight": 0.0,
            "sell_hold_penalty_per_step": 0.0,
            "sell_turnover_penalty": 0.001,
            "walk_forward_segments": 3,
            "stress_replay": False,
            "live_replay_profile": False,
            "entry_delay_seconds": 0,
            "exit_delay_seconds": 0,
            "max_open_positions": None,
            "entry_max_fill_wait_seconds": None,
            "exit_max_fill_wait_seconds": None,
            "entry_price_protection_pct": None,
            "entry_fixed_cost_bnb": 0.0,
            "exit_fixed_cost_bnb": 0.0,
            "label_fixed_stake_bnb": None,
            "label_entry_fixed_cost_bnb": None,
            "label_exit_fixed_cost_bnb": None,
            "label_entry_price_protection_pct": None,
            "entry_execution_failure_rate": 0.0,
            "exit_execution_failure_rate": 0.0,
            "max_pending_entries": None,
            "execution_calibration": None,
            "catboost_params": {
                "iterations": 500,
                "learning_rate": 0.05,
                "depth": 5,
                "l2_leaf_reg": 10.0,
                "random_strength": 1.0,
                "bagging_temperature": 1.0,
                "rsm": 0.8,
                "od_wait": 50,
            },
        })

    def test_script_runs_as_subprocess(self):
        project_root = Path(__file__).resolve().parents[2]
        script_path = project_root / "scripts" / "run_hybrid_training.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--lifecycle-dir", result.stdout)
        self.assertIn("--target-threshold-value", result.stdout)
        self.assertIn("--label-target-return-pct", result.stdout)
        self.assertIn("--train-entry-value-model", result.stdout)
        self.assertIn("--entry-value-target-label-column", result.stdout)
        self.assertIn("--entry-ranking-mode", result.stdout)
        self.assertIn("--min-entry-score", result.stdout)
        self.assertIn("--label-live-downside-penalty-weight", result.stdout)
        self.assertIn("--label-delay-robust-entry-delays", result.stdout)
        self.assertIn("--train-split-ratio", result.stdout)
        self.assertIn("--validation-split-ratio", result.stdout)
        self.assertIn("--min-validation-files", result.stdout)
        self.assertIn("--min-eval-files", result.stdout)
        self.assertIn("--min-entry-unique-buyers", result.stdout)
        self.assertIn("--min-entry-buy-count", result.stdout)
        self.assertIn("--buy-calibration-ratio", result.stdout)
        self.assertIn("--buy-min-threshold", result.stdout)
        self.assertIn("--buy-sample-weighting", result.stdout)
        self.assertIn("--catboost-depth", result.stdout)
        self.assertIn("--position-fraction", result.stdout)
        self.assertIn("--max-position-fraction", result.stdout)
        self.assertIn("--no-fixed-stake-bnb", result.stdout)
        self.assertIn("--future-windows", result.stdout)
        self.assertIn("--max-hold-seconds", result.stdout)
        self.assertIn("--min-policy-hold-seconds", result.stdout)
        self.assertIn("--max-samples-per-token", result.stdout)
        self.assertIn("--fee-bps", result.stdout)
        self.assertIn("--allow-partial-exits", result.stdout)
        self.assertIn("--allow-token-reentry", result.stdout)
        self.assertIn("--risk-tune-max-trades", result.stdout)
        self.assertIn("--risk-tune-target-entry-rate", result.stdout)
        self.assertIn("--risk-tune-min-entry-rate", result.stdout)
        self.assertIn("--risk-tune-candidate-entry-rates", result.stdout)
        self.assertIn("--risk-tune-thresholds", result.stdout)
        self.assertIn("--risk-tune-probability-threshold-count", result.stdout)
        self.assertIn("--trailing-stop-pct", result.stdout)
        self.assertIn("--rug-sell-pressure", result.stdout)
        self.assertIn("--no-risk-tune-buy-threshold", result.stdout)
        self.assertIn("--walk-forward-segments", result.stdout)
        self.assertIn("--stress-replay", result.stdout)
        self.assertIn("--live-replay-profile", result.stdout)
        self.assertIn("--entry-delay-seconds", result.stdout)
        self.assertIn("--exit-delay-seconds", result.stdout)
        self.assertIn("--max-open-positions", result.stdout)
        self.assertIn("--entry-max-fill-wait-seconds", result.stdout)
        self.assertIn("--exit-max-fill-wait-seconds", result.stdout)
        self.assertIn("--entry-price-protection-pct", result.stdout)
        self.assertIn("--entry-fixed-cost-bnb", result.stdout)
        self.assertIn("--exit-fixed-cost-bnb", result.stdout)
        self.assertIn("--label-fixed-stake-bnb", result.stdout)
        self.assertIn("--label-entry-fixed-cost-bnb", result.stdout)
        self.assertIn("--label-exit-fixed-cost-bnb", result.stdout)
        self.assertIn("--label-entry-price-protection-pct", result.stdout)
        self.assertIn("--entry-execution-failure-rate", result.stdout)
        self.assertIn("--exit-execution-failure-rate", result.stdout)
        self.assertIn("--max-pending-entries", result.stdout)
        self.assertIn("--fit-artifacts-on-all-data", result.stdout)
        self.assertIn("--sample-cache-dir", result.stdout)
        self.assertIn("--no-sample-cache", result.stdout)

    def test_parse_args_includes_dataset_and_target_controls(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.sample_mode, "trade_event")
        self.assertEqual(args.max_sample_age_seconds, 300)
        self.assertEqual(args.future_windows, "300")
        self.assertEqual(args.max_hold_seconds, 300)
        self.assertEqual(args.min_policy_hold_seconds, 0)
        self.assertEqual(args.max_samples_per_token, 120)
        self.assertEqual(args.sample_cache_dir, ".cache/hybrid_samples")
        self.assertFalse(args.no_sample_cache)
        self.assertEqual(args.target_label_column, "executable_return_pct")
        self.assertEqual(args.target_threshold_value, 80.0)
        self.assertIsNone(args.label_target_return_pct)
        self.assertFalse(args.train_entry_value_model)
        self.assertEqual(args.entry_value_target_label_column, "live_risk_adjusted_return_pct")
        self.assertEqual(args.entry_ranking_mode, "chronological")
        self.assertIsNone(args.min_entry_score)
        self.assertEqual(args.label_live_downside_penalty_weight, 0.0)
        self.assertEqual(args.train_split_ratio, 0.8)
        self.assertEqual(args.validation_split_ratio, 0.0)
        self.assertEqual(args.min_validation_files, 1)
        self.assertEqual(args.min_eval_files, 1)
        self.assertEqual(args.min_entry_unique_buyers, 3)
        self.assertEqual(args.min_entry_buy_count, 5)
        self.assertEqual(args.buy_calibration_ratio, 0.2)
        self.assertEqual(args.min_calibration_samples, 20)
        self.assertEqual(args.buy_min_threshold, 0.5)
        self.assertEqual(args.buy_min_calibration_predictions, 20)
        self.assertEqual(args.buy_min_precision, 0.5)
        self.assertEqual(args.buy_sample_weighting, "none")
        self.assertEqual(args.stop_loss, -0.5)
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertFalse(args.include_trade_log)
        self.assertFalse(args.allow_partial_exits)
        self.assertEqual(args.fee_bps, 100.0)
        self.assertEqual(args.slippage_bps, 200.0)
        self.assertTrue(args.one_entry_per_token)
        self.assertEqual(args.max_trades_per_token, 1)
        self.assertEqual(args.trailing_start_pct, 0.3)
        self.assertEqual(args.trailing_stop_pct, 0.25)
        self.assertEqual(args.rug_sell_pressure, 0.95)
        self.assertTrue(args.risk_tune_buy_threshold)
        self.assertEqual(args.risk_tune_min_trades, 20)
        self.assertEqual(args.risk_tune_max_trades, 200)
        self.assertEqual(args.risk_tune_min_threshold, 0.5)
        self.assertEqual(args.risk_tune_target_entry_rate, 0.15)
        self.assertEqual(args.risk_tune_entry_rate_penalty, 0.25)
        self.assertIsNone(args.risk_tune_min_entry_rate)
        self.assertIsNone(args.risk_tune_max_entry_rate)
        self.assertEqual(args.risk_tune_candidate_entry_rates, "0.05,0.10,0.15,0.25,0.40")
        self.assertIsNone(args.risk_tune_thresholds)
        self.assertEqual(args.risk_tune_max_drawdown_pct, -40.0)
        self.assertEqual(args.risk_tune_min_win_rate, 0.5)
        self.assertEqual(args.risk_tune_drawdown_penalty, 1.0)
        self.assertEqual(args.risk_tune_turnover_penalty, 0.001)
        self.assertEqual(args.risk_tune_probability_threshold_count, 0)
        self.assertEqual(args.sell_turnover_penalty, 0.001)
        self.assertEqual(args.walk_forward_segments, 3)
        self.assertFalse(args.stress_replay)
        self.assertFalse(args.live_replay_profile)
        self.assertIsNone(args.entry_delay_seconds)
        self.assertIsNone(args.exit_delay_seconds)
        self.assertIsNone(args.max_open_positions)
        self.assertIsNone(args.entry_max_fill_wait_seconds)
        self.assertIsNone(args.exit_max_fill_wait_seconds)
        self.assertIsNone(args.entry_price_protection_pct)
        self.assertEqual(args.catboost_iterations, 500)
        self.assertEqual(args.catboost_depth, 5)

    def test_main_passes_extended_config(self):
        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_pipeline.run_hybrid_training = lambda config: {"artifacts": {}, "evaluation": {}}

        with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
            with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                cli.main([
                    "--output-dir",
                    "tmp/models",
                    "--total-timesteps",
                    "32",
                    "--lifecycle-dir",
                    "tmp/lifecycle",
                    "--train-split-ratio",
                    "0.75",
                    "--validation-split-ratio",
                    "0.2",
                    "--min-validation-files",
                    "3",
                    "--min-eval-files",
                    "3",
                    "--min-entry-unique-buyers",
                    "2",
                    "--min-entry-buy-count",
                    "4",
                    "--buy-calibration-ratio",
                    "0.35",
                    "--min-calibration-samples",
                    "12",
                    "--buy-min-threshold",
                    "0.7",
                    "--buy-sample-weighting",
                    "token_balanced",
                    "--buy-min-calibration-predictions",
                    "4",
                    "--future-windows",
                    "180,300",
                    "--max-hold-seconds",
                    "420",
                    "--min-policy-hold-seconds",
                    "5",
                    "--max-samples-per-token",
                    "60",
                    "--label-live-downside-penalty-weight",
                    "0.75",
                    "--label-delay-robust-entry-delays",
                    "1,2,3",
                    "--label-delay-robust-min-weight",
                    "0.65",
                    "--label-target-return-pct",
                    "25",
                    "--train-entry-value-model",
                    "--entry-value-target-label-column",
                    "live_risk_adjusted_return_pct",
                    "--entry-ranking-mode",
                    "entry_value",
                    "--min-entry-score",
                    "12.5",
                    "--stop-loss",
                    "-0.4",
                    "--catboost-iterations",
                    "123",
                    "--catboost-depth",
                    "4",
                    "--catboost-l2-leaf-reg",
                    "15",
                    "--position-fraction",
                    "0.2",
                    "--max-position-fraction",
                    "0.15",
                    "--initial-equity-bnb",
                    "2.0",
                    "--fixed-stake-bnb",
                    "0.25",
                    "--include-trade-log",
                    "--allow-partial-exits",
                    "--fee-bps",
                    "80",
                    "--slippage-bps",
                    "150",
                    "--allow-token-reentry",
                    "--max-trades-per-token",
                    "2",
                    "--trailing-start-pct",
                    "0.25",
                    "--trailing-stop-pct",
                    "0.15",
                    "--rug-sell-pressure",
                    "0.9",
                    "--risk-tune-min-trades",
                    "5",
                    "--risk-tune-max-trades",
                    "50",
                    "--risk-tune-min-threshold",
                    "0.91",
                    "--risk-tune-target-entry-rate",
                    "0.3",
                    "--risk-tune-entry-rate-penalty",
                    "0.7",
                    "--risk-tune-min-entry-rate",
                    "0.01",
                    "--risk-tune-max-entry-rate",
                    "0.4",
                    "--risk-tune-candidate-entry-rates",
                    "0.1,0.3",
                    "--risk-tune-thresholds",
                    "0.95,0.9715",
                    "--risk-tune-max-drawdown-pct",
                    "-20",
                    "--risk-tune-min-win-rate",
                    "0.6",
                    "--risk-tune-drawdown-penalty",
                    "2.0",
                    "--risk-tune-turnover-penalty",
                    "0.01",
                    "--risk-tune-probability-threshold-count",
                    "120",
                    "--sell-drawdown-penalty-weight",
                    "0.3",
                    "--sell-hold-penalty-per-step",
                    "0.004",
                    "--sell-turnover-penalty",
                    "0.02",
                    "--walk-forward-segments",
                    "4",
                    "--stress-replay",
                    "--entry-delay-seconds",
                    "2",
                    "--exit-delay-seconds",
                    "3",
                    "--max-open-positions",
                    "8",
                    "--entry-max-fill-wait-seconds",
                    "4",
                    "--exit-max-fill-wait-seconds",
                    "7",
                    "--entry-price-protection-pct",
                    "0.2",
                    "--entry-execution-failure-rate",
                    "0.12",
                    "--exit-execution-failure-rate",
                    "0.04",
                    "--max-pending-entries",
                    "10",
                    "--fit-artifacts-on-all-data",
                ])

        mock_run.assert_called_once()
        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["lifecycle_dir"], "tmp/lifecycle")
        self.assertEqual(cfg["total_timesteps"], 32)
        self.assertEqual(cfg["train_split_ratio"], 0.75)
        self.assertEqual(cfg["validation_split_ratio"], 0.2)
        self.assertEqual(cfg["min_validation_files"], 3)
        self.assertEqual(cfg["min_eval_files"], 3)
        self.assertEqual(cfg["min_entry_unique_buyers"], 2)
        self.assertEqual(cfg["min_entry_buy_count"], 4)
        self.assertEqual(cfg["buy_calibration_ratio"], 0.35)
        self.assertEqual(cfg["min_calibration_samples"], 12)
        self.assertEqual(cfg["buy_min_threshold"], 0.7)
        self.assertEqual(cfg["buy_sample_weighting"], "token_balanced")
        self.assertEqual(cfg["buy_min_calibration_predictions"], 4)
        self.assertEqual(cfg["future_windows"], [180, 300])
        self.assertEqual(cfg["max_hold_seconds"], 420)
        self.assertEqual(cfg["min_policy_hold_seconds"], 5)
        self.assertEqual(cfg["max_samples_per_token"], 60)
        self.assertEqual(cfg["label_live_downside_penalty_weight"], 0.75)
        self.assertEqual(cfg["label_delay_robust_entry_delay_seconds"], [1, 2, 3])
        self.assertEqual(cfg["label_delay_robust_min_weight"], 0.65)
        self.assertEqual(cfg["label_target_return_pct"], 25.0)
        self.assertTrue(cfg["train_entry_value_model"])
        self.assertEqual(cfg["entry_value_target_label_column"], "live_risk_adjusted_return_pct")
        self.assertEqual(cfg["entry_ranking_mode"], "entry_value")
        self.assertEqual(cfg["min_entry_score"], 12.5)
        self.assertEqual(cfg["stop_loss"], -0.4)
        self.assertEqual(cfg["catboost_params"]["iterations"], 123)
        self.assertEqual(cfg["catboost_params"]["depth"], 4)
        self.assertEqual(cfg["catboost_params"]["l2_leaf_reg"], 15.0)
        self.assertEqual(cfg["position_fraction"], 0.2)
        self.assertEqual(cfg["max_position_fraction"], 0.15)
        self.assertEqual(cfg["initial_equity_bnb"], 2.0)
        self.assertEqual(cfg["fixed_stake_bnb"], 0.25)
        self.assertTrue(cfg["include_trade_log"])
        self.assertTrue(cfg["allow_partial_exits"])
        self.assertEqual(cfg["fee_bps"], 80.0)
        self.assertEqual(cfg["slippage_bps"], 150.0)
        self.assertFalse(cfg["one_entry_per_token"])
        self.assertEqual(cfg["max_trades_per_token"], 2)
        self.assertEqual(cfg["trailing_start_pct"], 0.25)
        self.assertEqual(cfg["trailing_stop_pct"], 0.15)
        self.assertEqual(cfg["rug_sell_pressure"], 0.9)
        self.assertTrue(cfg["risk_tune_buy_threshold"])
        self.assertEqual(cfg["risk_tune_min_trades"], 5)
        self.assertEqual(cfg["risk_tune_max_trades"], 50)
        self.assertEqual(cfg["risk_tune_min_threshold"], 0.91)
        self.assertEqual(cfg["risk_tune_target_entry_rate"], 0.3)
        self.assertEqual(cfg["risk_tune_entry_rate_penalty"], 0.7)
        self.assertEqual(cfg["risk_tune_min_entry_rate"], 0.01)
        self.assertEqual(cfg["risk_tune_max_entry_rate"], 0.4)
        self.assertEqual(cfg["risk_tune_candidate_entry_rates"], [0.1, 0.3])
        self.assertEqual(cfg["risk_tune_thresholds"], [0.95, 0.9715])
        self.assertEqual(cfg["risk_tune_max_drawdown_pct"], -20.0)
        self.assertEqual(cfg["risk_tune_min_win_rate"], 0.6)
        self.assertEqual(cfg["risk_tune_drawdown_penalty"], 2.0)
        self.assertEqual(cfg["risk_tune_turnover_penalty"], 0.01)
        self.assertEqual(cfg["risk_tune_probability_threshold_count"], 120)
        self.assertEqual(cfg["sell_drawdown_penalty_weight"], 0.3)
        self.assertEqual(cfg["sell_hold_penalty_per_step"], 0.004)
        self.assertEqual(cfg["sell_turnover_penalty"], 0.02)
        self.assertEqual(cfg["walk_forward_segments"], 4)
        self.assertTrue(cfg["stress_replay"])
        self.assertFalse(cfg["live_replay_profile"])
        self.assertEqual(cfg["entry_delay_seconds"], 2)
        self.assertEqual(cfg["exit_delay_seconds"], 3)
        self.assertEqual(cfg["max_open_positions"], 8)
        self.assertEqual(cfg["entry_max_fill_wait_seconds"], 4)
        self.assertEqual(cfg["exit_max_fill_wait_seconds"], 7)
        self.assertEqual(cfg["entry_price_protection_pct"], 0.2)
        self.assertEqual(cfg["entry_execution_failure_rate"], 0.12)
        self.assertEqual(cfg["exit_execution_failure_rate"], 0.04)
        self.assertEqual(cfg["max_pending_entries"], 10)
        self.assertTrue(cfg["fit_artifacts_on_all_data"])

    def test_live_replay_profile_applies_default_execution_controls(self):
        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_pipeline.run_hybrid_training = lambda config: {"artifacts": {}, "evaluation": {}}

        with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
            with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                cli.main(["--live-replay-profile"])

        cfg = mock_run.call_args.args[0]
        self.assertTrue(cfg["live_replay_profile"])
        self.assertEqual(cfg["entry_delay_seconds"], 3)
        self.assertEqual(cfg["exit_delay_seconds"], 3)
        self.assertEqual(cfg["max_open_positions"], 8)
        self.assertEqual(cfg["entry_max_fill_wait_seconds"], 3)
        self.assertEqual(cfg["exit_max_fill_wait_seconds"], 6)
        self.assertEqual(cfg["entry_price_protection_pct"], 0.25)
        self.assertEqual(cfg["entry_execution_failure_rate"], 0.0)
        self.assertEqual(cfg["exit_execution_failure_rate"], 0.0)
        self.assertIsNone(cfg["max_pending_entries"])
        self.assertEqual(cfg["entry_fixed_cost_bnb"], 0.0)
        self.assertEqual(cfg["exit_fixed_cost_bnb"], 0.0)
        self.assertIsNone(cfg["label_fixed_stake_bnb"])
        self.assertIsNone(cfg["label_entry_fixed_cost_bnb"])
        self.assertIsNone(cfg["label_exit_fixed_cost_bnb"])
        self.assertIsNone(cfg["label_entry_price_protection_pct"])
        self.assertEqual(cfg["initial_equity_bnb"], 1.0)
        self.assertEqual(cfg["fixed_stake_bnb"], 0.1)
        self.assertTrue(cfg["stress_replay"])

    def test_no_fixed_stake_keeps_live_profile_fractional(self):
        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_pipeline.run_hybrid_training = lambda config: {"artifacts": {}, "evaluation": {}}

        with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
            with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                cli.main(["--live-replay-profile", "--no-fixed-stake-bnb"])

        cfg = mock_run.call_args.args[0]
        self.assertTrue(cfg["live_replay_profile"])
        self.assertIsNone(cfg["fixed_stake_bnb"])
        self.assertEqual(cfg["position_fraction"], 0.1)
        self.assertEqual(cfg["max_position_fraction"], 0.1)

    def test_execution_calibration_file_overrides_default_replay_controls(self):
        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_pipeline.run_hybrid_training = lambda config: {"artifacts": {}, "evaluation": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "execution_calibration.json"
            calibration = {
                "replay_overrides": {
                    "entry_delay_seconds": 5,
                    "entry_max_fill_wait_seconds": 9,
                    "exit_delay_seconds": 4,
                    "exit_max_fill_wait_seconds": 8,
                    "entry_price_protection_pct": 0.18,
                    "entry_execution_failure_rate": 0.12,
                    "exit_execution_failure_rate": 0.04,
                }
            }
            calibration_path.write_text(json.dumps(calibration), encoding="utf-8")

            with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
                with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                    cli.main(["--execution-calibration-file", str(calibration_path)])

        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["entry_delay_seconds"], 5)
        self.assertEqual(cfg["entry_max_fill_wait_seconds"], 9)
        self.assertEqual(cfg["exit_delay_seconds"], 4)
        self.assertEqual(cfg["exit_max_fill_wait_seconds"], 8)
        self.assertEqual(cfg["entry_price_protection_pct"], 0.18)
        self.assertEqual(cfg["entry_execution_failure_rate"], 0.12)
        self.assertEqual(cfg["exit_execution_failure_rate"], 0.04)
        self.assertEqual(cfg["execution_calibration"]["replay_overrides"], calibration["replay_overrides"])

    def test_explicit_execution_controls_override_calibration_file(self):
        cli = _load_cli()
        fake_pipeline = types.ModuleType("src.pipeline.train_hybrid")
        fake_pipeline.run_hybrid_training = lambda config: {"artifacts": {}, "evaluation": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "execution_calibration.json"
            calibration_path.write_text(json.dumps({
                "replay_overrides": {
                    "entry_delay_seconds": 5,
                    "entry_price_protection_pct": 0.5,
                    "exit_delay_seconds": 4,
                }
            }), encoding="utf-8")

            with patch.dict(sys.modules, {"src.pipeline.train_hybrid": fake_pipeline}):
                with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                    cli.main([
                        "--execution-calibration-file", str(calibration_path),
                        "--entry-delay-seconds", "1",
                        "--entry-price-protection-pct", "0.26",
                    ])

        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["entry_delay_seconds"], 1)
        self.assertEqual(cfg["entry_price_protection_pct"], 0.26)
        self.assertEqual(cfg["exit_delay_seconds"], 4)


if __name__ == "__main__":
    unittest.main()
