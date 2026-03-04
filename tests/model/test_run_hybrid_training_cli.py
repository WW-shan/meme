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
        project_root = Path(__file__).resolve().parents[2]
        script_path = project_root / "scripts" / "run_hybrid_training.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--output-dir",
                "tmp/models",
                "--total-timesteps",
                "16",
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
