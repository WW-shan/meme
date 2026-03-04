from __future__ import annotations


def estimate_execution_cost(
    order_size: float,
    lp_depth: float,
    imbalance: float,
    k_temp: float = 0.02,
    k_perm: float = 0.01,
) -> float:
    size = max(float(order_size), 0.0)
    depth = max(float(lp_depth), 1e-9)
    signed_imbalance = max(min(float(imbalance), 1.0), -1.0)
    intensity = size / depth

    temporary_cost = float(k_temp) * intensity
    permanent_cost = float(k_perm) * (intensity ** 2)
    imbalance_penalty = max(0.0, signed_imbalance) * 0.01

    return float(max(temporary_cost + permanent_cost + imbalance_penalty, 0.0))


def simulate_sell_fill(order_size: float, lp_depth: float, max_fill_ratio: float = 0.8):
    size = max(float(order_size), 0.0)
    depth = max(float(lp_depth), 0.0)
    ratio_cap = max(0.0, min(float(max_fill_ratio), 1.0))

    if size <= 0.0:
        return {"filled_size": 0.0, "unfilled_size": 0.0, "fill_ratio": 0.0}

    if depth <= 0.0:
        fill_ratio = 0.0
    else:
        depth_ratio = depth / size
        fill_ratio = min(1.0, max(ratio_cap, depth_ratio))

    filled_size = size * fill_ratio

    return {
        "filled_size": float(filled_size),
        "unfilled_size": float(size - filled_size),
        "fill_ratio": float(fill_ratio),
    }
