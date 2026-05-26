import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.pipeline import added_trade_boundary_policy_probe as probe


def _row(token, return_pct, risk):
    return {
        "trade": {
            "token": token,
            "entry_signal_time": 100,
            "entry_time": 101,
            "return_pct": return_pct,
            "exit_reason": "TIME_EXIT" if return_pct > 0 else "STOP_LOSS",
        },
        "matched_sample_time": 100,
        "features": {"risk_score": risk, "unused_missing": None},
        "labels": {"bad_loss": return_pct < 0},
    }


def _wide_row(token, return_pct, risk):
    row = _row(token, return_pct, risk)
    for index in range(30):
        row["features"][f"risk_score_{index:02d}"] = risk
    return row


class TestAddedTradeBoundaryPolicyProbe(unittest.TestCase):
    def test_selects_validation_only_cost_sensitive_keep_rule_and_evaluates_final(self):
        validation_rows = [
            _row("0xwin1", 30.0, 0.10),
            _row("0xwin2", 20.0, 0.20),
            _row("0xloss1", -10.0, 0.80),
            _row("0xloss2", -12.0, 0.90),
        ]
        final_rows = [
            _row("0xfinalwin", 25.0, 0.15),
            _row("0xfinalloss", -15.0, 0.85),
        ]

        report = probe.build_added_trade_boundary_policy_report(
            validation_rows=validation_rows,
            final_rows=final_rows,
            loss_cost=3.0,
            min_keep_count=2,
            min_reject_count=1,
        )

        self.assertEqual(report["contract"]["live_switch_evidence"], False)
        self.assertEqual(report["decision"], "shadow_promote_to_replay")
        self.assertEqual(report["selected_rule"]["feature"], "risk_score")
        self.assertEqual(report["selected_rule"]["operator"], "<=")
        self.assertEqual(report["validation"]["kept"]["loss_count"], 0)
        self.assertGreater(report["validation"]["cost_adjusted_utility_delta"], 0.0)
        self.assertEqual(report["final"]["kept"]["trade_count"], 1)
        self.assertEqual(report["final"]["kept"]["loss_count"], 0)
        self.assertGreater(report["final"]["cost_adjusted_utility_delta"], 0.0)

    def test_rejects_when_no_validation_rule_passes_support(self):
        validation_rows = [
            _row("0xwin1", 20.0, 0.10),
            _row("0xloss1", -10.0, 0.90),
        ]

        report = probe.build_added_trade_boundary_policy_report(
            validation_rows=validation_rows,
            final_rows=[],
            min_keep_count=3,
            min_reject_count=1,
        )

        self.assertEqual(report["decision"], "reject_no_supported_rule")
        self.assertIsNone(report["selected_rule"])

    def test_supported_candidate_count_is_not_truncated_to_top_candidates(self):
        validation_rows = [
            _wide_row("0xwin1", 30.0, 0.10),
            _wide_row("0xwin2", 20.0, 0.20),
            _wide_row("0xloss1", -10.0, 0.80),
            _wide_row("0xloss2", -12.0, 0.90),
        ]

        report = probe.build_added_trade_boundary_policy_report(
            validation_rows=validation_rows,
            final_rows=[],
            loss_cost=3.0,
            min_keep_count=2,
            min_reject_count=1,
        )

        self.assertEqual(len(report["top_supported_candidates"]), 25)
        self.assertGreater(report["supported_candidate_count"], len(report["top_supported_candidates"]))

    def test_cli_writes_report_from_trade_delta_attribution(self):
        payload = {
            "selected_trade_delta_attribution": {
                "validation": {
                    "matched_feature_rows": {
                        "added_candidate_trades": [
                            _row("0xwin1", 30.0, 0.10),
                            _row("0xwin2", 20.0, 0.20),
                            _row("0xloss1", -10.0, 0.80),
                            _row("0xloss2", -12.0, 0.90),
                        ]
                    }
                },
                "final": {
                    "matched_feature_rows": {
                        "added_candidate_trades": [
                            _row("0xfinalwin", 25.0, 0.15),
                            _row("0xfinalloss", -15.0, 0.85),
                        ]
                    }
                },
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            input_path = tmpdir / "trade_delta.json"
            output_path = tmpdir / "probe.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/probe_added_trade_boundary_policy.py",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--loss-cost",
                    "3.0",
                    "--min-keep-count",
                    "2",
                    "--min-reject-count",
                    "1",
                ],
                check=False,
                cwd=Path(__file__).resolve().parents[2],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"], "shadow_promote_to_replay")
            self.assertIn("output=", result.stdout)


if __name__ == "__main__":
    unittest.main()
