import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _SellNonePolicy:
    def predict(self, obs, deterministic=True):
        return 0, None


class _FakeBuyModel:
    def predict_proba(self, rows):
        return [[0.01, 0.99] for _row in rows]


def _sample(
    *,
    token="0xdead",
    sample_time=110,
    create_timestamp=100,
    price=0.30,
    max_price=1.0,
    creator_is_seller=1,
    creator_sell_volume=2.0,
    buy_pressure=0.25,
    volume_30s=2.5,
    price_volatility=0.25,
):
    return {
        "features": {
            "current_price": price,
            "max_price": max_price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "creator_is_seller": creator_is_seller,
            "creator_sell_volume": creator_sell_volume,
            "buy_pressure": buy_pressure,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }


class TestDeadBounceVetoReplay(unittest.TestCase):
    def test_dead_bounce_veto_rejects_primary_signal_after_peak_crash_and_creator_sell(self):
        m = _load_module()
        episodes = [[_sample(), _sample(sample_time=120, price=0.28, max_price=1.0)]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["entry_signal_count"], 1)
        self.assertEqual(result["entry_score_reject_count"], 0)
        self.assertEqual(result["entry_quality_reject_count"], 0)
        self.assertEqual(result["dead_bounce_veto_signal_count"], 1)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])

    def test_dead_bounce_veto_allows_peak_drawdown_without_creator_or_sell_pressure(self):
        m = _load_module()
        episodes = [[
            _sample(creator_is_seller=0, creator_sell_volume=0.0, buy_pressure=0.55),
            _sample(
                sample_time=120,
                price=0.40,
                max_price=1.0,
                creator_is_seller=0,
                creator_sell_volume=0.0,
                buy_pressure=0.55,
            ),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_signal_count"], 0)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_requires_creator_sell_volume_floor(self):
        m = _load_module()
        episodes = [[
            _sample(creator_is_seller=1, creator_sell_volume=0.25, buy_pressure=0.55),
            _sample(
                sample_time=120,
                price=0.28,
                max_price=1.0,
                creator_is_seller=1,
                creator_sell_volume=0.25,
                buy_pressure=0.55,
            ),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_signal_count"], 0)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_uses_only_current_sample_features(self):
        m = _load_module()
        episodes = [[
            _sample(
                price=1.0,
                max_price=1.0,
                creator_is_seller=0,
                creator_sell_volume=0.0,
                buy_pressure=0.55,
            ),
            _sample(
                sample_time=120,
                price=0.30,
                max_price=2.0,
                creator_is_seller=1,
                creator_sell_volume=4.0,
                buy_pressure=0.1,
            ),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_does_not_apply_to_near_threshold_rescue_entries(self):
        m = _load_module()
        episodes = [[
            _sample(creator_is_seller=1, creator_sell_volume=2.0, buy_pressure=0.25),
            _sample(
                sample_time=120,
                price=0.28,
                max_price=1.0,
                creator_is_seller=1,
                creator_sell_volume=2.0,
                buy_pressure=0.25,
            ),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.95}],
            entry_scores_by_episode=[{0: 58.0}],
            buy_near_threshold_min_prob=0.94,
            buy_near_min_pred_return=35.0,
            buy_near_min_entry_volume_30s=1.5,
            buy_near_min_entry_price_volatility=0.10,
            buy_near_min_age_seconds=0.0,
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_signal_count"], 0)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["near_threshold_entry_count"], 1)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_rejects_invalid_runtime_params(self):
        m = _load_module()
        invalid = [
            {"buy_dead_bounce_veto_max_age_seconds": -1.0},
            {"buy_dead_bounce_veto_min_peak_drawdown_pct": float("nan")},
            {"buy_dead_bounce_veto_min_creator_sell_volume_bnb": -0.01},
            {"buy_dead_bounce_veto_max_buy_pressure": 1.5},
            {"buy_dead_bounce_veto_min_entry_volume_30s": float("inf")},
            {"buy_dead_bounce_veto_min_entry_price_volatility": -0.01},
        ]

        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    m._run_eval_replay(
                        [[_sample()]],
                        None,
                        0.98,
                        _SellNonePolicy(),
                        buy_probabilities_by_episode=[{0: 0.991}],
                        entry_scores_by_episode=[{0: 58.0}],
                        min_entry_score=35.0,
                        **overrides,
                    )

    def test_selected_runtime_params_exclude_dead_bounce_veto_replay_only_params(self):
        m = _load_module()
        selected = m._selected_runtime_params_from_evaluation({
            "buy_threshold": 0.98,
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
            "runtime_replay": {
                "buy_dead_bounce_veto_max_age_seconds": 20.0,
            },
        })
        self.assertEqual(selected["buy_threshold"], 0.98)
        for key in selected:
            self.assertFalse(key.startswith("buy_dead_bounce_veto_"))

    def test_run_ab_evaluation_propagates_dead_bounce_veto_replay_params(self):
        m = _load_module()
        params = {
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
            "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 1.0,
            "buy_dead_bounce_veto_max_buy_pressure": 0.35,
            "buy_dead_bounce_veto_min_entry_volume_30s": 1.5,
            "buy_dead_bounce_veto_min_entry_price_volatility": 0.10,
        }
        calls = []

        def fake_replay(episodes, buy_model, threshold, sell_policy, **kwargs):
            calls.append(dict(kwargs))
            return {
                "total_trades": 1,
                "entry_count": 1,
                "entry_rate": 0.5,
                "win_rate": 1.0,
                "net_return_pct": 12.0,
                "max_drawdown_pct": 0.0,
                "sortino_ratio": 1.0,
                "stake_mode": "fraction",
                "final_equity_bnb": 1.01,
                "net_profit_bnb": 0.01,
                "account_multiple": 1.01,
                "max_open_positions": kwargs.get("max_open_positions"),
                "dead_bounce_veto_signal_count": 3,
                "dead_bounce_veto_reject_count": 2,
                **{key: kwargs.get(key) for key in params},
            }

        eval_samples = [
            _sample(token="0xprop-a", sample_time=100),
            _sample(token="0xprop-a", sample_time=110),
            _sample(token="0xprop-b", sample_time=200),
            _sample(token="0xprop-b", sample_time=210),
        ]
        config = {
            "eval_samples": eval_samples,
            "position_fraction": 0.1,
            "stress_replay_scenarios": [{"name": "stress_dead_bounce"}],
            "walk_forward_segments": 2,
            **params,
        }

        with patch.object(m, "_run_eval_replay", side_effect=fake_replay):
            result = m.run_ab_evaluation(
                config,
                {"model": _FakeBuyModel(), "threshold": 0.98},
                {"model": _SellNonePolicy(), "total_timesteps": 0},
                {"bc_samples": 0},
            )

        self.assertGreaterEqual(len(calls), 5)
        for call in calls:
            for key, value in params.items():
                self.assertEqual(call.get(key), value)
        for key, value in params.items():
            self.assertEqual(result.get(key), value)
            self.assertEqual(result["runtime_replay"].get(key), value)
            self.assertEqual(result["all_in_replay"].get(key), value)
            self.assertEqual(result["stress_replay"][0].get(key), value)
            self.assertEqual(result["walk_forward"][0].get(key), value)
        self.assertEqual(result["dead_bounce_veto_signal_count"], 3)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 2)


if __name__ == "__main__":
    unittest.main()
