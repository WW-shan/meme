# 2026-05-26 Flow-Compatible Rescue

## Live Evidence

- Active live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Bot and collector were running through `memectl`; the latest state check had no open positions and balance `0.002945172589791142`.
- Live attribution report: `data/replay_reports/live_trade_attribution_20260526_flow_compatible_rescue_round.json`.
- Since `2026-05-26T00:00:00`, closed trades were `2`, both near-threshold-like losses, total `-0.000051381969067633784` BNB:
  - `CHILLCAT`: `dead_flow_timeout` / `TIME_EXIT`, `prob=0.9777056414540839`, `PredReturn=39.122827526674016`, entry-anchor MFE/MAE `-1.9802%/-1.9802%`, net `-0.000025319026715831417` BNB.
  - `BNBGUY`: `unprofitable_other` / `PPO_SELL100`, `prob=0.9763632505354203`, `PredReturn=46.86545461286604`, entry-anchor MFE/MAE `5.0035%/-2.1063%`, net `-0.000026062942351802367` BNB.
- Rejected per-token candidates were `140`: `slow_runner=13`, `fast_profit=6`, `fast_profit_then_collapse=14`, `flat_timeout=87`, `stop_first=20`.

## Research Evidence

SmartSearch artifacts are in this directory. `xAI Responses`, `Tavily`, and `Context7` were available; `EXA_API_KEY`, `ZHIPU_API_KEY`, and `FIRECRAWL_API_KEY` were not configured.

Fetched evidence supports:

- Use triple-barrier/meta-label style second-stage filters instead of global threshold relaxation.
- Selective classification is a better framing than forcing every candidate into a trade/no-trade action.
- Conformal/risk-control ideas map to this repo as strict validation, final, walk-forward, stress, and support gates.
- Order-flow/liquidity evidence is relevant for short-horizon price movement, but the current replay path did not expose true flow metrics without expensive sample rebuilding.

## Direction Selection

Rejected alternatives:

- Full flow-feature rescue gate: best aligned with the research, but a validation distribution build with `include_flow_features=True` ran over 10 minutes with high memory and no cache/report output. This is kept as a future data-pipeline improvement, not the smallest viable replay for this round.
- Quick-take-profit rescue: rejected because recent evidence is mixed and repeats known broad quick-profit failure modes.

Selected experiment:

- Parameterized liquidity-compatible preserve-base runner-retention replay.
- Grid file: `docs/research/20260526-flow-compatible-rescue/flow_liquidity_grid.json`.
- Replay report: `data/replay_reports/runner_retention_flow_liquidity_replay_20260526.json`.

## Experiment Result

Decision: `reject`.

Best validation candidate:

- Baseline: `32` trades, `415.3104%` return, `0.02109487` BNB profit, `75.00%` win rate, `-9.8821%` max drawdown.
- Candidate: `33` trades, `412.3852%` return, `0.02094629` BNB profit, `75.76%` win rate, `-11.0481%` max drawdown.
- Failed gates: net profit, max drawdown, walk-forward drawdown, stress return/profit/drawdown.

Final confirmation:

- Baseline: `21` trades, `101.8745%` return, `0.00517452` BNB profit, `52.38%` win rate, `-18.2292%` max drawdown.
- Candidate: `20` trades, `100.0909%` return, `0.00508392` BNB profit, `50.00%` win rate, `-18.2292%` max drawdown.
- Failed gates: net profit, win rate, stress return/profit.

The liquidity-compatible filter reduced the previous over-expansion problem but did not improve expected live profitability. The scorer still relied on `PredReturn`, `volume_30s`, `price_volatility`, and `prob`; `flow_metrics_available` was `0.0`, so this was a liquidity-volume experiment rather than a true order-flow experiment.

## Business Decision

No live switch. No `.env`, threshold, sizing, model artifact, or bot restart change.

Do not continue tuning `volume_30s` as a substitute for flow. The next useful direction is either a replay data-pipeline improvement that makes accepted and rejected replay rows support true flow fields cheaply, or a stricter coverage/LCB selector over an already support-complete candidate set.
