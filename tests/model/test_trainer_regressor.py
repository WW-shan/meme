import unittest
import tempfile
import pandas as pd
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


class TestTrainerRegressor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.trainer = MemeModelTrainer(data_dir=self.tmp.name, model_dir=self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_train_optional_regressor_skips_when_target_missing(self):
        train_df = pd.DataFrame({"f1": [1, 2], "is_moon": [0, 1]})
        val_df = pd.DataFrame({"f1": [3], "is_moon": [1]})
        test_df = pd.DataFrame({"f1": [4], "is_moon": [0]})

        out = self.trainer._train_optional_regressor(
            train_df=train_df,
            val_df=val_df,
            test_df=test_df,
            feature_cols=["f1"],
            save_dir=None,
            reg_params=None,
        )

        self.assertEqual(out["status"], "skipped")
        self.assertIn("reason", out)


if __name__ == "__main__":
    unittest.main()
