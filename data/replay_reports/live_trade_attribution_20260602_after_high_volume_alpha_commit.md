# Live Trade Attribution Refresh

Generated: `2026-06-02 01:24:26.257539`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `3`; wins: `1`; losses: `2`
- Net profit: `7.267236041361662e-05` BNB
- Failure labels: `{"dead_flow_timeout": 2, "profitable_exit": 1}`
- Close reasons: `{"TIME_EXIT": 2, "TRAILING_STOP": 1}`
- Lifecycle price paths: `3/3` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -4.5058877880741464e-05, "profitable_exit": 0.00011773123829435808}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `3`; labels: `{"dead_flow_timeout": 2, "profitable_exit": 1}`
- Primary net profit: `7.267236041361662e-05` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["宇宙所", "合规"], "profitable_exit": ["来了"]}`

## Rejected Signal Paths

- Signal decisions: `3285`; per-token candidates: `361`
- Barrier classes: `{"fast_profit": 11, "fast_profit_then_collapse": 14, "flat_timeout": 290, "slow_runner": 4, "stop_first": 42}`
- Recommended policies: `{"conditional_slow_hold": 4, "quick_take_profit": 25, "skip": 332}`
- Missing/unemitted candidates: `261`

## Ranked Directions

- Ranked directions total: `6`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 2,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 4.5058877880741464e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 4.5058877880741464e-05,
    "sort_opportunity_count": 2,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 14,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 14.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 14,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 11,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 11.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 11,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 4,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 4.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 4,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 290,
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
    "count": 42,
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
