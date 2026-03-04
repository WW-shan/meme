import unittest
from pathlib import Path
import importlib.util


def _load_worktree_run_training():
    run_path = Path(__file__).resolve().parents[2] / "scripts" / "run_full_training.py"
    spec = importlib.util.spec_from_file_location("worktree_run_training", run_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


run_training = _load_worktree_run_training()


class TestRunTrainingCli(unittest.TestCase):
    def test_parse_profile_env_uses_default_when_unset(self):
        profiles = run_training._parse_profile_env("precision_strict,precision_robust,precision_core")
        self.assertEqual(profiles, "precision_strict,precision_robust,precision_core")

    def test_parse_bool_env_honors_values(self):
        self.assertTrue(run_training._parse_bool_env("MISSING_BOOL_ENV", True))
        self.assertFalse(run_training._parse_bool_env("MISSING_BOOL_ENV", False))

    def test_project_root_points_to_repository_root(self):
        expected = str(Path(__file__).resolve().parents[2])
        self.assertEqual(str(run_training.PROJECT_ROOT), expected)


if __name__ == "__main__":
    unittest.main()
