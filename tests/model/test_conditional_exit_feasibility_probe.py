import json
import unittest

from src.pipeline import conditional_exit_feasibility_probe as p


class TestConditionalExitFeasibilityProbe(unittest.TestCase):
    def _sample_inputs(self):
        live_attribution = {
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
                {
                    "symbol": "FENGSHUI",
                    "failure_label": "entry_slippage_failure",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": None},
                },
                {
                    "symbol": "CMC",
                    "failure_label": "mfe_then_giveback",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": 17.0},
                },
                {
                    "symbol": "AUCA",
                    "failure_label": "mfe_then_giveback",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": 18.0},
                },
                {
                    "symbol": "币安 x402",
                    "failure_label": "dead_flow_timeout",
                    "near_threshold_like": True,
                    "entry_anchor": {"time_to_plus_25_seconds": None},
                },
                {
                    "symbol": "黄金夏日",
                    "failure_label": "dead_flow_timeout",
                    "near_threshold_like": True,
                    "entry_anchor": {"time_to_plus_25_seconds": None},
                },
                {
                    "symbol": "币安队长",
                    "failure_label": "dead_flow_timeout",
                    "near_threshold_like": True,
                    "entry_anchor": {"time_to_plus_25_seconds": None},
                },
                {
                    "symbol": "赵长娥",
                    "failure_label": "profitable_exit",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": 4.0},
                },
            ],
        }
        train = {"class_counts": {"post_target_collapse": 5, "post_target_continuation": 42, "post_target_unresolved": 2, "target_not_hit": 10}}
        validation = {"class_counts": {"post_target_collapse": 0, "post_target_continuation": 22, "post_target_unresolved": 1, "target_not_hit": 4}}
        final = {"class_counts": {"post_target_collapse": 4, "post_target_continuation": 25, "post_target_unresolved": 2, "target_not_hit": 0}}
        return live_attribution, train, validation, final

    def test_build_feasibility_report_counts_support_and_no_go(self):
        live_attribution, train, validation, final = self._sample_inputs()

        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
        )

        self.assertEqual(report["active_model"], "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(report["go_no_go"]["status"], "NO_GO_FOR_LIVE_RULE")
        self.assertIn("validation_positives is 0", report["go_no_go"]["reason"])

        checks = {row["bucket"]: row for row in report["candidate_bucket_checks"]}
        self.assertEqual(checks["post_target_collapse_or_live_mfe_giveback"]["train_positives"], 5)
        self.assertEqual(checks["post_target_collapse_or_live_mfe_giveback"]["validation_positives"], 0)
        self.assertEqual(checks["post_target_collapse_or_live_mfe_giveback"]["final_positives"], 4)
        self.assertEqual(checks["post_target_collapse_or_live_mfe_giveback"]["live_positives"], 3)

        self.assertEqual(report["live_counts"]["entry_plus25_count"], 3)
        self.assertEqual(report["live_counts"]["post_target_loss_count"], 3)
        self.assertEqual(report["near_threshold_breakdown"]["near_trade_count"], 3)
        self.assertEqual(report["near_threshold_breakdown"]["near_failure_labels"]["dead_flow_timeout"], 3)
        self.assertEqual(report["live_symbols_by_bucket"]["mfe_then_giveback"], ["CMC", "AUCA"])

        text = p.to_json_text(report)
        self.assertNotIn("NaN", text)
        self.assertIn("NO_GO_FOR_LIVE_RULE", text)
        self.assertIsInstance(json.loads(text), dict)

    def test_build_feasibility_report_accepts_live_trade_attribution_sample_schema(self):
        live_attribution = {
            "active_model": "data/models/20260519_v95_v84_selective_nearmiss_gate",
            "failure_label_counts": {
                "mfe_then_giveback": 4,
                "profitable_exit": 1,
            },
            "reason_counts": {
                "ENTRY_SLIPPAGE_PROTECTION": 1,
                "STOP_LOSS": 4,
            },
            "trade_count": 5,
            "win_count": 1,
            "loss_count": 4,
            "trade_sample": [
                {
                    "symbol": "SampleGiveback",
                    "failure_label": "mfe_then_giveback",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": 12.0},
                },
                {
                    "symbol": "SampleProfit",
                    "failure_label": "profitable_exit",
                    "near_threshold_like": False,
                    "entry_anchor": {"time_to_plus_25_seconds": 4.0},
                },
            ],
            "unemitted_trade_count": 3,
        }
        train = {"class_counts": {"post_target_collapse": 8}}
        validation = {"class_counts": {"post_target_collapse": 3}}
        final = {"class_counts": {"post_target_collapse": 5}}

        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
        )

        self.assertEqual(report["live_counts"]["trade_count"], 5)
        self.assertEqual(report["live_counts"]["failure_label_counts"]["mfe_then_giveback"], 4)
        self.assertEqual(report["live_counts"]["post_target_loss_count"], 4)
        self.assertEqual(report["live_counts"]["entry_plus25_count"], 2)
        self.assertEqual(report["live_symbols_by_bucket"]["mfe_then_giveback"], ["SampleGiveback"])

    def test_to_markdown_text_includes_bucket_table_and_no_go(self):
        live_attribution, train, validation, final = self._sample_inputs()
        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
        )

        md = p.to_markdown_text(report)

        self.assertIn("NO_GO_FOR_LIVE_RULE", md)
        self.assertIn("| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |", md)
        self.assertIn("mfe_then_giveback", md)

    def test_build_feasibility_report_uses_optional_dead_flow_support_report(self):
        live_attribution, train, validation, final = self._sample_inputs()
        dead_flow_support = {
            "support_gate": {
                "status": "NO_GO_FOR_DEAD_FLOW_RULE",
                "train_positives": 5,
                "validation_positives": 1,
                "final_positives": 4,
                "live_positives": 6,
                "passes_support_gate": False,
                "reason": "validation support below gate",
            },
            "live_recall": {
                "dead_flow_label_count": 7,
                "matched_dead_flow_count": 6,
                "passes_live_recall_gate": True,
            },
        }

        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
            dead_flow_support_report=dead_flow_support,
        )

        checks = {row["bucket"]: row for row in report["candidate_bucket_checks"]}
        self.assertEqual(checks["dead_flow_timeout"]["train_positives"], 5)
        self.assertEqual(checks["dead_flow_timeout"]["validation_positives"], 1)
        self.assertEqual(checks["dead_flow_timeout"]["final_positives"], 4)
        self.assertEqual(checks["dead_flow_timeout"]["live_positives"], 6)
        self.assertFalse(checks["dead_flow_timeout"]["passes_min_support_gate"])
        self.assertIn("validation support below gate", checks["dead_flow_timeout"]["falsification_reason"])

    def test_supported_dead_flow_report_stays_no_live_switch_with_accurate_reason(self):
        live_attribution, train, validation, final = self._sample_inputs()
        dead_flow_support = {
            "support_gate": {
                "status": "PASS_DEAD_FLOW_SUPPORT_GATE",
                "train_positives": 4,
                "validation_positives": 3,
                "final_positives": 3,
                "live_positives": 7,
                "passes_support_gate": True,
                "reason": "dead-flow support passed for replay follow-up",
            },
        }

        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
            dead_flow_support_report=dead_flow_support,
        )

        self.assertEqual(report["go_no_go"]["status"], "NO_GO_FOR_LIVE_RULE")
        self.assertEqual(report["go_no_go"]["supported_bucket"], "dead_flow_timeout")
        self.assertIn("passes the diagnostic support gate", report["go_no_go"]["reason"])
        self.assertIn("not live-switch evidence", report["go_no_go"]["reason"])
        self.assertNotIn("No candidate bucket has", report["go_no_go"]["reason"])

    def test_malformed_passing_dead_flow_report_does_not_pass_support_gate(self):
        live_attribution, train, validation, final = self._sample_inputs()
        dead_flow_support = {
            "support_gate": {
                "status": "PASS_DEAD_FLOW_SUPPORT_GATE",
                "train_positives": 4,
                "validation_positives": 3,
                "final_positives": 3,
                "passes_support_gate": True,
                "reason": "missing live count should not pass",
            },
        }

        report = p.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train,
            validation_post_target_report=validation,
            final_post_target_report=final,
            dead_flow_support_report=dead_flow_support,
        )

        dead_flow = {row["bucket"]: row for row in report["candidate_bucket_checks"]}["dead_flow_timeout"]
        self.assertIsNone(dead_flow["live_positives"])
        self.assertFalse(dead_flow["passes_min_support_gate"])
        self.assertIn("missing one or more required positive counts", dead_flow["falsification_reason"])


if __name__ == "__main__":
    unittest.main()
