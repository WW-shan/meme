import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "build_dataset_new.py"
    spec = importlib.util.spec_from_file_location("build_dataset_new", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBuildDatasetNewCli(unittest.TestCase):
    def _run_main(self, cli, argv, env=None):
        with tempfile.TemporaryDirectory() as tmpdir:
            lifecycle_dir = Path(tmpdir) / "training"
            output_dir = Path(tmpdir) / "datasets"
            lifecycle_dir.mkdir()
            (lifecycle_dir / "lifecycle_20260521.jsonl").write_text("{}\n", encoding="utf-8")

            with patch.dict(os.environ, env or {}, clear=True), \
                 patch.object(sys, "argv", ["build_dataset_new.py", "--lifecycle-dir", str(lifecycle_dir), "--output-dir", str(output_dir), *argv]), \
                 patch.object(cli, "DatasetBuilder") as mock_builder:
                builder = mock_builder.return_value
                builder.load_lifecycle_files.return_value = 1
                builder.get_stats.return_value = {
                    "total_samples": 1,
                    "profitable_samples": 1,
                    "profitable_ratio": 1.0,
                    "return_class_distribution": {0: 1},
                }

                cli.main()

        return mock_builder.call_args.kwargs

    def test_include_flow_features_flag_reaches_dataset_builder(self):
        cli = _load_cli()

        kwargs = self._run_main(cli, ["--include-flow-features"])

        self.assertTrue(kwargs["include_flow_features"])

    def test_include_flow_features_env_reaches_dataset_builder(self):
        cli = _load_cli()

        kwargs = self._run_main(cli, [], env={"DATASET_INCLUDE_FLOW_FEATURES": "true"})

        self.assertTrue(kwargs["include_flow_features"])


if __name__ == "__main__":
    unittest.main()
