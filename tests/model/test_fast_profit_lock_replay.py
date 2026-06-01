import importlib.util
import unittest
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _HoldPolicy:
    def predict(self, obs, deterministic=True):
        return 0, None


def _sample(sample_time, price, token="0xprofitlock"):
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": 2.0,
            "price_volatility": 0.10,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": 90,
        },
    }


class TestFastProfitLockReplay(unittest.TestCase):
    def _run_path(self, prices, *, times=None, **overrides):
        m = _load_module()
        if times is None:
            times = [100 + idx * 20 for idx in range(len(prices))]
        episodes = [[_sample(sample_time, price) for sample_time, price in zip(times, prices)]]
        config = {
            "buy_probabilities_by_episode": [{0: 0.99}],
            "entry_scores_by_episode": [{0: 40.0}],
            "min_entry_score": 35.0,
            "stop_loss": -0.18,
            "position_fraction": 0.1,
            "include_trade_log": True,
        }
        config.update(overrides)
        return m._run_eval_replay(
            episodes,
            None,
            0.98,
            _HoldPolicy(),
            **config,
        )

    def test_default_off_preserves_baseline_exit(self):
        result = self._run_path([1.00, 1.35, 0.82], times=[100, 130, 150])

        self.assertEqual(result["trade_log"][0]["exit_reason"], "STOP_LOSS")
        self.assertNotEqual(result["trade_log"][0]["exit_reason"], "PROFIT_LOCK_TAKE_PROFIT")
        self.assertIsNone(result["profit_lock_take_profit_pct"])
        self.assertIsNone(result["profit_lock_max_hold_seconds"])
        self.assertEqual(result["profit_lock_take_profit_count"], 0)

    def test_trade_log_includes_entry_signal_context_features(self):
        result = self._run_path([1.00, 1.35, 0.82], times=[100, 130, 150])

        trade = result["trade_log"][0]
        self.assertEqual(trade["entry_volume_30s"], 2.0)
        self.assertEqual(trade["entry_price_volatility"], 0.10)
        self.assertEqual(trade["entry_token_age_seconds"], 10.0)

    def test_fast_profit_lock_exits_before_later_stop_loss(self):
        result = self._run_path(
            [1.00, 1.26, 0.82],
            times=[100, 130, 150],
            profit_lock_take_profit_pct=0.25,
            profit_lock_max_hold_seconds=60,
        )

        self.assertEqual(result["trade_log"][0]["exit_reason"], "PROFIT_LOCK_TAKE_PROFIT")
        self.assertEqual(result["profit_lock_take_profit_count"], 1)
        self.assertEqual(result["profit_lock_take_profit_pct"], 0.25)
        self.assertEqual(result["profit_lock_max_hold_seconds"], 60.0)
        self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)

    def test_profit_lock_does_not_fire_after_window(self):
        result = self._run_path(
            [1.00, 1.26, 0.82],
            times=[100, 170, 190],
            profit_lock_take_profit_pct=0.25,
            profit_lock_max_hold_seconds=60,
        )

        self.assertEqual(result["trade_log"][0]["exit_reason"], "STOP_LOSS")
        self.assertEqual(result["profit_lock_take_profit_count"], 0)

    def test_profit_lock_count_increments_after_delayed_exit_fill(self):
        result = self._run_path(
            [1.00, 1.26, 1.20],
            times=[100, 130, 145],
            profit_lock_take_profit_pct=0.25,
            profit_lock_max_hold_seconds=60,
            exit_delay_seconds=10,
        )

        self.assertEqual(result["trade_log"][0]["exit_reason"], "PROFIT_LOCK_TAKE_PROFIT")
        self.assertEqual(result["trade_log"][0]["exit_time"], 145)
        self.assertEqual(result["profit_lock_take_profit_count"], 1)

    def test_profit_lock_count_does_not_increment_when_exit_execution_fails(self):
        result = self._run_path(
            [1.00, 1.26, 0.82],
            times=[100, 130, 150],
            profit_lock_take_profit_pct=0.25,
            profit_lock_max_hold_seconds=60,
            exit_execution_failure_rate=1.0,
        )

        self.assertEqual(result["profit_lock_take_profit_count"], 0)
        self.assertEqual(result["trade_log"][0]["exit_reason"], "REPLAY_END")

    def test_profit_lock_requires_both_parameters(self):
        cases = [
            {"profit_lock_take_profit_pct": 0.25},
            {"profit_lock_max_hold_seconds": 60},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self._run_path([1.00, 1.26], **overrides)

    def test_profit_lock_rejects_negative_nan_and_infinite_values(self):
        cases = [
            {"profit_lock_take_profit_pct": -0.01, "profit_lock_max_hold_seconds": 60},
            {"profit_lock_take_profit_pct": float("nan"), "profit_lock_max_hold_seconds": 60},
            {"profit_lock_take_profit_pct": float("inf"), "profit_lock_max_hold_seconds": 60},
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": -1},
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": float("nan")},
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": float("inf")},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self._run_path([1.00, 1.26], **overrides)


if __name__ == "__main__":
    unittest.main()
