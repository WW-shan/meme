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


def _write_lifecycle(
    path: Path,
    token_address: str,
    symbol: str = "",
    purchases=None,
    sales=None,
):
    lifecycle = {
        "token_address": token_address,
        "name": token_address,
        "symbol": symbol or token_address,
        "created_at": 1,
        "purchases": purchases or [],
        "sales": sales or [],
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
        self.assertEqual(set(seen_tokens), {"old", "new"})

    def test_default_pattern_orders_numeric_incremental_files_semantically(self):
        extra_old = self.lifecycle_dir / "lifecycle_incremental_2.jsonl"
        extra_new = self.lifecycle_dir / "lifecycle_incremental_10.jsonl"
        _write_lifecycle(extra_old, "TWO")
        _write_lifecycle(extra_new, "TEN")

        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files("lifecycle_incremental_*.jsonl")

        self.assertEqual(loaded, 4)
        self.assertEqual(seen_tokens, ["two", "ten", "old", "new"])

    def test_default_pattern_includes_and_orders_incremental_part_files(self):
        base = self.lifecycle_dir / "lifecycle_incremental_20260215_120000.jsonl"
        part2 = self.lifecycle_dir / "lifecycle_incremental_20260215_120000_part002.jsonl"
        part1 = self.lifecycle_dir / "lifecycle_incremental_20260215_120000_part001.jsonl"
        _write_lifecycle(base, "BASE")
        _write_lifecycle(part2, "PART2")
        _write_lifecycle(part1, "PART1")

        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files("lifecycle_incremental_*.jsonl")

        self.assertEqual(loaded, 5)
        self.assertEqual(seen_tokens[-3:], ["base", "part1", "part2"])

    def test_default_pattern_prefers_incremental_files_when_present(self):
        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_files()

        self.assertEqual(loaded, 2)
        self.assertEqual(self.builder.total_tokens, 2)
        self.assertEqual(set(seen_tokens), {"old", "new"})
    def test_load_lifecycle_paths_bypasses_auto_discovery(self):
        manual_file = self.lifecycle_dir / "manual_order.jsonl"
        _write_lifecycle(manual_file, "MANUAL")

        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_paths([str(manual_file)])

        self.assertEqual(loaded, 1)
        self.assertEqual(self.builder.total_tokens, 1)
        self.assertEqual(seen_tokens, ["manual"])

    def test_load_lifecycle_paths_processes_files_in_given_order(self):
        first = self.lifecycle_dir / "z_manual.jsonl"
        second = self.lifecycle_dir / "a_manual.jsonl"
        _write_lifecycle(first, "TOKEN_FIRST")
        _write_lifecycle(second, "TOKEN_SECOND")

        seen_tokens = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_paths([str(first), str(second)])

        self.assertEqual(loaded, 2)
        self.assertEqual(seen_tokens, ["token_first", "token_second"])

    def test_load_lifecycle_paths_keeps_merge_replacement_semantics(self):
        same_token_old = self.lifecycle_dir / "same_token_old.jsonl"
        same_token_new = self.lifecycle_dir / "same_token_new.jsonl"

        shared_activity = [
            {"timestamp": 2, "account": "a", "ether_amount": 0.1, "token_amount": 10}
        ]
        _write_lifecycle(
            same_token_old,
            token_address="SAME",
            symbol="OLD_VERSION",
            purchases=shared_activity,
        )
        _write_lifecycle(
            same_token_new,
            token_address="SAME",
            symbol="NEW_VERSION",
            purchases=shared_activity,
        )

        seen_symbols = []

        def _capture_and_skip(lifecycle):
            seen_symbols.append(lifecycle["symbol"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_paths([str(same_token_old), str(same_token_new)])

        self.assertEqual(loaded, 1)
        self.assertEqual(seen_symbols, ["NEW_VERSION"])

    def test_load_lifecycle_paths_merges_mixed_case_token_addresses(self):
        same_token_old = self.lifecycle_dir / "same_token_old_case.jsonl"
        same_token_new = self.lifecycle_dir / "same_token_new_case.jsonl"

        shared_activity = [
            {"timestamp": 2, "account": "a", "ether_amount": 0.1, "token_amount": 10}
        ]
        _write_lifecycle(
            same_token_old,
            token_address="0xAbC",
            symbol="OLD_CASE",
            purchases=shared_activity,
        )
        _write_lifecycle(
            same_token_new,
            token_address="0xaBc",
            symbol="NEW_CASE",
            purchases=shared_activity,
        )

        seen_tokens = []
        seen_symbols = []

        def _capture_and_skip(lifecycle):
            seen_tokens.append(lifecycle["token_address"])
            seen_symbols.append(lifecycle["symbol"])
            return []

        with patch.object(self.builder, "_generate_samples_from_lifecycle", side_effect=_capture_and_skip):
            loaded = self.builder.load_lifecycle_paths([str(same_token_old), str(same_token_new)])

        self.assertEqual(loaded, 1)
        self.assertEqual(seen_tokens, ["0xabc"])
        self.assertEqual(seen_symbols, ["NEW_CASE"])

    def test_entry_activity_gate_is_configurable_for_live_alignment(self):
        lifecycle_path = self.lifecycle_dir / "entry_activity.jsonl"
        _write_lifecycle(
            lifecycle_path,
            token_address="ENTRY_ACTIVITY",
            purchases=[
                {"timestamp": 2, "account": "buyer1", "ether_amount": 0.1, "token_amount": 10},
                {"timestamp": 4, "account": "buyer2", "ether_amount": 0.2, "token_amount": 10},
            ],
            sales=[
                {"timestamp": 8, "account": "seller1", "ether_amount": 0.3, "token_amount": 10},
            ],
        )

        default_builder = DatasetBuilder(
            lifecycle_dir=str(self.lifecycle_dir),
            sample_mode="trade_event",
            future_windows=[10],
        )
        default_builder.load_lifecycle_paths([str(lifecycle_path)])
        self.assertEqual(default_builder.samples, [])

        live_aligned_builder = DatasetBuilder(
            lifecycle_dir=str(self.lifecycle_dir),
            sample_mode="trade_event",
            future_windows=[10],
            min_entry_unique_buyers=2,
            min_entry_buy_count=2,
        )
        live_aligned_builder.load_lifecycle_paths([str(lifecycle_path)])

        self.assertEqual(len(live_aligned_builder.samples), 1)
        self.assertEqual(live_aligned_builder.samples[0]["features"]["unique_buyers"], 2)
        self.assertEqual(live_aligned_builder.samples[0]["features"]["total_buys"], 2)

    def test_samples_include_decision_time_chain_lag_without_terminal_staleness(self):
        lifecycle = {
            "token_address": "CHAIN_LAG",
            "name": "Chain Lag",
            "symbol": "CLAG",
            "creator": "creator",
            "create_timestamp": 100,
            "last_update": 250,
            "last_update_local": 2_000.0,
            "total_supply": 1_000_000_000_000_000_000,
            "launch_fee": 10_000_000_000_000_000,
            "unique_buyers": [],
            "unique_sellers": [],
            "buys": [
                {"timestamp": 110, "account": "buyer1", "bnb_amount": 0.1, "token_amount": 10.0, "price": 1.0},
                {"timestamp": 119, "account": "buyer2", "bnb_amount": 0.2, "token_amount": 10.0, "price": 1.1},
            ],
            "sells": [
                {"timestamp": 125, "account": "seller1", "bnb_amount": 0.1, "token_amount": 5.0, "price": 1.2},
                {"timestamp": 140, "account": "seller2", "bnb_amount": 0.1, "token_amount": 5.0, "price": 1.3},
            ],
            "price_history": [],
        }
        builder = DatasetBuilder(
            lifecycle_dir=str(self.lifecycle_dir),
            future_windows=[50],
            min_entry_unique_buyers=2,
            min_entry_buy_count=2,
        )

        samples = builder._generate_samples_from_lifecycle(lifecycle, sample_intervals=[30])

        self.assertEqual(len(samples), 1)
        features = samples[0]["features"]
        self.assertEqual(features["lifecycle_status_chain_lag_seconds"], 5.0)
        self.assertNotIn("lifecycle_status_staleness_seconds", features)

    def test_save_dataset_records_flow_feature_config(self):
        import json
        import tempfile

        builder = DatasetBuilder(
            lifecycle_dir=str(self.lifecycle_dir),
            include_flow_features=True,
        )
        builder.samples = [
            {
                "features": {"current_price": 1.0, "sell_pressure_10s": 0.2},
                "label": {"profitable": True},
                "meta": {"token_address": "0xFLOW", "sample_time": 1},
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            builder.save_dataset(output_dir=tmpdir)
            metadata_path = next(Path(tmpdir).glob("metadata_*.json"))
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertTrue(metadata["dataset_config"]["include_flow_features"])


if __name__ == "__main__":
    unittest.main()
