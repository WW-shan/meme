from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.dataset_builder import DatasetBuilder, stable_lifecycle_order
from src.model.buy_catboost import BuyCatBoostModel
from src.model.hybrid_inference import (
    build_feature_frame,
    coerce_action,
    load_feature_names_from_schema,
    normalize_feature_names,
)
try:
    from src.model.hybrid_inference import build_feature_frame_many
except Exception:  # pragma: no cover - compatibility with older/stubbed inference modules
    def build_feature_frame_many(feature_rows, feature_names=None, ignored_feature_names=None):
        rows = list(feature_rows or [])
        if feature_names is None:
            return pd.DataFrame(rows)
        validated_rows = []
        for row in rows:
            try:
                validated = build_feature_frame(row, feature_names, ignored_feature_names)
            except TypeError:
                validated = build_feature_frame(row, feature_names)
            if hasattr(validated, "iloc"):
                validated_rows.append(validated.iloc[0].to_dict())
            else:
                validated_rows.append(validated)
        return pd.DataFrame(validated_rows, columns=feature_names)
try:
    from src.model.hybrid_inference import load_feature_schema_from_file
except Exception:  # pragma: no cover - compatibility with older/stubbed inference modules
    def load_feature_schema_from_file(schema_path):
        return {
            "feature_names": load_feature_names_from_schema(schema_path),
            "ignored_feature_names": [],
        }
from src.rl.trading_env import MultiEpisodeTradingEnv, build_sell_observation, sell_fraction_for_action
try:
    from src.rl.trading_env import canonical_sell_action
except Exception:  # pragma: no cover - compatibility with older/stubbed env modules
    def canonical_sell_action(action, *, allow_partial_exits=True):
        action_value = int(action)
        if allow_partial_exits:
            return action_value
        return 0 if action_value == 0 else 3
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


_INVALID_FEATURE_PREFIXES = ("future_", "target_", "label_")


def _is_invalid_feature_name(name):
    value = str(name)
    return value.startswith(_INVALID_FEATURE_PREFIXES)


def _prune_training_feature_rows(rows, *, drop_constant=True):
    raw_feature_names = sorted({str(name) for row in rows for name in row.keys()})
    invalid_features = [name for name in raw_feature_names if _is_invalid_feature_name(name)]
    valid_feature_names = [name for name in raw_feature_names if name not in set(invalid_features)]

    frame = pd.DataFrame(rows)
    constant_features = []
    if drop_constant and valid_feature_names:
        for name in valid_feature_names:
            series = frame[name] if name in frame.columns else pd.Series([np.nan] * len(rows))
            if int(series.nunique(dropna=False)) <= 1:
                constant_features.append(name)

    constant_set = set(constant_features)
    feature_names = [name for name in valid_feature_names if name not in constant_set]
    if not feature_names:
        raise ValueError("no usable training features after pruning invalid and constant columns")

    pruned_rows = []
    for row in rows:
        pruned_rows.append({name: row.get(name) for name in feature_names})

    return pruned_rows, feature_names, {
        "invalid": invalid_features,
        "constant": constant_features,
    }


def _indices_have_two_classes(indices, labels):
    return len({int(labels[index]) for index in indices}) >= 2


def _split_samples_for_calibration(samples, labels, *, ratio=0.2, min_samples=20, random_state=42):
    sample_count = len(samples)
    all_indices = list(range(sample_count))
    split_ratio = float(ratio)
    if split_ratio <= 0.0:
        return all_indices, []
    if split_ratio >= 1.0:
        raise ValueError(f"buy_calibration_ratio must be less than 1.0, got {split_ratio}")

    groups = {}
    for idx, sample in enumerate(samples):
        token = _sample_token(sample) or f"__row_{idx}"
        groups.setdefault(token, []).append(idx)

    tokens = sorted(groups.keys())
    if len(tokens) < 2:
        return all_indices, []

    rng = np.random.default_rng(int(random_state))
    shuffled_tokens = list(tokens)
    rng.shuffle(shuffled_tokens)

    required_min_samples = max(1, int(min_samples))
    target_samples = max(required_min_samples, int(round(sample_count * split_ratio)))
    target_samples = min(target_samples, sample_count - 1)

    best = None
    for split_count in range(1, len(shuffled_tokens)):
        calibration_tokens = set(shuffled_tokens[:split_count])
        calibration_indices = sorted(
            index for token in calibration_tokens for index in groups[token]
        )
        fit_indices = sorted(index for token in shuffled_tokens[split_count:] for index in groups[token])

        if len(calibration_indices) < required_min_samples:
            continue
        if not fit_indices:
            continue
        if not _indices_have_two_classes(calibration_indices, labels):
            continue
        if not _indices_have_two_classes(fit_indices, labels):
            continue

        distance = abs(len(calibration_indices) - target_samples)
        candidate = (distance, len(calibration_indices), fit_indices, calibration_indices)
        if best is None or candidate[:2] < best[:2]:
            best = candidate

    if best is None:
        return all_indices, []

    return best[2], best[3]


def _take_indices(values, indices):
    return [values[index] for index in indices]


def _positive_probabilities(prob):
    prob_arr = np.asarray(prob, dtype=float)
    if prob_arr.ndim == 2:
        return prob_arr[:, 1]
    return prob_arr


def _coerce_float_list(raw, default=None):
    if raw is None:
        return list(default or [])
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = list(raw)
    values = []
    for part in parts:
        if part == "":
            continue
        try:
            values.append(float(part))
        except (TypeError, ValueError):
            continue
    return values


def _threshold_classification_metrics(y_true, prob, threshold):
    y_arr = np.asarray(y_true, dtype=int)
    pos_prob = _positive_probabilities(prob)
    pred = pos_prob >= float(threshold)
    tp = int(np.sum((pred == 1) & (y_arr == 1)))
    fp = int(np.sum((pred == 1) & (y_arr == 0)))
    fn = int(np.sum((pred == 0) & (y_arr == 1)))
    pred_count = int(np.sum(pred == 1))
    positive_count = int(np.sum(y_arr == 1))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return {
        "sample_count": int(len(y_arr)),
        "positive_count": positive_count,
        "predicted_positive_count": pred_count,
        "precision": float(precision),
        "recall": float(recall),
    }


def _stop_loss_config_to_pct(value):
    stop_loss = float(value)
    if -1.0 <= stop_loss <= 1.0:
        return stop_loss * 100.0
    return stop_loss


def _load_samples(config):
    if "samples" in config:
        samples = list(config.get("samples") or [])
    else:
        entry_age_seconds = int(config.get("max_entry_age_seconds", config.get("max_sample_age_seconds", 300)))
        hold_seconds = max(0, int(config.get("max_hold_seconds", 300)))
        dataset_max_age_seconds = int(
            config.get("dataset_max_sample_age_seconds", entry_age_seconds + hold_seconds)
        )
        label_stop_loss_pct = config.get("label_stop_loss_pct")
        if label_stop_loss_pct is None:
            label_stop_loss_pct = _stop_loss_config_to_pct(config.get("stop_loss", -0.50))
        builder = DatasetBuilder(
            lifecycle_dir=config.get("lifecycle_dir", "data/training"),
            sample_mode=config.get("sample_mode", "trade_event"),
            max_sample_age_seconds=dataset_max_age_seconds,
            future_windows=config.get("future_windows", [300]),
            max_samples_per_token=config.get("max_samples_per_token"),
            label_fee_bps=float(config.get("label_fee_bps", config.get("fee_bps", 0.0))),
            label_slippage_bps=float(config.get("label_slippage_bps", config.get("slippage_bps", 0.0))),
            label_stop_loss_pct=float(label_stop_loss_pct),
            label_target_return_pct=float(config.get("label_target_return_pct", config.get("target_threshold_value", 80.0))),
        )
        lifecycle_paths = config.get("lifecycle_paths") or []
        if lifecycle_paths:
            builder.load_lifecycle_paths(lifecycle_paths)
        else:
            builder.load_lifecycle_files()
        samples = builder.samples

    samples = _filter_samples_by_tokens(
        samples,
        include_tokens=config.get("include_token_addresses"),
        exclude_tokens=config.get("exclude_token_addresses"),
    )
    return _limit_samples_per_token(samples, config.get("max_samples_per_token"))


def _normalize_token_set(tokens):
    normalized = set()
    for token in tokens or []:
        value = str(token or "").strip().lower()
        if value:
            normalized.add(value)
    return normalized


def _sample_token(sample):
    return str(sample.get("meta", {}).get("token_address") or "").strip().lower()


def _sample_age_seconds(sample):
    meta = sample.get("meta", {}) or {}
    if "sample_interval" in meta:
        try:
            return int(meta.get("sample_interval") or 0)
        except Exception:
            return 0
    if "create_timestamp" in meta and "sample_time" in meta:
        try:
            return int(meta.get("sample_time") or 0) - int(meta.get("create_timestamp") or 0)
        except Exception:
            return 0
    return 0


def _max_entry_age_seconds(config):
    return int(config.get("max_entry_age_seconds", config.get("max_sample_age_seconds", 300)))


def _filter_samples_by_entry_window(samples, config):
    max_age = _max_entry_age_seconds(config)
    return [sample for sample in samples if _sample_age_seconds(sample) <= max_age]


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


def _samples_for_tokens(samples, tokens):
    normalized = _normalize_token_set(tokens)
    return [sample for sample in samples if _sample_token(sample) in normalized]


def _limit_samples_per_token(samples, max_samples_per_token=None):
    if max_samples_per_token is None:
        return list(samples)
    limit = int(max_samples_per_token)
    if limit <= 0:
        return list(samples)

    grouped = {}
    for original_index, sample in enumerate(samples):
        token = _sample_token(sample) or f"__row_{original_index}"
        grouped.setdefault(token, []).append((original_index, sample))

    limited = []
    for values in grouped.values():
        ordered = sorted(
            values,
            key=lambda item: (
                int(item[1].get("meta", {}).get("sample_time", 0) or 0),
                item[0],
            ),
        )
        if len(ordered) <= limit:
            limited.extend(ordered)
            continue

        selected_positions = sorted({int(round(pos)) for pos in np.linspace(0, len(ordered) - 1, limit)})
        limited.extend(ordered[position] for position in selected_positions)

    return [sample for _original_index, sample in sorted(limited, key=lambda item: item[0])]


def train_buy_model(config):
    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = _load_samples(config)
    buy_samples = _filter_samples_by_entry_window(samples, config)
    target_label_column = config.get("target_label_column", "executable_return_pct")
    target_threshold_value = float(config.get("target_threshold_value", 80.0))
    rows, labels, metas = _prepare_training_rows(
        buy_samples,
        target_label_column,
        target_threshold_value,
    )

    rows, feature_names, dropped_features = _prune_training_feature_rows(
        rows,
        drop_constant=bool(config.get("drop_constant_features", True)),
    )
    X = pd.DataFrame(rows)
    X = X.reindex(columns=feature_names)
    y = np.asarray(labels, dtype=int)

    fit_indices, calibration_indices = _split_samples_for_calibration(
        buy_samples,
        labels,
        ratio=float(config.get("buy_calibration_ratio", 0.2)),
        min_samples=int(config.get("min_calibration_samples", 20)),
        random_state=int(config.get("buy_random_state", config.get("random_state", 42))),
    )

    X_fit = X.iloc[fit_indices].reset_index(drop=True)
    y_fit = y[fit_indices]
    calibration_used = bool(calibration_indices)
    if calibration_used:
        X_threshold = X.iloc[calibration_indices].reset_index(drop=True)
        y_threshold = y[calibration_indices]
        eval_set = (X_threshold, y_threshold)
        threshold_source = "calibration"
    else:
        X_threshold = X
        y_threshold = y
        eval_set = None
        threshold_source = "train"

    model = BuyCatBoostModel(
        cat_feature_names=config.get("cat_feature_names", []),
        random_state=int(config.get("buy_random_state", config.get("random_state", 42))),
        catboost_params=config.get("catboost_params"),
    )
    model.fit(X_fit, y_fit, eval_set=eval_set)
    proba = model.predict_proba(X_threshold)
    threshold = model.select_threshold(
        y_threshold,
        proba,
        min_precision=float(config.get("buy_min_precision", 0.50)),
        min_threshold=float(config.get("buy_min_threshold", 0.5)),
        min_predictions=int(config.get("buy_min_calibration_predictions", 20)),
    )
    threshold_metrics = _threshold_classification_metrics(y_threshold, proba, threshold)

    model_path = output_dir / "buy_model.cbm"
    model.model.save_model(str(model_path))

    threshold_path = output_dir / "buy_threshold.json"
    threshold_path.write_text(json.dumps({"threshold": float(threshold)}, ensure_ascii=False, indent=2), encoding="utf-8")

    feature_schema_path = output_dir / "feature_schema.json"
    feature_schema_path.write_text(
        json.dumps(
            {
                "feature_names": feature_names,
                "dropped_features": dropped_features,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "model_path": str(model_path),
        "threshold": float(threshold),
        "threshold_path": str(threshold_path),
        "feature_schema_path": str(feature_schema_path),
        "feature_names": feature_names,
        "dropped_features": dropped_features,
        "target_label_column": target_label_column,
        "target_threshold_value": target_threshold_value,
        "threshold_source": threshold_source,
        "calibration": {
            "source": threshold_source,
            "sample_count": int(len(y_threshold)),
            "fit_sample_count": int(len(y_fit)),
            "token_count": int(len({_sample_token(buy_samples[index]) for index in calibration_indices})) if calibration_used else 0,
            "metrics": threshold_metrics,
        },
        "sell_training_samples": _samples_for_tokens(
            samples,
            {_sample_token(buy_samples[index]) for index in fit_indices},
        ),
        "calibration_samples": _samples_for_tokens(
            samples,
            {_sample_token(buy_samples[index]) for index in calibration_indices},
        ) if calibration_used else [],
        "model": model,
        "samples": buy_samples,
        "all_samples": samples,
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
    sell_samples = buy_artifact.get("sell_training_samples") or buy_artifact.get("samples", [])
    for sample in sell_samples:
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
        fee_bps=float(config.get("fee_bps", 0.0)),
        slippage_bps=float(config.get("slippage_bps", 0.0)),
        drawdown_penalty_weight=float(config.get("sell_drawdown_penalty_weight", 0.0)),
        hold_penalty_per_step=float(config.get("sell_hold_penalty_per_step", 0.0)),
        turnover_penalty=float(config.get("sell_turnover_penalty", 0.0)),
        allow_partial_exits=bool(config.get("allow_partial_exits", False)),
    )
    return {"env": env, "episodes": episodes, "episode_count": len(episodes)}


def _torch_save(obj, path):
    import torch
    torch.save(obj, path)


def _event_price(event):
    return float(event.get("mid_price", 0.0) or 0.0)


def _event_ts(event):
    return float(event.get("ts", 0.0) or 0.0)


def _profit_path_exit_action(episode, index, config, *, entry_price, peak_price, entry_ts):
    event = episode[index]
    price = _event_price(event)
    if entry_price <= 0.0 or price <= 0.0:
        return 0

    current_return = (price / entry_price) - 1.0
    peak_return = (peak_price / entry_price) - 1.0 if peak_price > 0.0 else current_return
    drawdown_from_peak = (price / peak_price) - 1.0 if peak_price > 0.0 else 0.0
    age_seconds = max(0.0, _event_ts(event) - float(entry_ts))

    stop_loss = float(config.get("stop_loss", -0.35))
    if current_return <= stop_loss:
        return 3

    min_hold_seconds = float(config.get("bc_profit_path_min_hold_seconds", 0.0))
    if age_seconds < min_hold_seconds:
        return 0

    trailing_start = config.get("bc_profit_path_trailing_start_pct", config.get("trailing_start_pct", 0.25))
    trailing_stop = config.get("bc_profit_path_trailing_stop_pct", config.get("trailing_stop_pct", 0.20))
    if (
        trailing_start is not None
        and trailing_stop is not None
        and peak_return >= float(trailing_start)
        and drawdown_from_peak <= -float(trailing_stop)
    ):
        return 3

    max_hold_seconds = config.get("max_hold_seconds")
    future_events = []
    for future_event in episode[index:]:
        if max_hold_seconds is not None and _event_ts(future_event) - float(entry_ts) > float(max_hold_seconds):
            break
        future_events.append(future_event)

    if not future_events:
        return 3 if current_return > 0.0 else 0

    future_returns = [
        (_event_price(future_event) / entry_price) - 1.0
        for future_event in future_events
        if _event_price(future_event) > 0.0
    ]
    if not future_returns:
        return 0

    future_best_return = max(future_returns)
    sell_margin = float(config.get("bc_profit_path_sell_margin_pct", 0.05))
    if future_best_return >= current_return + sell_margin:
        return 0

    if index >= len(episode) - 1:
        return 3

    sell100_pct = float(config.get("bc_profit_path_sell100_pct", 0.80))
    if current_return >= sell100_pct:
        return 3

    if bool(config.get("allow_partial_exits", False)):
        sell50_pct = float(config.get("bc_profit_path_sell50_pct", 0.50))
        sell25_pct = float(config.get("bc_profit_path_sell25_pct", 0.20))
        if current_return >= sell50_pct:
            return 2
        if current_return >= sell25_pct:
            return 1

    final_future_return = future_returns[-1]
    if current_return > 0.0 and final_future_return <= current_return - sell_margin:
        return 3

    return 0


def _build_bc_arrays(episodes, config=None):
    config = dict(config or {})
    label_mode = str(config.get("bc_label_mode", "sell_pressure") or "sell_pressure").strip().lower()
    obs_rows, action_rows = [], []
    for ep in episodes:
        if label_mode == "profit_path":
            entry_event = ep[0] if ep else {}
            entry_price = max(_event_price(entry_event), 1e-9)
            entry_ts = _event_ts(entry_event)
            peak_price = entry_price
            for index, event in enumerate(ep):
                price = _event_price(event)
                if price > 0.0:
                    peak_price = max(peak_price, price)
                obs_rows.append(
                    build_sell_observation(
                        event,
                        entry_price=entry_price,
                        peak_price=peak_price,
                        position_remaining=1.0,
                        entry_ts=entry_ts,
                        episode_start_ts=entry_ts,
                    )
                )
                action_rows.append(
                    _profit_path_exit_action(
                        ep,
                        index,
                        config,
                        entry_price=entry_price,
                        peak_price=peak_price,
                        entry_ts=entry_ts,
                    )
                )
            continue

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
    obs_arr, act_arr = _build_bc_arrays(episodes, config)
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

    return {
        "weights": str(weight_path),
        "bc_samples": int(obs_arr.shape[0]),
        "bc_label_mode": str(config.get("bc_label_mode", "sell_pressure") or "sell_pressure"),
    }


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
    return sorted(episodes, key=_episode_start_time)


def _episode_start_time(episode):
    if not episode:
        return 0
    return int(episode[0].get("meta", {}).get("sample_time", 0) or 0)


def _split_episodes_for_walk_forward(episodes, segment_count):
    count = max(0, int(segment_count))
    if count <= 1:
        return []
    ordered = sorted(episodes, key=_episode_start_time)
    if not ordered:
        return []

    segment_size = int(np.ceil(len(ordered) / count))
    segments = []
    for index in range(count):
        start = index * segment_size
        end = min(len(ordered), start + segment_size)
        segment = ordered[start:end]
        if segment:
            segments.append((index, segment))
    return segments


def _rule_exit_action(event):
    sp = float(event.get("sell_pressure", 0.0))
    if sp >= 0.9:
        return 3
    if sp >= 0.8:
        return 2
    if sp >= 0.5:
        return 1
    return 0


def _choose_exit_action(
    event,
    sell_policy,
    *,
    entry_price=None,
    peak_price=None,
    position_remaining=1.0,
    entry_ts=None,
    episode_start_ts=None,
):
    if sell_policy is not None and hasattr(sell_policy, "predict"):
        obs = build_sell_observation(
            event,
            entry_price=entry_price,
            peak_price=peak_price,
            position_remaining=position_remaining,
            entry_ts=entry_ts,
            episode_start_ts=episode_start_ts,
        )
        action, _ = sell_policy.predict(obs, deterministic=True)
        return coerce_action(action)
    return _rule_exit_action(event)


def _sell_exit_reason(action, *, allow_partial_exits):
    action_value = int(action)
    if action_value == 1:
        return "SELL25" if allow_partial_exits else "SELL25_FULL_EXIT"
    if action_value == 2:
        return "SELL50" if allow_partial_exits else "SELL50_FULL_EXIT"
    if action_value == 3:
        return "SELL100"
    return "SELL"


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


def _episode_buy_probabilities(
    episodes,
    buy_model,
    *,
    feature_names=None,
    ignored_feature_names=None,
    max_entry_age_seconds=None,
):
    entry_age_limit = None if max_entry_age_seconds is None else int(max_entry_age_seconds)
    probabilities_by_episode = []

    for episode in episodes:
        candidate_indices = []
        candidate_rows = []
        for idx, sample in enumerate(episode[:-1]):
            event = _sample_to_event(sample)
            if float(event.get("mid_price", 0.0)) <= 0.0:
                continue
            if entry_age_limit is not None and _sample_age_seconds(sample) > entry_age_limit:
                continue
            candidate_indices.append(idx)
            candidate_rows.append(dict(sample.get("features", {})))

        buy_prob_by_index = {}
        if candidate_rows:
            X = build_feature_frame_many(candidate_rows, feature_names, ignored_feature_names)
            proba = buy_model.predict_proba(X)
            positive_probabilities = np.asarray(_positive_probabilities(proba), dtype=float).reshape(-1)
            for idx, probability in zip(candidate_indices, positive_probabilities):
                buy_prob_by_index[idx] = float(probability)

        probabilities_by_episode.append(buy_prob_by_index)

    return probabilities_by_episode


def _run_eval_replay(
    episodes,
    buy_model,
    threshold,
    sell_policy,
    feature_names=None,
    ignored_feature_names=None,
    stop_loss=-0.50,
    position_fraction=1.0,
    include_trade_log=False,
    trailing_start_pct=None,
    trailing_stop_pct=None,
    rug_sell_pressure=None,
    fee_bps=0.0,
    slippage_bps=0.0,
    one_entry_per_token=True,
    max_trades_per_token=None,
    max_entry_age_seconds=None,
    max_hold_seconds=None,
    min_policy_hold_seconds=0,
    max_position_fraction=None,
    allow_partial_exits=False,
    buy_probabilities_by_episode=None,
):
    initial_equity = 1.0
    episode_count = int(len(episodes or []))
    cash = initial_equity
    positions = {}
    latest_prices = {}
    latest_sample_times = {}
    equity_curve = [initial_equity]
    step_returns = []
    trade_returns = []
    trade_log = []
    stake_fraction = max(0.0, min(1.0, float(position_fraction)))
    max_stake_fraction = None if max_position_fraction is None else max(0.0, float(max_position_fraction))
    fee_rate = max(0.0, float(fee_bps)) / 10000.0
    slippage_rate = max(0.0, float(slippage_bps)) / 10000.0
    max_entries_per_token = None
    if max_trades_per_token is not None:
        max_entries_per_token = max(0, int(max_trades_per_token))
    entry_age_limit = None if max_entry_age_seconds is None else int(max_entry_age_seconds)
    hold_time_limit = None if max_hold_seconds is None else int(max_hold_seconds)
    policy_hold_floor = max(0, int(min_policy_hold_seconds or 0))
    entry_counts_by_token = {}
    entry_count = 0
    partial_exits_enabled = bool(allow_partial_exits)
    if buy_probabilities_by_episode is None:
        buy_probabilities_by_episode = _episode_buy_probabilities(
            episodes,
            buy_model,
            feature_names=feature_names,
            ignored_feature_names=ignored_feature_names,
            max_entry_age_seconds=max_entry_age_seconds,
        )

    def _entry_allowed(token):
        token_key = str(token or "").strip().lower()
        count = int(entry_counts_by_token.get(token_key, 0))
        if bool(one_entry_per_token) and count > 0:
            return False
        if max_entries_per_token is not None and count >= max_entries_per_token:
            return False
        return True

    def _mark_entry(token):
        nonlocal entry_count
        token_key = str(token or "").strip().lower()
        entry_counts_by_token[token_key] = int(entry_counts_by_token.get(token_key, 0)) + 1
        entry_count += 1

    def _stake_amount():
        stake = cash * stake_fraction
        if max_stake_fraction is not None:
            stake = min(stake, initial_equity * max_stake_fraction)
        return min(cash, max(0.0, stake))

    def _entry_fill(stake, price):
        execution_price = float(price) * (1.0 + slippage_rate)
        if execution_price <= 0.0:
            return 0.0, 0.0
        size = float(stake) * (1.0 - fee_rate) / execution_price
        effective_price = float(stake) / max(size, 1e-12)
        return size, effective_price

    def _exit_proceeds(size, price):
        execution_price = float(price) * max(0.0, 1.0 - slippage_rate)
        gross = float(size) * execution_price
        proceeds = gross * (1.0 - fee_rate)
        return proceeds, execution_price

    def _position_liquidation_value(position):
        price = latest_prices.get(position["token"])
        if position["size"] <= 0.0 or price is None or float(price) <= 0.0:
            return 0.0
        proceeds, _execution_price = _exit_proceeds(position["size"], price)
        return proceeds

    def _portfolio_equity():
        return cash + sum(_position_liquidation_value(position) for position in positions.values())

    def _append_equity_point():
        equity = _portfolio_equity()
        prev_equity = equity_curve[-1]
        if prev_equity > 0:
            step_returns.append((equity / prev_equity) - 1.0)
        equity_curve.append(equity)

    def _record_exit(
        *,
        position,
        exit_time,
        exit_index,
        exit_price,
        exit_reason,
        proceeds,
        realized_cost_basis,
        size_fraction,
        requested_size_fraction=None,
    ):
        trade_return = (proceeds - realized_cost_basis) / max(realized_cost_basis, 1e-9)
        trade_returns.append(trade_return)
        if include_trade_log:
            requested_fraction = size_fraction if requested_size_fraction is None else requested_size_fraction
            trade_log.append(
                {
                    "token": str(position["token"]),
                    "entry_time": int(position["entry_time"]),
                    "entry_index": int(position["entry_index"]),
                    "entry_price": float(position["entry_price"]),
                    "exit_time": int(exit_time),
                    "exit_index": int(exit_index),
                    "exit_price": float(exit_price),
                    "exit_reason": str(exit_reason),
                    "return_pct": float(trade_return * 100.0),
                    "buy_prob": float(position["buy_prob"]),
                    "position_fraction": float(stake_fraction),
                    "max_position_fraction": None if max_stake_fraction is None else float(max_stake_fraction),
                    "size_fraction": float(size_fraction),
                    "requested_size_fraction": float(requested_fraction),
                    "fee_bps": float(fee_rate * 10000.0),
                    "slippage_bps": float(slippage_rate * 10000.0),
                    "allow_partial_exits": bool(partial_exits_enabled),
                    "max_adverse_excursion_pct": float(((position["min_price"] / position["entry_price"]) - 1.0) * 100.0) if position["entry_price"] > 0 else 0.0,
                    "max_favorable_excursion_pct": float(((position["max_price"] / position["entry_price"]) - 1.0) * 100.0) if position["entry_price"] > 0 else 0.0,
                }
            )

    timeline = []
    for episode_index, episode in enumerate(episodes):
        episode_start_time = int(episode[0].get("meta", {}).get("sample_time", 0) or 0) if episode else 0
        if episode_index < len(buy_probabilities_by_episode):
            buy_prob_by_index = dict(buy_probabilities_by_episode[episode_index] or {})
        else:
            buy_prob_by_index = {}
        for idx, sample in enumerate(episode):
            sample_time = int(sample.get("meta", {}).get("sample_time", 0) or 0)
            timeline.append((sample_time, episode_index, idx, sample, episode_start_time, buy_prob_by_index, idx >= len(episode) - 1))

    timeline.sort(key=lambda item: (item[0], item[1], item[2]))

    for sample_time, _episode_index, idx, sample, episode_start_time, buy_prob_by_index, is_last_sample in timeline:
        event = _sample_to_event(sample)
        price = float(event.get("mid_price", 0.0))
        token = _sample_token(sample)
        if price <= 0.0:
            _append_equity_point()
            continue

        latest_prices[token] = price
        latest_sample_times[token] = sample_time
        position = positions.get(token)

        if position is None:
            buy_prob = buy_prob_by_index.get(idx)
            if (
                buy_prob is not None
                and buy_prob >= threshold
                and cash > 0.0
                and stake_fraction > 0.0
                and _entry_allowed(token)
            ):
                stake = _stake_amount()
                position_size, effective_entry_price = _entry_fill(stake, price)
                if position_size > 0.0:
                    cash -= stake
                    positions[token] = {
                        "token": token,
                        "size": position_size,
                        "entry_size": position_size,
                        "cost_basis": stake,
                        "entry_price": effective_entry_price,
                        "entry_time": sample_time,
                        "entry_index": idx,
                        "buy_prob": float(buy_prob),
                        "min_price": effective_entry_price,
                        "max_price": effective_entry_price,
                        "episode_start_time": episode_start_time,
                    }
                    _mark_entry(token)
            _append_equity_point()
            continue

        position["min_price"] = min(position["min_price"], price)
        position["max_price"] = max(position["max_price"], price)
        basis_entry_price = position["cost_basis"] / max(position["size"], 1e-9)
        pnl_pct = (price - basis_entry_price) / basis_entry_price if basis_entry_price > 0.0 else 0.0
        peak_pnl_pct = (position["max_price"] / position["entry_price"]) - 1.0 if position["entry_price"] > 0.0 else 0.0
        drawdown_from_peak_pct = (price / position["max_price"]) - 1.0 if position["max_price"] > 0.0 else 0.0
        risk_exit_reason = None
        if stop_loss is not None and pnl_pct <= float(stop_loss):
            risk_exit_reason = "STOP_LOSS"
        elif hold_time_limit is not None and sample_time - position["entry_time"] >= hold_time_limit:
            risk_exit_reason = "TIME_EXIT"
        elif rug_sell_pressure is not None and float(event.get("sell_pressure", 0.0)) >= float(rug_sell_pressure):
            risk_exit_reason = "RUG_EXIT"
        elif (
            trailing_start_pct is not None
            and trailing_stop_pct is not None
            and peak_pnl_pct >= float(trailing_start_pct)
            and drawdown_from_peak_pct <= -float(trailing_stop_pct)
        ):
            risk_exit_reason = "TRAILING_STOP"

        if risk_exit_reason is not None:
            fraction = 1.0
            requested_fraction = 1.0
            exit_reason = risk_exit_reason
        else:
            if sample_time - position["entry_time"] < policy_hold_floor:
                action = 0
            else:
                action = _choose_exit_action(
                    event,
                    sell_policy,
                    entry_price=position["entry_price"],
                    peak_price=position["max_price"],
                    position_remaining=position["size"] / max(position["entry_size"], 1e-9),
                    entry_ts=position["entry_time"],
                    episode_start_ts=position["episode_start_time"],
                )
            action = canonical_sell_action(action, allow_partial_exits=partial_exits_enabled)
            requested_fraction = sell_fraction_for_action(action, allow_partial_exits=True)
            fraction = sell_fraction_for_action(action, allow_partial_exits=partial_exits_enabled)
            exit_reason = _sell_exit_reason(action, allow_partial_exits=partial_exits_enabled)
            if fraction <= 0.0 and is_last_sample:
                fraction = 1.0
                requested_fraction = 1.0
                exit_reason = "EPISODE_END"

        if fraction > 0.0:
            sell_size = position["size"] * fraction
            proceeds, exit_execution_price = _exit_proceeds(sell_size, price)
            basis_fraction = sell_size / max(position["size"], 1e-9)
            realized_cost_basis = position["cost_basis"] * basis_fraction
            _record_exit(
                position=position,
                exit_time=sample_time,
                exit_index=idx,
                exit_price=exit_execution_price,
                exit_reason=exit_reason,
                proceeds=proceeds,
                realized_cost_basis=realized_cost_basis,
                size_fraction=fraction,
                requested_size_fraction=requested_fraction,
            )
            cash += proceeds
            position["size"] -= sell_size
            position["cost_basis"] -= realized_cost_basis
            if position["size"] <= 1e-12:
                positions.pop(token, None)

        _append_equity_point()

    for token, position in sorted(positions.items(), key=lambda item: item[1]["entry_time"]):
        final_price = latest_prices.get(token, position["entry_price"])
        final_time = latest_sample_times.get(token, position["entry_time"])
        proceeds, final_execution_price = _exit_proceeds(position["size"], final_price)
        realized_cost_basis = position["cost_basis"]
        _record_exit(
            position=position,
            exit_time=final_time,
            exit_index=position["entry_index"],
            exit_price=final_execution_price,
            exit_reason="REPLAY_END",
            proceeds=proceeds,
            realized_cost_basis=realized_cost_basis,
            size_fraction=1.0,
        )
        cash += proceeds
        _append_equity_point()

    final_equity = equity_curve[-1] if equity_curve else initial_equity
    total_trades = len(trade_returns)
    base_result = {
        "total_trades": int(total_trades),
        "entry_count": int(entry_count),
        "episode_count": episode_count,
        "entry_rate": float(entry_count / episode_count) if episode_count > 0 else 0.0,
        "position_fraction": float(stake_fraction),
        "max_position_fraction": None if max_stake_fraction is None else float(max_stake_fraction),
        "fee_bps": float(fee_rate * 10000.0),
        "slippage_bps": float(slippage_rate * 10000.0),
        "one_entry_per_token": bool(one_entry_per_token),
        "max_trades_per_token": max_entries_per_token,
        "max_entry_age_seconds": entry_age_limit,
        "max_hold_seconds": hold_time_limit,
        "min_policy_hold_seconds": policy_hold_floor,
        "allow_partial_exits": bool(partial_exits_enabled),
    }
    if total_trades == 0:
        result = dict(
            base_result,
            win_rate=0.0,
            net_return_pct=0.0,
            max_drawdown_pct=0.0,
            sortino_ratio=0.0,
        )
        if include_trade_log:
            result["trade_log"] = trade_log
        return result

    wins = sum(1 for value in trade_returns if value > 0.0)
    result = dict(
        base_result,
        win_rate=float(wins / total_trades),
        net_return_pct=float((final_equity / initial_equity - 1.0) * 100.0),
        max_drawdown_pct=float(_max_drawdown_pct(equity_curve)),
        sortino_ratio=float(_sortino_ratio_from_returns(step_returns)),
    )
    if include_trade_log:
        result["trade_log"] = trade_log
    return result


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


def _load_feature_contract_from_artifact(buy_artifact):
    feature_names = normalize_feature_names(buy_artifact.get("feature_names"))
    ignored_feature_names = buy_artifact.get("dropped_features")
    if feature_names is not None:
        return feature_names, ignored_feature_names

    feature_schema_path = buy_artifact.get("feature_schema_path")
    if not feature_schema_path:
        return None, ignored_feature_names

    schema = load_feature_schema_from_file(feature_schema_path)
    feature_names = schema["feature_names"]
    if ignored_feature_names is None:
        ignored_feature_names = schema["ignored_feature_names"]

    return feature_names, ignored_feature_names


def _episode_buy_probability_maxima(
    episodes,
    buy_model,
    *,
    feature_names=None,
    ignored_feature_names=None,
    max_entry_age_seconds=None,
):
    probabilities_by_episode = _episode_buy_probabilities(
        episodes,
        buy_model,
        feature_names=feature_names,
        ignored_feature_names=ignored_feature_names,
        max_entry_age_seconds=max_entry_age_seconds,
    )
    return [
        float(max(probabilities.values()))
        for probabilities in probabilities_by_episode
        if probabilities
    ]


def _risk_tune_threshold_candidates(config, current_threshold, probability_values=None):
    configured = config.get("risk_tune_thresholds")
    if configured:
        values = [float(value) for value in configured]
    else:
        values = list(np.linspace(0.5, 0.99, 11)) + [0.995, 0.999]
    values.append(float(current_threshold))

    probability_values = [
        max(0.0, min(1.0, float(value)))
        for value in (probability_values or [])
        if math.isfinite(float(value))
    ]
    if probability_values:
        raw_threshold_count = int(config.get("risk_tune_probability_threshold_count", 0) or 0)
        if bool(config.get("risk_tune_include_probability_values", False)) and raw_threshold_count <= 0:
            raw_threshold_count = int(config.get("risk_tune_max_probability_thresholds", 50) or 50)
        if raw_threshold_count > 0:
            unique_probabilities = sorted(set(probability_values))
            if len(unique_probabilities) <= raw_threshold_count:
                values.extend(unique_probabilities)
            else:
                positions = sorted(
                    {int(round(pos)) for pos in np.linspace(0, len(unique_probabilities) - 1, raw_threshold_count)}
                )
                values.extend(unique_probabilities[position] for position in positions)

        entry_rates = _coerce_float_list(
            config.get("risk_tune_candidate_entry_rates"),
            default=[0.05, 0.10, 0.15, 0.25, 0.40],
        )
        target_entry_rate = config.get("risk_tune_target_entry_rate")
        if target_entry_rate is not None:
            entry_rates.append(float(target_entry_rate))

        prob_arr = np.asarray(probability_values, dtype=float)
        for entry_rate in entry_rates:
            rate = max(0.0, min(1.0, float(entry_rate)))
            if rate <= 0.0:
                continue
            threshold = float(np.quantile(prob_arr, max(0.0, 1.0 - rate)))
            values.append(threshold)

    min_threshold = float(config.get("risk_tune_min_threshold", config.get("buy_min_threshold", 0.5)))
    return sorted(
        {
            max(0.0, min(1.0, float(value)))
            for value in values
            if float(value) >= min_threshold
        }
    )


def _replay_entry_rate(replay):
    if "entry_rate" in replay:
        return float(replay.get("entry_rate", 0.0))
    episode_count = int(replay.get("episode_count", 0) or 0)
    entry_count = int(replay.get("entry_count", replay.get("total_trades", 0)) or 0)
    return (entry_count / episode_count) if episode_count > 0 else 0.0


def _risk_tune_replay_score(config, replay):
    final_equity = max(1e-12, 1.0 + (float(replay.get("net_return_pct", 0.0)) / 100.0))
    log_equity = math.log(final_equity)
    drawdown_penalty = (
        abs(min(0.0, float(replay.get("max_drawdown_pct", 0.0)))) / 100.0
    ) * float(config.get("risk_tune_drawdown_penalty", 1.0))
    entry_rate = _replay_entry_rate(replay)
    turnover_penalty = entry_rate * float(config.get("risk_tune_turnover_penalty", 0.0))
    entry_rate_penalty = 0.0
    target_entry_rate = config.get("risk_tune_target_entry_rate")
    if target_entry_rate is not None:
        entry_rate_penalty = (
            abs(entry_rate - float(target_entry_rate))
            * float(config.get("risk_tune_entry_rate_penalty", 0.0))
        )
    return float(log_equity - drawdown_penalty - turnover_penalty - entry_rate_penalty)


def _tune_buy_threshold_by_replay(config, buy_artifact, ppo_artifact):
    if not bool(config.get("risk_tune_buy_threshold", False)):
        return None

    calibration_samples = list(buy_artifact.get("calibration_samples") or [])
    episodes = _build_eval_episodes(calibration_samples)
    if not episodes:
        return {
            "status": "skipped",
            "reason": "no calibration episodes",
            "threshold": float(buy_artifact.get("threshold", 1.0)),
            "candidates": [],
        }

    buy_model = buy_artifact.get("model")
    if buy_model is None:
        raise ValueError("buy artifact missing trained model")

    sell_policy = ppo_artifact.get("model")
    if sell_policy is None:
        sell_policy = _load_ppo_policy(ppo_artifact.get("policy_path"))

    feature_names, ignored_feature_names = _load_feature_contract_from_artifact(buy_artifact)
    current_threshold = float(buy_artifact.get("threshold", 1.0))
    min_trades = int(config.get("risk_tune_min_trades", 10))
    max_trades = config.get("risk_tune_max_trades")
    max_trades = None if max_trades is None else int(max_trades)
    max_drawdown_pct = float(config.get("risk_tune_max_drawdown_pct", -40.0))
    min_win_rate = float(config.get("risk_tune_min_win_rate", 0.0))
    max_entry_rate = config.get("risk_tune_max_entry_rate")
    max_entry_rate = None if max_entry_rate is None else float(max_entry_rate)
    position_fraction = float(config.get("position_fraction", 1.0))
    fee_bps = float(config.get("fee_bps", 0.0))
    slippage_bps = float(config.get("slippage_bps", 0.0))
    one_entry_per_token = bool(config.get("one_entry_per_token", True))
    max_trades_per_token = config.get("max_trades_per_token")
    max_entry_age_seconds = _max_entry_age_seconds(config)
    max_hold_seconds = config.get("max_hold_seconds")
    min_policy_hold_seconds = int(config.get("min_policy_hold_seconds", 0) or 0)
    max_position_fraction = config.get("max_position_fraction", 0.1)
    allow_partial_exits = bool(config.get("allow_partial_exits", False))
    buy_probabilities_by_episode = _episode_buy_probabilities(
        episodes,
        buy_model,
        feature_names=feature_names,
        ignored_feature_names=ignored_feature_names,
        max_entry_age_seconds=max_entry_age_seconds,
    )
    probability_maxima = [
        float(max(probabilities.values()))
        for probabilities in buy_probabilities_by_episode
        if probabilities
    ]
    candidates = []

    best = None
    best_score = None
    for threshold in _risk_tune_threshold_candidates(config, current_threshold, probability_maxima):
        replay = _run_eval_replay(
            episodes,
            buy_model,
            threshold,
            sell_policy,
            feature_names=feature_names,
            ignored_feature_names=ignored_feature_names,
            stop_loss=float(config.get("stop_loss", -0.50)),
            position_fraction=position_fraction,
            include_trade_log=False,
            trailing_start_pct=config.get("trailing_start_pct"),
            trailing_stop_pct=config.get("trailing_stop_pct"),
            rug_sell_pressure=config.get("rug_sell_pressure"),
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            one_entry_per_token=one_entry_per_token,
            max_trades_per_token=max_trades_per_token,
            max_entry_age_seconds=max_entry_age_seconds,
            max_hold_seconds=max_hold_seconds,
            min_policy_hold_seconds=min_policy_hold_seconds,
            max_position_fraction=max_position_fraction,
            allow_partial_exits=allow_partial_exits,
            buy_probabilities_by_episode=buy_probabilities_by_episode,
        )
        feasible = (
            int(replay["total_trades"]) >= min_trades
            and (max_trades is None or int(replay["total_trades"]) <= max_trades)
            and (max_entry_rate is None or float(replay.get("entry_rate", 0.0)) <= max_entry_rate)
            and float(replay["max_drawdown_pct"]) >= max_drawdown_pct
            and float(replay["win_rate"]) >= min_win_rate
        )
        score_value = _risk_tune_replay_score(config, replay)
        candidate = {
            "threshold": float(threshold),
            "feasible": bool(feasible),
            "score": float(score_value),
            "replay": replay,
        }
        candidates.append(candidate)
        if feasible:
            score = (
                score_value,
                float(replay["max_drawdown_pct"]),
                float(replay["win_rate"]),
                -int(replay["total_trades"]),
                float(threshold),
            )
            if best_score is None or score > best_score:
                best_score = score
                best = candidate

    if best is None:
        blocked_threshold = 1.0 if bool(config.get("risk_tune_block_if_infeasible", True)) else current_threshold
        return {
            "status": "infeasible",
            "threshold": float(blocked_threshold),
            "previous_threshold": current_threshold,
            "constraints": {
                "min_trades": min_trades,
                "max_trades": max_trades,
                "max_drawdown_pct": max_drawdown_pct,
                "min_win_rate": min_win_rate,
                "max_entry_rate": max_entry_rate,
                "position_fraction": position_fraction,
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "one_entry_per_token": one_entry_per_token,
                "max_trades_per_token": max_trades_per_token,
                "max_entry_age_seconds": max_entry_age_seconds,
                "max_hold_seconds": max_hold_seconds,
                "min_policy_hold_seconds": min_policy_hold_seconds,
                "max_position_fraction": None if max_position_fraction is None else float(max_position_fraction),
                "allow_partial_exits": allow_partial_exits,
                "target_entry_rate": config.get("risk_tune_target_entry_rate"),
                "entry_rate_penalty": config.get("risk_tune_entry_rate_penalty"),
                "candidate_entry_rates": _coerce_float_list(config.get("risk_tune_candidate_entry_rates")),
            },
            "candidates": candidates,
            "replay": {
                "total_trades": 0,
                "entry_count": 0,
                "win_rate": 0.0,
                "net_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sortino_ratio": 0.0,
                "position_fraction": position_fraction,
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "one_entry_per_token": one_entry_per_token,
                "max_trades_per_token": max_trades_per_token,
                "max_entry_age_seconds": max_entry_age_seconds,
                "max_hold_seconds": max_hold_seconds,
                "min_policy_hold_seconds": min_policy_hold_seconds,
                "max_position_fraction": None if max_position_fraction is None else float(max_position_fraction),
                "allow_partial_exits": allow_partial_exits,
                "episode_count": int(len(episodes)),
                "entry_rate": 0.0,
            },
        }

    return {
        "status": "selected",
        "threshold": float(best["threshold"]),
        "previous_threshold": current_threshold,
        "constraints": {
            "min_trades": min_trades,
            "max_trades": max_trades,
            "max_drawdown_pct": max_drawdown_pct,
            "min_win_rate": min_win_rate,
            "max_entry_rate": max_entry_rate,
            "position_fraction": position_fraction,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
            "one_entry_per_token": one_entry_per_token,
            "max_trades_per_token": max_trades_per_token,
            "max_entry_age_seconds": max_entry_age_seconds,
            "max_hold_seconds": max_hold_seconds,
            "min_policy_hold_seconds": min_policy_hold_seconds,
            "max_position_fraction": None if max_position_fraction is None else float(max_position_fraction),
            "allow_partial_exits": allow_partial_exits,
            "target_entry_rate": config.get("risk_tune_target_entry_rate"),
            "entry_rate_penalty": config.get("risk_tune_entry_rate_penalty"),
            "candidate_entry_rates": _coerce_float_list(config.get("risk_tune_candidate_entry_rates")),
        },
        "candidates": candidates,
        "replay": best["replay"],
    }


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

    feature_names, ignored_feature_names = _load_feature_contract_from_artifact(buy_artifact)

    position_fraction = float(config.get("position_fraction", 1.0))
    include_trade_log = bool(config.get("include_trade_log", False))
    fee_bps = float(config.get("fee_bps", 0.0))
    slippage_bps = float(config.get("slippage_bps", 0.0))
    one_entry_per_token = bool(config.get("one_entry_per_token", True))
    max_trades_per_token = config.get("max_trades_per_token")
    max_entry_age_seconds = _max_entry_age_seconds(config)
    max_hold_seconds = config.get("max_hold_seconds")
    min_policy_hold_seconds = int(config.get("min_policy_hold_seconds", 0) or 0)
    max_position_fraction = config.get("max_position_fraction", 0.1)
    allow_partial_exits = bool(config.get("allow_partial_exits", False))
    buy_probabilities_by_episode = _episode_buy_probabilities(
        episodes,
        buy_model,
        feature_names=feature_names,
        ignored_feature_names=ignored_feature_names,
        max_entry_age_seconds=max_entry_age_seconds,
    )
    buy_probabilities_by_episode_id = {
        id(episode): probabilities
        for episode, probabilities in zip(episodes, buy_probabilities_by_episode)
    }

    runtime_replay = _run_eval_replay(
        episodes,
        buy_model,
        threshold,
        sell_policy,
        feature_names=feature_names,
        ignored_feature_names=ignored_feature_names,
        stop_loss=float(config.get("stop_loss", -0.50)),
        position_fraction=position_fraction,
        include_trade_log=include_trade_log,
        trailing_start_pct=config.get("trailing_start_pct"),
        trailing_stop_pct=config.get("trailing_stop_pct"),
        rug_sell_pressure=config.get("rug_sell_pressure"),
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        one_entry_per_token=one_entry_per_token,
        max_trades_per_token=max_trades_per_token,
        max_entry_age_seconds=max_entry_age_seconds,
        max_hold_seconds=max_hold_seconds,
        min_policy_hold_seconds=min_policy_hold_seconds,
        max_position_fraction=max_position_fraction,
        allow_partial_exits=allow_partial_exits,
        buy_probabilities_by_episode=buy_probabilities_by_episode,
    )
    all_in_replay = _run_eval_replay(
        episodes,
        buy_model,
        threshold,
        sell_policy,
        feature_names=feature_names,
        ignored_feature_names=ignored_feature_names,
        stop_loss=float(config.get("stop_loss", -0.50)),
        position_fraction=1.0,
        include_trade_log=False,
        trailing_start_pct=config.get("trailing_start_pct"),
        trailing_stop_pct=config.get("trailing_stop_pct"),
        rug_sell_pressure=config.get("rug_sell_pressure"),
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
        one_entry_per_token=one_entry_per_token,
        max_trades_per_token=max_trades_per_token,
        max_entry_age_seconds=max_entry_age_seconds,
        max_hold_seconds=max_hold_seconds,
        min_policy_hold_seconds=min_policy_hold_seconds,
        max_position_fraction=None,
        allow_partial_exits=allow_partial_exits,
        buy_probabilities_by_episode=buy_probabilities_by_episode,
    )

    result = {
        "total_trades": int(runtime_replay["total_trades"]),
        "entry_count": int(runtime_replay.get("entry_count", runtime_replay["total_trades"])),
        "entry_rate": float(runtime_replay.get("entry_rate", 0.0)),
        "win_rate": float(runtime_replay["win_rate"]),
        "net_return_pct": float(runtime_replay["net_return_pct"]),
        "max_drawdown_pct": float(runtime_replay["max_drawdown_pct"]),
        "sortino_ratio": float(runtime_replay["sortino_ratio"]),
        "buy_threshold": threshold,
        "stop_loss": float(config.get("stop_loss", -0.50)),
        "position_fraction": position_fraction,
        "trailing_start_pct": config.get("trailing_start_pct"),
        "trailing_stop_pct": config.get("trailing_stop_pct"),
        "rug_sell_pressure": config.get("rug_sell_pressure"),
        "fee_bps": fee_bps,
        "slippage_bps": slippage_bps,
        "one_entry_per_token": one_entry_per_token,
        "max_trades_per_token": max_trades_per_token,
        "max_entry_age_seconds": max_entry_age_seconds,
        "max_hold_seconds": max_hold_seconds,
        "min_policy_hold_seconds": min_policy_hold_seconds,
        "max_position_fraction": None if max_position_fraction is None else float(max_position_fraction),
        "allow_partial_exits": allow_partial_exits,
        "runtime_replay": {key: value for key, value in runtime_replay.items() if key != "trade_log"},
        "all_in_replay": all_in_replay,
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
    if include_trade_log:
        result["trade_log"] = runtime_replay.get("trade_log", [])
    walk_forward_segments = []
    for segment_index, segment_episodes in _split_episodes_for_walk_forward(
        episodes,
        int(config.get("walk_forward_segments", 0)),
    ):
        segment_probabilities = [
            buy_probabilities_by_episode_id.get(id(episode), {})
            for episode in segment_episodes
        ]
        segment_replay = _run_eval_replay(
            segment_episodes,
            buy_model,
            threshold,
            sell_policy,
            feature_names=feature_names,
            ignored_feature_names=ignored_feature_names,
            stop_loss=float(config.get("stop_loss", -0.50)),
            position_fraction=position_fraction,
            include_trade_log=False,
            trailing_start_pct=config.get("trailing_start_pct"),
            trailing_stop_pct=config.get("trailing_stop_pct"),
            rug_sell_pressure=config.get("rug_sell_pressure"),
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            one_entry_per_token=one_entry_per_token,
            max_trades_per_token=max_trades_per_token,
            max_entry_age_seconds=max_entry_age_seconds,
            max_hold_seconds=max_hold_seconds,
            min_policy_hold_seconds=min_policy_hold_seconds,
            max_position_fraction=max_position_fraction,
            allow_partial_exits=allow_partial_exits,
            buy_probabilities_by_episode=segment_probabilities,
        )
        walk_forward_segments.append(
            {
                "segment_index": int(segment_index),
                "episode_count": int(len(segment_episodes)),
                **segment_replay,
            }
        )
    if walk_forward_segments:
        result["walk_forward"] = walk_forward_segments
        result["walk_forward_segment_count"] = int(len(walk_forward_segments))
        result["walk_forward_worst_net_return_pct"] = float(
            min(segment.get("net_return_pct", 0.0) for segment in walk_forward_segments)
        )
        result["walk_forward_worst_max_drawdown_pct"] = float(
            min(segment.get("max_drawdown_pct", 0.0) for segment in walk_forward_segments)
        )
        result["walk_forward_min_win_rate"] = float(
            min(segment.get("win_rate", 0.0) for segment in walk_forward_segments)
        )
    return result


def _summarize_trade_log_by_exit_reason(trade_log):
    buckets = {}
    for row in trade_log or []:
        reason = str(row.get("exit_reason", "UNKNOWN") or "UNKNOWN")
        buckets.setdefault(reason, []).append(row)

    summary = {}
    for reason, rows in sorted(buckets.items()):
        returns = np.asarray([float(row.get("return_pct", 0.0) or 0.0) for row in rows], dtype=float)
        holds = []
        for row in rows:
            if "entry_time" not in row or "exit_time" not in row:
                continue
            try:
                holds.append(float(row.get("exit_time", 0) or 0) - float(row.get("entry_time", 0) or 0))
            except Exception:
                continue
        hold_arr = np.asarray(holds, dtype=float)
        summary[reason] = {
            "count": int(len(rows)),
            "mean_return_pct": float(np.mean(returns)) if returns.size else 0.0,
            "median_return_pct": float(np.median(returns)) if returns.size else 0.0,
            "min_return_pct": float(np.min(returns)) if returns.size else 0.0,
            "max_return_pct": float(np.max(returns)) if returns.size else 0.0,
            "mean_hold_seconds": float(np.mean(hold_arr)) if hold_arr.size else 0.0,
            "median_hold_seconds": float(np.median(hold_arr)) if hold_arr.size else 0.0,
        }

    return summary


def _externalize_trade_log(evaluation, output_dir):
    trade_log = evaluation.pop("trade_log", None)
    if not trade_log:
        return evaluation

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    trade_log_path = output_dir / "trade_log.jsonl"
    with trade_log_path.open("w", encoding="utf-8") as handle:
        for row in trade_log:
            handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    worst_trades = sorted(
        trade_log,
        key=lambda row: float(row.get("return_pct", 0.0)),
    )[:20]
    evaluation["trade_log_path"] = str(trade_log_path)
    evaluation["trade_log_count"] = int(len(trade_log))
    evaluation["worst_trades"] = worst_trades
    evaluation["exit_reason_summary"] = _summarize_trade_log_by_exit_reason(trade_log)
    return evaluation


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
    risk_tuning = _tune_buy_threshold_by_replay(train_config, buy_artifact, ppo_artifact)
    if risk_tuning is not None:
        tuned_threshold = float(risk_tuning.get("threshold", buy_artifact.get("threshold", 1.0)))
        buy_artifact["threshold"] = tuned_threshold
        buy_artifact["risk_tuning"] = risk_tuning
        threshold_path = buy_artifact.get("threshold_path")
        if threshold_path:
            Path(threshold_path).write_text(
                json.dumps({"threshold": tuned_threshold}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
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
    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluation = run_ab_evaluation(eval_config, buy_artifact, ppo_artifact, bc_artifact)
    evaluation = _externalize_trade_log(evaluation, output_dir)

    result = {
        "artifacts": {
            "buy_model": {
                "model_path": buy_artifact.get("model_path"),
                "threshold": buy_artifact.get("threshold"),
                "threshold_path": buy_artifact.get("threshold_path"),
                "feature_schema_path": buy_artifact.get("feature_schema_path"),
                "feature_names": buy_artifact.get("feature_names"),
                "dropped_features": buy_artifact.get("dropped_features"),
                "target_label_column": buy_artifact.get("target_label_column"),
                "target_threshold_value": buy_artifact.get("target_threshold_value"),
                "threshold_source": buy_artifact.get("threshold_source"),
                "calibration": buy_artifact.get("calibration"),
                "risk_tuning": buy_artifact.get("risk_tuning"),
            },
            "sell_policy": {
                "policy_path": ppo_artifact.get("policy_path"),
                "total_timesteps": ppo_artifact.get("total_timesteps"),
            },
            "bc_warmstart": bc_artifact,
        },
        "evaluation": evaluation,
    }

    manifest_path = output_dir / "hybrid_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
