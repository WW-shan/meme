import argparse
import builtins
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
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
        self.assertEqual(args.entry_ranking_modes, "chronological")
        self.assertTrue(args.use_cache)

    def test_entry_ranking_modes_accepts_entry_value(self):
        cli = _load_cli()

        self.assertEqual(cli._parse_entry_ranking_modes("chronological,entry_value"), ["chronological", "entry_value"])

    def test_min_entry_score_grid_keeps_unfiltered_baseline(self):
        cli = _load_cli()

        scores = cli._parse_min_entry_scores("none,12.5")
        candidates = cli._candidate_grid(
            [0.8],
            [-0.25],
            [(0.2, 0.1)],
            8,
            entry_ranking_modes=["chronological"],
            min_entry_scores=scores,
        )

        self.assertEqual(candidates, [
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8},
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8, "min_entry_score": 12.5},
        ])

    def test_min_policy_hold_grid_adds_hold_floor_candidates(self):
        cli = _load_cli()

        candidates = cli._candidate_grid(
            [0.8],
            [-0.25],
            [(0.2, 0.1)],
            8,
            entry_ranking_modes=["chronological"],
            min_entry_scores=[None],
            min_policy_holds=[5, 15],
        )

        self.assertEqual(candidates, [
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8, "min_policy_hold_seconds": 5},
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8, "min_policy_hold_seconds": 15},
        ])

    def test_main_calls_run_parameter_search(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_parameter_search = lambda **kwargs: {"candidate_count": 1}
        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            with patch.object(fake_module, "run_parameter_search", return_value={"candidate_count": 1}) as mock_run:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = cli.main([
                        "--model-dir", "data/models/example",
                        "--output", "data/replay_reports/search.json",
                        "--thresholds", "0.8,0.85",
                        "--stop-losses", "-0.25",
                        "--trailing-pairs", "0.2:0.1",
                    "--entry-ranking-modes", "chronological,buy_prob",
                    "--fast-selection",
                    "--no-cache",
                ])

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["model_dir"], "data/models/example")
        self.assertEqual(kwargs["output_path"], "data/replay_reports/search.json")
        self.assertEqual(kwargs["candidates"], [
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8},
            {"buy_threshold": 0.8, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8, "entry_ranking_mode": "buy_prob"},
            {"buy_threshold": 0.85, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8},
            {"buy_threshold": 0.85, "stop_loss": -0.25, "trailing_start_pct": 0.2, "trailing_stop_pct": 0.1, "max_open_positions": 8, "entry_ranking_mode": "buy_prob"},
        ])
        self.assertFalse(kwargs["use_cache"])
        self.assertTrue(kwargs["fast_selection"])
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(stdout.getvalue(), '{"candidate_count": 1}\n')

    def test_main_passes_execution_calibration_to_parameter_search(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_parameter_search = lambda **kwargs: {"candidate_count": 1}

        with tempfile.TemporaryDirectory() as tmpdir:
            calibration_path = Path(tmpdir) / "execution_calibration.json"
            calibration_path.write_text(
                json.dumps(
                    {
                        "replay_overrides": {
                            "entry_delay_seconds": 1,
                            "entry_max_fill_wait_seconds": 4,
                            "exit_delay_seconds": 4,
                            "entry_price_protection_pct": 0.113,
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with patch.object(fake_module, "run_parameter_search", return_value={"candidate_count": 1}) as mock_run:
                    cli.main([
                        "--model-dir", "data/models/example",
                        "--execution-calibration-file", str(calibration_path),
                    ])

        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args.kwargs["base_overrides"], {
            "entry_delay_seconds": 1,
            "entry_max_fill_wait_seconds": 4,
            "exit_delay_seconds": 4,
            "entry_price_protection_pct": 0.113,
        })

    def test_main_passes_live_sizing_overrides_to_parameter_search(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_parameter_search = lambda **kwargs: {"candidate_count": 1}

        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            with patch.object(fake_module, "run_parameter_search", return_value={"candidate_count": 1}) as mock_run:
                cli.main([
                    "--model-dir", "data/models/example",
                    "--initial-equity-bnb", "0.0102",
                    "--position-fraction", "0.1",
                    "--max-position-fraction", "0.1",
                    "--no-fixed-stake-bnb",
                    "--entry-fixed-cost-bnb", "0.000019",
                    "--exit-fixed-cost-bnb", "0.000013",
                ])

        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args.kwargs["base_overrides"], {
            "initial_equity_bnb": 0.0102,
            "position_fraction": 0.1,
            "max_position_fraction": 0.1,
            "fixed_stake_bnb": None,
            "entry_fixed_cost_bnb": 0.000019,
            "exit_fixed_cost_bnb": 0.000013,
        })

    def test_parse_trailing_pairs_rejects_invalid_format(self):
        cli = _load_cli()
        with self.assertRaises(argparse.ArgumentTypeError):
            cli._parse_trailing_pairs("0.2")

    def test_invalid_grid_input_exits_without_traceback(self):
        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "scripts" / "search_replay_params.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--model-dir",
                "data/models/example",
                "--trailing-pairs",
                "0.2",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_grid_input_does_not_import_model_replay(self):
        cli = _load_cli()
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "src.pipeline.model_replay":
                raise AssertionError("model replay imported before grid validation")
            return real_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=guarded_import):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc:
                    cli.main([
                        "--model-dir",
                        "data/models/example",
                        "--thresholds",
                        "abc",
                    ])

        self.assertEqual(exc.exception.code, 2)

    def test_empty_grid_exits_before_run_parameter_search(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_parameter_search = lambda **kwargs: {"candidate_count": 1}
        with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
            with patch.object(fake_module, "run_parameter_search") as mock_run:
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exc:
                        cli.main([
                            "--model-dir",
                            "data/models/example",
                            "--thresholds",
                            ",",
                        ])

        self.assertEqual(exc.exception.code, 2)
        mock_run.assert_not_called()

    def test_help_lists_search_controls(self):
        repo_root = Path(__file__).resolve().parents[2]
        script_path = repo_root / "scripts" / "search_replay_params.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--thresholds", result.stdout)
        self.assertIn("--trailing-pairs", result.stdout)
        self.assertIn("--entry-ranking-modes", result.stdout)
        self.assertIn("--min-entry-scores", result.stdout)
        self.assertIn("--initial-equity-bnb", result.stdout)
        self.assertIn("--no-fixed-stake-bnb", result.stdout)
        self.assertIn("--fast-selection", result.stdout)


if __name__ == "__main__":
    unittest.main()
