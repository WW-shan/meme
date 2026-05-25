import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_flow_abstention_feature_scan.py"
    spec = importlib.util.spec_from_file_location("probe_flow_abstention_feature_scan", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestFlowAbstentionFeatureScanCli(unittest.TestCase):
    def test_main_writes_read_only_report(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "scan.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {"symbol": "BAD", "barrier_class": "flat_timeout", "flow_sell_pressure_30s": 1.0},
                            {"symbol": "GOOD", "barrier_class": "fast_profit", "flow_sell_pressure_30s": 0.0},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--input-report",
                        str(input_path),
                        "--output",
                        str(output_path),
                        "--min-selected",
                        "1",
                    ]
                )

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(report["probe_contract"]["read_only"])
            self.assertEqual(report["inputs"]["input_reports"], [str(input_path)])
            self.assertIn("eligible_rules=", stdout.getvalue())

    def test_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--input-report",
                        str(input_path),
                        "--output",
                        str(Path(tmpdir) / "scan.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
