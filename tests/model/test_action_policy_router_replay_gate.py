import unittest
from unittest.mock import patch

from src.pipeline import action_policy_replay_gate as gate


class _FakeBuyModel:
    def predict_proba(self, rows):
        return [[0.01, 0.99] for _row in rows]


class _FakeEntryModel:
    def predict(self, rows):
        return [40.0 for _row in rows]


class TestActionPolicyRouterReplayGate(unittest.TestCase):
    def test_scores_candidate_gate_eval_samples_into_action_routes(self):
        train_rejected = {
            "candidate_sample": [
                {
                    "symbol": "REJ_QTP",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 40.0,
                    "volume_30s": 1.0,
                    "sell_volume_30s": 0.1,
                    "total_flow_volume_30s": 1.1,
                    "sell_pressure_30s": 0.1,
                    "flow_buy_sell_ratio_30s": 10.0,
                    "flow_total_volume_30s": 1.1,
                    "flow_sell_pressure_30s": 0.1,
                    "buy_sell_overlap_ratio_60s": 0.10,
                    "recent_seller_reentry_ratio_30s": 0.02,
                    "buyer_set_churn_10s_vs_prev50s": 0.3,
                },
                {
                    "symbol": "REJ_SKIP",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 40.0,
                    "volume_30s": 0.2,
                    "sell_volume_30s": 1.5,
                    "total_flow_volume_30s": 1.7,
                    "sell_pressure_30s": 1.5,
                    "flow_buy_sell_ratio_30s": 0.13333333333333333,
                    "flow_total_volume_30s": 1.7,
                    "flow_sell_pressure_30s": 1.5,
                    "buy_sell_overlap_ratio_60s": 0.95,
                    "recent_seller_reentry_ratio_30s": 0.6,
                    "buyer_set_churn_10s_vs_prev50s": 0.9,
                },
            ]
        }
        train_accepted = {
            "candidate_sample": [
                {
                    "symbol": "ACC_HOLD",
                    "classification": "post_target_continuation",
                    "recommended_policy": "continue_hold",
                    "prob": 0.99,
                    "pred_return": 55.0,
                    "volume_30s": 2.5,
                    "sell_volume_30s": 0.2,
                    "total_flow_volume_30s": 2.7,
                    "sell_pressure_30s": 0.2,
                    "flow_buy_sell_ratio_30s": 12.5,
                    "flow_total_volume_30s": 2.7,
                    "flow_sell_pressure_30s": 0.2,
                    "buy_sell_overlap_ratio_60s": 0.15,
                    "recent_seller_reentry_ratio_30s": 0.05,
                    "buyer_set_churn_10s_vs_prev50s": 0.1,
                    "post_target_window_returns_pct": {"60": 50.0},
                }
            ]
        }
        episode = [
            {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": 1.8,
                    "price_volatility": 0.16,
                    "sell_volume_30s": 0.1,
                    "total_flow_volume_30s": 1.9,
                    "sell_pressure_30s": 0.1,
                    "buy_sell_overlap_ratio_60s": 0.11,
                    "recent_seller_reentry_ratio_30s": 0.04,
                    "buyer_set_churn_10s_vs_prev50s": 0.15,
                },
                "meta": {"token_address": "0xroute", "sample_time": 100, "create_timestamp": 70},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "volume_30s": 1.8,
                    "price_volatility": 0.16,
                    "sell_volume_30s": 1.5,
                    "total_flow_volume_30s": 3.3,
                    "sell_pressure_30s": 1.5,
                    "buy_sell_overlap_ratio_60s": 0.95,
                    "recent_seller_reentry_ratio_30s": 0.6,
                    "buyer_set_churn_10s_vs_prev50s": 0.9,
                },
                "meta": {"token_address": "0xroute", "sample_time": 105, "create_timestamp": 70},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "volume_30s": 1.8,
                    "price_volatility": 0.16,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                },
                "meta": {"token_address": "0xroute", "sample_time": 110, "create_timestamp": 70},
            },
        ]
        buy_artifact = {
            "model": _FakeBuyModel(),
            "entry_value_model": {"model": _FakeEntryModel()},
            "feature_names": ["current_price", "volume_30s", "price_volatility"],
            "dropped_features": [
                "buyer_set_churn_10s_vs_prev50s",
                "buy_sell_overlap_ratio_60s",
                "recent_seller_reentry_ratio_30s",
                "sell_pressure_30s",
                "sell_volume_30s",
                "total_flow_volume_30s",
            ],
        }
        runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.10,
        }

        route_maps, metadata = gate.fit_action_policy_router_and_route_episodes(
            train_rejected_reports=[train_rejected],
            train_accepted_reports=[train_accepted],
            eval_episodes=[episode],
            buy_artifact=buy_artifact,
            runtime_params=runtime_params,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
        )

        self.assertTrue(metadata["trained"])
        self.assertEqual(metadata["intended_use"], "action_policy_router_route_map_for_replay_only")
        self.assertIn("flow_buy_sell_ratio_30s", metadata["feature_names"])
        self.assertIn("flow_total_volume_30s", metadata["feature_names"])
        self.assertIn("flow_sell_pressure_30s", metadata["feature_names"])
        self.assertEqual(route_maps[0]["__episode_meta__"]["token"], "0xroute")
        self.assertIn(route_maps[0][0]["route"], {"continue_hold", "quick_take_profit"})
        self.assertGreaterEqual(route_maps[0][0]["confidence"], 0.5)
        self.assertIn(route_maps[0][1]["route"], metadata["route_names"])
        self.assertGreaterEqual(route_maps[0][1]["confidence"], 0.0)

    def test_router_route_map_preserves_decision_time_candidate_fields(self):
        train_rejected = {
            "candidate_sample": [{
                "symbol": "REJ_SKIP",
                "recommended_policy": "skip",
                "prob": 0.99,
                "pred_return": 75.0,
                "volume_30s": 1.8,
                "price_volatility": 0.16,
                "flow_sell_pressure_30s": 0.9,
                "time_to_minus_18_seconds": 5.0,
            }]
        }
        train_accepted = {
            "candidate_sample": [{
                "symbol": "ACC_RUNNER",
                "classification": "post_target_continuation",
                "recommended_policy": "continue_hold",
                "prob": 0.99,
                "pred_return": 40.0,
                "volume_30s": 2.0,
                "price_volatility": 0.2,
                "flow_sell_pressure_30s": 0.1,
                "post_target_window_returns_pct": {"60": 50.0},
            }]
        }
        eval_episode = [
            {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": 2.4,
                    "price_volatility": 0.18,
                    "flow_sell_pressure_30s": 0.1,
                },
                "meta": {"token_address": "0xguard", "sample_time": 100, "create_timestamp": 70},
            },
            {
                "features": {
                    "current_price": 1.2,
                    "volume_30s": 2.5,
                    "price_volatility": 0.20,
                    "flow_sell_pressure_30s": 0.1,
                },
                "meta": {"token_address": "0xguard", "sample_time": 130, "create_timestamp": 70},
            },
        ]

        with patch.object(gate.ranker_probe, "_score_samples", return_value=([0.989], [42.0])):
            route_maps, metadata = gate.fit_action_policy_router_and_route_episodes(
                train_rejected_reports=[train_rejected],
                train_accepted_reports=[train_accepted],
                eval_episodes=[eval_episode],
                buy_artifact={},
                runtime_params={"buy_threshold": 0.98, "min_entry_score": 35.0},
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertEqual(metadata["scored_candidate_count"], 1)
        route = route_maps[0][0]
        self.assertIn(route["route"], {"continue_hold", "skip"})
        self.assertEqual(route["prob"], 0.989)
        self.assertEqual(route["pred_return"], 42.0)
        self.assertEqual(route["volume_30s"], 2.4)
        self.assertEqual(route["price_volatility"], 0.18)
        self.assertEqual(route["age_seconds"], 30.0)


if __name__ == "__main__":
    unittest.main()
