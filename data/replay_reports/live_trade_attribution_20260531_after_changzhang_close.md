# Live Trade Attribution Refresh

Generated: `2026-05-31 17:10:23.785461`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `1`; wins: `0`; losses: `1`
- Net profit: `-5.421706409925337e-05` BNB
- Failure labels: `{"dead_flow_timeout": 1}`
- Close reasons: `{"TIME_EXIT": 1}`
- Lifecycle price paths: `1/1` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -5.421706409925337e-05}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `1`; labels: `{"dead_flow_timeout": 1}`
- Primary net profit: `-5.421706409925337e-05` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["长涨"]}`

## Rejected Signal Paths

- Signal decisions: `10338`; per-token candidates: `740`
- Barrier classes: `{"fast_profit": 24, "fast_profit_then_collapse": 33, "flat_timeout": 511, "slow_runner": 15, "stop_first": 157}`
- Recommended policies: `{"conditional_slow_hold": 15, "quick_take_profit": 57, "skip": 668}`
- Missing/unemitted candidates: `540`

## Ranked Directions

- Ranked directions total: `6`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 1,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 5.421706409925337e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 5.421706409925337e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 33,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 33.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 33,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 24,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 24.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 24,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 15,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 15.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 15,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 511,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "stop_first",
    "count": 157,
    "direction_id": "rejected_stop_first_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.
