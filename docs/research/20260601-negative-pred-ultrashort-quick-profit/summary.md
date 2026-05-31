# Negative-PredReturn Ultrashort Quick-Profit Replay

Date: 2026-06-01

## Hypothesis

Try a replay-only ultrashort quick-profit overlay for high-probability, very young candidates even when `PredReturn` is negative or near zero. This is a structural change from the earlier positive-PredReturn quick-profit sweeps.

Live trigger:

- `绷`
- `fast_profit_then_collapse`
- `prob=0.9861301029760093`
- `PredReturn=-3.5090795581680494`
- `age_seconds=4.0`
- `entry_volume_30s=2.762079206940594`
- `entry_price_volatility=0.1269888643505633`
- `MFE=+226.5028121997165%`
- `MAE=-20.985212898098037%`

## Experiment

Replay command:

```bash
venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json docs/research/20260601-negative-pred-ultrashort-quick-profit/negative_pred_ultrashort_grid.json \
  --output data/replay_reports/negative_pred_ultrashort_quick_profit_replay_20260601.json \
  --write-selected-trade-delta \
  --force
```

## Result

Outcome tier: `Rejected`.

Key report:

- validation baseline net profit: `0.022842003299308057` BNB
- best validation net profit: `0.0386373291806712` BNB
- final confirmation: `false`
- selected validation candidate trades: `511`
- selected validation candidate win rate: `0.48336594911937375`
- selected validation candidate max drawdown: `-19.539228260041263`
- selected validation candidate stress worst net profit: `0.0038020963980450392`
- selected validation candidate stress worst max drawdown: `-40.98081744394935`
- selected validation candidate walk-forward worst net return: `141.86358689027213`
- final baseline net profit: `0.002130506358905197` BNB
- final candidate net profit: `-0.0038727655404503423` BNB
- final candidate trades: `440`
- final candidate win rate: `0.35454545454545455`
- final candidate max drawdown: `-85.7854786802085`
- final candidate stress worst net profit: `-0.005077346322729664`
- final candidate stress worst max drawdown: `-99.96147508278437`
- final candidate walk-forward worst net return: `-90.068888168559`

The replay gained raw validation profit, but the trade count expanded far beyond the strict live-sized baseline and the final confirmation failed the drawdown, stress, and win-rate gates. That is not a promotion path.

Paired trade-delta:

- validation added candidate trades: `474`, win rate `0.4578059071729958`, return sum `3122.8745054777387%`
- validation removed baseline trades: `1`, win rate `1.0`, return sum `119.84497165394427%`
- final added candidate trades: `423`, win rate `0.3475177304964539`, return sum `-2789.5140152916892%`
- final removed baseline trades: `4`, win rate `0.5`, return sum `118.98565314754502%`
- final common trades: `17`, worsened `10`, unchanged `7`, improved `0`

## Decision

Reject the negative-PredReturn ultrashort quick-profit overlay as a deployable direction.

Keep the live model unchanged. Use the result only as evidence that the `绷` shape is real but too broad to promote with the current quick-profit overlay gate.

`docs/model_scoreboard.md` was intentionally not updated because the result is a hard-rejected replay with no model status promotion, no live-risk interpretation change, and no new accepted baseline.
