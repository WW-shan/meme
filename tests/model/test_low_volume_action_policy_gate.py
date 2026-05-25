import unittest

from src.pipeline.train_hybrid import _run_eval_replay


def _sample(token, sample_time, price, *, age=30, volume_30s=1.2, price_volatility=0.16):
    return {
        "features": {
            "current_price": price,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "total_buy_volume": 1.0,
            "total_sell_volume": 0.0,
        },
        "label": {},
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - age,
        },
    }


def _episode(token="0xlowvolume"):
    return [
        _sample(token, 100, 1.0),
        _sample(token, 105, 1.35),
        _sample(token, 110, 1.40),
    ]


def _base_replay_kwargs(**overrides):
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
        "max_hold_seconds": 8,
        "initial_equity_bnb": 1.0,
        "max_open_positions": 8,
        "entry_ranking_mode": "entry_value",
        "min_entry_score": 35.0,
        "min_entry_volume_30s": 1.5,
        "min_entry_price_volatility": 0.10,
        "buy_probabilities_by_episode": [{0: 0.989}],
        "entry_scores_by_episode": [{0: 40.0}],
        "buy_low_volume_rescue_min_prob": 0.982,
        "buy_low_volume_rescue_min_entry_volume_30s": 0.95,
        "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
        "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
        "buy_low_volume_rescue_max_age_seconds": 60.0,
        "buy_low_volume_rescue_take_profit_pct": 0.25,
    }
    kwargs.update(overrides)
    return kwargs


class TestLowVolumeActionPolicyGate(unittest.TestCase):
    def test_low_volume_rescue_default_score_gate_off_preserves_existing_entry(self):
        result = _run_eval_replay(**_base_replay_kwargs())

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["low_volume_rescue_signal_count"], 1)
        self.assertEqual(result["low_volume_rescue_entry_count"], 1)
        self.assertEqual(result["low_volume_rescue_reject_count"], 0)

    def test_low_volume_rescue_rejects_missing_action_policy_score_when_enabled(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                low_volume_rescue_scores_by_episode=[{}],
                buy_low_volume_rescue_min_action_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["low_volume_rescue_signal_count"], 1)
        self.assertEqual(result["low_volume_rescue_entry_count"], 0)
        self.assertEqual(result["low_volume_rescue_reject_count"], 1)

    def test_low_volume_rescue_rejects_low_action_policy_score(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                low_volume_rescue_scores_by_episode=[{0: 0.25}],
                buy_low_volume_rescue_min_action_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["low_volume_rescue_entry_count"], 0)
        self.assertEqual(result["low_volume_rescue_reject_count"], 1)

    def test_low_volume_rescue_allows_high_action_policy_score(self):
        result = _run_eval_replay(
            **_base_replay_kwargs(
                low_volume_rescue_scores_by_episode=[{"0": 0.75}],
                buy_low_volume_rescue_min_action_score=0.5,
            )
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["low_volume_rescue_entry_count"], 1)
        self.assertEqual(result["low_volume_rescue_reject_count"], 0)


if __name__ == "__main__":
    unittest.main()
