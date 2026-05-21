import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_conditional_exit_feasibility.py"
    spec = importlib.util.spec_from_file_location("probe_conditional_exit_feasibility", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _output_root(cli):
    root = cli._allowed_output_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestConditionalExitFeasibilityProbeCli(unittest.TestCase):
    def test_parse_args_defaults_to_research_outputs(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(
            args.live_attribution,
            "docs/research/20260521-conditional-exit-flow-state/live_attribution.json",
        )
        self.assertTrue(args.dead_flow_support_report.endswith("dead-flow-support.json"))
        self.assertTrue(args.output_json.endswith("10-exit-state-attribution.json"))
        self.assertTrue(args.output_md.endswith("11-exit-state-attribution.md"))

    def test_main_writes_json_and_markdown_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            live_path = Path(tmpdir) / "live.json"
            train_path = Path(tmpdir) / "train.json"
            validation_path = Path(tmpdir) / "validation.json"
            final_path = Path(tmpdir) / "final.json"
            dead_flow_path = Path(tmpdir) / "dead-flow.json"
            live_path.write_text(
                json.dumps(
                    {
                        "active_model": "data/models/20260519_v95_v84_selective_nearmiss_gate",
                        "failure_label_counts": {
                            "dead_flow_timeout": 7,
                            "entry_slippage_failure": 2,
                            "mfe_then_giveback": 3,
                            "profitable_exit": 2,
                            "stop_first_after_entry": 1,
                            "unprofitable_other": 3,
                        },
                        "reason_counts": {
                            "ENTRY_SLIPPAGE_PROTECTION": 2,
                            "PPO_SELL100": 5,
                            "STOP_LOSS": 4,
                            "TIME_EXIT": 7,
                        },
                        "trade_count": 18,
                        "win_count": 2,
                        "loss_count": 16,
                        "trades": [
                            {"symbol": "CMC", "failure_label": "mfe_then_giveback", "near_threshold_like": False, "entry_anchor": {"time_to_plus_25_seconds": 17.0}},
                            {"symbol": "AUCA", "failure_label": "mfe_then_giveback", "near_threshold_like": False, "entry_anchor": {"time_to_plus_25_seconds": 18.0}},
                            {"symbol": "币安队长", "failure_label": "dead_flow_timeout", "near_threshold_like": True, "entry_anchor": {"time_to_plus_25_seconds": None}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            train_path.write_text(json.dumps({"class_counts": {"post_target_collapse": 5}}), encoding="utf-8")
            validation_path.write_text(json.dumps({"class_counts": {"post_target_collapse": 0}}), encoding="utf-8")
            final_path.write_text(json.dumps({"class_counts": {"post_target_collapse": 4}}), encoding="utf-8")
            dead_flow_path.write_text(
                json.dumps(
                    {
                        "support_gate": {
                            "status": "NO_GO_FOR_DEAD_FLOW_RULE",
                            "train_positives": 3,
                            "validation_positives": 1,
                            "final_positives": 3,
                            "live_positives": 1,
                            "passes_support_gate": False,
                            "reason": "validation support below gate",
                        },
                        "live_recall": {
                            "dead_flow_label_count": 1,
                            "matched_dead_flow_count": 1,
                            "passes_live_recall_gate": False,
                        },
                    }
                ),
                encoding="utf-8",
            )

            with tempfile.TemporaryDirectory(dir=_output_root(cli)) as output_tmpdir:
                output_json = Path(output_tmpdir) / "out.json"
                output_md = Path(output_tmpdir) / "out.md"
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = cli.main(
                        [
                            "--live-attribution",
                            str(live_path),
                            "--train-post-target-report",
                            str(train_path),
                            "--validation-post-target-report",
                            str(validation_path),
                            "--final-post-target-report",
                            str(final_path),
                            "--dead-flow-support-report",
                            str(dead_flow_path),
                            "--output-json",
                            str(output_json),
                            "--output-md",
                            str(output_md),
                        ]
                    )

                self.assertEqual(result, 0)
                self.assertTrue(output_json.exists())
                self.assertTrue(output_md.exists())
                report = json.loads(output_json.read_text(encoding="utf-8"))
                self.assertEqual(report["go_no_go"]["status"], "NO_GO_FOR_LIVE_RULE")
                dead_flow = {row["bucket"]: row for row in report["candidate_bucket_checks"]}["dead_flow_timeout"]
                self.assertEqual(dead_flow["validation_positives"], 1)
                self.assertIn("wrote", stdout.getvalue())

    def test_main_refuses_output_outside_research_dir(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            live_path = Path(tmpdir) / "live.json"
            train_path = Path(tmpdir) / "train.json"
            validation_path = Path(tmpdir) / "validation.json"
            final_path = Path(tmpdir) / "final.json"
            live_path.write_text(json.dumps({"active_model": "x", "trades": [], "failure_label_counts": {}, "reason_counts": {}, "trade_count": 0, "win_count": 0, "loss_count": 0}), encoding="utf-8")
            train_path.write_text(json.dumps({"class_counts": {}}), encoding="utf-8")
            validation_path.write_text(json.dumps({"class_counts": {}}), encoding="utf-8")
            final_path.write_text(json.dumps({"class_counts": {}}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--live-attribution",
                        str(live_path),
                        "--train-post-target-report",
                        str(train_path),
                        "--validation-post-target-report",
                        str(validation_path),
                        "--final-post-target-report",
                        str(final_path),
                        "--output-json",
                        str(Path(tmpdir) / "out.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
