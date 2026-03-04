import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
import subprocess
import sys


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

    def test_main_calls_pipeline(self):
        cli = _load_cli()
        with patch.object(cli, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
            cli.main(["--output-dir", "tmp/models", "--total-timesteps", "512"])
        mock_run.assert_called_once()

    def test_script_runs_as_subprocess(self):
        """Verify the script is importable and args parse correctly via subprocess."""
        project_root = Path(__file__).resolve().parents[2]
        script_path = project_root / "scripts" / "run_hybrid_training.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--help",
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--lifecycle-dir", result.stdout)
        self.assertIn("--target-threshold-value", result.stdout)

    def test_parse_args_includes_dataset_and_target_controls(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.sample_mode, "trade_event")
        self.assertEqual(args.target_threshold_value, 80.0)

    def test_main_passes_extended_config(self):
        cli = _load_cli()
        with patch.object(cli, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
            cli.main(["--output-dir", "tmp/models", "--total-timesteps", "32", "--lifecycle-dir", "tmp/lifecycle"])
        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["lifecycle_dir"], "tmp/lifecycle")
        self.assertEqual(cfg["total_timesteps"], 32)


if __name__ == "__main__":
    unittest.main()
