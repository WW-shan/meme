import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_action_policy_reward_lcb.py"
    spec = importlib.util.spec_from_file_location("probe_action_policy_reward_lcb", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestActionPolicyRewardLcbProbeCli(unittest.TestCase):
    def test_main_writes_lcb_report_under_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            input_path = Path(tmpdir) / "reward.json"
            output_path = Path(tmpdir) / "lcb.json"
            input_path.write_text(
                json.dumps(
                    {
                        "decision": "shadow_reward_positive_replay_required",
                        "validation": {
                            "selected_rewards": [
                                {"symbol": "REJ_VALID", "source_family": "rejected", "replay_reward_pct": 25.0},
                                {"symbol": "ACC_VALID", "source_family": "accepted", "replay_reward_pct": 60.0},
                            ]
                        },
                        "final": {
                            "selected_rewards": [
                                {"symbol": "REJ_FINAL", "source_family": "rejected", "replay_reward_pct": 20.0},
                                {"symbol": "ACC_FINAL", "source_family": "accepted", "replay_reward_pct": 50.0},
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--reward-report",
                        str(input_path),
                        "--output",
                        str(output_path),
                        "--bootstrap-samples",
                        "100",
                        "--confidence-level",
                        "0.9",
                        "--force",
                    ]
                )

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(report["probe_contract"]["read_only"])
            self.assertEqual(report["inputs"]["reward_report"], str(input_path))
            self.assertEqual(report["decision"], "shadow_reward_positive_lcb_replay_required")
            self.assertIn("decision=shadow_reward_positive_lcb_replay_required", stdout.getvalue())

    def test_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "reward.json"
            output_path = Path(tmpdir) / "lcb.json"
            input_path.write_text(json.dumps({"validation": {}, "final": {}}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--reward-report",
                        str(input_path),
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
