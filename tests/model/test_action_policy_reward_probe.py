import json
import unittest

from src.pipeline import action_policy_reward_probe as p


class TestActionPolicyRewardProbe(unittest.TestCase):
    def test_post_target_collapse_lock_reward_uses_return_pct_not_fraction(self):
        reward_policy, reward_pct, reward_known = p._accepted_action_reward(
            {
                "classification": "post_target_collapse",
                "target_pct": 0.25,
                "target_hit_return_pct": 29.5,
            },
            post_target_window_seconds=60.0,
            default_lock_profit_pct=25.0,
        )

        self.assertEqual(reward_policy, "lock_profit")
        self.assertTrue(reward_known)
        self.assertEqual(reward_pct, 29.5)

        _policy, fallback_pct, _known = p._accepted_action_reward(
            {
                "classification": "post_target_collapse",
                "target_pct": 0.25,
            },
            post_target_window_seconds=60.0,
            default_lock_profit_pct=25.0,
        )
        self.assertEqual(fallback_pct, 25.0)

    def test_scores_selected_action_policy_by_replay_reward_without_ex_post_features(self):
        rejected_train = {
            "candidate_sample": [
                {
                    "symbol": "REJ_TRAIN_WIN",
                    "barrier_class": "fast_profit_then_collapse",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 20.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "time_to_plus_25_seconds": 8.0,
                    "time_to_minus_18_seconds": 120.0,
                },
                {
                    "symbol": "REJ_TRAIN_LOSS",
                    "barrier_class": "stop_first",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 20.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                    "time_to_plus_25_seconds": None,
                    "time_to_minus_18_seconds": 12.0,
                },
            ]
        }
        accepted_train = {
            "candidate_sample": [
                {
                    "symbol": "ACC_TRAIN_WIN",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 40.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.20,
                    "post_target_window_returns_pct": {"60": 55.0},
                },
                {
                    "symbol": "ACC_TRAIN_LOSS",
                    "classification": "target_not_hit",
                    "recommended_policy": "no_action",
                    "prob": 0.99,
                    "pred_return": 5.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                    "post_target_window_returns_pct": {"60": -10.0},
                },
            ]
        }
        rejected_validation = {
            "candidate_sample": [
                {
                    "symbol": "REJ_VALID_WIN",
                    "barrier_class": "fast_profit_then_collapse",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 22.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.12,
                    "time_to_plus_25_seconds": 10.0,
                    "time_to_minus_18_seconds": 90.0,
                },
                {
                    "symbol": "REJ_VALID_SKIP",
                    "barrier_class": "stop_first",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 22.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.88,
                    "time_to_plus_25_seconds": None,
                    "time_to_minus_18_seconds": 4.0,
                },
            ]
        }
        accepted_validation = {
            "candidate_sample": [
                {
                    "symbol": "ACC_VALID_WIN",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 42.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.16,
                    "post_target_window_returns_pct": {"60": 60.0},
                },
                {
                    "symbol": "ACC_VALID_SKIP",
                    "classification": "target_not_hit",
                    "recommended_policy": "no_action",
                    "prob": 0.99,
                    "pred_return": 8.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.92,
                    "post_target_window_returns_pct": {"60": -12.0},
                },
            ]
        }

        report = p.build_action_policy_reward_report(
            train_rejected_reports=[rejected_train],
            train_accepted_reports=[accepted_train],
            validation_rejected_reports=[rejected_validation],
            validation_accepted_reports=[accepted_validation],
            probability_threshold=0.5,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
            min_selected_per_family=1,
        )

        self.assertEqual(report["decision"], "shadow_reward_positive_replay_required")
        self.assertTrue(report["support_gate"]["passes"])
        self.assertIn("flow_buy_sell_overlap_ratio_60s", report["model"]["feature_names"])
        self.assertNotIn("mfe_pct", report["model"]["feature_names"])
        self.assertNotIn("barrier_class", report["model"]["feature_names"])
        self.assertEqual(report["validation"]["selected_count"], 2)
        self.assertEqual(report["validation"]["selected_family_counts"], {"accepted": 1, "rejected": 1})
        self.assertAlmostEqual(report["validation"]["selected_reward_pct"], 85.0)
        self.assertAlmostEqual(report["validation"]["selected_average_reward_pct"], 42.5)
        self.assertEqual(report["validation"]["selected_reward_policy_counts"], {"continue_hold": 1, "quick_take_profit": 1})
        self.assertIn("REJ_VALID_WIN", report["validation"]["selected_symbols"])
        self.assertIn("ACC_VALID_WIN", report["validation"]["selected_symbols"])
        json.loads(p.to_json_text(report))

    def test_marks_fresh_holdout_without_family_support_as_shadow_only(self):
        train_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_TRAIN_WIN",
                    "barrier_class": "fast_profit",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 20.0,
                },
                {
                    "symbol": "REJ_TRAIN_LOSS",
                    "barrier_class": "stop_first",
                    "recommended_policy": "skip",
                    "prob": 0.95,
                    "pred_return": 5.0,
                },
            ]
        }
        train_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_TRAIN_WIN",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 40.0,
                    "post_target_window_returns_pct": {"60": 20.0},
                }
            ]
        }
        fresh_rejected = {
            "rejected_signal_paths": {
                "candidate_sample": [
                    {
                        "symbol": "FRESH_ONLY_REJECTED",
                        "barrier_class": "fast_profit_then_collapse",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.99,
                        "pred_return": 20.0,
                        "time_to_plus_25_seconds": 7.0,
                        "time_to_minus_18_seconds": 80.0,
                    }
                ]
            }
        }

        report = p.build_action_policy_reward_report(
            train_rejected_reports=[train_rejected],
            train_accepted_reports=[train_accepted],
            validation_rejected_reports=[fresh_rejected],
            validation_accepted_reports=[],
            probability_threshold=0.5,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
            min_selected_per_family=1,
        )

        self.assertEqual(report["decision"], "shadow_only_support_limited")
        self.assertFalse(report["support_gate"]["passes"])
        self.assertIn("validation_accepted_selection_below_min", report["support_gate"]["reasons"])
        self.assertEqual(report["validation"]["source_family_counts"], {"rejected": 1})


if __name__ == "__main__":
    unittest.main()
