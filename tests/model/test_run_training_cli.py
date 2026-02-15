import unittest
from pathlib import Path
import importlib.util


def _load_worktree_run_training():
    run_path = Path(__file__).resolve().parents[2] / "run_training.py"
    spec = importlib.util.spec_from_file_location("worktree_run_training", run_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


run_training = _load_worktree_run_training()


class TestRunTrainingCli(unittest.TestCase):
    def test_parse_args_profile_and_gate(self):
        args = run_training.parse_args(["--profile", "balanced", "--no-gate", "--dataset-ts", "20260215_120000"])
        self.assertEqual(args.profile, "balanced")
        self.assertFalse(args.gate)
        self.assertEqual(args.dataset_ts, "20260215_120000")

    def test_defaults_enable_gate_and_time_aware_split(self):
        args = run_training.parse_args([])
        self.assertTrue(args.gate)
        self.assertTrue(args.time_aware_split)

    def test_chdir_to_script_directory(self):
        expected = str(Path(__file__).resolve().parents[2])
        self.assertEqual(run_training.SCRIPT_DIR, expected)


if __name__ == "__main__":
    unittest.main()
