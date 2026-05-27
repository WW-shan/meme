import json
import math
import unittest

from src.pipeline import flow_abstention_feature_scan as p


class TestFlowAbstentionFeatureScan(unittest.TestCase):
    def test_scans_causal_numeric_features_and_rejects_leaky_outcome_fields(self):
        report = p.build_scan_report(
            reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "DEAD",
                            "barrier_class": "flat_timeout",
                            "flow_sell_pressure_30s": 0.95,
                            "flow_signed_imbalance_30s": -0.90,
                            "flow_window_seconds": 120.0,
                            "entry_volume_30s": 0.2,
                            "mfe_pct": -1.0,
                        },
                        {
                            "symbol": "STOP",
                            "barrier_class": "stop_first",
                            "flow_sell_pressure_30s": 0.80,
                            "flow_signed_imbalance_30s": -0.70,
                            "flow_window_seconds": 60.0,
                            "entry_volume_30s": 0.8,
                            "mfe_pct": -2.0,
                        },
                        {
                            "symbol": "RUNNER",
                            "barrier_class": "slow_runner",
                            "flow_sell_pressure_30s": 0.10,
                            "flow_signed_imbalance_30s": 0.85,
                            "flow_window_seconds": 30.0,
                            "entry_volume_30s": 1.4,
                            "mfe_pct": 240.0,
                        },
                    ]
                }
            ],
            min_selected=2,
            min_bad_precision=0.9,
            max_protected_selected=0,
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertIn("flow_sell_pressure_30s", report["feature_scan"]["scanned_features"])
        self.assertNotIn("flow_window_seconds", report["feature_scan"]["scanned_features"])
        self.assertNotIn("mfe_pct", report["feature_scan"]["scanned_features"])
        self.assertEqual(report["eligible_rule_results"][0]["feature"], "flow_sell_pressure_30s")
        self.assertEqual(report["eligible_rule_results"][0]["operator"], ">=")
        self.assertEqual(report["eligible_rule_results"][0]["bad_count"], 2)
        self.assertEqual(report["eligible_rule_results"][0]["protected_count"], 0)
        self.assertIn("flat_timeout", report["class_feature_summaries"])

    def test_reads_nested_live_attribution_rejected_signal_paths(self):
        rows = p.candidate_rows_from_report(
            {
                "trade_sample": [
                    {"symbol": "LIVE", "failure_label": "dead_flow_timeout"}
                ],
                "rejected_signal_paths": {
                    "candidate_sample": [
                        {"symbol": "A", "barrier_class": "flat_timeout", "flow_event_count_30s": 1}
                    ]
                }
            },
            source_name="live_attr",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "A")
        self.assertEqual(rows[0]["source_report"], "live_attr")

    def test_custom_bad_and_protected_classes_rank_feature_contrast(self):
        report = p.build_scan_report(
            reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "COLLAPSE",
                            "barrier_class": "fast_profit_then_collapse",
                            "flow_sell_pressure_30s": 0.90,
                            "flow_signed_imbalance_30s": -0.80,
                        },
                        {
                            "symbol": "FAST",
                            "barrier_class": "fast_profit",
                            "flow_sell_pressure_30s": 0.10,
                            "flow_signed_imbalance_30s": 0.75,
                        },
                    ]
                }
            ],
            bad_classes=["fast_profit_then_collapse"],
            protected_classes=["fast_profit"],
            min_selected=1,
            min_bad_precision=1.0,
        )

        self.assertEqual(report["parameters"]["bad_classes"], ["fast_profit_then_collapse"])
        self.assertEqual(report["parameters"]["protected_classes"], ["fast_profit"])
        self.assertEqual(report["eligible_rule_results"][0]["feature"], "flow_sell_pressure_30s")
        contrast = report["bad_vs_protected_feature_contrast"][0]
        self.assertEqual(contrast["feature"], "flow_sell_pressure_30s")
        self.assertGreater(contrast["median_delta_bad_minus_protected"], 0.0)

    def test_json_text_sanitizes_nonfinite_values(self):
        text = p.to_json_text({"value": math.nan, "nested": {"inf": math.inf}})

        self.assertNotIn("NaN", text)
        self.assertNotIn("Infinity", text)
        parsed = json.loads(text)
        self.assertIsNone(parsed["value"])
        self.assertIsNone(parsed["nested"]["inf"])


if __name__ == "__main__":
    unittest.main()
