# Live Trade Attribution Refresh

Generated: `2026-06-01 18:24:06.076232`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `3`; wins: `0`; losses: `3`
- Net profit: `-0.00011912908202403903` BNB
- Failure labels: `{"dead_flow_timeout": 1, "stop_first_after_entry": 1, "unprofitable_other": 1}`
- Close reasons: `{"PPO_SELL100": 1, "STOP_LOSS": 1, "TIME_EXIT": 1}`
- Lifecycle price paths: `3/3` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -1.8453680629394758e-05, "stop_first_after_entry": -7.774843550956278e-05, "unprofitable_other": -2.2926965885081488e-05}`

## Near Threshold Split

- Near trades: `2`; labels: `{"dead_flow_timeout": 1, "unprofitable_other": 1}`
- Near net profit: `-4.1380646514476246e-05` BNB
- Primary trades: `1`; labels: `{"stop_first_after_entry": 1}`
- Primary net profit: `-7.774843550956278e-05` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["新时代。"], "stop_first_after_entry": ["LPCA"], "unprofitable_other": ["球股票交易平台"]}`

## Rejected Signal Paths

- Signal decisions: `1035`; per-token candidates: `107`
- Barrier classes: `{"fast_profit": 1, "fast_profit_then_collapse": 5, "flat_timeout": 92, "slow_runner": 2, "stop_first": 7}`
- Recommended policies: `{"conditional_slow_hold": 2, "quick_take_profit": 6, "skip": 99}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `8`

```json
[
  {
    "bucket": "stop_first_after_entry",
    "count": 1,
    "direction_id": "live_stop_first_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 7.774843550956278e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "pre_entry_stop_risk_filter",
    "rank": 1,
    "sort_loss_bnb": 7.774843550956278e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "unprofitable_other",
    "count": 1,
    "direction_id": "live_unprofitable_other_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.2926965885081488e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "diagnostic_replay",
    "rank": 2,
    "sort_loss_bnb": 2.2926965885081488e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "dead_flow_timeout",
    "count": 1,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 1.8453680629394758e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 3,
    "sort_loss_bnb": 1.8453680629394758e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 5,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 5.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 5,
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
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 2,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 1,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 1.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 1,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 92,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 7,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "stop_first",
    "count": 7,
    "direction_id": "rejected_stop_first_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 8,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.
