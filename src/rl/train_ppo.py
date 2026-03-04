from __future__ import annotations

try:
    from stable_baselines3 import PPO
except Exception:  # pragma: no cover - fallback for environments without SB3
    class PPO:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError("stable-baselines3 is required to train PPO")


def train_ppo(
    env,
    total_timesteps: int = 20000,
    seed: int = 42,
    policy_kwargs=None,
    bc_state_dict=None,
):
    model = PPO(
        "MlpPolicy",
        env,
        seed=seed,
        policy_kwargs=policy_kwargs or dict(net_arch=[128, 128]),
        verbose=0,
    )

    if bc_state_dict is not None:
        model.policy.load_state_dict(bc_state_dict, strict=False)

    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    return model
