# Live Trade Attribution Refresh

Generated: `2026-05-26 14:43:21.003038`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `2`; wins: `0`; losses: `2`
- Net profit: `-5.1381969067633784e-05` BNB
- Failure labels: `{"dead_flow_timeout": 1, "unprofitable_other": 1}`
- Close reasons: `{"PPO_SELL100": 1, "TIME_EXIT": 1}`
- Lifecycle price paths: `2/2` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -2.5319026715831417e-05, "unprofitable_other": -2.6062942351802367e-05}`

## Near Threshold Split

- Near trades: `2`; labels: `{"dead_flow_timeout": 1, "unprofitable_other": 1}`
- Near net profit: `-5.1381969067633784e-05` BNB
- Primary trades: `0`; labels: `{}`
- Primary net profit: `0` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["CHILLCAT"], "unprofitable_other": ["BNBGUY"]}`

## Rejected Signal Paths

- Signal decisions: `3923`; per-token candidates: `148`
- Barrier classes: `{"fast_profit": 6, "fast_profit_then_collapse": 14, "flat_timeout": 91, "slow_runner": 13, "stop_first": 24}`
- Recommended policies: `{"conditional_slow_hold": 13, "quick_take_profit": 20, "skip": 115}`
- Missing/unemitted candidates: `48`

## Ranked Directions

- Ranked directions total: `7`

```json
[
  {
    "bucket": "unprofitable_other",
    "count": 1,
    "direction_id": "live_unprofitable_other_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.6062942351802367e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "diagnostic_replay",
    "rank": 1,
    "sort_loss_bnb": 2.6062942351802367e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "dead_flow_timeout",
    "count": 1,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.5319026715831417e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 2,
    "sort_loss_bnb": 2.5319026715831417e-05,
    "sort_opportunity_count": 1,
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
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 14,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 13,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 13.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 13,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 6,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 6.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 6,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 91,
    "direction_id": "rejected_flat_timeout_skip_replay",
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
    "bucket": "stop_first",
    "count": 24,
    "direction_id": "rejected_stop_first_skip_replay",
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
