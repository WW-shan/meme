import tempfile
import unittest
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
