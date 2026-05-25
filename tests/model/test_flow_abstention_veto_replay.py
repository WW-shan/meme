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
    token="0xflowabstain",
    sample_time=120,
    create_timestamp=100,
    price=1.0,
    volume_30s=2.0,
    price_volatility=0.12,
    flow_buy_sell_ratio_30s=0.80,
    flow_sell_pressure_30s=0.56,
    flow_signed_imbalance_30s=-0.12,
):
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "flow_buy_sell_ratio_30s": flow_buy_sell_ratio_30s,
            "flow_sell_pressure_30s": flow_sell_pressure_30s,
            "flow_signed_imbalance_30s": flow_signed_imbalance_30s,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }


class TestFlowAbstentionVetoReplay(unittest.TestCase):
    def _run_case(self, *, sample_kwargs=None, buy_prob=0.99, **overrides):
        m = _load_module()
        sample_kwargs = dict(sample_kwargs or {})
        episodes = [[
            _sample(sample_time=120, price=1.0, **sample_kwargs),
            _sample(sample_time=180, price=1.1, **sample_kwargs),
        ]]
        config = {
            "buy_probabilities_by_episode": [{0: buy_prob}],
            "entry_scores_by_episode": [{0: 40.0}],
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.10,
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

    def test_flow_abstention_veto_is_default_off(self):
        result = self._run_case()

        self.assertEqual(result["total_trades"], 1)
        self.assertEqual(result["flow_abstention_veto_signal_count"], 0)
        self.assertEqual(result["flow_abstention_veto_reject_count"], 0)
        self.assertIsNone(result["buy_flow_abstention_min_prob"])
        self.assertIsNone(result["buy_flow_abstention_max_buy_sell_ratio_30s"])

    def test_flow_abstention_veto_rejects_toxic_current_flow_after_entry_gates(self):
        result = self._run_case(
            buy_flow_abstention_min_prob=0.98,
            buy_flow_abstention_max_age_seconds=60.0,
            buy_flow_abstention_min_entry_volume_30s=1.5,
            buy_flow_abstention_min_entry_price_volatility=0.10,
            buy_flow_abstention_max_buy_sell_ratio_30s=1.0,
            buy_flow_abstention_min_sell_pressure_30s=0.50,
            buy_flow_abstention_max_signed_imbalance_30s=0.0,
        )

        self.assertEqual(result["entry_signal_count"], 1)
        self.assertEqual(result["entry_score_reject_count"], 0)
        self.assertEqual(result["entry_quality_reject_count"], 0)
        self.assertEqual(result["flow_abstention_veto_signal_count"], 1)
        self.assertEqual(result["flow_abstention_veto_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])
        self.assertEqual(result["buy_flow_abstention_min_prob"], 0.98)
        self.assertEqual(result["buy_flow_abstention_max_age_seconds"], 60.0)
        self.assertEqual(result["buy_flow_abstention_min_entry_volume_30s"], 1.5)
        self.assertEqual(result["buy_flow_abstention_min_entry_price_volatility"], 0.10)
        self.assertEqual(result["buy_flow_abstention_max_buy_sell_ratio_30s"], 1.0)
        self.assertEqual(result["buy_flow_abstention_min_sell_pressure_30s"], 0.50)
        self.assertEqual(result["buy_flow_abstention_max_signed_imbalance_30s"], 0.0)

    def test_flow_abstention_veto_allows_missing_or_clean_flow(self):
        cases = [
            {"flow_buy_sell_ratio_30s": 2.0, "flow_sell_pressure_30s": 0.30, "flow_signed_imbalance_30s": 0.40},
            {"flow_buy_sell_ratio_30s": None, "flow_sell_pressure_30s": None, "flow_signed_imbalance_30s": None},
        ]
        for sample_kwargs in cases:
            with self.subTest(sample_kwargs=sample_kwargs):
                result = self._run_case(
                    sample_kwargs=sample_kwargs,
                    buy_flow_abstention_min_prob=0.98,
                    buy_flow_abstention_max_age_seconds=60.0,
                    buy_flow_abstention_min_entry_volume_30s=1.5,
                    buy_flow_abstention_min_entry_price_volatility=0.10,
                    buy_flow_abstention_max_buy_sell_ratio_30s=1.0,
                    buy_flow_abstention_min_sell_pressure_30s=0.50,
                    buy_flow_abstention_max_signed_imbalance_30s=0.0,
                )

                self.assertEqual(result["flow_abstention_veto_signal_count"], 0)
                self.assertEqual(result["flow_abstention_veto_reject_count"], 0)
                self.assertEqual(result["total_trades"], 1)

    def test_run_ab_evaluation_propagates_flow_abstention_params(self):
        m = _load_module()
        veto_params = {
            "buy_flow_abstention_min_prob": 0.98,
            "buy_flow_abstention_max_age_seconds": 60.0,
            "buy_flow_abstention_min_entry_volume_30s": 1.5,
            "buy_flow_abstention_min_entry_price_volatility": 0.10,
            "buy_flow_abstention_max_buy_sell_ratio_30s": 1.0,
            "buy_flow_abstention_min_sell_pressure_30s": 0.50,
            "buy_flow_abstention_max_signed_imbalance_30s": 0.0,
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
                "flow_abstention_veto_signal_count": 4,
                "flow_abstention_veto_reject_count": 3,
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
            "stress_replay_scenarios": [{"name": "stress_flow_abstention"}],
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
        self.assertEqual(result["flow_abstention_veto_signal_count"], 4)
        self.assertEqual(result["flow_abstention_veto_reject_count"], 3)


if __name__ == "__main__":
    unittest.main()
