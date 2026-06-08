import json
import unittest
from pathlib import Path

from scripts import probe_execution_freshness_abstention as cli
from src.pipeline import execution_freshness_abstention_probe as p


def _open(symbol, index, lag, net, *, source="lifecycle", fast=True, fill_lag=1.0):
    return {
        "action": "OPEN",
        "token": f"0x{index:040x}",
        "symbol": symbol,
        "entry_signal_time": f"2026-05-30 00:{index:02d}:00",
        "time": f"2026-05-30 00:{index:02d}:02",
        "is_real_trade": True,
        "prob": 0.98,
        "pred_return": 40.0,
        "token_status_source": source,
        "buy_fast_status_used": fast,
        "lifecycle_status_chain_lag_seconds": lag,
        "lifecycle_status_staleness_seconds": 0.01,
        "entry_fill_lag_seconds": fill_lag,
    }, {
        "action": "CLOSE",
        "token": f"0x{index:040x}",
        "symbol": symbol,
        "time": f"2026-05-30 00:{index:02d}:40",
        "reason": "TIME_EXIT" if net <= 0 else "TRAILING_STOP",
        "net_profit": net,
        "return_pct": net,
        "is_real_trade": True,
    }


def _rows(entries):
    rows = []
    for entry in entries:
        if isinstance(entry, dict):
            rows.extend(_open(**entry))
        else:
            rows.extend(_open(*entry))
    return rows


class TestExecutionFreshnessAbstentionProbe(unittest.TestCase):
    def test_selects_chain_lag_rule_from_train_and_validates_on_later_splits(self):
        rows = _rows(
            [
                ("T1", 1, 0.2, 0.001),
                ("T2", 2, 2.0, -0.004),
                ("T3", 3, 2.2, -0.003),
                ("T4", 4, 2.4, -0.002),
                ("T5", 5, 0.1, 0.001),
                ("T6", 6, 1.9, -0.001),
                ("V1", 7, 2.1, -0.002),
                ("V2", 8, 0.2, 0.001),
                ("F1", 9, 2.3, -0.002),
                ("F2", 10, 0.2, 0.0005),
            ]
        )

        report = p.build_execution_freshness_abstention_report(
            trade_rows=rows,
            train_fraction=0.60,
            validation_fraction=0.20,
            min_train_selected=3,
            min_train_loss_precision=1.0,
            max_train_winner_count=0,
            max_validation_winner_count=0,
            max_final_winner_count=1,
            generated_at=None,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        selected = report["selected_candidate"]
        self.assertTrue(selected["passes_research_alpha_proxy_gate"])
        self.assertEqual(selected["rule"]["type"], "numeric_gte")
        self.assertEqual(selected["rule"]["field"], "lifecycle_status_chain_lag_seconds")
        self.assertGreater(selected["validation"]["abstention_delta_bnb"], 0.0)
        self.assertGreaterEqual(selected["final"]["abstention_delta_bnb"], 0.0)
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])

    def test_can_emit_selected_trade_delta_attribution(self):
        rows = _rows(
            [
                ("T1", 1, 0.2, 0.001),
                ("T2", 2, 2.0, -0.004),
                ("T3", 3, 2.2, -0.003),
                ("T4", 4, 2.4, -0.002),
                ("T5", 5, 0.1, 0.001),
                ("T6", 6, 1.9, -0.001),
                ("V1", 7, 2.1, -0.002),
                ("V2", 8, 0.2, 0.001),
                ("F1", 9, 2.3, -0.002),
                ("F2", 10, 0.2, 0.0005),
            ]
        )

        report = p.build_execution_freshness_abstention_report(
            trade_rows=rows,
            train_fraction=0.60,
            validation_fraction=0.20,
            min_train_selected=3,
            min_train_loss_precision=1.0,
            max_train_winner_count=0,
            max_validation_winner_count=0,
            max_final_winner_count=1,
            include_trade_delta_attribution=True,
        )

        attribution = report["selected_trade_delta_attribution"]
        self.assertEqual(set(attribution), {"validation", "final"})
        self.assertEqual(attribution["validation"]["candidate_rule"]["field"], "lifecycle_status_chain_lag_seconds")
        self.assertEqual(
            attribution["validation"]["delta_summary"]["removed_baseline_trades"]["trade_count"],
            1,
        )
        self.assertEqual(
            attribution["validation"]["removed_baseline_trades"][0]["token"],
            "0x0000000000000000000000000000000000000007",
        )
        self.assertEqual(
            attribution["validation"]["delta_summary"]["candidate"]["trade_count"],
            1,
        )

    def test_diagnostic_fill_lag_is_not_scanned_as_policy_field(self):
        rows = _rows(
            [
                {"symbol": "T1", "index": 1, "lag": 1.0, "net": 0.001, "fill_lag": 1.0},
                {"symbol": "T2", "index": 2, "lag": 1.0, "net": -0.004, "fill_lag": 10.0},
                {"symbol": "T3", "index": 3, "lag": 1.0, "net": -0.003, "fill_lag": 11.0},
                {"symbol": "T4", "index": 4, "lag": 1.0, "net": -0.002, "fill_lag": 12.0},
                {"symbol": "T5", "index": 5, "lag": 1.0, "net": 0.001, "fill_lag": 1.0},
            ]
        )

        report = p.build_execution_freshness_abstention_report(
            trade_rows=rows,
            min_train_selected=2,
            min_train_loss_precision=1.0,
        )

        scanned_labels = json.dumps([row["rule"] for row in report["train_top_rules"]], ensure_ascii=False)
        self.assertNotIn("entry_fill_lag_seconds", scanned_labels)
        self.assertIn("entry_fill_lag_seconds", report["probe_contract"]["diagnostic_only_fields"])
        self.assertEqual(report["outcome_tier"], "Rejected")

    def test_signal_context_latency_volatility_risk_can_be_policy_field(self):
        rows = _rows(
            [
                ("T1", 1, 4.0, 0.001),
                ("T2", 2, 4.0, -0.004),
                ("T3", 3, 4.0, -0.003),
                ("T4", 4, 4.0, -0.002),
                ("T5", 5, 0.1, 0.001),
                ("T6", 6, 4.0, -0.001),
                ("V1", 7, 4.0, -0.002),
                ("V2", 8, 4.0, 0.001),
                ("F1", 9, 4.0, -0.002),
                ("F2", 10, 4.0, 0.0005),
            ]
        )
        signal_rows = []
        high_vol_indexes = {2, 3, 4, 6, 7, 9}
        for index in range(1, 11):
            signal_rows.append({
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "token": f"0x{index:040x}",
                "symbol": f"T{index}",
                "time": f"2026-05-30 00:{index:02d}:00",
                "price_volatility": 0.50 if index in high_vol_indexes else 0.05,
                "volume_30s": 2.0,
            })

        report = p.build_execution_freshness_abstention_report(
            trade_rows=rows,
            signal_rows=signal_rows,
            train_fraction=0.60,
            validation_fraction=0.20,
            min_train_selected=3,
            min_train_loss_precision=1.0,
            max_train_winner_count=0,
            max_validation_winner_count=0,
            max_final_winner_count=0,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        selected = report["selected_candidate"]
        self.assertTrue(selected["passes_research_alpha_proxy_gate"])
        self.assertEqual(selected["rule"]["field"], "freshness_latency_volatility_risk")
        self.assertGreater(selected["validation"]["abstention_delta_bnb"], 0.0)
        self.assertEqual(
            selected["train"]["selected_sample"][0]["freshness_latency_volatility_risk"],
            1.0,
        )

    def test_signal_context_only_policy_can_use_signal_chain_lag_for_volume_risk(self):
        rows = _rows(
            [
                ("T1", 1, 0.1, 0.001),
                ("T2", 2, 0.1, -0.004),
                ("T3", 3, 0.1, -0.003),
                ("T4", 4, 0.1, -0.002),
                ("T5", 5, 0.1, 0.001),
                ("T6", 6, 0.1, -0.001),
                ("V1", 7, 0.1, -0.002),
                ("V2", 8, 0.1, 0.001),
                ("F1", 9, 0.1, -0.002),
                ("F2", 10, 0.1, 0.0005),
            ]
        )
        high_volume_indexes = {2, 3, 4, 6, 7, 9}
        signal_rows = []
        for index in range(1, 11):
            signal_rows.append({
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "token": f"0x{index:040x}",
                "symbol": f"T{index}",
                "time": f"2026-05-30 00:{index:02d}:00",
                "lifecycle_status_chain_lag_seconds": 9.0,
                "lifecycle_status_staleness_seconds": 0.02,
                "price_volatility": 0.50,
                "volume_30s": 2.0 if index in high_volume_indexes else 0.01,
            })

        report = p.build_execution_freshness_abstention_report(
            trade_rows=rows,
            signal_rows=signal_rows,
            train_fraction=0.60,
            validation_fraction=0.20,
            min_train_selected=3,
            min_train_loss_precision=1.0,
            max_train_winner_count=0,
            max_validation_winner_count=0,
            max_final_winner_count=0,
            signal_context_policy_source="signal_context",
            policy_field_scope="signal_context_only",
            include_trade_delta_attribution=True,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["parameters"]["signal_context_policy_source"], "signal_context")
        self.assertEqual(report["parameters"]["policy_field_scope"], "signal_context_only")
        selected = report["selected_candidate"]
        self.assertEqual(selected["rule"]["field"], "freshness_latency_volume_risk")
        self.assertAlmostEqual(
            selected["train"]["selected_sample"][0]["freshness_latency_volume_risk"],
            3.0 * 0.50 * 1.0986122886681098,
        )
        self.assertNotIn("token_status_source", report["policy_fields"]["categorical"])
        validation_delta = report["selected_trade_delta_attribution"]["validation"]
        coverage = validation_delta["policy_feature_coverage"]["removed_baseline_trades"]
        by_field = {row["field"]: row for row in coverage["fields"]}
        self.assertEqual(coverage["matched_trade_count"], 1)
        self.assertEqual(by_field["lifecycle_status_chain_lag_seconds"]["status"], "available")
        self.assertEqual(by_field["freshness_latency_volume_risk"]["status"], "available")
        self.assertAlmostEqual(
            validation_delta["removed_baseline_trades"][0]["policy_context_features"]["freshness_latency_volume_risk"],
            3.0 * 0.50 * 1.0986122886681098,
        )

    def test_cli_writes_replay_report_and_refuses_non_replay_output(self):
        input_path = Path("data/replay_reports/test_execution_freshness_cli_input.jsonl")
        signal_path = Path("data/replay_reports/test_execution_freshness_cli_signal.jsonl")
        output_path = Path("data/replay_reports/test_execution_freshness_cli_output.json")
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text(
            "\n".join(json.dumps(row) for row in _rows([
                ("T1", 1, 0.2, 0.001),
                ("T2", 2, 2.0, -0.004),
                ("T3", 3, 2.2, -0.003),
                ("T4", 4, 2.4, -0.002),
                ("T5", 5, 0.1, 0.001),
                ("T6", 6, 1.9, -0.001),
                ("V1", 7, 2.1, -0.002),
                ("V2", 8, 0.2, 0.001),
                ("F1", 9, 2.3, -0.002),
                ("F2", 10, 0.2, 0.0005),
            ]))
            + "\n",
            encoding="utf-8",
        )
        signal_path.write_text("", encoding="utf-8")
        try:
            rc = cli.main([
                "--paper-trades",
                str(input_path),
                "--signal-audit",
                str(signal_path),
                "--output",
                str(output_path),
                "--force",
                "--min-train-loss-precision",
                "1.0",
                "--max-train-winner-count",
                "0",
                "--write-selected-trade-delta",
            ])
            self.assertEqual(rc, 0)
            out = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(out["outcome_tier"], "Research Alpha")
            self.assertIn("selected_trade_delta_attribution", out)

            rejected_rc = cli.main([
                "--paper-trades",
                str(input_path),
                "--signal-audit",
                str(signal_path),
                "--output",
                "docs/research/bad.json",
            ])
            self.assertEqual(rejected_rc, 2)
        finally:
            input_path.unlink(missing_ok=True)
            signal_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
