import json
import unittest
import tempfile
from pathlib import Path
import importlib.util


def _load_worktree_trainer():
    trainer_path = Path(__file__).resolve().parents[2] / "src" / "model" / "trainer.py"
    spec = importlib.util.spec_from_file_location("worktree_trainer", trainer_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.MemeModelTrainer


MemeModelTrainer = _load_worktree_trainer()


class TestTrainerDatasetSplit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name) / "datasets"
        self.model_dir = Path(self.tmp.name) / "models"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_jsonl(self, fp, rows):
        with fp.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def test_load_by_timestamp_and_time_split(self):
        ts = "20260215_120000"
        meta = {"feature_names": ["f1"], "label_names": ["is_moon"]}
        (self.data_dir / f"metadata_{ts}.json").write_text(json.dumps(meta), encoding="utf-8")

        rows = []
        for t in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            rows.append({
                "features": {"f1": t},
                "label": {"is_moon": 1 if t >= 8 else 0},
                "meta": {"sample_time": t, "token_address": f"0x{t}", "symbol": "X"},
            })

        self._write_jsonl(self.data_dir / f"train_{ts}.jsonl", rows[:6])
        self._write_jsonl(self.data_dir / f"val_{ts}.jsonl", rows[6:8])
        self._write_jsonl(self.data_dir / f"test_{ts}.jsonl", rows[8:])

        trainer = MemeModelTrainer(data_dir=str(self.data_dir), model_dir=str(self.model_dir))
        train_df, val_df, test_df, _ = trainer.load_dataset(
            dataset_timestamp=ts,
            time_aware_split=True,
            split_ratio=(0.7, 0.1, 0.2),
        )

        self.assertEqual(len(train_df), 7)
        self.assertEqual(len(val_df), 1)
        self.assertEqual(len(test_df), 2)
        self.assertLessEqual(train_df["sample_time"].max(), val_df["sample_time"].min())
        self.assertLessEqual(val_df["sample_time"].max(), test_df["sample_time"].min())


if __name__ == "__main__":
    unittest.main()
