import json
import tempfile
import unittest
from pathlib import Path

from src.model.action_policy_router_runtime import ActionPolicyRouterRuntime


def _accepted_report():
    return {
        "candidate_sample": [
            {
                "symbol": "ACC",
                "classification": "post_target_continuation",
                "recommended_policy": "continue_hold",
                "prob": 0.99,
                "pred_return": 55.0,
                "volume_30s": 2.5,
                "price_volatility": 0.2,
                "flow_buy_sell_ratio_30s": 12.0,
                "flow_total_volume_30s": 2.6,
                "flow_signed_imbalance_30s": 2.2,
                "post_target_window_returns_pct": {"60": 45.0},
            }
        ]
    }


def _rejected_report():
    return {
        "candidate_sample": [
            {
                "symbol": "REJ",
                "recommended_policy": "quick_take_profit",
                "prob": 0.99,
                "pred_return": 25.0,
                "volume_30s": 2.0,
                "price_volatility": 0.12,
                "flow_buy_sell_ratio_30s": 1.0,
                "flow_total_volume_30s": 2.3,
                "flow_signed_imbalance_30s": -0.4,
                "time_to_plus_25_seconds": 12.0,
            }
        ]
    }


class TestActionPolicyRouterRuntime(unittest.TestCase):
    def _write_report(self, root: Path, name: str, payload: dict) -> str:
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_runtime_predicts_high_confidence_continue_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accepted = self._write_report(root, "accepted.json", _accepted_report())
            rejected = self._write_report(root, "rejected.json", _rejected_report())
            runtime = ActionPolicyRouterRuntime.from_report_paths(
                train_rejected_report_paths=[rejected],
                train_accepted_report_paths=[accepted],
                runtime_params={
                    "buy_threshold": 0.98,
                    "min_entry_score": 35.0,
                    "min_entry_volume_30s": 1.5,
                    "min_entry_price_volatility": 0.10,
                },
                min_confidence=0.40,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
                min_live_features=1,
            )

        decision = runtime.predict(
            lifecycle={"last_update": 100, "create_timestamp": 70},
            features={
                "current_price": 1.0,
                "volume_30s": 2.5,
                "price_volatility": 0.2,
                "flow_buy_sell_ratio_30s": 12.0,
                "flow_total_volume_30s": 2.6,
                "flow_signed_imbalance_30s": 2.2,
            },
            prob=0.99,
            pred_return=55.0,
            token_address="0xToken",
        )

        self.assertTrue(runtime.enabled)
        self.assertTrue(decision["used"])
        self.assertEqual(decision["route"], "continue_hold")
        self.assertGreaterEqual(decision["confidence"], 0.40)

    def test_runtime_passes_through_when_live_feature_support_is_too_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            accepted = self._write_report(root, "accepted.json", _accepted_report())
            rejected = self._write_report(root, "rejected.json", _rejected_report())
            runtime = ActionPolicyRouterRuntime.from_report_paths(
                train_rejected_report_paths=[rejected],
                train_accepted_report_paths=[accepted],
                runtime_params={"buy_threshold": 0.98, "min_entry_score": 35.0},
                min_confidence=0.40,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
                min_live_features=99,
            )

        decision = runtime.predict(
            lifecycle={"last_update": 100, "create_timestamp": 70},
            features={"current_price": 1.0},
            prob=0.99,
            pred_return=55.0,
            token_address="0xToken",
        )

        self.assertFalse(decision["used"])
        self.assertEqual(decision["reason"], "live_feature_count_below_min")


if __name__ == "__main__":
    unittest.main()
