import unittest

from src.pipeline import action_policy_live_shadow as shadow


class FakeRuntime:
    enabled = True
    min_confidence = 0.4
    min_live_features = 2
    route_names = ["continue_hold", "skip"]
    feature_names = ["prob", "pred_return", "volume_30s"]
    metadata = {"trained": True}

    def predict(self, *, lifecycle, features, prob, pred_return, token_address=None, sample_time=None, create_timestamp=None):
        used = float(prob) >= 0.98 and float(pred_return or 0.0) >= 35.0
        return {
            "used": used,
            "route": "continue_hold" if used else "skip",
            "confidence": 0.75 if used else 0.25,
            "reason": "continue_hold" if used else "non_continue_hold_route",
            "live_feature_count": len(features),
            "route_probabilities": {"continue_hold": 0.75 if used else 0.25, "skip": 0.25 if used else 0.75},
        }


class ActionPolicyLiveShadowTest(unittest.TestCase):
    def test_matches_queued_signal_to_live_trade_and_summarizes_shadow_route(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-05-29 00:00:00",
                "token": "0xabc",
                "symbol": "ABC",
                "prob": 0.99,
                "pred_return": 40.0,
                "volume_30s": 2.0,
                "price_volatility": 0.2,
                "token_age_seconds": 30.0,
                "min_pred_return": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.1,
            }
        ]
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xabc",
                "symbol": "ABC",
                "entry_signal_time": "2026-05-29 00:00:01",
                "time": "2026-05-29 00:00:03",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xabc",
                "symbol": "ABC",
                "time": "2026-05-29 00:01:00",
                "reason": "PPO_SELL100",
                "net_profit": 0.001,
                "is_real_trade": True,
            },
        ]

        report = shadow.build_live_shadow_report(
            signal_rows=signal_rows,
            trade_rows=trade_rows,
            runtime=FakeRuntime(),
            since="2026-05-29 00:00:00",
            active_model="model",
        )

        self.assertEqual(report["summary"]["signal_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_matched_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_matched_net_profit_bnb"], 0.001)
        self.assertEqual(report["go_no_go"]["status"], "has_matched_shadow_route")

    def test_runtime_params_are_derived_from_live_signal_rows(self):
        params = shadow.runtime_params_from_signal_rows(
            [
                {
                    "min_pred_return": 36.0,
                    "min_entry_volume_30s": 1.7,
                    "min_entry_price_volatility": 0.12,
                    "buy_near_threshold_min_prob": 0.93,
                }
            ],
            primary_min_prob=0.981,
        )

        self.assertEqual(params["buy_threshold"], 0.981)
        self.assertEqual(params["min_entry_score"], 36.0)
        self.assertEqual(params["min_entry_volume_30s"], 1.7)
        self.assertEqual(params["min_entry_price_volatility"], 0.12)
        self.assertEqual(params["buy_near_threshold_min_prob"], 0.93)


if __name__ == "__main__":
    unittest.main()
