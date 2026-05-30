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


if __name__ == "__main__":
    unittest.main()
