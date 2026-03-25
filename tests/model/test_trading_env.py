import unittest
from pathlib import Path
import importlib.util


def _load_env_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "trading_env.py"
    spec = importlib.util.spec_from_file_location("trading_env", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTradingEnv(unittest.TestCase):
    def _episode(self):
        return [
            {"mid_price": 1.0, "lp_depth": 8.0, "sell_pressure": 0.3, "buy_sell_ratio": 1.2, "holders": 40, "ts": 1},
            {"mid_price": 1.1, "lp_depth": 7.0, "sell_pressure": 0.4, "buy_sell_ratio": 1.0, "holders": 42, "ts": 2},
            {"mid_price": 0.9, "lp_depth": 0.1, "sell_pressure": 1.8, "buy_sell_ratio": 0.4, "holders": 35, "ts": 3},
        ]

    def test_trading_env_is_gym_env(self):
        m = _load_env_module()
        self.assertTrue(issubclass(m.TradingEnv, m.gym.Env))

    def test_trading_env_exposes_action_and_observation_space(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode())
        self.assertEqual(env.action_space.n, 4)
        self.assertEqual(tuple(env.observation_space.shape), (5,))

    def test_reset_rotates_across_multiple_episodes(self):
        m = _load_env_module()
        episodes = [
            [
                {"mid_price": 1.0, "lp_depth": 8.0, "sell_pressure": 0.3, "buy_sell_ratio": 1.2, "holders": 40, "ts": 1},
                {"mid_price": 1.1, "lp_depth": 7.0, "sell_pressure": 0.4, "buy_sell_ratio": 1.0, "holders": 42, "ts": 2},
            ],
            [
                {"mid_price": 2.0, "lp_depth": 6.0, "sell_pressure": 0.2, "buy_sell_ratio": 1.4, "holders": 50, "ts": 10},
                {"mid_price": 2.1, "lp_depth": 5.0, "sell_pressure": 0.5, "buy_sell_ratio": 0.9, "holders": 52, "ts": 11},
            ],
        ]

        env = m.TradingEnv(episodes)
        obs1, _ = env.reset()
        obs2, _ = env.reset()

        self.assertEqual(float(obs1[0]), 1.0)
        self.assertEqual(float(obs2[0]), 2.0)

    def test_step_sell50_reduces_position_more_than_sell25(self):
        m = _load_env_module()
        env_sell25 = m.TradingEnv(self._episode())
        env_sell25.reset()
        _, _, _, _, info25 = env_sell25.step(1)

        env_sell50 = m.TradingEnv(self._episode())
        env_sell50.reset()
        _, _, _, _, info50 = env_sell50.step(2)

        self.assertLess(info50["position_remaining"], info25["position_remaining"])

    def test_step_sell100_closes_position(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode())
        env.reset()
        _, _, terminated, _, info = env.step(3)
        self.assertTrue(terminated)
        self.assertEqual(info.get("done_reason"), "position_closed")

    def test_step_rejects_invalid_action(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode())
        env.reset()
        with self.assertRaises(ValueError):
            env.step(9)

    def test_dynamic_termination_on_liquidity_exhaustion(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode(), liquidity_floor=0.2, stall_steps=1)
        env.reset()
        _, _, terminated, _, info = env.step(0)
        _, _, terminated, _, info = env.step(0)
        self.assertTrue(terminated)
        self.assertEqual(info.get("done_reason"), "liquidity_exhausted")


if __name__ == "__main__":
    unittest.main()
