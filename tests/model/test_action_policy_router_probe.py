import json
import unittest

from src.pipeline import action_policy_router_probe as p


class TestActionPolicyRouterProbe(unittest.TestCase):
    def test_routes_candidates_into_multiple_action_policies_without_ex_post_features(self):
        train_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_TRAIN_QTP",
                    "barrier_class": "fast_profit_then_collapse",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 30.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "time_to_plus_25_seconds": 7.0,
                    "time_to_minus_18_seconds": 80.0,
                },
                {
                    "symbol": "REJ_TRAIN_SKIP",
                    "barrier_class": "stop_first",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 30.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                    "time_to_plus_25_seconds": None,
                    "time_to_minus_18_seconds": 8.0,
                },
            ]
        }
        train_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_TRAIN_HOLD",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 50.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.15,
                    "post_target_window_returns_pct": {"60": 55.0},
                },
                {
                    "symbol": "ACC_TRAIN_SKIP",
                    "classification": "target_not_hit",
                    "recommended_policy": "no_action",
                    "prob": 0.99,
                    "pred_return": 8.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                },
            ]
        }
        validation_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_VALID_QTP",
                    "barrier_class": "fast_profit_then_collapse",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 31.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.12,
                    "time_to_plus_25_seconds": 9.0,
                    "time_to_minus_18_seconds": 70.0,
                },
                {
                    "symbol": "REJ_VALID_SKIP",
                    "barrier_class": "stop_first",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 31.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.96,
                    "time_to_plus_25_seconds": None,
                    "time_to_minus_18_seconds": 6.0,
                },
            ]
        }
        validation_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_VALID_HOLD",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 52.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.14,
                    "post_target_window_returns_pct": {"60": 60.0},
                }
            ]
        }

        report = p.build_action_policy_router_report(
            train_rejected_reports=[train_rejected],
            train_accepted_reports=[train_accepted],
            validation_rejected_reports=[validation_rejected],
            validation_accepted_reports=[validation_accepted],
            route_confidence_threshold=0.5,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
            min_selected_per_family=1,
        )

        self.assertEqual(report["decision"], "shadow_router_positive_replay_required")
        self.assertTrue(report["support_gate"]["passes"])
        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertIn("flow_buy_sell_overlap_ratio_60s", report["model"]["feature_names"])
        self.assertNotIn("time_to_plus_25_seconds", report["model"]["feature_names"])
        self.assertNotIn("barrier_class", report["model"]["feature_names"])
        self.assertEqual(report["route_counts"]["train"], {"continue_hold": 1, "quick_take_profit": 1, "skip": 2})
        self.assertEqual(report["validation"]["routed_policy_counts"], {"continue_hold": 1, "quick_take_profit": 1})
        self.assertEqual(report["validation"]["selected_family_counts"], {"accepted": 1, "rejected": 1})
        self.assertAlmostEqual(report["validation"]["selected_reward_pct"], 85.0)
        self.assertEqual(report["validation"]["selected_symbols"], ["REJ_VALID_QTP", "ACC_VALID_HOLD"])
        json.loads(p.to_json_text(report))

    def test_blocks_when_training_has_only_skip_route(self):
        report = p.build_action_policy_router_report(
            train_rejected_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "REJ_SKIP",
                            "recommended_policy": "skip",
                            "prob": 0.99,
                            "pred_return": 5.0,
                        }
                    ]
                }
            ],
            train_accepted_reports=[],
            validation_rejected_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "REJ_VALID_SKIP",
                            "recommended_policy": "skip",
                            "prob": 0.99,
                            "pred_return": 5.0,
                        }
                    ]
                }
            ],
            validation_accepted_reports=[],
            min_common_features=1,
        )

        self.assertEqual(report["decision"], "diagnostic_only_support_blocked")
        self.assertFalse(report["support_gate"]["passes"])
        self.assertIn("train_route_labels_below_two_classes", report["support_gate"]["reasons"])


if __name__ == "__main__":
    unittest.main()
