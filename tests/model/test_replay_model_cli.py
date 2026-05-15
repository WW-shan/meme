import contextlib
import importlib.util
import io
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
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
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
        self.assertEqual(stdout.getvalue(), '{"evaluation": {"net_profit_bnb": 1.2}}\n')

    def test_overrides_from_args_maps_live_tuning_controls(self):
        cli = _load_cli()
        args = cli.parse_args([
            "--model-dir", "data/models/example",
            "--initial-equity-bnb", "0.0102",
            "--position-fraction", "0.1",
            "--max-position-fraction", "0.1",
            "--no-fixed-stake-bnb",
            "--threshold", "0.73",
            "--stop-loss", "-0.22",
            "--trailing-start-pct", "0.31",
            "--trailing-stop-pct", "0.14",
            "--min-policy-hold-seconds", "10",
            "--entry-price-protection-pct", "0.45",
            "--max-pending-entries", "3",
            "--entry-ranking-mode", "buy_prob",
            "--min-entry-score", "12.5",
            "--entry-fixed-cost-bnb", "0.00002",
            "--exit-fixed-cost-bnb", "0.000013",
            "--skip-all-in-replay",
        ])

        self.assertEqual(cli._overrides_from_args(args), {
            "initial_equity_bnb": 0.0102,
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "fixed_stake_bnb": None,
            "buy_threshold": 0.73,
            "stop_loss": -0.22,
            "trailing_start_pct": 0.31,
            "trailing_stop_pct": 0.14,
            "min_policy_hold_seconds": 10,
            "entry_price_protection_pct": 0.45,
            "max_pending_entries": 3,
            "entry_ranking_mode": "buy_prob",
            "min_entry_score": 12.5,
            "entry_fixed_cost_bnb": 0.00002,
            "exit_fixed_cost_bnb": 0.000013,
            "skip_all_in_replay": True,
        })

    def test_entry_ranking_mode_accepts_entry_value(self):
        cli = _load_cli()
        args = cli.parse_args([
            "--model-dir", "data/models/example",
            "--entry-ranking-mode", "entry_value",
        ])

        self.assertEqual(cli._overrides_from_args(args), {"entry_ranking_mode": "entry_value"})

    def test_help_lists_live_controls(self):
        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "scripts" / "replay_model.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--max-open-positions", result.stdout)
        self.assertIn("--threshold", result.stdout)
        self.assertIn("--stop-loss", result.stdout)
        self.assertIn("--min-policy-hold-seconds", result.stdout)
        self.assertIn("--entry-ranking-mode", result.stdout)
        self.assertIn("--min-entry-score", result.stdout)
        self.assertIn("--initial-equity-bnb", result.stdout)
        self.assertIn("--no-fixed-stake-bnb", result.stdout)
        self.assertIn("--entry-fixed-cost-bnb", result.stdout)
        self.assertIn("--exit-fixed-cost-bnb", result.stdout)
        self.assertIn("--skip-all-in-replay", result.stdout)
        self.assertIn("sidecar", result.stdout)
