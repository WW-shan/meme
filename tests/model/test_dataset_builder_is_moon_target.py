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


if __name__ == "__main__":
    unittest.main()
