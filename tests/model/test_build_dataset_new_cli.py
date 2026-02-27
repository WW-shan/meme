import tempfile
import unittest
from pathlib import Path
import importlib.util
from unittest.mock import patch


def _load_cli_module():
    module_path = Path(__file__).resolve().parents[2] / "tools" / "build_dataset_new.py"
    spec = importlib.util.spec_from_file_location("build_dataset_new", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _FakeBuilder:
    def __init__(self):
        self.loaded_pattern = None
        self.saved = False

    def load_lifecycle_files(self, file_pattern="lifecycle_*.jsonl"):
        self.loaded_pattern = file_pattern
        return 1

    def get_stats(self):
        return {
            "total_samples": 0,
            "profitable_samples": 0,
            "profitable_ratio": 0.0,
            "return_class_distribution": {},
        }

    def save_dataset(self):
        self.saved = True


class TestBuildDatasetNewCli(unittest.TestCase):
    def test_main_prefers_default_loader_and_does_not_require_snapshot_match(self):
        module = _load_cli_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            training_dir = Path(tmpdir) / "data" / "training"
            training_dir.mkdir(parents=True, exist_ok=True)
            # only incremental file exists
            (training_dir / "lifecycle_incremental_20260227_000001.jsonl").write_text("{}\n", encoding="utf-8")

            fake_builder = _FakeBuilder()
            with patch.object(module, "project_root", Path(tmpdir)), patch.object(module, "DatasetBuilder", return_value=fake_builder):
                module.main()

            self.assertEqual(fake_builder.loaded_pattern, "lifecycle_*.jsonl")
            self.assertTrue(fake_builder.saved)


if __name__ == "__main__":
    unittest.main()
