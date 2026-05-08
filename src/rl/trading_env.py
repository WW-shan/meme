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

OBSERVATION_SIZE = 11


def canonical_sell_action(action: int, *, allow_partial_exits: bool = True) -> int:
    action_value = int(action)
    if allow_partial_exits:
        return action_value
    return 0 if action_value == 0 else 3


def build_sell_observation(
    row: Dict,
    *,
    entry_price: float | None = None,
    peak_price: float | None = None,
    position_remaining: float = 1.0,
    entry_ts: float | None = None,
    episode_start_ts: float | None = None,
):
    price = float(row.get("mid_price", 0.0))
    ts = float(row.get("ts", 0.0) or 0.0)
    start_ts = ts if episode_start_ts is None else float(episode_start_ts)
    open_ts = start_ts if entry_ts is None else float(entry_ts)
    basis = price if entry_price is None else float(entry_price)
    basis = max(basis, 1e-9)
    peak = max(float(peak_price if peak_price is not None else basis), price, basis)
    unrealized_return = (price / basis) - 1.0 if price > 0.0 else -1.0
    peak_return = (peak / basis) - 1.0
    drawdown_from_peak = (price / peak) - 1.0 if peak > 0.0 and price > 0.0 else 0.0
    return np.array(
        [
            price,
            float(row.get("lp_depth", 0.0)),
            float(row.get("sell_pressure", 0.0)),
            float(row.get("buy_sell_ratio", 0.0)),
            float(row.get("holders", 0.0)),
            max(0.0, ts - start_ts),
            max(0.0, ts - open_ts),
            unrealized_return,
            peak_return,
            drawdown_from_peak,
            max(0.0, min(1.0, float(position_remaining))),
        ],
        dtype=np.float32,
    )


def sell_fraction_for_action(action: int, *, allow_partial_exits: bool = True) -> float:
    action_value = canonical_sell_action(action, allow_partial_exits=allow_partial_exits)
    if allow_partial_exits:
        return ACTION_TO_FRACTION.get(action_value, 0.0)
    return 1.0 if action_value == 3 else 0.0


class TradingEnv(gym.Env):
    def __init__(
        self,
        episode: List[Dict],
        liquidity_floor: float = 0.05,
        stall_steps: int = 3,
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
        drawdown_penalty_weight: float = 0.0,
        hold_penalty_per_step: float = 0.0,
        turnover_penalty: float = 0.0,
        allow_partial_exits: bool = False,
    ):
        super().__init__()
        self.episodes = self._normalize_episodes(episode)
        self.episode_idx = -1
        self.episode = list(self.episodes[0]) if self.episodes else []
        self.liquidity_floor = float(liquidity_floor)
        self.stall_steps = int(stall_steps)
        self.fee_rate = max(0.0, float(fee_bps)) / 10000.0
        self.slippage_rate = max(0.0, float(slippage_bps)) / 10000.0
        self.drawdown_penalty_weight = max(0.0, float(drawdown_penalty_weight))
        self.hold_penalty_per_step = max(0.0, float(hold_penalty_per_step))
        self.turnover_penalty = max(0.0, float(turnover_penalty))
        self.allow_partial_exits = bool(allow_partial_exits)

        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(OBSERVATION_SIZE,), dtype=np.float32)

        self.position_remaining = 1.0
        self.step_idx = 0
        self.low_liquidity_streak = 0
        self.sharpe_mean = 0.0
        self.sharpe_var = 1e-6
        self.done = False
        self.entry_price = 0.0
        self.peak_price = 0.0
        self.entry_ts = 0.0
        self.episode_start_ts = 0.0

    @staticmethod
    def _normalize_episodes(episode_input) -> List[List[Dict]]:
        if not episode_input:
            return []
        first = episode_input[0]
        if isinstance(first, dict):
            return [list(episode_input)]
        return [list(ep) for ep in episode_input if ep]

    def _obs_from_row(self, row: Dict):
        return build_sell_observation(
            row,
            entry_price=self.entry_price,
            peak_price=self.peak_price,
            position_remaining=self.position_remaining,
            entry_ts=self.entry_ts,
            episode_start_ts=self.episode_start_ts,
        )

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
            return np.zeros(OBSERVATION_SIZE, dtype=np.float32), {}

        self.episode_idx = (self.episode_idx + 1) % len(self.episodes)
        self.episode = list(self.episodes[self.episode_idx])
        first_row = self.episode[0]
        self.entry_price = max(float(first_row.get("mid_price", 0.0)), 1e-9)
        self.peak_price = self.entry_price
        self.episode_start_ts = float(first_row.get("ts", 0.0) or 0.0)
        self.entry_ts = self.episode_start_ts
        return self._obs_from_row(self.episode[0]), {}

    def step(self, action: int):
        if self.done:
            raise RuntimeError("episode already done")

        if not self.action_space.contains(action):
            raise ValueError(f"invalid action: {action}")

        row = self.episode[self.step_idx]
        sell_fraction = sell_fraction_for_action(action, allow_partial_exits=self.allow_partial_exits)

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
        price_return = (price / max(self.entry_price, 1e-9)) - 1.0 if price > 0.0 else -1.0
        realized_return = filled * price_return
        drawdown_from_peak = 0.0
        if self.peak_price > 0.0 and price > 0.0:
            drawdown_from_peak = max(0.0, 1.0 - (price / self.peak_price))
        penalty = (
            self.drawdown_penalty_weight * drawdown_from_peak
            + self.hold_penalty_per_step
            + self.turnover_penalty * filled
            + filled * (self.fee_rate + self.slippage_rate)
        )
        reward_state = compute_step_reward(
            realized_return=realized_return,
            impact_cost=impact,
            drawdown_penalty=penalty,
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
            next_price = float(next_row.get("mid_price", 0.0))
            if next_price > 0.0:
                self.peak_price = max(self.peak_price, next_price)
            next_lp_depth = float(next_row.get("lp_depth", 0.0))
            if next_lp_depth < self.liquidity_floor:
                self.low_liquidity_streak += 1
            else:
                self.low_liquidity_streak = 0

            if not self.done and self.low_liquidity_streak >= self.stall_steps:
                self.done = True
                done_reason = "liquidity_exhausted"

        obs = self._obs_from_row(next_row) if not self.done else np.zeros(OBSERVATION_SIZE, dtype=np.float32)

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
        fee_bps: float = 0.0,
        slippage_bps: float = 0.0,
        drawdown_penalty_weight: float = 0.0,
        hold_penalty_per_step: float = 0.0,
        turnover_penalty: float = 0.0,
        allow_partial_exits: bool = False,
    ):
        super().__init__()
        self.episodes = [list(ep) for ep in episodes if ep]
        if not self.episodes:
            raise ValueError("episodes must not be empty")
        self.liquidity_floor = float(liquidity_floor)
        self.stall_steps = int(stall_steps)
        self.fee_bps = float(fee_bps)
        self.slippage_bps = float(slippage_bps)
        self.drawdown_penalty_weight = float(drawdown_penalty_weight)
        self.hold_penalty_per_step = float(hold_penalty_per_step)
        self.turnover_penalty = float(turnover_penalty)
        self.allow_partial_exits = bool(allow_partial_exits)
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(OBSERVATION_SIZE,), dtype=np.float32)
        self._episode_index = -1
        self._current_env = None

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._episode_index = (self._episode_index + 1) % len(self.episodes)
        self._current_env = TradingEnv(
            self.episodes[self._episode_index],
            liquidity_floor=self.liquidity_floor,
            stall_steps=self.stall_steps,
            fee_bps=self.fee_bps,
            slippage_bps=self.slippage_bps,
            drawdown_penalty_weight=self.drawdown_penalty_weight,
            hold_penalty_per_step=self.hold_penalty_per_step,
            turnover_penalty=self.turnover_penalty,
            allow_partial_exits=self.allow_partial_exits,
        )
        return self._current_env.reset(seed=seed, options=options)

    def step(self, action: int):
        if self._current_env is None:
            raise RuntimeError("environment must be reset before stepping")
        return self._current_env.step(action)
