# 2026-05-30 Execution Freshness / Near-Threshold Low-Edge Check

## Trigger

Fresh live attribution after the `币安盲盒` loss found one closed trade since `2026-05-29 21:19:42`:

- Open: `2026-05-30 14:02:42.657690`
- Close: `2026-05-30 14:12:23.907557`
- Exit reason: `TIME_EXIT`
- Net PnL: `-0.000024987972169378226` BNB
- Failure label: `dead_flow_timeout`
- `prob=0.9780012658730048`
- `PredReturn=32.83665120883128`
- `token_status_source=helper`
- `buy_fast_status_used=false`
- `signal_to_open_seconds=8.723606`
- `entry_fill_lag_seconds=5.092701`
- `lifecycle_status_chain_lag_seconds=24.65839910507202`

Artifacts:

- `data/replay_reports/live_trade_attribution_20260530_after_binance_mystery_box_loss.json`
- `data/replay_reports/live_trade_attribution_20260530_after_binance_mystery_box_loss.md`
- `data/replay_reports/execution_costs_20260530_after_binance_mystery_box_loss.json`
- `data/replay_reports/execution_costs_20260530_recent_live_window.json`
- `data/replay_reports/execution_costs_20260530_all_live_history.json`

The loss was not enough evidence for a helper-source blacklist. Historical helper opens remained mixed rather than uniformly toxic. The live-derived issue was narrower: a lower-edge near-threshold rescue with extreme lifecycle chain lag and slow fill.

## Research

SmartSearch Deep Research artifacts:

- `00-deep-plan.json`
- `evidence/01-search.json`
- `evidence/02-search-event-driven.json`
- `evidence/02-exa.json`
- `evidence/03-fetch-quantstart-event-driven.md`
- `evidence/04-fetch-paybis-backtest-latency.md`
- `evidence/05-fetch-luxalgo-slippage-liquidity.md`
- `evidence/06-fetch-ml4trading-point-in-time.md`

Useful constraints applied here:

- Use event-driven, point-in-time replay assumptions for latency and stale data checks.
- Model realistic slippage, fill latency, and execution failure instead of assuming immediate fills.
- Keep walk-forward and stress checks separate from a single split headline metric.
- Avoid hard-coding a live-only blacklist from one trade when historical evidence is mixed.

`exa-search` was unavailable because `EXA_API_KEY` is not configured; the provider gap is recorded in `evidence/02-exa.json`.

## Direction Portfolio

Ranked directions after attribution and prior review:

1. Near-threshold lower-edge hardening.
   - Evidence: the new loss sat at `PredReturn=32.8366`, just above the current rescue floor, with dead-flow timeout and slow execution.
   - Expected impact: small but directly falsifiable by replay.
   - Cost: low, because the existing near-threshold replay grid already covers the behavior.
2. Execution freshness / latency-aware abstention.
   - Evidence: recent execution calibration showed the new loss was a chain-lag tail event.
   - Expected impact: potentially higher, but it needs a replay-integrated feature or friction model rather than a one-off helper rule.
3. Live shadow evaluator for freshness and would-buy decisions.
   - Evidence: would collect decision-time stale/fresh labels on the actual live stream.
   - Expected impact: useful for future gating, but it is slower to falsify than the current replay grid.

Selected minimal experiment: test whether raising the lower near-threshold `PredReturn` rescue floor around `33-35` improves strict replay metrics.

## Experiment

Code change:

- `scripts/run_near_threshold_hardening_replay.py` now includes `0.94` near-threshold candidates with `buy_near_min_pred_return` of `33.0`, `34.0`, and `35.0`.
- `tests/model/test_near_threshold_hardening_replay_cli.py` now covers the lower-edge candidate range.

Replay command:

```bash
venv/bin/python scripts/run_near_threshold_hardening_replay.py \
  --output data/replay_reports/near_threshold_hardening_replay_20260530_low_edge_after_binance_mystery_box_loss.json \
  --force
```

Uncertainty command:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/near_threshold_hardening_replay_20260530_low_edge_after_binance_mystery_box_loss.json \
  --candidate-id near_threshold_predret33_low_edge_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_near_threshold_low_edge_after_binance_mystery_box_loss.json \
  --force
```

Targeted verification:

```bash
venv/bin/python -m unittest tests.model.test_near_threshold_hardening_replay_cli
venv/bin/python -m py_compile scripts/run_near_threshold_hardening_replay.py
```

Both passed.

## Result

Tier: `Rejected`.

Selected candidate:

- Candidate index: `1`
- `buy_near_threshold_min_prob=0.94`
- `buy_near_min_pred_return=33.0`
- `buy_near_min_entry_volume_30s=1.5`
- `buy_near_min_entry_price_volatility=0.1`
- `buy_near_min_age_seconds=0.0`

Validation baseline to selected:

- Net profit: `0.022842003299 -> 0.022534078445` BNB
- Trades: `38 -> 38`
- Win rate: `0.815789 -> 0.815789`
- Max drawdown: unchanged at `-10.187954%`
- Walk-forward worst return: unchanged at `101.883108%`
- Near-threshold entries: `3 -> 1`
- Stress worst net profit: `0.011661288085 -> 0.012142055178` BNB

Final baseline to selected:

- Net profit: `0.002032913328 -> 0.001942316935` BNB
- Trades: `18 -> 17`
- Win rate: `0.666667 -> 0.647059`
- Max drawdown: unchanged at `-16.256141%`
- Walk-forward worst return: unchanged at `-5.576362%`
- Near-threshold entries: `1 -> 0`
- Harsh-stress worst net profit: `-0.000066180250 -> -0.000151146271` BNB
- Harsh-stress max drawdown: `-31.511910% -> -32.658220%`

Uncertainty result:

- Decision: `uncertainty_gate_rejected`
- Outcome tier: `Rejected`
- Rejection reasons: `validation_trade_delta_missing`, `final_trade_delta_missing`

This is not a Research Alpha result. The lower-edge hardening removed near-threshold exposure but reduced validation and final net profit, lowered final win rate, and worsened the harsh execution stress case. Do not continue this exact near-threshold low-edge parameter sweep.

## Decision

No live switch. No `.env`, model artifact, threshold, sizing, bot process, collector process, runtime enablement, or restart changed.

Useful next direction: convert the execution-freshness finding into a structural, replay-integrated freshness/latency feature or shadow evaluator. Do not hard-code `helper` as toxic, because helper-history evidence is mixed.

`docs/model_scoreboard.md` was updated because this experiment changes the near-threshold hardening direction status and the next structural direction.
