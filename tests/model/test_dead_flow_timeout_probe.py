import datetime as dt
import json
import unittest

from src.pipeline import dead_flow_timeout_probe as p


class TestDeadFlowTimeoutProbe(unittest.TestCase):
    def test_classify_live_shape_uses_shared_dead_flow_features(self):
        row = {
            "symbol": "币安队长",
            "failure_label": "profitable_exit",
            "hold_duration_seconds": 563.0,
            "entry_anchor": {"mfe_pct": -1.98, "time_to_plus_25_seconds": None},
            "pre_signal_10s_flow": {"sell_pressure": 1.0},
            "near_threshold_like": True,
        }

        result = p.classify_dead_flow_timeout(row, source="live")

        self.assertEqual(result["classification"], "replay_dead_flow_timeout")
        self.assertTrue(result["is_dead_flow_timeout"])
        self.assertEqual(result["mfe_pct"], -1.98)
        self.assertEqual(result["sell_pressure"], 1.0)
        self.assertFalse(result["used_failure_label"])

    def test_classify_rejects_short_hold_and_large_mfe(self):
        short_hold = {
            "symbol": "too-fast",
            "hold_duration_seconds": 120.0,
            "entry_anchor": {"mfe_pct": -1.0, "time_to_plus_25_seconds": None},
            "pre_signal_10s_flow": {"sell_pressure": 1.0},
        }
        large_mfe = {
            "symbol": "runner",
            "hold_duration_seconds": 565.0,
            "entry_anchor": {"mfe_pct": 12.0, "time_to_plus_25_seconds": None},
            "pre_signal_10s_flow": {"sell_pressure": 1.0},
        }
        target_hit = {
            "symbol": "already-hit",
            "target_hit": True,
            "hold_duration_seconds": 565.0,
            "entry_anchor": {"mfe_pct": -1.0, "time_to_plus_25_seconds": None},
            "pre_signal_10s_flow": {"sell_pressure": 1.0},
        }

        self.assertEqual(
            p.classify_dead_flow_timeout(short_hold, source="live")["classification"],
            "insufficient_hold_window",
        )
        self.assertEqual(
            p.classify_dead_flow_timeout(large_mfe, source="live")["classification"],
            "mfe_above_dead_flow_floor",
        )
        self.assertEqual(
            p.classify_dead_flow_timeout(target_hit, source="live")["classification"],
            "target_hit_or_post_target",
        )

    def test_build_report_counts_replay_support_and_live_recall(self):
        train = {
            "candidate_sample": [
                {"symbol": "t1", "target_hit": False, "mfe_pct": -1.0, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.1}},
                {"symbol": "t2", "target_hit": False, "mfe_pct": 2.0, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.4}},
                {"symbol": "t3", "target_hit": True, "mfe_pct": 50.0, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 1.0}},
            ],
        }
        validation = {
            "candidate_sample": [
                {"symbol": "v1", "target_hit": False, "mfe_pct": -2.0, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.3}},
                {"symbol": "v2", "target_hit": False, "mfe_pct": 9.0, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.3}},
            ],
        }
        final = {
            "candidate_sample": [
                {"symbol": "f1", "target_hit": False, "mfe_pct": -0.5, "horizon_seconds": 900, "flow": {"pre_buy_pressure": 0.2}},
            ],
        }
        live = {
            "trades": [
                {
                    "symbol": "live-hit",
                    "failure_label": "dead_flow_timeout",
                    "hold_duration_seconds": 564,
                    "entry_anchor": {"mfe_pct": -1.98, "time_to_plus_25_seconds": None},
                    "pre_signal_10s_flow": {"sell_pressure": 1.0},
                },
                {
                    "symbol": "live-miss",
                    "failure_label": "dead_flow_timeout",
                    "hold_duration_seconds": 80,
                    "entry_anchor": {"mfe_pct": -1.0, "time_to_plus_25_seconds": None},
                    "pre_signal_10s_flow": {"sell_pressure": 1.0},
                },
                {
                    "symbol": "winner",
                    "failure_label": "profitable_exit",
                    "hold_duration_seconds": 49,
                    "entry_anchor": {"mfe_pct": 45.0, "time_to_plus_25_seconds": 8.0},
                    "pre_signal_10s_flow": {"sell_pressure": 0.0},
                },
            ],
        }

        report = p.build_support_report(
            train_report=train,
            validation_report=validation,
            final_report=final,
            live_attribution=live,
            generated_at=dt.datetime(2026, 5, 22, 1, 0, 0),
        )

        self.assertEqual(report["split_counts"]["train"]["class_counts"]["replay_dead_flow_timeout"], 2)
        self.assertEqual(report["split_counts"]["validation"]["class_counts"]["replay_dead_flow_timeout"], 1)
        self.assertEqual(report["split_counts"]["final"]["class_counts"]["replay_dead_flow_timeout"], 1)
        self.assertEqual(report["live_recall"]["dead_flow_label_count"], 2)
        self.assertEqual(report["live_recall"]["shape_matched_live_count"], 1)
        self.assertEqual(report["live_recall"]["shape_matched_non_dead_flow_count"], 0)
        self.assertEqual(report["live_recall"]["matched_dead_flow_count"], 1)
        self.assertEqual(report["support_gate"]["status"], "NO_GO_FOR_DEAD_FLOW_RULE")
        self.assertEqual(report["support_scope"]["replay_input"], "existing_post_target_replay_reports_only")

    def test_json_and_markdown_are_deterministic_and_read_only(self):
        report = p.build_support_report(
            train_report={"candidate_sample": []},
            validation_report={"candidate_sample": []},
            final_report={"candidate_sample": []},
            live_attribution={"trades": []},
            generated_at=dt.datetime(2026, 5, 22, 1, 0, 0),
        )

        first = p.to_json_text(report)
        second = p.to_json_text(report)

        self.assertEqual(first, second)
        self.assertNotIn("NaN", first)
        self.assertFalse(json.loads(first)["contract"]["live_switch_evidence"])
        self.assertIn("existing_post_target_replay_reports_only", first)
        self.assertIn("parity_caveat", first)
        self.assertIn("NO_GO_FOR_DEAD_FLOW_RULE", p.to_markdown_text(report))


if __name__ == "__main__":
    unittest.main()
