from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.dataset_builder import DatasetBuilder
from src.model.buy_catboost import BuyCatBoostModel
from src.rl.trading_env import TradingEnv
from src.rl.train_ppo import train_ppo

try:
    from src.rl.warmstart_bc import train_bc
except Exception:  # pragma: no cover - fallback when torch is unavailable
    def train_bc(*args, **kwargs):  # type: ignore[no-redef]
        raise ModuleNotFoundError("torch is required to train BC warm-start policy")


def _prepare_training_rows(samples, target_label_column, target_threshold_value):
    if not samples:
        raise ValueError("no samples generated from DatasetBuilder")

    feature_rows, labels, metas = [], [], []
    for sample in samples:
        label_value = float(sample.get("label", {}).get(target_label_column, 0.0))
        feature_rows.append(dict(sample.get("features", {})))
        labels.append(1 if label_value >= float(target_threshold_value) else 0)
        metas.append(dict(sample.get("meta", {})))

    if len(set(labels)) < 2:
        raise ValueError("buy target has single class; cannot train classifier")

    return feature_rows, labels, metas


def _load_samples(config):
    builder = DatasetBuilder(
        lifecycle_dir=config.get("lifecycle_dir", "data/training"),
        sample_mode=config.get("sample_mode", "trade_event"),
        max_sample_age_seconds=int(config.get("max_sample_age_seconds", 180)),
        future_windows=config.get("future_windows", [240]),
    )
    builder.load_lifecycle_files()
    return builder.samples


def train_buy_model(config):
    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = _load_samples(config)
    rows, labels, metas = _prepare_training_rows(
        samples,
        config.get("target_label_column", "max_return_pct"),
        float(config.get("target_threshold_value", 80.0)),
    )

    X = pd.DataFrame(rows)
    y = np.asarray(labels, dtype=int)

    model = BuyCatBoostModel(cat_feature_names=config.get("cat_feature_names", []))
    model.fit(X, y)
    proba = model.predict_proba(X)
    threshold = model.select_threshold(y, proba, min_precision=float(config.get("buy_min_precision", 0.10)))

    model_path = output_dir / "buy_model.cbm"
    model.model.save_model(str(model_path))

    threshold_path = output_dir / "buy_threshold.json"
    threshold_path.write_text(json.dumps({"threshold": float(threshold)}, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "model_path": str(model_path),
        "threshold": float(threshold),
        "threshold_path": str(threshold_path),
        "samples": samples,
        "labels": labels,
        "meta": metas,
    }


def _sample_to_event(sample):
    f = sample.get("features", {})
    buy_vol = float(f.get("total_buy_volume", 0.0))
    sell_vol = float(f.get("total_sell_volume", 0.0))
    buy_sell_ratio = buy_vol / max(sell_vol, 1e-9)
    sell_pressure = sell_vol / max(buy_vol + sell_vol, 1e-9)
    return {
        "mid_price": float(f.get("current_price", 0.0)),
        "lp_depth": float(f.get("launch_fee", 0.0)),
        "sell_pressure": float(sell_pressure),
        "buy_sell_ratio": float(buy_sell_ratio),
        "holders": float(f.get("holder_count", 0.0)),
        "ts": int(sample.get("meta", {}).get("sample_time", 0) or 0),
    }


def build_sell_env(config, buy_artifact):
    grouped = {}
    for sample in buy_artifact.get("samples", []):
        token = str(sample.get("meta", {}).get("token_address", ""))
        grouped.setdefault(token, []).append(sample)

    episodes = []
    for token_samples in grouped.values():
        ordered = sorted(token_samples, key=lambda s: int(s.get("meta", {}).get("sample_time", 0) or 0))
        episode = [_sample_to_event(s) for s in ordered]
        if len(episode) >= 2:
            episodes.append(episode)

    if not episodes:
        raise ValueError("no sell episodes could be built from samples")

    env = TradingEnv(
        episodes[0],
        liquidity_floor=float(config.get("liquidity_floor", 0.05)),
        stall_steps=int(config.get("stall_steps", 3)),
    )
    return {"env": env, "episodes": episodes, "episode_count": len(episodes)}


def _torch_save(obj, path):
    import torch
    torch.save(obj, path)


def _build_bc_arrays(episodes):
    obs_rows, action_rows = [], []
    for ep in episodes:
        for event in ep:
            obs_rows.append([
                float(event.get("mid_price", 0.0)),
                float(event.get("lp_depth", 0.0)),
                float(event.get("sell_pressure", 0.0)),
                float(event.get("buy_sell_ratio", 0.0)),
                float(event.get("holders", 0.0)),
            ])
            sp = float(event.get("sell_pressure", 0.0))
            if sp >= 1.2:
                action_rows.append(3)
            elif sp >= 0.8:
                action_rows.append(2)
            elif sp >= 0.5:
                action_rows.append(1)
            else:
                action_rows.append(0)
    return np.asarray(obs_rows, dtype=np.float32), np.asarray(action_rows, dtype=np.int64)


def _as_torch_tensors(obs_arr, act_arr):
    import torch
    obs = torch.tensor(obs_arr, dtype=torch.float32)
    actions = torch.tensor(act_arr, dtype=torch.long)
    return obs, actions


def run_bc_warmstart(config, env_bundle):
    episodes = env_bundle.get("episodes", [])
    obs_arr, act_arr = _build_bc_arrays(episodes)
    if obs_arr.size == 0:
        raise ValueError("no BC samples generated from episodes")

    obs, actions = _as_torch_tensors(obs_arr, act_arr)

    state = train_bc(
        obs,
        actions,
        hidden_dim=int(config.get("bc_hidden_dim", 64)),
        epochs=int(config.get("bc_epochs", 20)),
        lr=float(config.get("bc_lr", 1e-3)),
    )

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    weight_path = output_dir / "bc.pt"
    _torch_save(state, str(weight_path))

    return {"weights": str(weight_path), "bc_samples": int(obs_arr.shape[0])}


def _torch_load(path):
    import torch
    return torch.load(path, map_location="cpu")


def run_ppo_finetune(config, env_bundle, bc_artifact):
    env = env_bundle.get("env")
    if env is None:
        raise ValueError("env bundle missing env")

    bc_path = bc_artifact.get("weights")
    bc_state = _torch_load(bc_path) if bc_path else None

    model = train_ppo(
        env,
        total_timesteps=int(config.get("total_timesteps", 20000)),
        seed=int(config.get("ppo_seed", 42)),
        policy_kwargs={"net_arch": list(config.get("ppo_policy_net_arch", [128, 128]))},
        bc_state_dict=bc_state,
    )

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_path = output_dir / "sell_policy.zip"
    model.save(str(policy_path))

    return {"policy_path": str(policy_path), "total_timesteps": int(config.get("total_timesteps", 20000))}


def run_ab_evaluation(config, buy_artifact, ppo_artifact, env_bundle, bc_artifact):
    labels = np.asarray(buy_artifact.get("labels", []), dtype=float)
    positive_rate = float(labels.mean()) if labels.size > 0 else 0.0

    return {
        "buy_positive_rate": positive_rate,
        "buy_threshold": float(buy_artifact.get("threshold", 1.0)),
        "sell_episode_count": int(env_bundle.get("episode_count", 0)),
        "bc_samples": int(bc_artifact.get("bc_samples", 0)),
        "ppo_total_timesteps": int(ppo_artifact.get("total_timesteps", 0)),
        "pipeline_status": "ok",
    }


def run_hybrid_training(config):
    buy_artifact = train_buy_model(config)
    env_bundle = build_sell_env(config, buy_artifact)
    bc_artifact = run_bc_warmstart(config, env_bundle)
    ppo_artifact = run_ppo_finetune(config, env_bundle, bc_artifact)
    evaluation = run_ab_evaluation(config, buy_artifact, ppo_artifact, env_bundle, bc_artifact)

    result = {
        "artifacts": {
            "buy_model": {
                "model_path": buy_artifact.get("model_path"),
                "threshold": buy_artifact.get("threshold"),
                "threshold_path": buy_artifact.get("threshold_path"),
            },
            "sell_policy": ppo_artifact,
            "bc_warmstart": bc_artifact,
        },
        "evaluation": evaluation,
    }

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "hybrid_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
