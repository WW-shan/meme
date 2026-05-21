import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_support_action_policy.py"
    spec = importlib.util.spec_from_file_location("probe_support_action_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSupportActionPolicyProbeCli(unittest.TestCase):
    def test_parse_args_defaults_to_live_feature_report_input(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(
            args.time_to_barrier_report,
            "data/replay_reports/time_to_barrier_probe_20260521_post_commit_live_features.json",
        )
        self.assertTrue(args.output.startswith("data/replay_reports/support_action_policy_probe_"))
        self.assertTrue(args.output.endswith(".json"))
        self.assertEqual(args.min_selected, 3)

    def test_main_writes_read_only_report_with_input_path(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            input_path = Path(tmpdir) / "time.json"
            output_path = Path(tmpdir) / "out.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "A",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.99,
                                "pred_return": 10.0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
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
            self.assertFalse(report["probe_contract"]["live_switch_evidence"])
            self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
            self.assertEqual(report["inputs"]["time_to_barrier_report"], str(input_path))
            self.assertIn("wrote", stdout.getvalue())
            self.assertIn("eligible_rules=", stdout.getvalue())

    def test_main_refuses_to_overwrite_input_or_existing_output_without_force(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            input_path = Path(tmpdir) / "time.json"
            output_path = Path(tmpdir) / "out.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            output_path.write_text("existing", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                same_path = cli.main(["--time-to-barrier-report", str(input_path), "--output", str(input_path)])
                existing_path = cli.main(["--time-to-barrier-report", str(input_path), "--output", str(output_path)])

            self.assertEqual(same_path, 2)
            self.assertEqual(existing_path, 2)
            self.assertIn("refusing", stderr.getvalue())
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")

    def test_main_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "time.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(input_path),
                        "--output",
                        str(Path(tmpdir) / "out.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
