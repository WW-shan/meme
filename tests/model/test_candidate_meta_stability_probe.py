import json
import unittest

from src.pipeline import candidate_meta_stability_probe as p


def _report(prefix: str):
    return {
        "candidate_sample": [
            {
                "symbol": f"{prefix}_POS",
                "recommended_policy": "quick_take_profit",
                "prob": 0.991,
                "entry_volume_30s": 1.8,
                "entry_price_volatility": 0.12,
                "flow_buy_sell_overlap_ratio_60s": 0.1,
            },
            {
                "symbol": f"{prefix}_NEG",
                "recommended_policy": "skip",
                "prob": 0.991,
                "entry_volume_30s": 1.7,
                "entry_price_volatility": 0.11,
                "flow_buy_sell_overlap_ratio_60s": 0.9,
            },
            {
                "symbol": f"{prefix}_FILTERED",
                "recommended_policy": "quick_take_profit",
                "prob": 0.991,
                "entry_volume_30s": 0.2,
                "entry_price_volatility": 0.12,
                "flow_buy_sell_overlap_ratio_60s": 0.1,
            },
        ]
    }


class TestCandidateMetaStabilityProbe(unittest.TestCase):
    def test_scores_parameter_grid_across_rolling_source_windows(self):
        report = p.build_candidate_meta_stability_report(
            time_to_barrier_reports=[_report("R0"), _report("R1"), _report("R2")],
            source_names=["r0", "r1", "r2"],
            validation_report_counts=[1],
            probability_thresholds=[0.5],
            max_depths=[1],
            min_samples_leaf_values=[1],
            min_validation_selected=1,
            min_train_selected=1,
            min_stable_precision=0.75,
            candidate_filters=[("entry_volume_30s", ">=", 1.25)],
        )

        self.assertEqual(report["decision"], "probe_only_replay_required")
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["candidate_counts"]["source_reports"], 3)
        self.assertEqual(report["parameters"]["candidate_filters"], [{"field": "entry_volume_30s", "op": ">=", "value": 1.25}])
        self.assertEqual(len(report["grid_results"]), 1)
        result = report["grid_results"][0]
        self.assertEqual(result["fold_count"], 2)
        self.assertEqual(result["eligible_fold_count"], 2)
        self.assertTrue(result["all_folds_eligible"])
        self.assertTrue(result["stable"])
        self.assertEqual(result["min_validation_selected_count"], 1)
        self.assertEqual(result["total_selected_count"], 2)
        self.assertEqual(result["total_selected_positive_count"], 2)
        self.assertEqual(result["pooled_precision"], 1.0)
        self.assertEqual(result["min_validation_precision"], 1.0)
        self.assertEqual(report["top_stable_results"][0]["rank"], 1)

        parsed = json.loads(p.to_json_text(report))
        self.assertEqual(parsed["grid_results"][0]["folds"][0]["validation_sources"], ["r1"])

    def test_rejects_too_few_reports_for_rolling_validation(self):
        with self.assertRaisesRegex(ValueError, "at least three source reports"):
            p.build_candidate_meta_stability_report(
                time_to_barrier_reports=[_report("R0"), _report("R1")],
                validation_report_counts=[1],
            )

    def test_rejects_validation_count_without_train_and_validation_folds(self):
        with self.assertRaisesRegex(ValueError, "validation_report_counts must leave"):
            p.build_candidate_meta_stability_report(
                time_to_barrier_reports=[_report("R0"), _report("R1"), _report("R2")],
                validation_report_counts=[3],
                min_stable_precision=0.0,
            )


if __name__ == "__main__":
    unittest.main()
