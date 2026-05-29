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
        return {
            "used": True,
            "route": "continue_hold",
            "confidence": 0.9,
            "reason": "continue_hold",
            "live_feature_count": len(features),
            "route_probabilities": {"continue_hold": 0.9, "skip": 0.1},
        }


class ActionPolicyActivationShadowTest(unittest.TestCase):
    def test_classifies_activation_release_and_stop_paths(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-05-29 00:00:00",
                "token": "0xaaa",
                "symbol": "AAA",
                "prob": 0.99,
                "pred_return": 40.0,
                "token_age_seconds": 30.0,
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-05-29 01:00:00",
                "token": "0xbbb",
                "symbol": "BBB",
                "prob": 0.99,
                "pred_return": 40.0,
                "token_age_seconds": 30.0,
            },
        ]
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xaaa",
                "symbol": "AAA",
                "entry_signal_time": "2026-05-29 00:00:00",
                "entry_price": 1.0,
                "time": "2026-05-29 00:00:01",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xaaa",
                "symbol": "AAA",
                "time": "2026-05-29 00:00:20",
                "reason": "PPO_SELL100",
                "net_profit": 0.001,
                "hold_duration": 20.0,
                "is_real_trade": True,
            },
            {
                "action": "OPEN",
                "token": "0xbbb",
                "symbol": "BBB",
                "entry_signal_time": "2026-05-29 01:00:00",
                "entry_price": 1.0,
                "time": "2026-05-29 01:00:01",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xbbb",
                "symbol": "BBB",
                "time": "2026-05-29 01:00:20",
                "reason": "STOP_LOSS",
                "net_profit": -0.001,
                "hold_duration": 20.0,
                "is_real_trade": True,
            },
        ]
        lifecycles = {
            "0xaaa": {
                "price_history": [
                    {"time": "2026-05-29 00:00:01", "price": 1.0},
                    {"time": "2026-05-29 00:00:05", "price": 1.4},
                    {"time": "2026-05-29 00:00:10", "price": 1.8},
                ]
            },
            "0xbbb": {
                "price_history": [
                    {"time": "2026-05-29 01:00:01", "price": 1.0},
                    {"time": "2026-05-29 01:00:05", "price": 1.4},
                    {"time": "2026-05-29 01:00:10", "price": 0.8},
                ]
            },
        }

        report = shadow.build_activation_shadow_report(
            signal_rows=signal_rows,
            trade_rows=trade_rows,
            lifecycles=lifecycles,
            runtime=FakeRuntime(),
            since="2026-05-29 00:00:00",
        )

        self.assertEqual(report["summary"]["queued_shadow_used_matched_count"], 2)
        self.assertEqual(report["summary"]["activation_hit_count"], 2)
        self.assertEqual(report["summary"]["release_hit_count"], 1)
        self.assertEqual(report["summary"]["activated_then_stop_count"], 1)
        self.assertEqual(report["summary"]["stop_before_activation_count"], 0)
        self.assertEqual(report["summary"]["outcome_counts"]["activated_released"], 1)
        self.assertEqual(report["summary"]["outcome_counts"]["activated_then_stop"], 1)

    def test_classifies_stop_before_late_activation_paths(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-05-29 02:00:00",
                "token": "0xccc",
                "symbol": "CCC",
                "prob": 0.99,
                "pred_return": 40.0,
                "token_age_seconds": 30.0,
            },
        ]
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xccc",
                "symbol": "CCC",
                "entry_signal_time": "2026-05-29 02:00:00",
                "entry_price": 1.0,
                "time": "2026-05-29 02:00:01",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xccc",
                "symbol": "CCC",
                "time": "2026-05-29 02:00:20",
                "reason": "PPO_SELL100",
                "net_profit": -0.001,
                "is_real_trade": True,
            },
        ]
        lifecycles = {
            "0xccc": {
                "price_history": [
                    {"time": "2026-05-29 02:00:01", "price": 1.0},
                    {"time": "2026-05-29 02:00:05", "price": 0.8},
                    {"time": "2026-05-29 02:00:10", "price": 1.4},
                ]
            },
        }

        report = shadow.build_activation_shadow_report(
            signal_rows=signal_rows,
            trade_rows=trade_rows,
            lifecycles=lifecycles,
            runtime=FakeRuntime(),
            since="2026-05-29 02:00:00",
        )

        self.assertEqual(report["summary"]["queued_shadow_used_matched_count"], 1)
        self.assertEqual(report["summary"]["activated_then_stop_count"], 0)
        self.assertEqual(report["summary"]["stop_before_activation_count"], 1)
        self.assertEqual(report["summary"]["outcome_counts"]["stop_before_activation"], 1)


if __name__ == "__main__":
    unittest.main()
