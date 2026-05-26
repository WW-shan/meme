# 2026-05-26 True-Flow Replay Compatibility

## Objective

Verify whether the runner-retention candidate gate can consume DatasetBuilder true-flow samples instead of using `volume_30s` as a proxy, then run a strict live-sized replay against the current v95 canary baseline.

## Changes

- Added DatasetBuilder flow-name compatibility for runner-retention rescue flow filters:
  - `total_flow_volume_*`
  - `sell_pressure_*`
  - `signed_imbalance_*`
  - `sell_volume_*`
  - `flow_event_count_*` from sample metadata
- Kept the v95 buy/entry-value feature schema strict by ignoring optional replay-only flow fields when the deployed model was not trained on them.
- Applied the same optional-flow ignore contract in candidate-ranker scoring, where runner-retention scoring reuses the v95 buy and entry-value models on flow-enriched samples.

## Verification

- `python -m unittest tests.model.test_train_hybrid_pipeline`
- `python -m unittest tests.model.test_candidate_ranker_probe`
- `python -m unittest tests.model.test_runner_retention_replay_gate`

## Replay

Command:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py \
  --candidate-grid-json docs/research/20260526-true-flow-replay-compatibility/flow_true_grid.json \
  --preserve-base-candidates \
  --output data/replay_reports/runner_retention_true_flow_replay_20260526.json \
  --force
```

Result: rejected.

Validation baseline:

- trades: `32`
- net return: `415.3104%`
- net profit: `0.02109487` BNB
- win rate: `75.00%`
- max drawdown: `-9.8821%`
- worst stress return: `219.4896%`

Best validation candidate:

- candidate index: `0`
- trades: `32`
- net return: `411.9837%`
- net profit: `0.02092590` BNB
- win rate: `75.00%`
- max drawdown: `-10.1529%`
- worst stress return: `199.0069%`
- acceptance gate: failed on net profit, max drawdown, stress profit/return/drawdown, and walk-forward drawdown.

Final baseline:

- trades: `21`
- net return: `101.8745%`
- net profit: `0.00517452` BNB
- win rate: `52.3810%`
- max drawdown: `-18.2292%`

Final candidate:

- trades: `20`
- net return: `101.0825%`
- net profit: `0.00513429` BNB
- win rate: `50.00%`
- max drawdown: `-18.2292%`
- final confirmation: failed.

## Decision

No live switch. Do not change `.env`, threshold, sizing, model artifacts, or restart the bot.

The compatibility work is useful infrastructure, but this specific true-flow runner-retention rescue does not improve live-sized replay. The best candidate preserved trade count but reduced validation and final profit, worsened validation drawdown, and weakened stress replay.

## Next Direction

The replay report still shows the runner-retention ranker mostly using `volume_30s`, `pred_return`, and `price_volatility`. The next useful direction is not another static `volume_30s` substitute. Prefer either:

- exporting true-flow values into runner-retention candidate rows so the ranker can learn from them directly, then testing whether `flow_metrics_available` becomes informative, or
- moving to the support-complete / LCB selector path that already showed stronger shadow evidence with positive validation and final reward lower bounds.
