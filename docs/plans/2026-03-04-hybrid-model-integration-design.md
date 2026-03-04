# Hybrid Model Integration Design

## Goal

Replace old XGBoost+LightGBM inference in bot and backtest with the new CatBoost (buy) + PPO (sell) hybrid model. Add post-training backtest with real metrics.

## Architecture

### HybridModel Adapter (`src/model/hybrid_inference.py`)

Single entry point for loading and running inference on the trained hybrid artifacts.

```
HybridModel
├── load(model_dir)        → loads buy_model.cbm + buy_threshold.json + sell_policy.zip
├── predict_buy(features)  → (prob: float, should_buy: bool)
└── predict_sell(obs)      → action: int (0=hold, 1=sell25, 2=sell50, 3=sell100, -1=unavailable)
```

- `predict_buy` accepts a features dict (from `extract_features`), converts to DataFrame internally, calls CatBoost `predict_proba`, compares against threshold.
- `predict_sell` accepts a 5-dim observation array `[mid_price, lp_depth, sell_pressure, buy_sell_ratio, holders]` matching `TradingEnv.observation_space`. Returns -1 if sell_policy is None (caller falls back to rules).
- CatBoost and SB3 imports are lazy (inside methods) to avoid hard crashes when deps missing.

### Bot Changes (`src/trader/bot.py`)

Three modification points:

1. **`_load_models`**: Replace XGBoost/LightGBM loading with `HybridModel.load(model_dir)`. Sentinel file changes from `classifier_xgb.pkl` to `buy_model.cbm`. Remove `self.clf`, `self.reg`, `self.prob_calibrator`, `self.meta`; replace with `self.hybrid`.

2. **`_run_model_inference`**: Call `self.hybrid.predict_buy(features_dict)`. Returns `(prob, should_buy)` instead of `(prob, pred_return)`.

3. **Sell logic**: At each price update, construct obs from current features and call `self.hybrid.predict_sell(obs)`. If returns -1 (no PPO model), fall back to existing rule-based sell. Hard stop-loss at -50% always applies as risk floor regardless of PPO action.

### Backtest Changes (`src/backtest/engine.py`)

1. **Constructor**: Add optional `hybrid_model` parameter. When None, existing TradeFilter + rule-based behavior preserved.

2. **Buy signal**: When `hybrid_model` is set, extract features from lifecycle and call `predict_buy` instead of `TradeFilter.should_buy`.

3. **Sell signal**: When `hybrid_model` is set, call `predict_sell` at each price tick instead of hardcoded take-profit/stop-loss rules. -50% hard stop-loss retained.

4. **Metrics**: Add `sortino_ratio`, `max_drawdown`, `net_return_pct` to `_generate_stats`.

### Post-Training Backtest (`src/pipeline/train_hybrid.py`)

Replace placeholder `run_ab_evaluation` with real backtest:
- Load the just-trained model via `HybridModel.load(output_dir)`
- Instantiate `BacktestEngine` with hybrid model
- Run on training lifecycle data
- Write results (sortino, maxdd, net_return, win_rate) into `hybrid_manifest.json` evaluation field

### Cleanup

- Old files (`trainer.py`, `run_full_training.py`) preserved but bot no longer references them.
- `self.clf`/`self.reg`/`self.prob_calibrator`/`self.meta` removed from bot.
- `calibration_latest.json` no longer read; threshold comes from `buy_threshold.json`.

## Files Changed

| File | Action |
|------|--------|
| `src/model/hybrid_inference.py` | New — adapter |
| `src/trader/bot.py` | Modify — model loading + inference + sell logic |
| `src/backtest/engine.py` | Modify — inject hybrid model, buy/sell signals, metrics |
| `src/pipeline/train_hybrid.py` | Modify — real post-training backtest |
| `tests/model/test_hybrid_inference.py` | New — adapter tests |
| `tests/model/test_backtest_hybrid.py` | New — backtest integration tests |

## Risk Mitigations

- PPO unavailable → `predict_sell` returns -1 → bot falls back to rule-based sell
- CatBoost unavailable → `HybridModel.load` raises clear error at startup
- -50% hard stop-loss always enforced regardless of PPO decision
- Old training code preserved for reference, not deleted
