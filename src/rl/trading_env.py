from __future__ import annotations

from typing import Dict, List

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except Exception:  # pragma: no cover - local fallback when gymnasium is unavailable
    class _FallbackEnv:
        def reset(self, *, seed=None, options=None):
            self.np_random = np.random.default_rng(seed)
            return None

    class _FallbackDiscrete:
        def __init__(self, n: int):
            self.n = int(n)

        def contains(self, x) -> bool:
            try:
                value = int(x)
            except (TypeError, ValueError):
                return False
            return 0 <= value < self.n

    class _FallbackBox:
        def __init__(self, low, high, shape, dtype=np.float32):
            self.shape = tuple(shape)
            self.dtype = np.dtype(dtype)
            self.low = np.full(self.shape, low, dtype=self.dtype)
            self.high = np.full(self.shape, high, dtype=self.dtype)

    class _FallbackSpaces:
        Discrete = _FallbackDiscrete
        Box = _FallbackBox

    class _FallbackGym:
        Env = _FallbackEnv

    gym = _FallbackGym()
    spaces = _FallbackSpaces()

from src.backtest.impact_model import estimate_execution_cost, simulate_sell_fill
from src.rl.reward import compute_step_reward


ACTION_TO_FRACTION = {
    0: 0.0,
    1: 0.25,
    2: 0.5,
    3: 1.0,
}


def build_sell_observation(row: Dict):
    return np.array(
        [
            float(row.get("mid_price", 0.0)),
            float(row.get("lp_depth", 0.0)),
            float(row.get("sell_pressure", 0.0)),
            float(row.get("buy_sell_ratio", 0.0)),
            float(row.get("holders", 0.0)),
        ],
        dtype=np.float32,
    )


def sell_fraction_for_action(action: int) -> float:
    return ACTION_TO_FRACTION.get(int(action), 0.0)


class TradingEnv(gym.Env):
    def __init__(
        self,
        episode: List[Dict],
        liquidity_floor: float = 0.05,
        stall_steps: int = 3,
    ):
        super().__init__()
        self.episodes = self._normalize_episodes(episode)
        self.episode_idx = -1
        self.episode = list(self.episodes[0]) if self.episodes else []
        self.liquidity_floor = float(liquidity_floor)
        self.stall_steps = int(stall_steps)

        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)

        self.position_remaining = 1.0
        self.step_idx = 0
        self.low_liquidity_streak = 0
        self.sharpe_mean = 0.0
        self.sharpe_var = 1e-6
        self.done = False

    @staticmethod
    def _normalize_episodes(episode_input) -> List[List[Dict]]:
        if not episode_input:
            return []
        first = episode_input[0]
        if isinstance(first, dict):
            return [list(episode_input)]
        return [list(ep) for ep in episode_input if ep]

    def _obs_from_row(self, row: Dict):
        return build_sell_observation(row)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.position_remaining = 1.0
        self.step_idx = 0
        self.low_liquidity_streak = 0
        self.sharpe_mean = 0.0
        self.sharpe_var = 1e-6
        self.done = False

        if not self.episodes:
            self.episode = []
            self.done = True
            return np.zeros(5, dtype=np.float32), {}

        self.episode_idx = (self.episode_idx + 1) % len(self.episodes)
        self.episode = list(self.episodes[self.episode_idx])
        return self._obs_from_row(self.episode[0]), {}

    def step(self, action: int):
        if self.done:
            raise RuntimeError("episode already done")

        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action}")

        row = self.episode[self.step_idx]
        sell_fraction = sell_fraction_for_action(action)

        sell_request = self.position_remaining * sell_fraction
        fill = simulate_sell_fill(
            order_size=sell_request,
            lp_depth=float(row.get("lp_depth", 0.0)),
            max_fill_ratio=0.8,
        )
        filled = float(fill["filled_size"])

        if self.position_remaining > 0.0:
            execution_imbalance = float(row.get("sell_pressure", 0.0)) - float(row.get("buy_sell_ratio", 0.0))
            impact = estimate_execution_cost(
                order_size=filled,
                lp_depth=float(row.get("lp_depth", 0.0)),
                imbalance=execution_imbalance,
            )
        else:
            impact = 0.0

        price = float(row.get("mid_price", 0.0))
        realized_return = filled * price
        reward_state = compute_step_reward(
            realized_return=realized_return,
            impact_cost=impact,
            drawdown_penalty=0.0,
            prev_mean=self.sharpe_mean,
            prev_var=self.sharpe_var,
        )
        reward = float(reward_state["reward"])
        self.sharpe_mean = float(reward_state["mean"])
        self.sharpe_var = float(reward_state["var"])

        self.position_remaining = max(0.0, self.position_remaining - filled)

        done_reason = None
        if self.position_remaining <= 1e-9:
            self.done = True
            done_reason = "position_closed"

        self.step_idx += 1
        truncated = False
        if self.step_idx >= len(self.episode):
            if not self.done:
                self.done = True
                done_reason = "episode_end"
            self.step_idx = len(self.episode) - 1
            next_row = self.episode[self.step_idx] if self.episode else {}
        else:
            next_row = self.episode[self.step_idx]
            next_lp_depth = float(next_row.get("lp_depth", 0.0))
            if next_lp_depth < self.liquidity_floor:
                self.low_liquidity_streak += 1
            else:
                self.low_liquidity_streak = 0

            if not self.done and self.low_liquidity_streak >= self.stall_steps:
                self.done = True
                done_reason = "liquidity_exhausted"

        obs = self._obs_from_row(next_row) if not self.done else np.zeros(5, dtype=np.float32)

        info = {
            "filled_size": filled,
            "position_remaining": float(self.position_remaining),
            "impact_cost": float(impact),
            "done_reason": done_reason,
        }

        return obs, reward, self.done, truncated, info


class MultiEpisodeTradingEnv(gym.Env):
    def __init__(
        self,
        episodes: List[List[Dict]],
        liquidity_floor: float = 0.05,
        stall_steps: int = 3,
    ):
        super().__init__()
        self.episodes = [list(ep) for ep in episodes if ep]
        if not self.episodes:
            raise ValueError("episodes must not be empty")
        self.liquidity_floor = float(liquidity_floor)
        self.stall_steps = int(stall_steps)
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)
        self._episode_index = -1
        self._current_env = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._episode_index = (self._episode_index + 1) % len(self.episodes)
        self._current_env = TradingEnv(
            self.episodes[self._episode_index],
            liquidity_floor=self.liquidity_floor,
            stall_steps=self.stall_steps,
        )
        return self._current_env.reset(seed=seed, options=options)

    def step(self, action: int):
        if self._current_env is None:
            raise RuntimeError("environment must be reset before stepping")
        return self._current_env.step(action)
