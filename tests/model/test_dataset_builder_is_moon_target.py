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

    def test_is_moon_stays_zero_below_200pct(self):
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
        self.assertEqual(label["is_moon"], 0)

    def test_is_moon_becomes_one_at_200pct(self):
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
        self.assertEqual(label["is_moon"], 1)

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


if __name__ == "__main__":
    unittest.main()
