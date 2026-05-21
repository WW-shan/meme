import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_support_action_policy_pool.py"
    spec = importlib.util.spec_from_file_location("probe_support_action_policy_pool", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSupportActionPolicyPoolCli(unittest.TestCase):
    def test_main_writes_pooled_report_from_multiple_inputs(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            first = Path(tmpdir) / "first.json"
            second = Path(tmpdir) / "second.json"
            output = Path(tmpdir) / "pooled.json"
            first.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            second.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(first),
                        "--time-to-barrier-report",
                        str(second),
                        "--output",
                        str(output),
                        "--min-pooled-selected",
                        "30",
                        "--min-pooled-positive",
                        "12",
                    ]
                )

            self.assertEqual(result, 0)
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["inputs"]["time_to_barrier_reports"], [str(first), str(second)])
            self.assertFalse(saved["probe_contract"]["live_switch_evidence"])
            self.assertIn("decision=", stdout.getvalue())

    def test_main_refuses_duplicate_input_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            path = Path(tmpdir) / "time.json"
            path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            output = Path(tmpdir) / "pooled.json"
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(path),
                        "--time-to-barrier-report",
                        str(path),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("duplicate", stderr.getvalue())

    def test_main_refuses_to_overwrite_any_input_report_with_force(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            first = Path(tmpdir) / "first.json"
            second = Path(tmpdir) / "second.json"
            first.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            original_second = json.dumps({"candidate_sample": [{"symbol": "KEEP"}]})
            second.write_text(original_second, encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(first),
                        "--time-to-barrier-report",
                        str(second),
                        "--output",
                        str(second),
                        "--force",
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("overwrite input report", stderr.getvalue())
            self.assertEqual(second.read_text(encoding="utf-8"), original_second)

    def test_main_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "first.json"
            second = Path(tmpdir) / "second.json"
            first.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            second.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(first),
                        "--time-to-barrier-report",
                        str(second),
                        "--output",
                        str(Path(tmpdir) / "out.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
