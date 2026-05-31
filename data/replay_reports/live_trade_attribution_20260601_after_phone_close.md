# Live Trade Attribution Refresh

Generated: `2026-06-01 01:00:21.101282`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `1`; wins: `0`; losses: `1`
- Net profit: `-2.3685576496972164e-05` BNB
- Failure labels: `{"dead_flow_timeout": 1}`
- Close reasons: `{"TIME_EXIT": 1}`
- Lifecycle price paths: `1/1` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -2.3685576496972164e-05}`

## Near Threshold Split

- Near trades: `1`; labels: `{"dead_flow_timeout": 1}`
- Near net profit: `-2.3685576496972164e-05` BNB
- Primary trades: `0`; labels: `{}`
- Primary net profit: `0` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["手机"]}`

## Rejected Signal Paths

- Signal decisions: `6454`; per-token candidates: `508`
- Barrier classes: `{"fast_profit": 15, "fast_profit_then_collapse": 24, "flat_timeout": 360, "missing_path": 1, "slow_runner": 9, "stop_first": 99}`
- Recommended policies: `{"conditional_slow_hold": 9, "quick_take_profit": 39, "skip": 460}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `7`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 1,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.3685576496972164e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 2.3685576496972164e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 24,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 24.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 24,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 15,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 15.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 15,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 9,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 9.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 9,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 360,
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
    "count": 99,
    "direction_id": "rejected_stop_first_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "missing_path",
    "count": 1,
    "direction_id": "rejected_missing_path_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 7,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.
