import json
from itertools import product
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def _select_best_candidate(
    candidates,
    max_drawdown_limit=35.0,
    min_trades=20,
    target_trade_rate=None,
    trade_rate_tolerance=0.005,
):
    filtered = []
    for c in candidates:
        if float(c.get("max_drawdown_pct", 999.0)) > max_drawdown_limit:
            continue
        if int(c.get("trades", 0)) < min_trades:
            continue

        if target_trade_rate is not None:
            trade_rate = c.get("trade_rate")
            if trade_rate is None:
                total_tokens = int(c.get("total_tokens", 0))
                trades = int(c.get("trades", 0))
                trade_rate = (trades / total_tokens) if total_tokens > 0 else 0.0
            if abs(float(trade_rate) - float(target_trade_rate)) > float(trade_rate_tolerance):
                continue

        filtered.append(c)

    if not filtered:
        return None

    if target_trade_rate is None:
        filtered.sort(
            key=lambda c: (
                float(c.get("return_pct", -1e9)),
                -float(c.get("max_drawdown_pct", 999.0)),
                int(c.get("trades", 0)),
            ),
            reverse=True,
        )
    else:
        filtered.sort(
            key=lambda c: (
                float(c.get("return_pct", -1e9)),
                -abs(float(c.get("trade_rate", 0.0)) - float(target_trade_rate)),
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
    first_take_profit=2.0,
    first_exit_ratio=0.6,
    drawdown_stop=0.25,
    stop_loss=-0.5,
):
    work_df = df.copy().reset_index(drop=True)

    probs = clf.predict_proba(work_df[feature_cols])[:, 1]
    pred_returns = reg.predict(work_df[feature_cols]) if reg is not None else np.zeros(len(work_df))
    work_df = work_df.assign(_prob=probs, _pred_return=pred_returns)

    returns = []

    first_take_profit = max(0.0, float(first_take_profit))
    first_exit_ratio = min(1.0, max(0.0, float(first_exit_ratio)))
    drawdown_stop = min(1.0, max(0.0, float(drawdown_stop)))
    stop_loss = max(-0.99, min(-0.01, float(stop_loss)))

    def _simulate_path_exit(token_df, entry_idx):
        entry_row = token_df.iloc[entry_idx]

        entry_price = float(entry_row.get("current_price", 0.0))
        if entry_price <= 0:
            entry_price = float(entry_row.get("first_price", 0.0))

        if entry_price <= 0:
            min_ret = float(entry_row.get("min_return_pct", 0.0))
            max_ret = float(entry_row.get("max_return_pct", 0.0)) / 100.0
            final_ret = float(entry_row.get("final_return_pct", entry_row.get("max_return_pct", 0.0))) / 100.0
            if max_ret >= first_take_profit:
                second_exit_ratio = 1.0 - first_exit_ratio
                first_exit_return = first_take_profit
                peak_from_entry = max(max_ret, first_take_profit)
                peak_multiple = 1.0 + peak_from_entry
                drawdown_exit_return = peak_multiple * (1.0 - drawdown_stop) - 1.0
                second_exit_return = final_ret if final_ret >= drawdown_exit_return else drawdown_exit_return
                return first_exit_ratio * first_exit_return + second_exit_ratio * second_exit_return
            if min_ret <= stop_loss * 100.0:
                return stop_loss
            return final_ret

        partial_sold = False
        remaining_ratio = 1.0
        realized_return = 0.0
        peak_price = 0.0
        last_valid_pnl = None

        for idx in range(entry_idx, len(token_df)):
            row = token_df.iloc[idx]
            current_price = float(row.get("current_price", 0.0))
            if current_price <= 0:
                continue

            pnl_pct = (current_price - entry_price) / entry_price
            last_valid_pnl = pnl_pct

            if pnl_pct <= stop_loss:
                realized_return += remaining_ratio * pnl_pct
                return realized_return

            if not partial_sold and pnl_pct >= first_take_profit:
                realized_return += first_exit_ratio * pnl_pct
                remaining_ratio = max(0.0, 1.0 - first_exit_ratio)
                partial_sold = True
                peak_price = current_price
                continue

            if partial_sold:
                peak_price = max(peak_price, current_price)
                if peak_price > 0:
                    drawdown_pct = (current_price - peak_price) / peak_price
                    if drawdown_pct <= -drawdown_stop:
                        realized_return += remaining_ratio * pnl_pct
                        return realized_return

        if last_valid_pnl is not None:
            realized_return += remaining_ratio * last_valid_pnl
            return realized_return

        final_ret = float(entry_row.get("final_return_pct", entry_row.get("max_return_pct", 0.0))) / 100.0
        realized_return += remaining_ratio * final_ret
        return realized_return

    if "token_address" not in work_df.columns:
        return {
            "prob_threshold": float(prob_threshold),
            "reg_min_return": float(reg_min_return),
            "max_age_seconds": int(max_age_seconds),
            "first_take_profit": float(first_take_profit),
            "first_exit_ratio": float(first_exit_ratio),
            "drawdown_stop": float(drawdown_stop),
            "stop_loss": float(stop_loss),
            "return_pct": -100.0,
            "max_drawdown_pct": 100.0,
            "trades": 0,
        }

    for _, token_df in work_df.groupby("token_address", sort=False):
        if "sample_interval" in token_df.columns:
            token_df = token_df.sort_values("sample_interval")
        elif "sample_time" in token_df.columns:
            token_df = token_df.sort_values("sample_time")

        token_df = token_df.reset_index(drop=True)

        for entry_idx, row in token_df.iterrows():
            age = float(row.get("time_since_launch", row.get("sample_interval", 0.0)))
            if age > max_age_seconds:
                break

            # 活跃度过滤: 与训练数据保持一致
            if int(row.get("unique_buyers", 0)) < 3:
                continue
            if int(row.get("total_buys", 0)) < 5:
                continue

            prob = float(row["_prob"])
            if prob < prob_threshold:
                continue

            if reg is not None and float(row["_pred_return"]) < reg_min_return:
                continue

            actual_return = _simulate_path_exit(token_df, entry_idx)

            size = 0.1
            fee_rate = 0.02
            buy_slippage = 0.20
            sell_slippage = 0.05
            effective_entry = size / (1 + buy_slippage)
            gross_value = effective_entry * (1 + actual_return)
            net_value = gross_value * (1 - sell_slippage) * (1 - fee_rate)
            profit = net_value - size
            returns.append(profit)

            # 每个 token 只在首次满足条件时买入一次
            break

    total_tokens = int(work_df["token_address"].nunique()) if "token_address" in work_df.columns else 0

    trades = int(len(returns))
    if trades == 0:
        return {
            "prob_threshold": float(prob_threshold),
            "reg_min_return": float(reg_min_return),
            "max_age_seconds": int(max_age_seconds),
            "first_take_profit": float(first_take_profit),
            "first_exit_ratio": float(first_exit_ratio),
            "drawdown_stop": float(drawdown_stop),
            "stop_loss": float(stop_loss),
            "return_pct": -100.0,
            "max_drawdown_pct": 100.0,
            "trades": 0,
            "total_tokens": total_tokens,
            "trade_rate": 0.0,
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

    trade_rate = (trades / total_tokens) if total_tokens > 0 else 0.0

    return {
        "prob_threshold": float(prob_threshold),
        "reg_min_return": float(reg_min_return),
        "max_age_seconds": int(max_age_seconds),
        "first_take_profit": float(first_take_profit),
        "first_exit_ratio": float(first_exit_ratio),
        "drawdown_stop": float(drawdown_stop),
        "stop_loss": float(stop_loss),
        "return_pct": return_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "trades": trades,
        "total_tokens": total_tokens,
        "trade_rate": float(trade_rate),
    }


def _evaluate_grid(
    prob_thresholds,
    reg_min_returns,
    max_age_seconds,
    first_take_profit_candidates,
    first_exit_ratio_candidates,
    drawdown_stop_candidates,
    stop_loss_candidates,
    df,
    feature_cols,
    clf,
    reg,
):
    rows = []
    combos = list(
        product(
            prob_thresholds,
            reg_min_returns,
            max_age_seconds,
            first_take_profit_candidates,
            first_exit_ratio_candidates,
            drawdown_stop_candidates,
            stop_loss_candidates,
        )
    )
    total = len(combos)
    for i, (prob_threshold, reg_min_return, age_limit, first_take_profit, first_exit_ratio, drawdown_stop, stop_loss) in enumerate(combos, 1):
        if i % 10 == 0 or i == total:
            print(f"\r  进度: {i}/{total} ({i*100//total}%)", end="", flush=True)
        rows.append(
            _evaluate_single_config(
                df=df,
                feature_cols=feature_cols,
                clf=clf,
                reg=reg,
                prob_threshold=prob_threshold,
                reg_min_return=reg_min_return,
                max_age_seconds=age_limit,
                first_take_profit=first_take_profit,
                first_exit_ratio=first_exit_ratio,
                drawdown_stop=drawdown_stop,
                stop_loss=stop_loss,
            )
        )
    print()  # 换行
    return rows


def run_profit_first_calibration(
    prob_thresholds,
    reg_min_returns,
    max_age_seconds,
    first_take_profit_candidates=None,
    first_exit_ratio_candidates=None,
    drawdown_stop_candidates=None,
    stop_loss_candidates=None,
    max_drawdown_limit=35.0,
    min_trades=20,
    top_k=10,
    target_trade_rate=None,
    trade_rate_tolerance=0.005,
    dataset_timestamp=None,
    model_timestamp=None,
    dataset_path=None,
    model_dir=None,
):
    loaded = _load_latest_dataset_and_model(dataset_path=dataset_path, model_dir=model_dir)

    first_take_profit_candidates = first_take_profit_candidates or [2.0]
    first_exit_ratio_candidates = first_exit_ratio_candidates or [0.6]
    drawdown_stop_candidates = drawdown_stop_candidates or [0.25]
    stop_loss_candidates = stop_loss_candidates or [-0.5]

    candidates = _evaluate_grid(
        prob_thresholds=prob_thresholds,
        reg_min_returns=reg_min_returns,
        max_age_seconds=max_age_seconds,
        first_take_profit_candidates=first_take_profit_candidates,
        first_exit_ratio_candidates=first_exit_ratio_candidates,
        drawdown_stop_candidates=drawdown_stop_candidates,
        stop_loss_candidates=stop_loss_candidates,
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
            "first_take_profit_candidates": list(first_take_profit_candidates),
            "first_exit_ratio_candidates": list(first_exit_ratio_candidates),
            "drawdown_stop_candidates": list(drawdown_stop_candidates),
            "stop_loss_candidates": list(stop_loss_candidates),
        },
        "constraints": {
            "max_drawdown_limit": float(max_drawdown_limit),
            "min_trades": int(min_trades),
            "target_trade_rate": float(target_trade_rate) if target_trade_rate is not None else None,
            "trade_rate_tolerance": float(trade_rate_tolerance),
        },
        "top_candidates": ranked[:top_k],
        "recommended": _select_best_candidate(
            ranked,
            max_drawdown_limit=max_drawdown_limit,
            min_trades=min_trades,
            target_trade_rate=target_trade_rate,
            trade_rate_tolerance=trade_rate_tolerance,
        ),
    }
