import importlib.util
import tempfile
import unittest
from pathlib import Path


def load_cli_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_signal_freshness_shadow.py"
    spec = importlib.util.spec_from_file_location("probe_signal_freshness_shadow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SignalFreshnessShadowProbeCliTest(unittest.TestCase):
    def test_refuses_output_outside_replay_reports(self):
        cli = load_cli_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit):
                cli._assert_output(str(Path(tmpdir) / "report.json"), force=True)

    def test_parse_args_defaults_to_rejected_and_queued_decisions(self):
        cli = load_cli_module()
        args = cli.parse_args(["--output-json", "data/replay_reports/x.json", "--output-md", "data/replay_reports/x.md"])
        self.assertIsNone(args.decision)
        self.assertEqual(args.min_candidates, 20)
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertFalse(args.split_stability)
        self.assertEqual(args.train_fraction, 0.6)
        self.assertEqual(args.validation_fraction, 0.2)

    def test_parse_args_accepts_split_stability(self):
        cli = load_cli_module()
        args = cli.parse_args([
            "--output-json", "data/replay_reports/x.json",
            "--output-md", "data/replay_reports/x.md",
            "--split-stability",
            "--min-split-candidates", "4",
            "--min-split-selected", "2",
        ])
        self.assertTrue(args.split_stability)
        self.assertEqual(args.min_split_candidates, 4)
        self.assertEqual(args.min_split_selected, 2)


if __name__ == "__main__":
    unittest.main()
