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


class _FakeBooster:
    def save_model(self, path):
        Path(path).write_text('{"fake": true}', encoding="utf-8")


class _FakeModel:
    def get_booster(self):
        return _FakeBooster()


class TestTrainerArtifacts(unittest.TestCase):
    def test_save_classifier_artifacts_writes_json_and_pkl(self):
        with tempfile.TemporaryDirectory() as d:
            trainer = MemeModelTrainer(data_dir=d, model_dir=d)
            out = Path(d) / "models_foo"
            out.mkdir(parents=True, exist_ok=True)

            trainer._save_classifier_artifacts(_FakeModel(), out)

            self.assertTrue((out / "classifier_xgb.pkl").exists())
            self.assertTrue((out / "classifier_xgb.json").exists())


if __name__ == "__main__":
    unittest.main()
