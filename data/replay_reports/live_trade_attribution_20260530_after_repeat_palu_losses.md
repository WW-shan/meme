# Live Trade Attribution Refresh

Generated: `2026-05-30 19:03:33.142706`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `2`; wins: `0`; losses: `2`
- Net profit: `-0.00018064396926906749` BNB
- Failure labels: `{"dead_flow_timeout": 1, "stop_first_after_entry": 1}`
- Close reasons: `{"STOP_LOSS": 1, "TIME_EXIT": 1}`
- Lifecycle price paths: `2/2` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -2.8313416286087603e-05, "stop_first_after_entry": -0.00015233055298297988}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `2`; labels: `{"dead_flow_timeout": 1, "stop_first_after_entry": 1}`
- Primary net profit: `-0.00018064396926906749` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["帕鲁"], "stop_first_after_entry": ["帕鲁"]}`

## Rejected Signal Paths

- Signal decisions: `708`; per-token candidates: `53`
- Barrier classes: `{"fast_profit": 2, "fast_profit_then_collapse": 4, "flat_timeout": 38, "slow_runner": 3, "stop_first": 6}`
- Recommended policies: `{"conditional_slow_hold": 3, "quick_take_profit": 6, "skip": 44}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `7`

```json
[
  {
    "bucket": "stop_first_after_entry",
    "count": 1,
    "direction_id": "live_stop_first_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00015233055298297988,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "pre_entry_stop_risk_filter",
    "rank": 1,
    "sort_loss_bnb": 0.00015233055298297988,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "dead_flow_timeout",
    "count": 1,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 2.8313416286087603e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 2,
    "sort_loss_bnb": 2.8313416286087603e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 4,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 4.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 4,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 3,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 3.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 3,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 2,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 2.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 2,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 38,
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
    "count": 6,
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
