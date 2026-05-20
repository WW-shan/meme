import unittest

from src.pipeline.train_hybrid import _run_eval_replay


def _sample(token, sample_time, price, *, age=9, volume_30s=3.2, price_volatility=0.27):
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


def _episode(**overrides):
    first = _sample("0xshadow", 100, 1.0, **overrides)
    second = _sample("0xshadow", 101, 1.05, **overrides)
    third = _sample("0xshadow", 103, 1.10, **overrides)
    return [first, second, third]


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
        "max_hold_seconds": 2,
        "initial_equity_bnb": 1.0,
        "max_open_positions": 8,
        "entry_ranking_mode": "entry_value",
        "min_entry_score": 35.0,
        "min_entry_volume_30s": 1.5,
        "min_entry_price_volatility": 0.10,
        "buy_probabilities_by_episode": [{0: 0.989}],
        "entry_scores_by_episode": [{0: -4.5}],
        "shadow_scores_by_episode": [{0: 0.75}],
    }
    kwargs.update(overrides)
    return kwargs


def _shadow_gate_kwargs(**overrides):
    kwargs = {
        "buy_shadow_meta_gate_min_prob": 0.988,
        "buy_shadow_meta_gate_max_entry_score": 10.0,
        "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
        "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
        "buy_shadow_meta_gate_max_age_seconds": 60.0,
        "buy_shadow_meta_gate_min_score": 0.50,
    }
    kwargs.update(overrides)
    return kwargs


class TestShadowMetaGateReplay(unittest.TestCase):
    def test_shadow_scores_are_default_off_for_score_rejected_primary_candidates(self):
        result = _run_eval_replay(**_base_replay_kwargs())

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["entry_signal_count"], 1)
        self.assertEqual(result["entry_score_reject_count"], 1)
        self.assertEqual(result["shadow_meta_gate_signal_count"], 0)
        self.assertEqual(result["shadow_meta_gate_entry_count"], 0)

    def test_shadow_meta_gate_rescues_learned_score_reject_candidate(self):
        result = _run_eval_replay(**_base_replay_kwargs(**_shadow_gate_kwargs()))

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["entry_score_reject_count"], 0)
        self.assertEqual(result["shadow_meta_gate_signal_count"], 1)
        self.assertEqual(result["shadow_meta_gate_entry_count"], 1)
        self.assertEqual(result["shadow_meta_gate_reject_count"], 0)
        self.assertTrue(result["trade_log"][0]["shadow_meta_gate_used"])

    def test_shadow_meta_gate_applies_probability_score_quality_age_and_meta_score_guards(self):
        cases = [
            ("probability", {"buy_probabilities_by_episode": [{0: 0.987}]}),
            ("entry_score", {"entry_scores_by_episode": [{0: 15.0}]}),
            ("volume", {"episodes": [_episode(volume_30s=1.99)]}),
            ("volatility", {"episodes": [_episode(price_volatility=0.19)]}),
            ("age", {"episodes": [_episode(age=61)]}),
            ("meta_score", {"shadow_scores_by_episode": [{0: 0.49}]}),
        ]

        for name, overrides in cases:
            with self.subTest(name=name):
                kwargs = _base_replay_kwargs(**_shadow_gate_kwargs())
                kwargs.update(overrides)

                result = _run_eval_replay(**kwargs)

                self.assertEqual(result["total_trades"], 0)
                self.assertEqual(result["shadow_meta_gate_signal_count"], 1)
                self.assertEqual(result["shadow_meta_gate_entry_count"], 0)
                self.assertEqual(result["shadow_meta_gate_reject_count"], 1)


if __name__ == "__main__":
    unittest.main()
