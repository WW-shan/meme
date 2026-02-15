import json
from itertools import product
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def _select_best_candidate(candidates, max_drawdown_limit=35.0, min_trades=20):
    filtered = [
        c
        for c in candidates
        if float(c.get("max_drawdown_pct", 999.0)) <= max_drawdown_limit
        and int(c.get("trades", 0)) >= min_trades
    ]
    if not filtered:
        return None

    filtered.sort(
        key=lambda c: (
            float(c.get("return_pct", -1e9)),
            -float(c.get("max_drawdown_pct", 999.0)),
            int(c.get("trades", 0)),
        ),
        reverse=True,
    )
    return filtered[0]


def _load_latest_dataset_and_model(dataset_path=None, model_dir=None):
    dataset_dir = Path(dataset_path) if dataset_path else Path("data/datasets")
    model_root = Path(model_dir) if model_dir else Path("data/models")

    test_files = sorted(dataset_dir.glob("test_*.jsonl"))
    if not test_files:
        raise FileNotFoundError("No test dataset found under data/datasets")
    latest_test = test_files[-1]

    model_dirs = sorted(d for d in model_root.glob("models_*") if d.is_dir())
    if not model_dirs:
        raise FileNotFoundError("No model directories found under data/models")

    latest_model = None
    for d in reversed(model_dirs):
        has_clf = (d / "classifier_xgb.pkl").exists()
        has_meta = (d / "model_metadata.json").exists()
        has_reg = (d / "regressor_lgb.pkl").exists()
        if has_clf and has_meta and has_reg:
            latest_model = d
            break
    if latest_model is None:
        raise FileNotFoundError(
            "No complete model bundle found (requires classifier_xgb.pkl + regressor_lgb.pkl + model_metadata.json)"
        )

    with latest_test.open("r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    df = pd.DataFrame([{**r["features"], **r["label"], **r["meta"]} for r in rows])
    clf = joblib.load(latest_model / "classifier_xgb.pkl")

    reg_path = latest_model / "regressor_lgb.pkl"
    reg = joblib.load(reg_path) if reg_path.exists() else None

    meta = {}
    meta_path = latest_model / "model_metadata.json"
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as f:
            meta = json.load(f)

    feature_cols = meta.get("features") or [
        k
        for k in df.columns
        if k
        not in {
            "is_moon",
            "max_return_pct",
            "min_return_pct",
            "token_address",
            "symbol",
            "sample_time",
            "sample_interval",
            "future_window",
        }
    ]

    return {
        "df": df,
        "clf": clf,
        "reg": reg,
        "feature_cols": feature_cols,
        "dataset_timestamp": latest_test.stem.replace("test_", ""),
        "model_timestamp": latest_model.name.replace("models_", ""),
    }


def _evaluate_single_config(
    df,
    feature_cols,
    clf,
    reg,
    prob_threshold,
    reg_min_return,
    max_age_seconds,
):
    work_df = df.sort_values("sample_time").reset_index(drop=True)

    probs = clf.predict_proba(work_df[feature_cols])[:, 1]
    pred_returns = reg.predict(work_df[feature_cols]) if reg is not None else np.zeros(len(work_df))

    traded_tokens = set()
    returns = []

    for i, row in work_df.iterrows():
        token_address = row.get("token_address")
        if token_address in traded_tokens:
            continue

        age = float(row.get("time_since_launch", 0.0))
        if age > max_age_seconds:
            continue

        prob = float(probs[i])
        if prob < prob_threshold:
            continue

        if reg is not None and float(pred_returns[i]) < reg_min_return:
            continue

        traded_tokens.add(token_address)

        label_moon = int(row.get("is_moon_200", row.get("is_moon", 0)))
        min_ret = float(row.get("min_return_pct", 0.0))
        max_ret = float(row.get("max_return_pct", 0.0)) / 100.0
        final_ret = float(row.get("final_return_pct", row.get("max_return_pct", 0.0))) / 100.0

        if label_moon == 1:
            first_exit_ratio = 0.6
            second_exit_ratio = 0.4
            drawdown_stop = 0.25
            first_exit_return = 2.0
            peak_from_entry = max(max_ret, 2.0)
            drawdown_exit_return = peak_from_entry * (1 - drawdown_stop)
            second_exit_return = final_ret if final_ret >= drawdown_exit_return else drawdown_exit_return
            actual_return = first_exit_ratio * first_exit_return + second_exit_ratio * second_exit_return
        elif min_ret <= -50.0:
            actual_return = -0.5
        else:
            actual_return = final_ret

        size = 0.1
        fee_rate = 0.02
        buy_slippage = 0.20
        sell_slippage = 0.05
        effective_entry = size / (1 + buy_slippage)
        gross_value = effective_entry * (1 + actual_return)
        net_value = gross_value * (1 - sell_slippage) * (1 - fee_rate)
        profit = net_value - size
        returns.append(profit)

    trades = int(len(returns))
    if trades == 0:
        return {
            "prob_threshold": float(prob_threshold),
            "reg_min_return": float(reg_min_return),
            "max_age_seconds": int(max_age_seconds),
            "return_pct": -100.0,
            "max_drawdown_pct": 100.0,
            "trades": 0,
        }

    balance = 1.0
    equity = [balance]
    for pnl in returns:
        balance += pnl
        equity.append(balance)

    equity_arr = np.array(equity, dtype=float)
    peaks = np.maximum.accumulate(equity_arr)
    drawdowns = (peaks - equity_arr) / peaks * 100
    max_drawdown_pct = float(np.max(drawdowns)) if len(drawdowns) else 0.0
    return_pct = float((balance - 1.0) * 100)

    return {
        "prob_threshold": float(prob_threshold),
        "reg_min_return": float(reg_min_return),
        "max_age_seconds": int(max_age_seconds),
        "return_pct": return_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "trades": trades,
    }


def _evaluate_grid(
    prob_thresholds,
    reg_min_returns,
    max_age_seconds,
    df,
    feature_cols,
    clf,
    reg,
):
    rows = []
    for prob_threshold, reg_min_return, age_limit in product(
        prob_thresholds,
        reg_min_returns,
        max_age_seconds,
    ):
        rows.append(
            _evaluate_single_config(
                df=df,
                feature_cols=feature_cols,
                clf=clf,
                reg=reg,
                prob_threshold=prob_threshold,
                reg_min_return=reg_min_return,
                max_age_seconds=age_limit,
            )
        )
    return rows


def run_profit_first_calibration(
    prob_thresholds,
    reg_min_returns,
    max_age_seconds,
    max_drawdown_limit=35.0,
    min_trades=20,
    top_k=10,
    dataset_timestamp=None,
    model_timestamp=None,
    dataset_path=None,
    model_dir=None,
):
    loaded = _load_latest_dataset_and_model(dataset_path=dataset_path, model_dir=model_dir)

    candidates = _evaluate_grid(
        prob_thresholds=prob_thresholds,
        reg_min_returns=reg_min_returns,
        max_age_seconds=max_age_seconds,
        df=loaded["df"],
        feature_cols=loaded["feature_cols"],
        clf=loaded["clf"],
        reg=loaded["reg"],
    )

    ranked = sorted(
        candidates,
        key=lambda c: (
            float(c.get("return_pct", -1e9)),
            -float(c.get("max_drawdown_pct", 999.0)),
            int(c.get("trades", 0)),
        ),
        reverse=True,
    )

    return {
        "dataset_timestamp": dataset_timestamp or loaded["dataset_timestamp"],
        "model_timestamp": model_timestamp or loaded["model_timestamp"],
        "search_space": {
            "prob_thresholds": list(prob_thresholds),
            "reg_min_returns": list(reg_min_returns),
            "max_age_seconds": list(max_age_seconds),
        },
        "constraints": {
            "max_drawdown_limit": float(max_drawdown_limit),
            "min_trades": int(min_trades),
        },
        "top_candidates": ranked[:top_k],
        "recommended": _select_best_candidate(
            ranked,
            max_drawdown_limit=max_drawdown_limit,
            min_trades=min_trades,
        ),
    }
