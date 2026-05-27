import unittest

from src.pipeline.train_hybrid import _run_eval_replay


def _sample(token, sample_time, price):
    return {
        "features": {
            "current_price": price,
            "volume_30s": 2.0,
            "price_volatility": 0.2,
        },
        "label": {},
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - 10,
        },
    }


def _episode(token="0xrouter"):
    return [
        _sample(token, 100, 1.0),
        _sample(token, 101, 1.30),
        _sample(token, 130, 1.20),
    ]


def _base_kwargs(**overrides):
    kwargs = {
        "episodes": [_episode()],
        "buy_model": None,
        "threshold": 0.98,
        "sell_policy": None,
        "stop_loss": -0.50,
        "position_fraction": 0.1,
        "max_position_fraction": 0.1,
        "include_trade_log": True,
        "one_entry_per_token": True,
        "max_hold_seconds": 60,
        "initial_equity_bnb": 1.0,
        "max_open_positions": 8,
        "entry_ranking_mode": "entry_value",
        "min_entry_score": 35.0,
        "min_entry_volume_30s": 1.5,
        "min_entry_price_volatility": 0.10,
        "buy_probabilities_by_episode": [{0: 0.989}],
        "entry_scores_by_episode": [{0: 40.0}],
    }
    kwargs.update(overrides)
    return kwargs


class TestActionPolicyRouterReplay(unittest.TestCase):
    def test_action_policy_router_default_off_preserves_primary_entry(self):
        result = _run_eval_replay(**_base_kwargs())

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["action_policy_router_signal_count"], 0)
        self.assertEqual(result["action_policy_router_entry_count"], 0)
        self.assertEqual(result["action_policy_router_reject_count"], 0)

    def test_action_policy_router_skip_route_rejects_primary_candidate(self):
        result = _run_eval_replay(
            **_base_kwargs(
                action_policy_routes_by_episode=[{0: {"route": "skip", "confidence": 0.92}}],
                buy_action_policy_router_min_confidence=0.55,
            )
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["action_policy_router_signal_count"], 1)
        self.assertEqual(result["action_policy_router_entry_count"], 0)
        self.assertEqual(result["action_policy_router_quick_take_profit_entry_count"], 0)
        self.assertEqual(result["action_policy_router_reject_count"], 1)

    def test_action_policy_router_skip_passthrough_preserves_primary_candidate(self):
        result = _run_eval_replay(
            **_base_kwargs(
                action_policy_routes_by_episode=[{0: {"route": "skip", "confidence": 0.92}}],
                buy_action_policy_router_min_confidence=0.55,
                buy_action_policy_router_skip_passthrough=True,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["action_policy_router_signal_count"], 1)
        self.assertEqual(result["action_policy_router_entry_count"], 0)
        self.assertEqual(result["action_policy_router_quick_take_profit_entry_count"], 0)
        self.assertEqual(result["action_policy_router_reject_count"], 0)
        self.assertEqual(result["action_policy_router_passthrough_count"], 1)

    def test_action_policy_router_passthrough_preserves_low_confidence_candidate(self):
        result = _run_eval_replay(
            **_base_kwargs(
                action_policy_routes_by_episode=[{0: {"route": "quick_take_profit", "confidence": 0.40}}],
                buy_action_policy_router_min_confidence=0.55,
                buy_action_policy_router_skip_passthrough=True,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["action_policy_router_signal_count"], 1)
        self.assertEqual(result["action_policy_router_entry_count"], 0)
        self.assertEqual(result["action_policy_router_reject_count"], 0)
        self.assertEqual(result["action_policy_router_passthrough_count"], 1)

    def test_action_policy_router_quick_take_profit_route_uses_quick_exit(self):
        result = _run_eval_replay(
            **_base_kwargs(
                action_policy_routes_by_episode=[{"0": {"route": "quick_take_profit", "confidence": 0.91}}],
                buy_action_policy_router_min_confidence=0.55,
                buy_quick_profit_overlay_take_profit_pct=0.25,
                buy_quick_profit_overlay_max_hold_seconds=120.0,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["action_policy_router_signal_count"], 1)
        self.assertEqual(result["action_policy_router_entry_count"], 1)
        self.assertEqual(result["action_policy_router_quick_take_profit_entry_count"], 1)
        self.assertEqual(result["quick_profit_overlay_entry_count"], 1)
        self.assertEqual(result["quick_profit_overlay_take_profit_count"], 1)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "QUICK_PROFIT_OVERLAY_TAKE_PROFIT")


if __name__ == "__main__":
    unittest.main()
