import unittest

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
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "time_to_plus_25_seconds": 5.0,
                },
                {
                    "symbol": "REJ_SKIP",
                    "recommended_policy": "skip",
                    "prob": 0.99,
                    "pred_return": 40.0,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
                    "time_to_minus_18_seconds": 5.0,
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
                    "flow_buy_sell_overlap_ratio_60s": 0.15,
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
                    "flow_buy_sell_overlap_ratio_60s": 0.11,
                },
                "meta": {"token_address": "0xroute", "sample_time": 100, "create_timestamp": 70},
            },
            {
                "features": {
                    "current_price": 1.1,
                    "volume_30s": 1.8,
                    "price_volatility": 0.16,
                    "flow_buy_sell_overlap_ratio_60s": 0.95,
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
            "feature_names": ["current_price", "volume_30s", "price_volatility", "flow_buy_sell_overlap_ratio_60s"],
            "dropped_features": [],
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
        self.assertIn("flow_buy_sell_overlap_ratio_60s", metadata["feature_names"])
        self.assertEqual(route_maps[0]["__episode_meta__"]["token"], "0xroute")
        self.assertEqual(route_maps[0][0]["route"], "quick_take_profit")
        self.assertGreaterEqual(route_maps[0][0]["confidence"], 0.5)
        self.assertEqual(route_maps[0][1]["route"], "skip")


if __name__ == "__main__":
    unittest.main()
