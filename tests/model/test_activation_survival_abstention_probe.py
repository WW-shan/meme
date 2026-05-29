import json
import unittest

from src.pipeline import activation_survival_abstention_probe as p


def _report(rows):
    return {"candidate_sample": rows}


class TestActivationSurvivalAbstentionProbe(unittest.TestCase):
    def test_selects_train_rule_and_evaluates_validation_final_without_leaky_fields(self):
        train = _report(
            [
                {
                    "symbol": "D1",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.92,
                    "entry_volume_30s": 1.1,
                    "mae_pct": -8.0,
                    "mfe_pct": 2.0,
                    "time_to_target_seconds": None,
                },
                {
                    "symbol": "D2",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.88,
                    "entry_volume_30s": 1.3,
                    "mae_pct": -4.0,
                    "mfe_pct": 1.0,
                },
                {
                    "symbol": "RUN",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.10,
                    "entry_volume_30s": 2.0,
                    "mfe_pct": 90.0,
                    "post_target_window_returns_pct": {"60": 80.0},
                },
            ]
        )
        validation = _report(
            [
                {
                    "symbol": "VD",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.91,
                    "entry_volume_30s": 1.2,
                    "mae_pct": -5.0,
                },
                {
                    "symbol": "VR",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.15,
                    "entry_volume_30s": 2.1,
                    "mfe_pct": 70.0,
                    "post_target_window_returns_pct": {"60": 65.0},
                },
            ]
        )
        final = _report(
            [
                {
                    "symbol": "FD",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.93,
                    "entry_volume_30s": 1.2,
                    "mae_pct": -3.0,
                },
                {
                    "symbol": "FR",
                    "classification": "post_target_collapse",
                    "flow_sell_pressure_30s": 0.20,
                    "entry_volume_30s": 2.0,
                    "mfe_pct": 35.0,
                    "post_target_window_returns_pct": {"60": 25.0},
                },
            ]
        )

        report = p.build_activation_survival_abstention_report(
            train_report=train,
            validation_report=validation,
            final_report=final,
            min_train_selected=2,
            min_train_bad_precision=1.0,
            max_train_protected=0,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        selected = report["selected_candidate"]
        self.assertEqual(selected["rule"]["feature"], "flow_sell_pressure_30s")
        self.assertEqual(selected["rule"]["operator"], ">=")
        self.assertTrue(selected["passes_research_alpha_proxy_gate"])
        self.assertEqual(selected["validation"]["bad_count"], 1)
        self.assertEqual(selected["validation"]["protected_count"], 0)
        self.assertGreater(selected["validation"]["abstention_utility_delta_pct"], 0.0)
        self.assertNotIn("time_to_target_seconds", report["train_eligible_rules"][0]["feature"])
        self.assertEqual(report["strict_metric_coverage"]["net_profit_bnb"], "not_computed_probe_only_requires_replay")

    def test_rejects_train_only_rule_that_hits_protected_validation_row(self):
        train = _report(
            [
                {"classification": "target_not_hit", "flow_event_count_30s": 1, "mae_pct": -2.0},
                {"classification": "target_not_hit", "flow_event_count_30s": 2, "mae_pct": -3.0},
                {"classification": "post_target_continuation", "flow_event_count_30s": 9, "mfe_pct": 50.0},
            ]
        )
        validation = _report(
            [
                {"classification": "post_target_continuation", "flow_event_count_30s": 1, "mfe_pct": 50.0},
            ]
        )
        final = _report(
            [
                {"classification": "target_not_hit", "flow_event_count_30s": 1, "mae_pct": -1.0},
            ]
        )

        report = p.build_activation_survival_abstention_report(
            train_report=train,
            validation_report=validation,
            final_report=final,
            min_train_selected=2,
            min_train_bad_precision=1.0,
            max_train_protected=0,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertEqual(report["decision"], "train_candidate_failed_validation_or_final_proxy_gate")
        self.assertFalse(report["selected_candidate"]["validation_passes"])

    def test_multicondition_rule_can_select_bad_rows_without_scalar_overfit(self):
        train = _report(
            [
                {
                    "symbol": "D1",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.90,
                    "entry_volume_30s": 1.0,
                    "mae_pct": -5.0,
                },
                {
                    "symbol": "D2",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.88,
                    "entry_volume_30s": 1.1,
                    "mae_pct": -4.0,
                },
                {
                    "symbol": "RUN_PRESSURE",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.91,
                    "entry_volume_30s": 2.5,
                    "mfe_pct": 90.0,
                },
                {
                    "symbol": "RUN_VOLUME",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.10,
                    "entry_volume_30s": 1.0,
                    "mfe_pct": 80.0,
                },
            ]
        )
        validation = _report(
            [
                {
                    "symbol": "VD",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.89,
                    "entry_volume_30s": 1.05,
                    "mae_pct": -3.0,
                },
                {
                    "symbol": "VR1",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.92,
                    "entry_volume_30s": 2.4,
                    "mfe_pct": 70.0,
                },
                {
                    "symbol": "VR2",
                    "classification": "post_target_continuation",
                    "flow_sell_pressure_30s": 0.12,
                    "entry_volume_30s": 1.0,
                    "mfe_pct": 75.0,
                },
            ]
        )
        final = _report(
            [
                {
                    "symbol": "FD",
                    "classification": "target_not_hit",
                    "flow_sell_pressure_30s": 0.89,
                    "entry_volume_30s": 1.05,
                    "mae_pct": -2.0,
                }
            ]
        )

        report = p.build_activation_survival_abstention_report(
            train_report=train,
            validation_report=validation,
            final_report=final,
            min_train_selected=2,
            min_train_bad_precision=1.0,
            max_train_protected=0,
            max_conditions=2,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        selected = report["selected_candidate"]
        self.assertEqual(selected["rule"]["condition_count"], 2)
        self.assertTrue(selected["passes_research_alpha_proxy_gate"])
        self.assertEqual(selected["validation"]["bad_count"], 1)
        self.assertEqual(selected["validation"]["protected_count"], 0)
        selected_features = {condition["feature"] for condition in selected["rule"]["conditions"]}
        self.assertEqual(selected_features, {"entry_volume_30s", "flow_sell_pressure_30s"})

    def test_json_text_sanitizes_nonfinite_values(self):
        text = p.to_json_text({"nan": float("nan"), "inf": float("inf")})

        parsed = json.loads(text)
        self.assertIsNone(parsed["nan"])
        self.assertIsNone(parsed["inf"])


if __name__ == "__main__":
    unittest.main()
