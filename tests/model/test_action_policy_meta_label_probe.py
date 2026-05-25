import json
import unittest

from src.pipeline import action_policy_meta_label_probe as p


class TestActionPolicyMetaLabelProbe(unittest.TestCase):
    def test_blocks_combined_probe_when_accepted_rows_lack_decision_feature_parity(self):
        report = p.build_action_policy_meta_label_report(
            rejected_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "REJECT_POS",
                            "recommended_policy": "quick_take_profit",
                            "prob": 0.991,
                            "pred_return": 12.0,
                        }
                    ]
                }
            ],
            accepted_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "ACCEPT_POS",
                            "recommended_policy": "continue_hold",
                            "target_hit": True,
                        }
                    ]
                }
            ],
            rejected_source_names=["validation"],
            accepted_source_names=["validation"],
            min_family_candidates=1,
            min_common_features=1,
            min_validation_selected=1,
        )

        self.assertEqual(report["decision"], "diagnostic_only_feature_parity_blocked")
        self.assertFalse(report["meta_label_model"]["trained"])
        self.assertEqual(report["feature_parity"]["common_feature_names"], [])
        self.assertEqual(report["source_family_counts"]["rejected"], 1)
        self.assertEqual(report["source_family_counts"]["accepted"], 1)
        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        json.loads(p.to_json_text(report))

    def test_trains_source_split_meta_label_when_accepted_and_rejected_share_decision_features(self):
        rejected_train = {
            "candidate_sample": [
                {
                    "symbol": "REJ_TRAIN_CLEAN",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.992,
                    "pred_return": 12.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                },
                {
                    "symbol": "REJ_TRAIN_TOXIC",
                    "recommended_policy": "skip",
                    "prob": 0.993,
                    "pred_return": 90.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                },
            ]
        }
        accepted_train = {
            "candidate_sample": [
                {
                    "symbol": "ACC_TRAIN_CLEAN",
                    "recommended_policy": "continue_hold",
                    "prob": 0.991,
                    "pred_return": 35.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.20,
                },
                {
                    "symbol": "ACC_TRAIN_TOXIC",
                    "recommended_policy": "no_action",
                    "prob": 0.991,
                    "pred_return": 5.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                },
            ]
        }
        rejected_validation = {
            "candidate_sample": [
                {
                    "symbol": "REJ_VALID_CLEAN",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.994,
                    "pred_return": 18.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.15,
                },
                {
                    "symbol": "REJ_VALID_TOXIC",
                    "recommended_policy": "skip",
                    "prob": 0.994,
                    "pred_return": 80.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.85,
                },
            ]
        }
        accepted_validation = {
            "candidate_sample": [
                {
                    "symbol": "ACC_VALID_CLEAN",
                    "recommended_policy": "lock_profit",
                    "prob": 0.990,
                    "pred_return": 31.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.12,
                },
                {
                    "symbol": "ACC_VALID_TOXIC",
                    "recommended_policy": "monitor_after_target",
                    "prob": 0.990,
                    "pred_return": 9.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.88,
                },
            ]
        }

        report = p.build_action_policy_meta_label_report(
            rejected_reports=[rejected_train, rejected_validation],
            accepted_reports=[accepted_train, accepted_validation],
            rejected_source_names=["train", "validation"],
            accepted_source_names=["train", "validation"],
            validation_source_count=1,
            probability_threshold=0.5,
            min_validation_selected=1,
            max_depth=1,
            min_samples_leaf=1,
            min_family_candidates=1,
            min_common_features=1,
        )

        self.assertEqual(report["decision"], "probe_only_replay_required")
        self.assertTrue(report["meta_label_model"]["trained"])
        self.assertEqual(report["split"]["train_source_groups"], ["train"])
        self.assertEqual(report["split"]["validation_source_groups"], ["validation"])
        self.assertIn("flow_buy_sell_overlap_ratio_60s", report["meta_label_model"]["feature_names"])
        self.assertIn("REJ_VALID_CLEAN", report["validation"]["selected_symbols"])
        self.assertIn("ACC_VALID_CLEAN", report["validation"]["selected_symbols"])
        self.assertNotIn("REJ_VALID_TOXIC", report["validation"]["selected_symbols"])
        self.assertNotIn("ACC_VALID_TOXIC", report["validation"]["selected_symbols"])
        self.assertEqual(report["validation"]["selected_family_counts"], {"accepted": 1, "rejected": 1})
        self.assertEqual(
            report["validation"]["selected_policy_counts"],
            {"lock_profit": 1, "quick_take_profit": 1},
        )
        self.assertEqual(report["validation"]["selected_sample"][0]["source_family"], "rejected")
        self.assertGreater(report["validation"]["precision_lift_vs_base"], 1.0)

    def test_blocks_when_validation_selection_does_not_cover_both_families(self):
        train_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_TRAIN_POS",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 10.0,
                },
                {
                    "symbol": "REJ_TRAIN_NEG",
                    "recommended_policy": "skip",
                    "prob": 0.95,
                    "pred_return": 5.0,
                },
            ]
        }
        train_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_TRAIN_POS",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 40.0,
                },
                {
                    "symbol": "ACC_TRAIN_NEG",
                    "recommended_policy": "no_action",
                    "prob": 0.95,
                    "pred_return": 4.0,
                },
            ]
        }
        validation_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_VALID_LOW_SCORE",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.95,
                    "pred_return": 5.0,
                }
            ]
        }
        validation_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_VALID_HIGH_SCORE",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 40.0,
                }
            ]
        }

        report = p.build_action_policy_meta_label_report(
            rejected_reports=[train_rejected, validation_rejected],
            accepted_reports=[train_accepted, validation_accepted],
            rejected_source_names=["train", "validation"],
            accepted_source_names=["train", "validation"],
            validation_source_count=1,
            probability_threshold=0.5,
            min_validation_selected=1,
            max_depth=1,
            min_samples_leaf=1,
            min_family_candidates=1,
            min_common_features=1,
            min_validation_selected_per_family=1,
        )

        self.assertEqual(report["decision"], "diagnostic_only_selected_family_support_blocked")
        self.assertFalse(report["support_gate"]["passes"])
        self.assertIn("validation_rejected_selection_below_min", report["support_gate"]["reasons"])
        self.assertEqual(report["validation"]["selected_family_counts"], {"accepted": 1})


if __name__ == "__main__":
    unittest.main()
