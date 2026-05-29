import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_replay_uncertainty_gate.py"
    spec = importlib.util.spec_from_file_location("probe_replay_uncertainty_gate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _delta_block():
    return {
        "delta_summary": {
            "baseline": {"trade_count": 4, "return_pct_sum": 0.0},
            "candidate": {"trade_count": 4, "return_pct_sum": 10.0},
            "common_trades": {"trade_count": 4, "return_delta_pct_sum": 10.0},
            "added_candidate_trades": {"trade_count": 0, "return_pct_sum": 0.0},
            "removed_baseline_trades": {"trade_count": 0, "return_pct_sum": 0.0},
        },
        "common_trade_deltas": [
            {"token": "a", "entry_signal_time": 1, "return_delta_pct": 4.0},
            {"token": "b", "entry_signal_time": 2, "return_delta_pct": 3.0},
            {"token": "c", "entry_signal_time": 3, "return_delta_pct": 2.0},
            {"token": "d", "entry_signal_time": 4, "return_delta_pct": 1.0},
        ],
        "added_candidate_trades": [],
        "removed_baseline_trades": [],
    }


class TestReplayUncertaintyGateProbeCli(unittest.TestCase):
    def test_main_writes_report_under_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / "data" / "replay_reports") as tmpdir:
            base = Path(tmpdir)
            source = base / "source.json"
            output = base / "uncertainty.json"
            source.write_text(
                json.dumps(
                    {
                        "selected_trade_delta_attribution": {
                            "validation": _delta_block(),
                            "final": _delta_block(),
                        },
                        "best_validation_candidate": {"passes_acceptance_gate": True, "gate_details": {}},
                        "final_confirmation": {"passes_acceptance_gate": True, "gate_details": {}},
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--report",
                        str(source),
                        "--candidate-id",
                        "unit_cli",
                        "--output",
                        str(output),
                        "--bootstrap-samples",
                        "100",
                        "--min-split-contributions",
                        "0",
                    ]
                )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(report["candidate_id"], "unit_cli")
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertIn("outcome_tier=", stdout.getvalue())

    def test_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.json"
            source.write_text(
                json.dumps({"selected_trade_delta_attribution": {"validation": _delta_block(), "final": _delta_block()}}),
                encoding="utf-8",
            )
            result = cli.main(
                [
                    "--report",
                    str(source),
                    "--output",
                    str(Path(tmpdir) / "out.json"),
                ]
            )

        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
