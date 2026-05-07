from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.dataset_builder import DatasetBuilder, stable_lifecycle_order
from src.model.buy_catboost import BuyCatBoostModel
from src.model.hybrid_inference import build_feature_frame, coerce_action, load_feature_names_from_schema, normalize_feature_names
from src.rl.trading_env import MultiEpisodeTradingEnv, build_sell_observation, sell_fraction_for_action
from src.rl.train_ppo import train_ppo

logger = logging.getLogger(__name__)

_FILENAME_ORDER_PATTERNS = (
    re.compile(r"^lifecycle_incremental_(?P<order>\d{8}_\d{6}|\d+)(?:_part(?P<part>\d+))?\.jsonl$"),
    re.compile(r"^lifecycle_(?P<order>\d{8}_\d{6}|\d+)\.jsonl$"),
)


def _filename_sort_key(path: Path):
    name = path.name
    for idx, pattern in enumerate(_FILENAME_ORDER_PATTERNS):
        match = pattern.match(name)
        if match:
            raw_value = match.group("order")
            normalized_value = raw_value.replace("_", "")
            part_value = match.groupdict().get("part") or "0"
            return idx, int(normalized_value), int(part_value), name
    return None


def _stable_lifecycle_order(files):
    return stable_lifecycle_order(files, log=logger)


def _discover_lifecycle_files(lifecycle_dir):
    base = Path(lifecycle_dir)
    incremental_files = sorted(base.glob("lifecycle_incremental_*.jsonl"))
    if incremental_files:
        return _stable_lifecycle_order(incremental_files)

    snapshot_files = sorted(base.glob("lifecycle_*.jsonl"))
    snapshot_files = [path for path in snapshot_files if _filename_sort_key(path) is not None and path.name.startswith("lifecycle_") and not path.name.startswith("lifecycle_incremental_")]
    if snapshot_files:
        return _stable_lifecycle_order(snapshot_files)

    raise ValueError(f"no lifecycle files found under {base}")


def _split_lifecycle_files(files, train_split_ratio, min_eval_files, *, enforce_no_overlap=True, return_token_sets=False):
    ordered = _stable_lifecycle_order(files)
    if not ordered:
        raise ValueError("no lifecycle files found")

    ratio = float(train_split_ratio)
    if ratio <= 0.0 or ratio >= 1.0:
        raise ValueError(f"train_split_ratio must be between 0 and 1 (exclusive), got {ratio}")
    required_eval = int(min_eval_files)
    if required_eval < 1:
        required_eval = 1

    train_count = int(len(ordered) * ratio)
    train_files = ordered[:train_count]
    eval_files = ordered[train_count:]

    if not train_files:
        raise ValueError("split produced no train files")
    if len(eval_files) < required_eval:
        raise ValueError(f"split produced insufficient eval files: {len(eval_files)} < {required_eval}")

    train_tokens, eval_tokens, overlap_token_count = _raw_token_split_details(train_files, eval_files)
    if enforce_no_overlap and overlap_token_count > 0:
        raise ValueError(
            f"train/eval leakage detected: overlap_token_count={overlap_token_count}; adjust lifecycle partitions before training"
        )

    if return_token_sets:
        return train_files, eval_files, overlap_token_count, train_tokens, eval_tokens

    return train_files, eval_files, overlap_token_count


def _collect_raw_token_addresses(paths):
    addresses = set()
    for path in paths:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    payload = json.loads(line.strip())
                except Exception:
                    continue
                token_address = str(payload.get("token_address") or "").strip().lower()
                if token_address:
                    addresses.add(token_address)
    return addresses


def _raw_overlap_token_count(train_files, eval_files):
    return _raw_token_split_details(train_files, eval_files)[2]


def _raw_token_split_details(train_files, eval_files):
    train_tokens = _collect_raw_token_addresses(train_files)
    eval_tokens = _collect_raw_token_addresses(eval_files)
    return train_tokens, eval_tokens, len(train_tokens.intersection(eval_tokens))


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
    if "samples" in config:
        samples = list(config.get("samples") or [])
    else:
        builder = DatasetBuilder(
            lifecycle_dir=config.get("lifecycle_dir", "data/training"),
            sample_mode=config.get("sample_mode", "trade_event"),
            max_sample_age_seconds=int(config.get("max_sample_age_seconds", 180)),
            future_windows=config.get("future_windows", [240]),
        )
        lifecycle_paths = config.get("lifecycle_paths") or []
        if lifecycle_paths:
            builder.load_lifecycle_paths(lifecycle_paths)
        else:
            builder.load_lifecycle_files()
        samples = builder.samples

    return _filter_samples_by_tokens(
        samples,
        include_tokens=config.get("include_token_addresses"),
        exclude_tokens=config.get("exclude_token_addresses"),
    )


def _normalize_token_set(tokens):
    normalized = set()
    for token in tokens or []:
        value = str(token or "").strip().lower()
        if value:
            normalized.add(value)
    return normalized


def _sample_token(sample):
    return str(sample.get("meta", {}).get("token_address") or "").strip().lower()


def _filter_samples_by_tokens(samples, include_tokens=None, exclude_tokens=None):
    include = _normalize_token_set(include_tokens)
    exclude = _normalize_token_set(exclude_tokens)
    if not include and not exclude:
        return list(samples)

    filtered = []
    for sample in samples:
        token = _sample_token(sample)
        if include and token not in include:
            continue
        if exclude and token in exclude:
            continue
        filtered.append(sample)
    return filtered


def _sample_overlap_token_count(train_samples, eval_samples):
    train_tokens = {_sample_token(sample) for sample in train_samples or []}
    eval_tokens = {_sample_token(sample) for sample in eval_samples or []}
    train_tokens.discard("")
    eval_tokens.discard("")
    return len(train_tokens.intersection(eval_tokens))


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
    feature_names = sorted(str(column) for column in X.columns)
    X = X.reindex(columns=feature_names)
    y = np.asarray(labels, dtype=int)

    model = BuyCatBoostModel(cat_feature_names=config.get("cat_feature_names", []))
    model.fit(X, y)
    proba = model.predict_proba(X)
    threshold = model.select_threshold(y, proba, min_precision=float(config.get("buy_min_precision", 0.10)))

    model_path = output_dir / "buy_model.cbm"
    model.model.save_model(str(model_path))

    threshold_path = output_dir / "buy_threshold.json"
    threshold_path.write_text(json.dumps({"threshold": float(threshold)}, ensure_ascii=False, indent=2), encoding="utf-8")

    feature_schema_path = output_dir / "feature_schema.json"
    feature_schema_path.write_text(
        json.dumps({"feature_names": feature_names}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "model_path": str(model_path),
        "threshold": float(threshold),
        "threshold_path": str(threshold_path),
        "feature_schema_path": str(feature_schema_path),
        "feature_names": feature_names,
        "model": model,
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
        token = str(sample.get("meta", {}).get("token_address", "")).strip().lower()
        if not token:
            continue
        grouped.setdefault(token, []).append(sample)

    episodes = []
    for token_samples in grouped.values():
        ordered = sorted(token_samples, key=lambda s: int(s.get("meta", {}).get("sample_time", 0) or 0))
        episode = [_sample_to_event(s) for s in ordered]
        if len(episode) >= 2:
            episodes.append(episode)

    if not episodes:
        raise ValueError("no sell episodes could be built from samples")

    env = MultiEpisodeTradingEnv(
        episodes,
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
            obs_rows.append(build_sell_observation(event))
            action_rows.append(_rule_exit_action(event))
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

    return {
        "policy_path": str(policy_path),
        "total_timesteps": int(config.get("total_timesteps", 20000)),
        "model": model,
    }


def _build_eval_episodes(eval_samples):
    grouped = {}
    for sample in eval_samples:
        token = str(sample.get("meta", {}).get("token_address", "")).strip().lower()
        if not token:
            continue
        grouped.setdefault(token, []).append(sample)

    episodes = []
    for token_samples in grouped.values():
        ordered = sorted(token_samples, key=lambda s: int(s.get("meta", {}).get("sample_time", 0) or 0))
        if len(ordered) >= 2:
            episodes.append(ordered)
    return episodes


def _rule_exit_action(event):
    sp = float(event.get("sell_pressure", 0.0))
    if sp >= 0.9:
        return 3
    if sp >= 0.8:
        return 2
    if sp >= 0.5:
        return 1
    return 0


def _choose_exit_action(event, sell_policy):
    if sell_policy is not None and hasattr(sell_policy, "predict"):
        obs = build_sell_observation(event)
        action, _ = sell_policy.predict(obs, deterministic=True)
        return coerce_action(action)
    return _rule_exit_action(event)


def _max_drawdown_pct(equity_curve):
    if not equity_curve:
        return 0.0
    peak = float(equity_curve[0])
    worst_dd = 0.0
    for eq in equity_curve:
        eqf = float(eq)
        if eqf > peak:
            peak = eqf
        if peak > 0:
            dd = (eqf / peak) - 1.0
            if dd < worst_dd:
                worst_dd = dd
    return float(worst_dd * 100.0)


def _sortino_ratio_from_returns(returns):
    if not returns:
        return 0.0
    arr = np.asarray(returns, dtype=float)
    downside = arr[arr < 0.0]
    if downside.size == 0:
        return 0.0
    downside_dev = float(np.sqrt(np.mean(np.square(downside))))
    if downside_dev <= 0.0:
        return 0.0
    return float(arr.mean() / downside_dev)


def _run_eval_replay(episodes, buy_model, threshold, sell_policy, feature_names=None):
    initial_equity = 1.0
    cash = initial_equity
    position_size = 0.0
    position_cost_basis = 0.0
    equity_curve = [initial_equity]
    step_returns = []
    trade_returns = []

    for episode in episodes:
        candidate_indices = []
        candidate_rows = []
        for idx, sample in enumerate(episode[:-1]):
            event = _sample_to_event(sample)
            if float(event.get("mid_price", 0.0)) <= 0.0:
                continue
            candidate_indices.append(idx)
            candidate_rows.append(dict(sample.get("features", {})))

        buy_prob_by_index = {}
        if candidate_rows:
            if feature_names is None:
                X = pd.DataFrame(candidate_rows)
            else:
                validated_rows = []
                for row in candidate_rows:
                    validated = build_feature_frame(row, feature_names)
                    validated_rows.append(validated.iloc[0].to_dict())
                X = pd.DataFrame(validated_rows, columns=feature_names)
            proba = buy_model.predict_proba(X)
            rows = proba if hasattr(proba, "__len__") and len(proba) > 0 else [proba]
            for idx, row in zip(candidate_indices, rows):
                buy_prob_by_index[idx] = float(row[1]) if hasattr(row, "__len__") and len(row) > 1 else float(row[0])

        for idx, sample in enumerate(episode):
            event = _sample_to_event(sample)
            price = float(event.get("mid_price", 0.0))
            if price <= 0.0:
                equity_curve.append(cash + position_size * price)
                continue

            if position_size <= 0.0:
                buy_prob = buy_prob_by_index.get(idx)
                if buy_prob is not None and buy_prob >= threshold and cash > 0.0:
                    position_size = cash / price
                    position_cost_basis = cash
                    cash = 0.0
            else:
                action = _choose_exit_action(event, sell_policy)
                fraction = sell_fraction_for_action(action)
                if fraction > 0.0:
                    sell_size = position_size * fraction
                    proceeds = sell_size * price
                    basis_fraction = sell_size / max(position_size, 1e-9)
                    realized_cost_basis = position_cost_basis * basis_fraction
                    trade_returns.append((proceeds - realized_cost_basis) / max(realized_cost_basis, 1e-9))
                    cash += proceeds
                    position_size -= sell_size
                    position_cost_basis -= realized_cost_basis

            equity = cash + position_size * price
            prev_equity = equity_curve[-1]
            if prev_equity > 0:
                step_returns.append((equity / prev_equity) - 1.0)
            equity_curve.append(equity)

        if position_size > 0.0:
            final_price = float(_sample_to_event(episode[-1]).get("mid_price", 0.0))
            proceeds = position_size * final_price
            realized_cost_basis = position_cost_basis
            trade_returns.append((proceeds - realized_cost_basis) / max(realized_cost_basis, 1e-9))
            cash += proceeds
            position_size = 0.0
            position_cost_basis = 0.0
            equity_curve.append(cash)

    final_equity = equity_curve[-1] if equity_curve else initial_equity
    total_trades = len(trade_returns)
    if total_trades == 0:
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "net_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "sortino_ratio": 0.0,
        }

    wins = sum(1 for value in trade_returns if value > 0.0)
    return {
        "total_trades": int(total_trades),
        "win_rate": float(wins / total_trades),
        "net_return_pct": float((final_equity / initial_equity - 1.0) * 100.0),
        "max_drawdown_pct": float(_max_drawdown_pct(equity_curve)),
        "sortino_ratio": float(_sortino_ratio_from_returns(step_returns)),
    }


def _load_ppo_policy(policy_path):
    if not policy_path:
        return None
    try:
        from stable_baselines3 import PPO
    except Exception:
        logger.warning("stable_baselines3 unavailable; falling back to rule-based exits")
        return None

    try:
        return PPO.load(str(policy_path))
    except Exception as exc:
        logger.warning("failed to load PPO policy from %s: %s", policy_path, exc)
        return None


def _load_feature_names_from_artifact(buy_artifact):
    feature_names = normalize_feature_names(buy_artifact.get("feature_names"))
    if feature_names is not None:
        return feature_names

    feature_schema_path = buy_artifact.get("feature_schema_path")
    if not feature_schema_path:
        return None

    return load_feature_names_from_schema(feature_schema_path)


def run_ab_evaluation(config, buy_artifact, ppo_artifact, bc_artifact):
    eval_samples = list(config.get("eval_samples") or [])
    episodes = _build_eval_episodes(eval_samples)
    if not episodes:
        raise ValueError("no eval episodes could be built from eval samples")

    buy_model = buy_artifact.get("model")
    threshold = float(buy_artifact.get("threshold", 1.0))
    if buy_model is None:
        raise ValueError("buy artifact missing trained model")

    sell_policy = ppo_artifact.get("model")
    if sell_policy is None:
        sell_policy = _load_ppo_policy(ppo_artifact.get("policy_path"))

    replay = _run_eval_replay(
        episodes,
        buy_model,
        threshold,
        sell_policy,
        feature_names=_load_feature_names_from_artifact(buy_artifact),
    )

    return {
        "total_trades": int(replay["total_trades"]),
        "win_rate": float(replay["win_rate"]),
        "net_return_pct": float(replay["net_return_pct"]),
        "max_drawdown_pct": float(replay["max_drawdown_pct"]),
        "sortino_ratio": float(replay["sortino_ratio"]),
        "buy_threshold": threshold,
        "sell_episode_count": int(len(episodes)),
        "bc_samples": int(bc_artifact.get("bc_samples", 0)),
        "ppo_total_timesteps": int(ppo_artifact.get("total_timesteps", 0)),
        "train_file_count": int(config.get("train_file_count", 0)),
        "eval_file_count": int(config.get("eval_file_count", 0)),
        "overlap_token_count": int(config.get("overlap_token_count", 0)),
        "raw_overlap_token_count": int(config.get("raw_overlap_token_count", config.get("overlap_token_count", 0))),
        "excluded_eval_token_count": int(config.get("excluded_eval_token_count", 0)),
        "pipeline_status": "ok",
    }


def run_hybrid_training(config):
    if "lifecycle_paths" in config:
        lifecycle_files = _stable_lifecycle_order(config.get("lifecycle_paths") or [])
    else:
        lifecycle_files = _discover_lifecycle_files(config.get("lifecycle_dir", "data/training"))

    split_result = _split_lifecycle_files(
        lifecycle_files,
        train_split_ratio=config.get("train_split_ratio", 0.8),
        min_eval_files=config.get("min_eval_files", 1),
        enforce_no_overlap=False,
        return_token_sets=True,
    )
    if len(split_result) == 5:
        train_files, eval_files, raw_overlap_token_count, train_raw_tokens, _eval_raw_tokens = split_result
    else:
        train_files, eval_files, raw_overlap_token_count = split_result
        train_raw_tokens = None

    train_config = dict(config)
    train_config["lifecycle_paths"] = train_files
    train_config["train_file_count"] = int(len(train_files))
    train_config["eval_file_count"] = int(len(eval_files))
    train_config["overlap_token_count"] = int(raw_overlap_token_count)
    train_config["raw_overlap_token_count"] = int(raw_overlap_token_count)

    eval_config = dict(config)
    eval_config["lifecycle_paths"] = eval_files
    eval_config["train_file_count"] = int(len(train_files))
    eval_config["eval_file_count"] = int(len(eval_files))
    eval_config["overlap_token_count"] = int(raw_overlap_token_count)
    eval_config["raw_overlap_token_count"] = int(raw_overlap_token_count)
    eval_config["excluded_eval_token_count"] = 0

    buy_artifact = train_buy_model(train_config)
    env_bundle = build_sell_env(train_config, buy_artifact)
    bc_artifact = run_bc_warmstart(train_config, env_bundle)
    ppo_artifact = run_ppo_finetune(train_config, env_bundle, bc_artifact)
    if "eval_samples" not in eval_config:
        eval_load_config = dict(eval_config)
        if raw_overlap_token_count > 0:
            if train_raw_tokens is None:
                train_raw_tokens = _collect_raw_token_addresses(train_files)
            eval_load_config["exclude_token_addresses"] = train_raw_tokens
            eval_config["excluded_eval_token_count"] = int(raw_overlap_token_count)
        eval_config["eval_samples"] = _load_samples(eval_load_config)
    sample_overlap_token_count = _sample_overlap_token_count(
        buy_artifact.get("samples", []),
        eval_config.get("eval_samples", []),
    )
    eval_config["overlap_token_count"] = int(sample_overlap_token_count)
    if sample_overlap_token_count > 0:
        raise ValueError(
            f"train/eval sample leakage detected: overlap_token_count={sample_overlap_token_count}; "
            "adjust lifecycle partitions or explicit eval samples before training"
        )
    evaluation = run_ab_evaluation(eval_config, buy_artifact, ppo_artifact, bc_artifact)

    result = {
        "artifacts": {
            "buy_model": {
                "model_path": buy_artifact.get("model_path"),
                "threshold": buy_artifact.get("threshold"),
                "threshold_path": buy_artifact.get("threshold_path"),
                "feature_schema_path": buy_artifact.get("feature_schema_path"),
                "feature_names": buy_artifact.get("feature_names"),
            },
            "sell_policy": {
                "policy_path": ppo_artifact.get("policy_path"),
                "total_timesteps": ppo_artifact.get("total_timesteps"),
            },
            "bc_warmstart": bc_artifact,
        },
        "evaluation": evaluation,
    }

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "hybrid_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
