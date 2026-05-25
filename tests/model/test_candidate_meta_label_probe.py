import json
import unittest

from src.pipeline import candidate_meta_label_probe as p


class TestCandidateMetaLabelProbe(unittest.TestCase):
    def test_trains_source_split_segment_model_from_decision_time_features(self):
        train_report = {
            "candidate_sample": [
                {
                    "symbol": "TRAIN_CLEAN",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.991,
                    "pred_return": 8.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "flow_recent_seller_reentry_ratio_30s": 0.0,
                    "flow_event_count_30s": 4,
                    "mfe_pct": 400.0,
                },
                {
                    "symbol": "TRAIN_TOXIC",
                    "recommended_policy": "skip",
                    "prob": 0.994,
                    "pred_return": 80.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                    "flow_recent_seller_reentry_ratio_30s": 0.8,
                    "flow_event_count_30s": 4,
                    "mfe_pct": 400.0,
                },
                {
                    "symbol": "TRAIN_LOW_PROB",
                    "recommended_policy": "skip",
                    "prob": 0.930,
                    "pred_return": 12.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "flow_recent_seller_reentry_ratio_30s": 0.0,
                    "flow_event_count_30s": 4,
                    "mfe_pct": 400.0,
                },
            ]
        }
        validation_report = {
            "candidate_sample": [
                {
                    "symbol": "VALID_CLEAN",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.992,
                    "pred_return": 9.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.20,
                    "flow_recent_seller_reentry_ratio_30s": 0.0,
                    "flow_event_count_30s": 3,
                    "mfe_pct": -99.0,
                },
                {
                    "symbol": "VALID_TOXIC",
                    "recommended_policy": "skip",
                    "prob": 0.993,
                    "pred_return": 90.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                    "flow_recent_seller_reentry_ratio_30s": 0.9,
                    "flow_event_count_30s": 5,
                    "mfe_pct": 999.0,
                },
            ]
        }

        report = p.build_candidate_meta_label_report(
            time_to_barrier_reports=[train_report, validation_report],
            source_names=["train_window", "validation_window"],
            min_validation_selected=1,
            probability_threshold=0.5,
            max_depth=2,
            min_samples_leaf=1,
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["split"]["train_sources"], ["train_window"])
        self.assertEqual(report["split"]["validation_sources"], ["validation_window"])
        self.assertIn("flow_buy_sell_overlap_ratio_60s", report["model"]["feature_names"])
        self.assertNotIn("mfe_pct", report["model"]["feature_names"])
        self.assertGreaterEqual(report["validation"]["selected_count"], 1)
        self.assertIn("VALID_CLEAN", report["validation"]["selected_symbols"])
        self.assertNotIn("VALID_TOXIC", report["validation"]["selected_symbols"])
        self.assertGreater(report["validation"]["precision_lift_vs_base"], 1.0)

        parsed = json.loads(p.to_json_text(report))
        self.assertEqual(parsed["decision"], "probe_only_replay_required")

    def test_rejects_single_class_or_single_source_training(self):
        positive_only = {"candidate_sample": [{"symbol": "A", "recommended_policy": "quick_take_profit", "prob": 0.99}]}
        negative_only = {"candidate_sample": [{"symbol": "B", "recommended_policy": "skip", "prob": 0.99}]}

        with self.assertRaisesRegex(ValueError, "at least two source reports"):
            p.build_candidate_meta_label_report(time_to_barrier_reports=[positive_only])

        with self.assertRaisesRegex(ValueError, "both positive and negative"):
            p.build_candidate_meta_label_report(time_to_barrier_reports=[positive_only, positive_only])

        with self.assertRaisesRegex(ValueError, "validation set"):
            p.build_candidate_meta_label_report(
                time_to_barrier_reports=[positive_only, negative_only],
                min_validation_selected=2,
            )

    def test_filters_candidate_universe_with_decision_time_conditions(self):
        train_report = {
            "candidate_sample": [
                {
                    "symbol": "TRAIN_POS_ACTIONABLE",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.991,
                    "entry_volume_30s": 1.8,
                    "entry_price_volatility": 0.12,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                },
                {
                    "symbol": "TRAIN_NEG_ACTIONABLE",
                    "recommended_policy": "skip",
                    "prob": 0.992,
                    "entry_volume_30s": 1.7,
                    "entry_price_volatility": 0.13,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                },
                {
                    "symbol": "TRAIN_LOW_VOLUME_EXCLUDED",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.993,
                    "entry_volume_30s": 0.7,
                    "entry_price_volatility": 0.20,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                },
            ]
        }
        validation_report = {
            "candidate_sample": [
                {
                    "symbol": "VALID_POS_ACTIONABLE",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.991,
                    "entry_volume_30s": 1.9,
                    "entry_price_volatility": 0.12,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                },
                {
                    "symbol": "VALID_LOW_VOLUME_EXCLUDED",
                    "recommended_policy": "skip",
                    "prob": 0.991,
                    "entry_volume_30s": 0.5,
                    "entry_price_volatility": 0.12,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                },
            ]
        }

        report = p.build_candidate_meta_label_report(
            time_to_barrier_reports=[train_report, validation_report],
            source_names=["train_window", "validation_window"],
            candidate_filters=[
                ("prob", ">=", 0.94),
                ("entry_volume_30s", ">=", 1.25),
                ("entry_price_volatility", ">=", 0.08),
            ],
            min_validation_selected=1,
            probability_threshold=0.5,
            max_depth=1,
            min_samples_leaf=1,
        )

        self.assertEqual(report["candidate_counts"]["pre_filter_candidates"], 5)
        self.assertEqual(report["candidate_counts"]["input_candidates"], 3)
        self.assertEqual(report["candidate_counts"]["filtered_out_candidates"], 2)
        self.assertEqual(report["split"]["train_candidate_count"], 2)
        self.assertEqual(report["split"]["validation_candidate_count"], 1)
        self.assertEqual(
            report["parameters"]["candidate_filters"],
            [
                {"field": "prob", "op": ">=", "value": 0.94},
                {"field": "entry_volume_30s", "op": ">=", "value": 1.25},
                {"field": "entry_price_volatility", "op": ">=", "value": 0.08},
            ],
        )


if __name__ == "__main__":
    unittest.main()
