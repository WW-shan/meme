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
    def predict_proba(self, frame):
        return [[0.01, 0.99] for _ in range(len(frame))]


def _sample(
    *,
    token="0xlatepump",
    sample_time=100,
    create_timestamp=100,
    price=1.0,
    volume_30s=3.2,
    price_volatility=0.24,
):
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }


class TestLatePumpExhaustionVetoReplay(unittest.TestCase):
    def _run_veto_case(self, *, candidate_sample, early_sample=None, **overrides):
        m = _load_module()
        early_sample = early_sample or _sample(sample_time=280, create_timestamp=100, price=1.0)
        episodes = [[
            early_sample,
            candidate_sample,
            _sample(sample_time=320, create_timestamp=100, price=2.0),
        ]]
        config = {
            "buy_probabilities_by_episode": [{1: 0.99}],
            "entry_scores_by_episode": [{1: 40.0}],
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 3.0,
            "min_entry_price_volatility": 0.20,
            "buy_late_pump_veto_min_age_seconds": 200,
            "buy_late_pump_veto_extension_window_seconds": 30,
            "buy_late_pump_veto_min_price_extension_pct": 1.0,
            "buy_late_pump_veto_min_entry_volume_30s": 3.0,
            "buy_late_pump_veto_min_entry_price_volatility": 0.20,
            "position_fraction": 0.1,
            "include_trade_log": True,
        }
        config.update(overrides)
        return m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            **config,
        )

    def test_late_pump_exhaustion_veto_rejects_extended_old_candidate_after_entry_gates(self):
        result = self._run_veto_case(
            candidate_sample=_sample(
                sample_time=310,
                create_timestamp=100,
                price=2.1,
                volume_30s=3.2,
                price_volatility=0.24,
            ),
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["entry_score_reject_count"], 0)
        self.assertEqual(result["entry_quality_reject_count"], 0)
        self.assertEqual(result["late_pump_veto_signal_count"], 1)
        self.assertEqual(result["late_pump_veto_reject_count"], 1)
        self.assertEqual(result["trade_log"], [])
        self.assertEqual(result["buy_late_pump_veto_min_age_seconds"], 200.0)
        self.assertEqual(result["buy_late_pump_veto_extension_window_seconds"], 30.0)
        self.assertEqual(result["buy_late_pump_veto_min_price_extension_pct"], 1.0)
        self.assertEqual(result["buy_late_pump_veto_min_entry_volume_30s"], 3.0)
        self.assertEqual(result["buy_late_pump_veto_min_entry_price_volatility"], 0.20)

    def test_late_pump_exhaustion_veto_allows_younger_less_extended_candidate(self):
        result = self._run_veto_case(
            early_sample=_sample(sample_time=280, create_timestamp=100, price=1.6),
            candidate_sample=_sample(
                sample_time=310,
                create_timestamp=190,
                price=2.1,
                volume_30s=3.2,
                price_volatility=0.24,
            ),
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["late_pump_veto_signal_count"], 0)
        self.assertEqual(result["late_pump_veto_reject_count"], 0)
        self.assertEqual(result["trade_log"][0]["token"], "0xlatepump")

    def test_late_pump_exhaustion_veto_rejects_recent_peak_then_fade_candidate(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, create_timestamp=100, price=1.0),
            _sample(sample_time=105, create_timestamp=100, price=2.6),
            _sample(sample_time=115, create_timestamp=100, price=1.6),
            _sample(sample_time=122, create_timestamp=100, price=1.05),
            _sample(sample_time=150, create_timestamp=100, price=1.0),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{3: 0.99}],
            entry_scores_by_episode=[{3: 40.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=3.0,
            min_entry_price_volatility=0.20,
            buy_late_pump_veto_min_age_seconds=15,
            buy_late_pump_veto_extension_window_seconds=30,
            buy_late_pump_veto_min_price_extension_pct=1.0,
            buy_late_pump_veto_min_drawdown_from_peak_pct=0.45,
            buy_late_pump_veto_min_entry_volume_30s=3.0,
            buy_late_pump_veto_min_entry_price_volatility=0.20,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["late_pump_veto_signal_count"], 1)
        self.assertEqual(result["late_pump_veto_reject_count"], 1)
        self.assertEqual(result["buy_late_pump_veto_min_drawdown_from_peak_pct"], 0.45)

    def test_late_pump_exhaustion_veto_requires_chronological_low_peak_fade(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, create_timestamp=100, price=2.6),
            _sample(sample_time=105, create_timestamp=100, price=1.0),
            _sample(sample_time=122, create_timestamp=100, price=1.05),
            _sample(sample_time=150, create_timestamp=100, price=1.0),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{2: 0.99}],
            entry_scores_by_episode=[{2: 40.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=3.0,
            min_entry_price_volatility=0.20,
            buy_late_pump_veto_min_age_seconds=15,
            buy_late_pump_veto_extension_window_seconds=30,
            buy_late_pump_veto_min_price_extension_pct=1.0,
            buy_late_pump_veto_min_drawdown_from_peak_pct=0.45,
            buy_late_pump_veto_min_entry_volume_30s=3.0,
            buy_late_pump_veto_min_entry_price_volatility=0.20,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["late_pump_veto_reject_count"], 0)

    def test_run_ab_evaluation_propagates_late_pump_veto_replay_params(self):
        m = _load_module()
        veto_params = {
            "buy_late_pump_veto_min_age_seconds": 210,
            "buy_late_pump_veto_extension_window_seconds": 30,
            "buy_late_pump_veto_min_price_extension_pct": 1.0,
            "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
            "buy_late_pump_veto_min_entry_volume_30s": 3.2,
            "buy_late_pump_veto_min_entry_price_volatility": 0.24,
        }
        calls = []

        def fake_replay(episodes, buy_model, threshold, sell_policy, **kwargs):
            calls.append(dict(kwargs))
            return {
                "total_trades": 1,
                "entry_count": 1,
                "entry_rate": 0.5,
                "win_rate": 1.0,
                "net_return_pct": 10.0,
                "max_drawdown_pct": 0.0,
                "sortino_ratio": 1.0,
                "stake_mode": "fraction",
                "final_equity_bnb": 1.01,
                "net_profit_bnb": 0.01,
                "account_multiple": 1.01,
                "max_open_positions": kwargs.get("max_open_positions"),
                "late_pump_veto_signal_count": 4,
                "late_pump_veto_reject_count": 3,
                **{key: kwargs.get(key) for key in veto_params},
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
            "stress_replay_scenarios": [{"name": "stress_late_pump"}],
            "walk_forward_segments": 2,
            **veto_params,
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
            for key, value in veto_params.items():
                self.assertEqual(call.get(key), value)
        for key, value in veto_params.items():
            self.assertEqual(result.get(key), value)
            self.assertEqual(result["runtime_replay"].get(key), value)
            self.assertEqual(result["all_in_replay"].get(key), value)
            self.assertEqual(result["stress_replay"][0].get(key), value)
            self.assertEqual(result["walk_forward"][0].get(key), value)
        self.assertEqual(result["late_pump_veto_signal_count"], 4)
        self.assertEqual(result["late_pump_veto_reject_count"], 3)


if __name__ == "__main__":
    unittest.main()
