import json
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_counterfactual_action_policy.py"
    spec = importlib.util.spec_from_file_location("probe_counterfactual_action_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCounterfactualActionProbeCli(unittest.TestCase):
    def _write_inputs(self, tmpdir: Path) -> tuple[Path, Path]:
        time_report = tmpdir / "time_to_barrier.json"
        post_report = tmpdir / "post_target.json"
        time_report.write_text(
            json.dumps(
                {
                    "probe_contract": {"read_only": True, "live_switch_evidence": False},
                    "candidate_sample": [
                        {
                            "token": "0xA",
                            "symbol": "Arnold",
                            "candidate_type": "rejected_signal_time_to_barrier",
                            "barrier_class": "fast_profit",
                            "recommended_policy": "quick_take_profit",
                            "prob": 0.9879,
                            "pred_return": 32.17,
                            "mfe_pct": 334.6,
                            "mae_pct": -9.7,
                            "time_to_plus_25_seconds": 56.9,
                        },
                        {
                            "token": "0xB",
                            "symbol": "MEMES",
                            "candidate_type": "rejected_signal_time_to_barrier",
                            "barrier_class": "stop_first",
                            "recommended_policy": "skip",
                            "prob": 0.987,
                            "pred_return": -34.0,
                            "mfe_pct": 89.0,
                            "mae_pct": -23.0,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        post_report.write_text(
            json.dumps(
                {
                    "probe_contract": {"read_only": True, "live_switch_evidence": False},
                    "candidate_sample": [
                        {
                            "token": "0xC",
                            "symbol": "CMC",
                            "candidate_type": "accepted_trade_post_target_exit_state",
                            "classification": "post_target_collapse",
                            "recommended_policy": "lock_profit",
                            "target_hit": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return time_report, post_report

    def test_writes_combined_report_under_replay_reports_and_prints_count(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            time_report, post_report = self._write_inputs(tmpdir)
            output = Path("data/replay_reports/counterfactual_action_probe_test.json")

            with unittest.mock.patch.object(cli, "ROOT", tmpdir):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(time_report),
                        "--post-target-report",
                        str(post_report),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            written_path = tmpdir / output
            self.assertTrue(written_path.is_file())
            self.assertTrue(written_path.resolve().is_relative_to((tmpdir / "data" / "replay_reports").resolve()))
            report = json.loads(written_path.read_text(encoding="utf-8"))
            self.assertEqual(len(report["actions"]), 3)
            self.assertFalse(report["probe_contract"]["safe_for_live_switch"])

    def test_prints_total_action_candidates_not_truncated_sample_count(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            time_report = tmpdir / "time_to_barrier.json"
            post_report = tmpdir / "post_target.json"
            time_report.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "token": f"0x{i}",
                                "symbol": f"T{i}",
                                "barrier_class": "flat_timeout",
                                "prob": 0.1,
                                "pred_return": 0.0,
                                "mfe_pct": 0.0,
                                "mae_pct": 0.0,
                            }
                            for i in range(205)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            post_report.write_text(json.dumps({"candidates": []}), encoding="utf-8")
            output = Path("data/replay_reports/counterfactual_action_probe_test.json")

            stdout = io.StringIO()
            with unittest.mock.patch.object(cli, "ROOT", tmpdir), redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(time_report),
                        "--post-target-report",
                        str(post_report),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            report = json.loads((tmpdir / output).read_text(encoding="utf-8"))
            self.assertEqual(len(report["actions"]), 200)
            self.assertIn("action_candidates=205", stdout.getvalue())

    def test_relative_output_is_rooted_to_project_root_not_current_working_directory(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as cwd_tmp:
            root = Path(root_tmp)
            cwd = Path(cwd_tmp)
            time_report, post_report = self._write_inputs(cwd)
            output = Path("data/replay_reports/counterfactual_action_probe_test.json")
            with patch.object(cli, "ROOT", root), patch("pathlib.Path.cwd", return_value=cwd):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(time_report),
                        "--post-target-report",
                        str(post_report),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertTrue((root / output).is_file())
            self.assertFalse((cwd / output).exists())

    def test_refuses_protected_output_paths(self):
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "probe_counterfactual_action_policy.py"
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            time_report, post_report = self._write_inputs(tmpdir)

            for protected in [".env", ".env.example", "docs/goals/live-model-optimization-goal.md", "outside.json"]:
                with self.subTest(protected=protected):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(script_path),
                            "--time-to-barrier-report",
                            str(time_report),
                            "--post-target-report",
                            str(post_report),
                            "--output",
                            protected,
                        ],
                        cwd=tmpdir,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("refusing output path", result.stderr)
                    self.assertFalse((tmpdir / protected).exists())

    def test_normalized_relative_text_preserves_dotfile_names_for_protected_check(self):
        cli = _load_cli()

        self.assertEqual(cli._normalized_relative_text(".env"), ".env")
        self.assertEqual(cli._normalized_relative_text("./.env.example"), ".env.example")

    def test_refuses_output_when_replay_reports_directory_is_symlink(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(root_tmp)
            outside = Path(outside_tmp)
            (root / "data").mkdir()
            (root / "data" / "replay_reports").symlink_to(outside, target_is_directory=True)

            with patch.object(cli, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    cli._validate_output_path("data/replay_reports/report.json")

    def test_refuses_traversal_output_paths_after_replay_reports_prefix(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as root_tmp:
            root = Path(root_tmp)
            (root / "data" / "replay_reports").mkdir(parents=True)

            with patch.object(cli, "ROOT", root):
                for output in [
                    "data/replay_reports/../../.env",
                    "data/replay_reports/../outside/report.json",
                ]:
                    with self.subTest(output=output):
                        with self.assertRaisesRegex(ValueError, "refusing output path"):
                            cli._validate_output_path(output)

    def test_refuses_nested_symlink_escape_under_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as root_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(root_tmp)
            outside = Path(outside_tmp)
            replay_root = root / "data" / "replay_reports"
            replay_root.mkdir(parents=True)
            (replay_root / "outside_link").symlink_to(outside, target_is_directory=True)

            with patch.object(cli, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "refusing output path"):
                    cli._validate_output_path("data/replay_reports/outside_link/report.json")


if __name__ == "__main__":
    unittest.main()
