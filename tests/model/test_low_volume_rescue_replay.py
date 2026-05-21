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
    token="0xrescue",
    sample_time=120,
    price=1.0,
    volume_30s=1.0,
    price_volatility=0.08,
    total_buys=10,
    create_timestamp=100,
):
    meta = {
        "token_address": token,
        "sample_time": sample_time,
    }
    if create_timestamp is not None:
        meta["create_timestamp"] = create_timestamp
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "total_buys": total_buys,
        },
        "meta": meta,
    }


class TestLowVolumeRescueReplay(unittest.TestCase):
    def _run_rescue_case(self, *, sample_kwargs=None, buy_prob=0.99, entry_score=35.0, **overrides):
        m = _load_module()
        sample_kwargs = dict(sample_kwargs or {})
        episodes = [[
            _sample(sample_time=120, price=1.0, **sample_kwargs),
            _sample(sample_time=130, price=1.2, **sample_kwargs),
        ]]
        config = {
            "buy_probabilities_by_episode": [{0: buy_prob}],
            "entry_scores_by_episode": [{0: entry_score}],
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_prob": 0.98,
            "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
            "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_entry_price_volatility": 0.05,
            "buy_low_volume_rescue_max_age_seconds": 60,
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

    def test_low_volume_primary_signal_can_be_rescued(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=1.0, price_volatility=0.08),
            _sample(sample_time=130, price=1.2, volume_30s=1.2, price_volatility=0.10),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 35.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            buy_low_volume_rescue_min_prob=0.98,
            buy_low_volume_rescue_min_entry_volume_30s=0.75,
            buy_low_volume_rescue_max_entry_volume_30s=1.5,
            buy_low_volume_rescue_min_entry_price_volatility=0.05,
            buy_low_volume_rescue_max_age_seconds=60,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["low_volume_rescue_signal_count"], 1)
        self.assertEqual(result["low_volume_rescue_entry_count"], 1)
        self.assertEqual(result["entry_quality_reject_count"], 0)
        self.assertTrue(result["trade_log"][0]["low_volume_rescue_used"])
        self.assertEqual(result["buy_low_volume_rescue_min_prob"], 0.98)
        self.assertEqual(result["buy_low_volume_rescue_min_entry_volume_30s"], 0.75)
        self.assertEqual(result["buy_low_volume_rescue_max_entry_volume_30s"], 1.5)
        self.assertEqual(result["buy_low_volume_rescue_min_entry_price_volatility"], 0.05)
        self.assertEqual(result["buy_low_volume_rescue_max_age_seconds"], 60.0)
        self.assertIsNone(result["buy_low_volume_rescue_take_profit_pct"])

    def test_low_volume_rescue_does_not_rescue_normal_volume_volatility_reject(self):
        result = self._run_rescue_case(
            sample_kwargs={"volume_30s": 1.5, "price_volatility": 0.08},
            min_entry_price_volatility=0.10,
            buy_low_volume_rescue_max_entry_volume_30s=2.0,
        )

        self.assertEqual(result["low_volume_rescue_signal_count"], 0)
        self.assertEqual(result["low_volume_rescue_entry_count"], 0)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])

    def test_low_volume_rescue_uses_rescue_volatility_floor_for_low_volume_candidate(self):
        result = self._run_rescue_case(
            sample_kwargs={"volume_30s": 1.0, "price_volatility": 0.08},
            min_entry_price_volatility=0.10,
            buy_low_volume_rescue_min_entry_price_volatility=0.05,
        )

        self.assertEqual(result["low_volume_rescue_signal_count"], 1)
        self.assertEqual(result["low_volume_rescue_entry_count"], 1)
        self.assertEqual(result["total_trades"], 1)
        self.assertTrue(result["trade_log"][0]["low_volume_rescue_used"])

    def test_low_volume_rescue_rejects_boundary_failures(self):
        cases = [
            (
                "probability below rescue floor",
                {"buy_prob": 0.985, "buy_low_volume_rescue_min_prob": 0.99},
                1,
            ),
            ("volume below rescue min", {"sample_kwargs": {"volume_30s": 0.70}}, 0),
            (
                "volume above rescue max",
                {
                    "sample_kwargs": {"volume_30s": 1.60},
                    "min_entry_volume_30s": 2.0,
                },
                0,
            ),
            ("price volatility below rescue min", {"sample_kwargs": {"price_volatility": 0.04}}, 1),
            ("missing age", {"sample_kwargs": {"create_timestamp": None}}, 1),
            ("nan age", {"sample_kwargs": {"create_timestamp": float("nan")}}, 1),
            ("age above max", {"sample_kwargs": {"create_timestamp": 0}}, 1),
            ("score below min_entry_score", {"entry_score": 34.0}, 0),
        ]

        for label, kwargs, expected_signal_count in cases:
            with self.subTest(label=label):
                result = self._run_rescue_case(**kwargs)

                self.assertEqual(result["low_volume_rescue_signal_count"], expected_signal_count)
                self.assertEqual(result["low_volume_rescue_entry_count"], 0)
                self.assertEqual(result["total_trades"], 0)
                self.assertEqual(result["trade_log"], [])

    def test_low_volume_rescue_quick_take_profit_exits_before_later_stop_loss(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=1.0, price_volatility=0.08),
            _sample(sample_time=130, price=1.25, volume_30s=1.2, price_volatility=0.10),
            _sample(sample_time=140, price=0.82, volume_30s=1.2, price_volatility=0.10),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 35.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            stop_loss=-0.18,
            buy_low_volume_rescue_min_prob=0.98,
            buy_low_volume_rescue_min_entry_volume_30s=0.75,
            buy_low_volume_rescue_max_entry_volume_30s=1.5,
            buy_low_volume_rescue_min_entry_price_volatility=0.05,
            buy_low_volume_rescue_max_age_seconds=60,
            buy_low_volume_rescue_take_profit_pct=0.25,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["trade_log"][0]["exit_reason"], "LOW_VOLUME_TAKE_PROFIT")
        self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)

    def test_primary_score_rescue_quick_take_profit_exits_before_later_stop_loss(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30),
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32),
            _sample(sample_time=140, price=0.82, volume_30s=3.2, price_volatility=0.32),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 30.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            stop_loss=-0.18,
            buy_quick_profit_overlay_min_prob=0.988,
            buy_quick_profit_overlay_min_pred_return=25.0,
            buy_quick_profit_overlay_max_pred_return=35.0,
            buy_quick_profit_overlay_min_entry_volume_30s=1.5,
            buy_quick_profit_overlay_min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_max_age_seconds=60.0,
            buy_quick_profit_overlay_take_profit_pct=0.25,
            buy_quick_profit_overlay_max_hold_seconds=120.0,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["trade_log"][0]["exit_reason"], "QUICK_PROFIT_OVERLAY_TAKE_PROFIT")
        self.assertEqual(result["quick_profit_overlay_take_profit_count"], 1)
        self.assertTrue(result["trade_log"][0]["quick_profit_overlay_used"])
        self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)

    def test_primary_score_rescue_quick_take_profit_requires_min_total_buys_when_configured(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30, total_buys=9),
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32, total_buys=12),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 30.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_min_prob=0.988,
            buy_quick_profit_overlay_min_pred_return=25.0,
            buy_quick_profit_overlay_max_pred_return=35.0,
            buy_quick_profit_overlay_min_entry_volume_30s=1.5,
            buy_quick_profit_overlay_min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_max_age_seconds=60.0,
            buy_quick_profit_overlay_take_profit_pct=0.25,
            buy_quick_profit_overlay_max_hold_seconds=120.0,
            buy_quick_profit_overlay_min_total_buys=10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["quick_profit_overlay_signal_count"], 1)
        self.assertEqual(result["quick_profit_overlay_entry_count"], 0)
        self.assertEqual(result["quick_profit_overlay_reject_count"], 1)
        self.assertEqual(result["buy_quick_profit_overlay_min_total_buys"], 10.0)

    def test_primary_score_rescue_quick_take_profit_accepts_min_total_buys_boundary(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30, total_buys=10),
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32, total_buys=12),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 30.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_min_prob=0.988,
            buy_quick_profit_overlay_min_pred_return=25.0,
            buy_quick_profit_overlay_max_pred_return=35.0,
            buy_quick_profit_overlay_min_entry_volume_30s=1.5,
            buy_quick_profit_overlay_min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_max_age_seconds=60.0,
            buy_quick_profit_overlay_take_profit_pct=0.25,
            buy_quick_profit_overlay_max_hold_seconds=120.0,
            buy_quick_profit_overlay_min_total_buys=10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["quick_profit_overlay_signal_count"], 1)
        self.assertEqual(result["quick_profit_overlay_entry_count"], 1)
        self.assertEqual(result["quick_profit_overlay_reject_count"], 0)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "QUICK_PROFIT_OVERLAY_TAKE_PROFIT")

    def test_primary_score_rescue_quick_take_profit_rejects_nonfinite_total_buys_floor(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30),
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32),
        ]]

        for invalid_total_buys_floor in (-1, float("nan"), float("inf")):
            with self.subTest(invalid_total_buys_floor=invalid_total_buys_floor):
                with self.assertRaises(ValueError):
                    m._run_eval_replay(
                        episodes,
                        None,
                        0.98,
                        _SellNonePolicy(),
                        buy_probabilities_by_episode=[{0: 0.99}],
                        entry_scores_by_episode=[{0: 30.0}],
                        min_entry_score=35.0,
                        min_entry_volume_30s=1.5,
                        min_entry_price_volatility=0.10,
                        buy_quick_profit_overlay_min_total_buys=invalid_total_buys_floor,
                    )

    def test_primary_score_rescue_quick_take_profit_rejects_missing_sample_total_buys(self):
        m = _load_module()
        first_sample = _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30)
        first_sample["features"].pop("total_buys")
        episodes = [[
            first_sample,
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32, total_buys=12),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 30.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_min_prob=0.988,
            buy_quick_profit_overlay_min_pred_return=25.0,
            buy_quick_profit_overlay_max_pred_return=35.0,
            buy_quick_profit_overlay_min_entry_volume_30s=1.5,
            buy_quick_profit_overlay_min_entry_price_volatility=0.10,
            buy_quick_profit_overlay_max_age_seconds=60.0,
            buy_quick_profit_overlay_take_profit_pct=0.25,
            buy_quick_profit_overlay_max_hold_seconds=120.0,
            buy_quick_profit_overlay_min_total_buys=10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["quick_profit_overlay_entry_count"], 0)
        self.assertEqual(result["quick_profit_overlay_reject_count"], 1)

    def test_primary_score_rescue_quick_take_profit_rejects_invalid_take_profit(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30),
            _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32),
        ]]

        for invalid_take_profit in (-0.01, float("nan"), float("inf")):
            with self.subTest(invalid_take_profit=invalid_take_profit):
                with self.assertRaises(ValueError):
                    m._run_eval_replay(
                        episodes,
                        None,
                        0.98,
                        _SellNonePolicy(),
                        buy_probabilities_by_episode=[{0: 0.99}],
                        entry_scores_by_episode=[{0: 30.0}],
                        min_entry_score=35.0,
                        min_entry_volume_30s=1.5,
                        min_entry_price_volatility=0.10,
                        buy_quick_profit_overlay_take_profit_pct=invalid_take_profit,
                    )

    def test_primary_score_rescue_quick_take_profit_rejects_unknown_or_stale_age(self):
        m = _load_module()
        missing_age = _sample(
            sample_time=120,
            price=1.0,
            volume_30s=3.0,
            price_volatility=0.30,
            create_timestamp=None,
        )
        malformed_age = _sample(
            sample_time=120,
            price=1.0,
            volume_30s=3.0,
            price_volatility=0.30,
        )
        malformed_age["meta"]["sample_interval"] = float("nan")
        stale_age = _sample(
            sample_time=180,
            price=1.0,
            volume_30s=3.0,
            price_volatility=0.30,
            create_timestamp=100,
        )

        for first_sample in (missing_age, malformed_age, stale_age):
            with self.subTest(meta=first_sample["meta"]):
                later_sample = _sample(
                    token=first_sample["meta"]["token_address"],
                    sample_time=int(first_sample["meta"].get("sample_time", 120)) + 10,
                    price=1.25,
                    volume_30s=3.2,
                    price_volatility=0.32,
                    create_timestamp=first_sample["meta"].get("create_timestamp"),
                )
                result = m._run_eval_replay(
                    [[first_sample, later_sample]],
                    None,
                    0.98,
                    _SellNonePolicy(),
                    buy_probabilities_by_episode=[{0: 0.99}],
                    entry_scores_by_episode=[{0: 30.0}],
                    min_entry_score=35.0,
                    min_entry_volume_30s=1.5,
                    min_entry_price_volatility=0.10,
                    buy_quick_profit_overlay_min_prob=0.988,
                    buy_quick_profit_overlay_min_pred_return=25.0,
                    buy_quick_profit_overlay_max_pred_return=35.0,
                    buy_quick_profit_overlay_min_entry_volume_30s=1.5,
                    buy_quick_profit_overlay_min_entry_price_volatility=0.10,
                    buy_quick_profit_overlay_max_age_seconds=60.0,
                    buy_quick_profit_overlay_take_profit_pct=0.25,
                    buy_quick_profit_overlay_max_hold_seconds=120.0,
                    position_fraction=0.1,
                    include_trade_log=True,
                )

                self.assertEqual(result["total_trades"], 0)
                self.assertEqual(result["quick_profit_overlay_entry_count"], 0)
                self.assertEqual(result["quick_profit_overlay_reject_count"], 1)

    def test_low_volume_rescue_rejects_invalid_numeric_runtime_params(self):
        invalid_overrides = [
            {"buy_low_volume_rescue_min_entry_volume_30s": float("nan")},
            {"buy_low_volume_rescue_max_entry_volume_30s": float("inf")},
            {
                "buy_low_volume_rescue_min_entry_volume_30s": 1.6,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            },
            {"buy_low_volume_rescue_min_entry_price_volatility": -0.01},
            {"buy_low_volume_rescue_max_age_seconds": float("nan")},
            {"buy_low_volume_rescue_take_profit_pct": -0.01},
        ]

        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self._run_rescue_case(**overrides)

    def test_low_volume_take_profit_does_not_exit_normal_position(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=120, price=1.0, volume_30s=1.6, price_volatility=0.08),
            _sample(sample_time=130, price=1.25, volume_30s=1.7, price_volatility=0.10),
            _sample(sample_time=140, price=0.82, volume_30s=1.7, price_volatility=0.10),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.99}],
            entry_scores_by_episode=[{0: 35.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            stop_loss=-0.18,
            buy_low_volume_rescue_min_prob=0.98,
            buy_low_volume_rescue_min_entry_volume_30s=0.75,
            buy_low_volume_rescue_max_entry_volume_30s=1.5,
            buy_low_volume_rescue_min_entry_price_volatility=0.05,
            buy_low_volume_rescue_max_age_seconds=60,
            buy_low_volume_rescue_take_profit_pct=0.25,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["low_volume_rescue_signal_count"], 0)
        self.assertEqual(result["low_volume_rescue_entry_count"], 0)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "STOP_LOSS")
        self.assertFalse(result["trade_log"][0]["low_volume_rescue_used"])

    def test_run_ab_evaluation_propagates_low_volume_rescue_replay_params(self):
        m = _load_module()
        low_volume_params = {
            "buy_low_volume_rescue_min_prob": 0.982,
            "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
            "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_entry_price_volatility": 0.08,
            "buy_low_volume_rescue_max_age_seconds": 120,
            "buy_low_volume_rescue_take_profit_pct": 0.35,
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
                "low_volume_rescue_signal_count": 3,
                "low_volume_rescue_entry_count": 2,
                "low_volume_rescue_reject_count": 1,
                **{key: kwargs.get(key) for key in low_volume_params},
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
            "stress_replay_scenarios": [{"name": "stress_low_volume"}],
            "walk_forward_segments": 2,
            **low_volume_params,
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
            for key, value in low_volume_params.items():
                self.assertEqual(call.get(key), value)
        for key, value in low_volume_params.items():
            self.assertEqual(result.get(key), value)
            self.assertEqual(result["runtime_replay"].get(key), value)
            self.assertEqual(result["all_in_replay"].get(key), value)
            self.assertEqual(result["stress_replay"][0].get(key), value)
            self.assertEqual(result["walk_forward"][0].get(key), value)
        self.assertEqual(result["low_volume_rescue_signal_count"], 3)
        self.assertEqual(result["low_volume_rescue_entry_count"], 2)
        self.assertEqual(result["low_volume_rescue_reject_count"], 1)

    def test_run_ab_evaluation_propagates_quick_profit_overlay_replay_params(self):
        m = _load_module()
        quick_profit_params = {
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.5,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.10,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            "buy_quick_profit_overlay_min_total_buys": 10.0,
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
                "quick_profit_overlay_signal_count": 3,
                "quick_profit_overlay_entry_count": 2,
                "quick_profit_overlay_reject_count": 1,
                "quick_profit_overlay_take_profit_count": 1,
                "quick_profit_overlay_timeout_count": 1,
                **{key: kwargs.get(key) for key in quick_profit_params},
            }

        eval_samples = [
            _sample(token="0xquick-a", sample_time=100),
            _sample(token="0xquick-a", sample_time=110),
            _sample(token="0xquick-b", sample_time=200),
            _sample(token="0xquick-b", sample_time=210),
        ]
        config = {
            "eval_samples": eval_samples,
            "position_fraction": 0.1,
            "stress_replay_scenarios": [{"name": "stress_quick_profit"}],
            "walk_forward_segments": 2,
            **quick_profit_params,
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
            for key, value in quick_profit_params.items():
                self.assertEqual(call.get(key), value)
        for key, value in quick_profit_params.items():
            self.assertEqual(result.get(key), value)
            self.assertEqual(result["runtime_replay"].get(key), value)
            self.assertEqual(result["all_in_replay"].get(key), value)
            self.assertEqual(result["stress_replay"][0].get(key), value)
            self.assertEqual(result["walk_forward"][0].get(key), value)
        self.assertEqual(result["quick_profit_overlay_signal_count"], 3)
        self.assertEqual(result["quick_profit_overlay_entry_count"], 2)
        self.assertEqual(result["quick_profit_overlay_reject_count"], 1)
        self.assertEqual(result["quick_profit_overlay_take_profit_count"], 1)
        self.assertEqual(result["quick_profit_overlay_timeout_count"], 1)

    def test_selected_runtime_params_exclude_low_volume_rescue_replay_only_params(self):
        m = _load_module()

        selected = m._selected_runtime_params_from_evaluation({
            "buy_threshold": 0.98,
            "buy_low_volume_rescue_min_prob": 0.982,
            "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
            "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_entry_price_volatility": 0.08,
            "buy_low_volume_rescue_max_age_seconds": 120.0,
            "buy_low_volume_rescue_take_profit_pct": 0.35,
            "runtime_replay": {
                "buy_low_volume_rescue_min_prob": 0.985,
                "buy_low_volume_rescue_take_profit_pct": 0.25,
            },
        })

        self.assertEqual(selected["buy_threshold"], 0.98)
        for key in selected:
            self.assertFalse(key.startswith("buy_low_volume_rescue_"))

    def test_threshold_tuning_ignores_replay_only_low_volume_rescue_params(self):
        m = _load_module()
        calls = []
        samples = [
            _sample(token="0xtune", sample_time=100, price=1.0, volume_30s=1.0),
            _sample(token="0xtune", sample_time=110, price=1.2, volume_30s=1.2),
        ]

        def fake_replay(episodes, buy_model, threshold, sell_policy, **kwargs):
            calls.append(dict(kwargs))
            return {
                "total_trades": 1,
                "entry_count": 1,
                "entry_rate": 0.5,
                "win_rate": 1.0,
                "net_return_pct": 12.0,
                "net_profit_bnb": 0.01,
                "max_drawdown_pct": 0.0,
                "sortino_ratio": 1.0,
            }

        with patch.object(m, "_run_eval_replay", side_effect=fake_replay):
            tuned = m._tune_buy_threshold_by_replay(
                {
                    "risk_tune_buy_threshold": True,
                    "risk_tune_thresholds": [0.5],
                    "risk_tune_min_trades": 1,
                    "risk_tune_max_drawdown_pct": -100.0,
                    "risk_tune_min_win_rate": 0.0,
                    "position_fraction": 0.1,
                    "buy_low_volume_rescue_min_prob": 0.982,
                    "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
                    "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
                    "buy_low_volume_rescue_min_entry_price_volatility": 0.08,
                    "buy_low_volume_rescue_max_age_seconds": 120,
                    "buy_low_volume_rescue_take_profit_pct": 0.35,
                },
                {
                    "model": _FakeBuyModel(),
                    "threshold": 0.5,
                    "calibration_samples": samples,
                },
                {"model": _SellNonePolicy()},
            )

        self.assertEqual(tuned["status"], "selected")
        self.assertGreaterEqual(len(calls), 1)
        for call in calls:
            for key in call:
                self.assertFalse(key.startswith("buy_low_volume_rescue_"))
        for key in tuned["constraints"]:
            self.assertFalse(key.startswith("buy_low_volume_rescue_"))


if __name__ == "__main__":
    unittest.main()
