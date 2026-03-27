import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util
import subprocess
import sys
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
                max_sample_age_seconds=180,
                target_label_column="max_return_pct",
                target_threshold_value=80.0,
                buy_min_precision=0.1,
                train_split_ratio=0.8,
                min_eval_files=1,
            )):
                with patch.object(fake_pipeline, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
                    cli.main([])

        mock_run.assert_called_once_with({
            "output_dir": "tmp/models",
            "total_timesteps": 512,
            "lifecycle_dir": "data/training",
            "sample_mode": "trade_event",
            "max_sample_age_seconds": 180,
            "target_label_column": "max_return_pct",
            "target_threshold_value": 80.0,
            "buy_min_precision": 0.1,
            "train_split_ratio": 0.8,
            "min_eval_files": 1,
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
        self.assertIn("--train-split-ratio", result.stdout)
        self.assertIn("--min-eval-files", result.stdout)

    def test_parse_args_includes_dataset_and_target_controls(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.sample_mode, "trade_event")
        self.assertEqual(args.target_threshold_value, 80.0)
        self.assertEqual(args.train_split_ratio, 0.8)
        self.assertEqual(args.min_eval_files, 1)

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
                    "--min-eval-files",
                    "3",
                ])

        mock_run.assert_called_once()
        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["lifecycle_dir"], "tmp/lifecycle")
        self.assertEqual(cfg["total_timesteps"], 32)
        self.assertEqual(cfg["train_split_ratio"], 0.75)
        self.assertEqual(cfg["min_eval_files"], 3)


if __name__ == "__main__":
    unittest.main()
