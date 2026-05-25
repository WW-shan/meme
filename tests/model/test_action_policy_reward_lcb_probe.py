import unittest

from src.pipeline import action_policy_reward_lcb_probe as p


class TestActionPolicyRewardLcbProbe(unittest.TestCase):
    def test_bootstrap_lcb_report_keeps_positive_support_and_replay_required_decision(self):
        reward_report = {
            "validation": {
                "selected_count": 2,
                "selected_family_counts": {"accepted": 1, "rejected": 1},
                "selected_rewards": [
                    {
                        "symbol": "REJ_VALID_WIN",
                        "source_family": "rejected",
                        "source_group": "validation_rejected_0",
                        "evidence_class": "fast_profit_then_collapse",
                        "recommended_policy": "quick_take_profit",
                        "replay_reward_policy": "quick_take_profit",
                        "replay_reward_pct": 25.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.99,
                    },
                    {
                        "symbol": "ACC_VALID_WIN",
                        "source_family": "accepted",
                        "source_group": "validation_accepted_0",
                        "evidence_class": "post_target_continuation",
                        "recommended_policy": "continue_hold",
                        "replay_reward_policy": "continue_hold",
                        "replay_reward_pct": 60.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.99,
                    },
                ],
            },
            "final": {
                "selected_count": 2,
                "selected_family_counts": {"accepted": 1, "rejected": 1},
                "selected_rewards": [
                    {
                        "symbol": "REJ_FINAL_WIN",
                        "source_family": "rejected",
                        "source_group": "final_rejected_0",
                        "evidence_class": "fast_profit_then_collapse",
                        "recommended_policy": "quick_take_profit",
                        "replay_reward_policy": "quick_take_profit",
                        "replay_reward_pct": 20.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.97,
                    },
                    {
                        "symbol": "ACC_FINAL_WIN",
                        "source_family": "accepted",
                        "source_group": "final_accepted_0",
                        "evidence_class": "post_target_continuation",
                        "recommended_policy": "continue_hold",
                        "replay_reward_policy": "continue_hold",
                        "replay_reward_pct": 50.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.97,
                    },
                ],
            },
        }

        report = p.build_action_policy_reward_lcb_report(
            reward_report,
            bootstrap_samples=500,
            confidence_level=0.9,
            min_selected_per_family=1,
            seed=7,
        )

        self.assertEqual(report["decision"], "shadow_reward_positive_lcb_replay_required")
        self.assertTrue(report["support_gate"]["passes"])
        self.assertGreater(report["validation"]["reward_lcb_pct"], 0.0)
        self.assertGreater(report["final"]["reward_lcb_pct"], 0.0)
        self.assertLessEqual(report["validation"]["reward_lcb_pct"], report["validation"]["selected_average_reward_pct"])
        self.assertLessEqual(report["final"]["reward_lcb_pct"], report["final"]["selected_average_reward_pct"])

    def test_bootstrap_lcb_report_marks_family_support_shortage_as_shadow_only(self):
        reward_report = {
            "validation": {
                "selected_count": 2,
                "selected_family_counts": {"accepted": 1, "rejected": 1},
                "selected_rewards": [
                    {
                        "symbol": "REJ_VALID_WIN",
                        "source_family": "rejected",
                        "source_group": "validation_rejected_0",
                        "evidence_class": "fast_profit_then_collapse",
                        "recommended_policy": "quick_take_profit",
                        "replay_reward_policy": "quick_take_profit",
                        "replay_reward_pct": 25.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.99,
                    },
                    {
                        "symbol": "ACC_VALID_WIN",
                        "source_family": "accepted",
                        "source_group": "validation_accepted_0",
                        "evidence_class": "post_target_continuation",
                        "recommended_policy": "continue_hold",
                        "replay_reward_policy": "continue_hold",
                        "replay_reward_pct": 60.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.99,
                    },
                ],
            },
            "final": {
                "selected_count": 1,
                "selected_family_counts": {"accepted": 1},
                "selected_rewards": [
                    {
                        "symbol": "ACC_FINAL_WIN",
                        "source_family": "accepted",
                        "source_group": "final_accepted_0",
                        "evidence_class": "post_target_continuation",
                        "recommended_policy": "continue_hold",
                        "replay_reward_policy": "continue_hold",
                        "replay_reward_pct": 50.0,
                        "replay_reward_known": True,
                        "meta_probability": 0.97,
                    }
                ],
            },
        }

        report = p.build_action_policy_reward_lcb_report(
            reward_report,
            bootstrap_samples=200,
            confidence_level=0.9,
            min_selected_per_family=1,
            seed=7,
        )

        self.assertEqual(report["decision"], "shadow_only_support_limited")
        self.assertFalse(report["support_gate"]["passes"])
        self.assertIn("final_rejected_selection_below_min", report["support_gate"]["reasons"])


if __name__ == "__main__":
    unittest.main()
