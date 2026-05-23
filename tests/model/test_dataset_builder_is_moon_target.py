import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util


def _load_worktree_dataset_builder():
    builder_path = Path(__file__).resolve().parents[2] / "src" / "data" / "dataset_builder.py"
    spec = importlib.util.spec_from_file_location("worktree_dataset_builder", builder_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.DatasetBuilder


DatasetBuilder = _load_worktree_dataset_builder()


class TestDatasetBuilderIsMoonTarget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.builder = DatasetBuilder(lifecycle_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_label_max_return_stays_below_200pct_when_peak_is_299pct_price(self):
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 2.99},
            ],
            "sells": [],
        }

        label = self.builder._calculate_label_with_window(
            lifecycle=lifecycle,
            sample_time=10,
            future_window=60,
        )

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 199.0)
        self.assertAlmostEqual(label["min_return_pct"], 199.0)
        self.assertAlmostEqual(label["final_return_pct"], 199.0)
        self.assertEqual(label["future_window_seconds"], 60)

    def test_label_max_return_reaches_200pct_at_3x_price(self):
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 3.0},
            ],
            "sells": [],
        }

        label = self.builder._calculate_label_with_window(
            lifecycle=lifecycle,
            sample_time=10,
            future_window=60,
        )

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["min_return_pct"], 200.0)
        self.assertAlmostEqual(label["final_return_pct"], 200.0)
        self.assertEqual(label["future_window_seconds"], 60)

    def test_executable_label_rejects_target_after_stop_loss(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 0.4},
                {"timestamp": 30, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(
            lifecycle=lifecycle,
            sample_time=10,
            future_window=60,
        )

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["cost_adjusted_max_return_pct"], 200.0)
        self.assertAlmostEqual(label["executable_return_pct"], -60.0)
        self.assertEqual(label["is_executable_target"], 0)
        self.assertEqual(label["target_hit_before_stop"], 0)
        self.assertEqual(label["stop_hit_before_target"], 1)
        self.assertEqual(label["time_to_target_seconds"], 0)

    def test_executable_label_accepts_target_before_stop_loss(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 2.0},
                {"timestamp": 30, "price": 0.4},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(
            lifecycle=lifecycle,
            sample_time=10,
            future_window=60,
        )

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["executable_return_pct"], 100.0)
        self.assertEqual(label["is_executable_target"], 1)
        self.assertEqual(label["target_hit_before_stop"], 1)
        self.assertEqual(label["stop_hit_before_target"], 0)
        self.assertEqual(label["time_to_target_seconds"], 10)

    def test_cost_adjusted_label_includes_buy_and_sell_costs(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_fee_bps=100.0,
            label_slippage_bps=100.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(
            lifecycle=lifecycle,
            sample_time=10,
            future_window=60,
        )

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 100.0)
        self.assertLess(label["cost_adjusted_max_return_pct"], 100.0)
        self.assertAlmostEqual(label["executable_return_pct"], label["cost_adjusted_max_return_pct"])
        self.assertEqual(label["is_executable_target"], 1)

    def test_live_label_uses_delayed_entry_price(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=3,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=40.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 13, "price": 2.0},
                {"timestamp": 20, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 1)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["live_entry_price"], 2.0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 50.0)
        self.assertEqual(label["live_target_hit_before_stop"], 1)

    def test_live_label_zero_entry_delay_uses_signal_price(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=0,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 1)
        self.assertEqual(label["live_entry_time"], 10)
        self.assertAlmostEqual(label["live_entry_price"], 1.0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 100.0)

    def test_live_label_uses_delayed_exit_price(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=3,
            label_exit_delay_seconds=3,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 13, "price": 1.0},
                {"timestamp": 20, "price": 3.0},
                {"timestamp": 23, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["live_cost_adjusted_max_return_pct"], 100.0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 100.0)
        self.assertEqual(label["live_time_to_target_seconds"], 13)

    def test_live_label_subtracts_fixed_execution_costs_from_small_stake(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=0,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_fixed_stake_bnb=0.1,
            label_entry_fixed_cost_bnb=0.01,
            label_exit_fixed_cost_bnb=0.02,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=60.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 20, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["label_fixed_stake_bnb"], 0.1)
        self.assertAlmostEqual(label["label_entry_fixed_cost_bnb"], 0.01)
        self.assertAlmostEqual(label["label_exit_fixed_cost_bnb"], 0.02)
        self.assertAlmostEqual(label["live_executable_return_pct"], (0.18 - 0.11) / 0.11 * 100.0)
        self.assertEqual(label["live_target_hit_before_stop"], 1)

    def test_live_label_marks_missing_delayed_entry_as_not_executable(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=10,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 15, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=8)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 0.0)
        self.assertEqual(label["live_target_hit_before_stop"], 0)

    def test_live_label_marks_over_protection_delayed_entry_as_not_executable(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=3,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_entry_price_protection_pct=0.25,
            label_target_return_pct=40.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 13, "price": 1.5},
                {"timestamp": 20, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 0)
        self.assertEqual(label["live_entry_blocked_by_price_protection"], 1)
        self.assertAlmostEqual(label["live_entry_slippage_pct"], 0.5)
        self.assertAlmostEqual(label["live_executable_return_pct"], 0.0)
        self.assertAlmostEqual(label["label_entry_price_protection_pct"], 0.25)

    def test_live_risk_adjusted_label_penalizes_delayed_downside(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=0,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-80.0,
            label_target_return_pct=80.0,
            label_live_downside_penalty_weight=0.5,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 12, "price": 0.5},
                {"timestamp": 20, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["live_executable_return_pct"], 100.0)
        self.assertAlmostEqual(label["live_cost_adjusted_min_return_pct"], -50.0)
        self.assertAlmostEqual(label["live_risk_adjusted_return_pct"], 75.0)
        self.assertAlmostEqual(label["label_live_downside_penalty_weight"], 0.5)

    def test_live_risk_adjusted_label_is_zero_without_delayed_entry(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=10,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_live_downside_penalty_weight=0.5,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 15, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=8)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 0)
        self.assertAlmostEqual(label["live_risk_adjusted_return_pct"], 0.0)
        self.assertAlmostEqual(label["label_live_downside_penalty_weight"], 0.5)

    def test_delay_robust_live_label_penalizes_signals_that_fail_when_entry_is_slower(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=0,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
            label_delay_robust_entry_delay_seconds=[0, 3],
            label_delay_robust_min_weight=1.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 11, "price": 3.0},
                {"timestamp": 13, "price": 10.0},
                {"timestamp": 20, "price": 9.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["live_risk_adjusted_return_pct"], 900.0)
        self.assertAlmostEqual(label["live_delay_robust_min_return_pct"], -10.0)
        self.assertAlmostEqual(label["live_delay_robust_return_pct"], -10.0)
        self.assertEqual(label["live_delay_robust_available_count"], 2)
        self.assertEqual(label["live_delay_robust_blocked_count"], 0)
        self.assertEqual(label["label_delay_robust_entry_delay_count"], 2)
        self.assertEqual(label["label_delay_robust_max_entry_delay_seconds"], 3)
        self.assertAlmostEqual(label["label_delay_robust_min_weight"], 1.0)

    def test_live_execution_label_uses_indexed_delayed_exit_lookup(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=1,
            label_exit_delay_seconds=2,
        )
        future_trades = [
            {"timestamp": 101 + index, "price": 1.0 + (index * 0.001)}
            for index in range(250)
        ]

        with patch.object(
            builder,
            "_first_trade_at_or_after",
            side_effect=AssertionError("linear delayed exit lookup should not be used"),
        ):
            label = builder._calculate_live_execution_label(
                future_trades,
                sample_time=100,
                future_window=300,
                current_price=1.0,
                fee_rate=0.0,
                slippage_rate=0.0,
            )

        self.assertEqual(label["live_entry_available"], 1)
        self.assertGreater(label["live_executable_return_pct"], 0.0)

    def test_generate_samples_passes_indexed_trade_windows_to_sample_builder(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            future_windows=[5],
        )
        lifecycle = {
            "token_address": "0xwindow",
            "symbol": "WIN",
            "create_timestamp": 100,
            "last_update": 200,
            "buys": [
                {"timestamp": 101, "price": 1.0, "account": "a"},
                {"timestamp": 102, "price": 1.1, "account": "b"},
                {"timestamp": 106, "price": 1.5, "account": "c"},
            ],
            "sells": [
                {"timestamp": 103, "price": 1.2, "account": "s1"},
                {"timestamp": 107, "price": 1.4, "account": "s2"},
            ],
            "unique_buyers": [],
            "unique_sellers": [],
        }
        sample = {"features": {}, "label": {}, "meta": {}}

        with patch.object(builder, "_create_sample_with_window", return_value=sample) as mock_create:
            samples = builder._generate_samples_from_lifecycle(lifecycle, sample_intervals=[2])

        self.assertEqual(samples, [sample])
        kwargs = mock_create.call_args.kwargs
        self.assertEqual([trade["timestamp"] for trade in kwargs["past_buys"]], [101, 102])
        self.assertEqual([trade["timestamp"] for trade in kwargs["past_sells"]], [])
        self.assertEqual([trade["timestamp"] for trade in kwargs["future_trades_sorted"]], [103, 106, 107])

    def test_sample_meta_records_decision_time_flow_event_counts(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            min_entry_unique_buyers=1,
            min_entry_buy_count=1,
        )
        lifecycle = {
            "token_address": "0xflowmeta",
            "symbol": "FLOWMETA",
            "create_timestamp": 100,
            "buys": [],
            "sells": [],
        }
        past_buys = [
            {"timestamp": 115, "price": 1.0, "account": "a", "bnb_amount": 1.0},
            {"timestamp": 130, "price": 1.1, "account": "b", "bnb_amount": 1.0},
            {"timestamp": 145, "price": 1.2, "account": "c", "bnb_amount": 1.0},
        ]
        past_sells = [
            {"timestamp": 125, "price": 1.0, "account": "s1", "bnb_amount": 0.2},
            {"timestamp": 148, "price": 1.1, "account": "s2", "bnb_amount": 0.2},
        ]

        with patch.object(builder, "_extract_features", return_value={"current_price": 1.2}):
            with patch.object(builder, "_calculate_label_with_window", return_value={"ok": True}):
                sample = builder._create_sample_with_window(
                    lifecycle,
                    sample_time=150,
                    future_window=60,
                    past_buys=past_buys,
                    past_sells=past_sells,
                )

        self.assertEqual(sample["meta"]["flow_event_count_10s"], 2)
        self.assertEqual(sample["meta"]["flow_event_count_30s"], 4)
        self.assertEqual(sample["meta"]["flow_event_count_60s"], 5)

    def test_get_stats_uses_max_return_when_legacy_fields_missing(self):
        self.builder.samples = [
            {"label": {"max_return_pct": -10.0}},
            {"label": {"max_return_pct": 20.0}},
            {"label": {"max_return_pct": 120.0}},
        ]

        stats = self.builder.get_stats()

        self.assertEqual(stats["total_samples"], 3)
        self.assertEqual(stats["profitable_samples"], 2)
        self.assertAlmostEqual(stats["profitable_ratio"], 2 / 3)
        self.assertEqual(stats["return_class_distribution"][0], 1)
        self.assertEqual(stats["return_class_distribution"][1], 1)
        self.assertEqual(stats["return_class_distribution"][3], 1)

    def test_get_stats_prefers_executable_return_when_present(self):
        self.builder.samples = [
            {"label": {"max_return_pct": 120.0, "executable_return_pct": -10.0}},
            {"label": {"max_return_pct": -20.0, "executable_return_pct": 20.0}},
        ]

        stats = self.builder.get_stats()

        self.assertEqual(stats["total_samples"], 2)
        self.assertEqual(stats["profitable_samples"], 1)
        self.assertAlmostEqual(stats["profitable_ratio"], 0.5)
        self.assertEqual(stats["return_class_distribution"][0], 1)
        self.assertEqual(stats["return_class_distribution"][1], 1)
        self.assertEqual(stats["return_class_distribution"][3], 0)


if __name__ == "__main__":
    unittest.main()
