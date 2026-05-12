import argparse
import builtins
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
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(stdout.getvalue(), '{"candidate_count": 1}\n')

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


if __name__ == "__main__":
    unittest.main()
