from __future__ import annotations


def differential_sharpe_increment(
    prev_mean: float,
    prev_var: float,
    reward: float,
    momentum: float = 0.1,
):
    alpha = max(min(float(momentum), 1.0), 1e-6)
    r = float(reward)

    new_mean = (1.0 - alpha) * float(prev_mean) + alpha * r
    centered = r - float(prev_mean)
    new_var = (1.0 - alpha) * float(prev_var) + alpha * (centered ** 2)

    prev_denom = max(float(prev_var) ** 0.5, 1e-9)
    new_denom = max(new_var ** 0.5, 1e-9)

    prev_sharpe = float(prev_mean) / prev_denom
    new_sharpe = new_mean / new_denom

    return {
        "increment": float(new_sharpe - prev_sharpe),
        "mean": float(new_mean),
        "var": float(new_var),
    }


def compute_step_reward(
    realized_return: float,
    impact_cost: float,
    drawdown_penalty: float,
    prev_mean: float = 0.0,
    prev_var: float = 1e-6,
):
    pnl = float(realized_return) - float(impact_cost) - float(drawdown_penalty)
    sharpe_state = differential_sharpe_increment(prev_mean, prev_var, pnl)
    return {
        "reward": float(sharpe_state["increment"]),
        "mean": float(sharpe_state["mean"]),
        "var": float(sharpe_state["var"]),
    }
