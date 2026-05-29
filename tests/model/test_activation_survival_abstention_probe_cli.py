import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_activation_survival_abstention.py"
    spec = importlib.util.spec_from_file_location("probe_activation_survival_abstention", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestActivationSurvivalAbstentionProbeCli(unittest.TestCase):
    def test_main_writes_report_under_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / "data" / "replay_reports") as tmpdir:
            base = Path(tmpdir)
            train = base / "train.json"
            validation = base / "validation.json"
            final = base / "final.json"
            output = base / "out.json"
            train.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {"classification": "target_not_hit", "flow_sell_pressure_30s": 0.9, "mae_pct": -3.0},
                            {"classification": "target_not_hit", "flow_sell_pressure_30s": 0.8, "mae_pct": -2.0},
                            {"classification": "post_target_continuation", "flow_sell_pressure_30s": 0.1, "mfe_pct": 80.0},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            validation.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {"classification": "target_not_hit", "flow_sell_pressure_30s": 0.85, "mae_pct": -1.0}
                        ]
                    }
                ),
                encoding="utf-8",
            )
            final.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {"classification": "target_not_hit", "flow_sell_pressure_30s": 0.86, "mae_pct": -1.0}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--train-report",
                        str(train),
                        "--validation-report",
                        str(validation),
                        "--final-report",
                        str(final),
                        "--output",
                        str(output),
                        "--min-train-selected",
                        "2",
                        "--min-train-bad-precision",
                        "1.0",
                        "--max-train-protected",
                        "0",
                        "--max-conditions",
                        "2",
                    ]
                )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertIn("outcome_tier=", stdout.getvalue())
        self.assertGreaterEqual(report["candidate_counts"]["train_eligible_rules"], 1)
        self.assertEqual(report["parameters"]["max_conditions"], 2)

    def test_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            path.write_text('{"candidate_sample":[]}', encoding="utf-8")
            result = cli.main(
                [
                    "--train-report",
                    str(path),
                    "--validation-report",
                    str(path),
                    "--final-report",
                    str(path),
                    "--output",
                    str(Path(tmpdir) / "out.json"),
                ]
            )

        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
