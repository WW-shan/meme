# Codex Local Analysis

## Status

Recommended next node: a narrow read-only `dead_flow_timeout` support probe. Do not change live config, model artifacts, or replay policy values in this node.

## Evidence

- Current live attribution has `18` closed trades, `2` wins, `16` losses, and `-0.001256566335` BNB net profit.
- `dead_flow_timeout` is the largest failure bucket: `7/18` trades.
- Near-threshold concentration is high: `6/8` near-threshold trades are `dead_flow_timeout`.
- The seven live dead-flow trades share a sharp shape:
  - `prob` median `0.9761`
  - `pred_return` median `39.9892`
  - hold duration median `564.7491` seconds
  - entry-anchor MFE median `-1.9802%`
  - pre-signal 10s sell pressure median `1.0000`
  - pre-signal 120s drawdown-from-peak median `-63.3476%`
- Existing conditional-exit gate remains `NO_GO_FOR_LIVE_RULE`; the post-target bucket has `train=5`, `validation=0`, `final=4`, `live=3`.

## Existing Code

- `src/pipeline/train_hybrid.py` already has a default-off replay mechanism for `buy_dead_flow_exit_min_hold_seconds` and `buy_dead_flow_exit_max_mfe_pct`.
- `src/pipeline/model_replay.py` exposes these runtime keys but defaults both to `None`.
- `tests/model/test_flow_activation_replay.py` covers the replay-level `DEAD_FLOW_TIME_EXIT` behavior.
- `data/replay_reports/flow_activation_replay_20260520_v95.json` selected candidate reports `dead_flow_exit_count=0`, so existing replay dead-flow trigger does not yet match the live failure bucket.
- `src/pipeline/time_to_barrier_probe.py` and `src/pipeline/flow_activation_probe.py` already contain reusable path, barrier, and pre-anchor flow helpers.

## Risks

- Label equivalence is currently missing. A live `dead_flow_timeout` label is not automatically the same as replay `DEAD_FLOW_TIME_EXIT`.
- The probe must not use `close_reason`, realized `net_profit_bnb`, or full-hold MFE/MAE as decision features.
- `near_threshold_like` must either be recomputed from causal replay fields or treated only as a reporting split; it cannot be copied from live-only labels into replay selection.

## Proposed Gate

No replay/live candidate may proceed unless a single shared classifier produces:

```text
train_positives >= 3
validation_positives >= 3
final_positives >= 3
live_positives >= 3
live_dead_flow_recall >= 6/7
```

If validation support or live recall fails, record a no-go and keep collecting labels.
