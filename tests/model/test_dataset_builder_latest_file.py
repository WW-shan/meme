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


class TestDatasetBuilderLatestFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lifecycle_dir = Path(self.tmp.name)
        self.old_name = "lifecycle_20260215_144327.jsonl"
        self.new_name = "lifecycle_20260215_154354.jsonl"

        _write_lifecycle(self.lifecycle_dir / self.old_name, "OLD")
        _write_lifecycle(self.lifecycle_dir / self.new_name, "NEW")

        self.builder = DatasetBuilder(lifecycle_dir=str(self.lifecycle_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_lifecycle_files_uses_latest_timestamp_by_default(self):
        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files()

        self.assertEqual(loaded, 1)
        self.assertEqual(self.builder.total_tokens, 1)
        self.assertEqual(seen_tokens, ["new"])

    def test_load_lifecycle_files_respects_explicit_filename(self):
        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files(self.old_name)

        self.assertEqual(loaded, 1)
        self.assertEqual(self.builder.total_tokens, 1)
        self.assertEqual(seen_tokens, ["old"])


if __name__ == "__main__":
    unittest.main()
