# Live Trade Attribution Refresh

Generated: `2026-06-02 03:36:55.952256`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `2`; wins: `0`; losses: `2`
- Net profit: `-4.1226224496676e-05` BNB
- Failure labels: `{"dead_flow_timeout": 2}`
- Close reasons: `{"TIME_EXIT": 2}`
- Lifecycle price paths: `2/2` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -4.1226224496676e-05}`

## Near Threshold Split

- Near trades: `1`; labels: `{"dead_flow_timeout": 1}`
- Near net profit: `-2.234354065953285e-05` BNB
- Primary trades: `1`; labels: `{"dead_flow_timeout": 1}`
- Primary net profit: `-1.8882683837143148e-05` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["有没有分红", "分红股"]}`

## Rejected Signal Paths

- Signal decisions: `1164`; per-token candidates: `135`
- Barrier classes: `{"fast_profit": 6, "fast_profit_then_collapse": 6, "flat_timeout": 105, "slow_runner": 2, "stop_first": 16}`
- Recommended policies: `{"conditional_slow_hold": 2, "quick_take_profit": 12, "skip": 121}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `6`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 2,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 4.1226224496676e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 4.1226224496676e-05,
    "sort_opportunity_count": 2,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit",
    "count": 6,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 6.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 6,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 6,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 6.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 6,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 2,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 2.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 2,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 105,
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
    "count": 16,
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
