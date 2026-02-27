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


def _write_new_format_lifecycle(path: Path, token_address: str, purchases_count: int = 0):
    purchases = []
    for i in range(purchases_count):
        purchases.append(
            {
                "timestamp": 100 + i,
                "account": f"0x{i:040x}",
                "token_amount": 100 + i,
                "ether_amount": 1 + i,
            }
        )

    lifecycle = {
        "token_address": token_address,
        "name": token_address,
        "symbol": token_address,
        "created_at": 1,
        "purchases": purchases,
        "sales": [],
        "total_supply": 1_000_000_000,
        "launch_fee": 0.01,
    }

    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(lifecycle, ensure_ascii=False) + "\n")


class TestDatasetBuilderIncrementalMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lifecycle_dir = Path(self.tmp.name)
        self.builder = DatasetBuilder(lifecycle_dir=str(self.lifecycle_dir))

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_load_merges_incremental_and_latest_snapshot(self):
        _write_new_format_lifecycle(
            self.lifecycle_dir / "lifecycle_incremental_20260215_100000.jsonl",
            token_address="INC",
            purchases_count=1,
        )
        _write_new_format_lifecycle(
            self.lifecycle_dir / "lifecycle_20260215_120000.jsonl",
            token_address="SNAP",
            purchases_count=1,
        )

        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files()

        self.assertEqual(loaded, 2)
        self.assertEqual(set(seen_tokens), {"INC", "SNAP"})

    def test_default_load_prefers_richer_lifecycle_for_same_token(self):
        _write_new_format_lifecycle(
            self.lifecycle_dir / "lifecycle_incremental_20260215_100000.jsonl",
            token_address="SAME",
            purchases_count=1,
        )
        _write_new_format_lifecycle(
            self.lifecycle_dir / "lifecycle_20260215_120000.jsonl",
            token_address="SAME",
            purchases_count=3,
        )

        captured_buys_lengths = []

        def _capture_and_skip(lifecycle):
            captured_buys_lengths.append(len(lifecycle.get("buys", [])))
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files()

        self.assertEqual(loaded, 1)
        self.assertEqual(captured_buys_lengths, [3])


if __name__ == "__main__":
    unittest.main()
