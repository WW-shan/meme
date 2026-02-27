import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util


def _load_worktree_dataset_builder():
    builder_path = Path(__file__).resolve().parents[2] / "src" / "data" / "dataset_builder.py"
    spec = importlib.util.spec_from_file_location("worktree_dataset_builder", builder_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.DatasetBuilder


DatasetBuilder = _load_worktree_dataset_builder()


def _write_lifecycle(path: Path, token_address: str):
    lifecycle = {
        "token_address": token_address,
        "name": token_address,
        "symbol": token_address,
        "created_at": 1,
        "purchases": [],
        "sales": [],
        "total_supply": 1_000_000_000,
        "launch_fee": 0.01,
    }
    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(lifecycle, ensure_ascii=False) + "\n")


class TestDatasetBuilderIncrementalFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lifecycle_dir = Path(self.tmp.name)

        self.incremental_old = "lifecycle_incremental_20260215_100000.jsonl"
        self.incremental_new = "lifecycle_incremental_20260215_110000.jsonl"

        _write_lifecycle(self.lifecycle_dir / self.incremental_old, "OLD")
        _write_lifecycle(self.lifecycle_dir / self.incremental_new, "NEW")

        self.builder = DatasetBuilder(lifecycle_dir=str(self.lifecycle_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def test_incremental_pattern_loads_all_files(self):
        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files("lifecycle_incremental_*.jsonl")

        self.assertEqual(loaded, 2)
        self.assertEqual(self.builder.total_tokens, 2)
        self.assertEqual(set(seen_tokens), {"OLD", "NEW"})

    def test_default_pattern_prefers_incremental_files_when_present(self):
        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files()

        self.assertEqual(loaded, 2)
        self.assertEqual(self.builder.total_tokens, 2)
        self.assertEqual(set(seen_tokens), {"OLD", "NEW"})


if __name__ == "__main__":
    unittest.main()
