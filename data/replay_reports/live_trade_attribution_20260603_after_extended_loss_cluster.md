# Live Trade Attribution Refresh

Generated: `2026-06-03 13:51:29.876034`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `7`; wins: `0`; losses: `7`
- Net profit: `-0.00018803661607591775` BNB
- Failure labels: `{"dead_flow_timeout": 6, "entry_slippage_failure": 1}`
- Close reasons: `{"ENTRY_SLIPPAGE_PROTECTION": 1, "TIME_EXIT": 6}`
- Lifecycle price paths: `7/7` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -0.00013045521755931057, "entry_slippage_failure": -5.758139851660718e-05}`

## Near Threshold Split

- Near trades: `3`; labels: `{"dead_flow_timeout": 3}`
- Near net profit: `-6.702131007131721e-05` BNB
- Primary trades: `4`; labels: `{"dead_flow_timeout": 3, "entry_slippage_failure": 1}`
- Primary net profit: `-0.00012101530600460054` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["有没有分红", "分红股", "闭眼冲", "分红股", "MARHABA", "超级金融平台"], "entry_slippage_failure": ["美股焚诀"]}`

## Rejected Signal Paths

- Signal decisions: `10701`; per-token candidates: `942`
- Barrier classes: `{"fast_profit": 48, "fast_profit_then_collapse": 40, "flat_timeout": 657, "slow_runner": 23, "stop_first": 174}`
- Recommended policies: `{"conditional_slow_hold": 23, "quick_take_profit": 88, "skip": 831}`
- Missing/unemitted candidates: `622`

## Ranked Directions

- Ranked directions total: `7`

```json
[
  {
    "bucket": "dead_flow_timeout",
    "count": 6,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00013045521755931057,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 1,
    "sort_loss_bnb": 0.00013045521755931057,
    "sort_opportunity_count": 6,
    "source": "live_trade_failure"
  },
  {
    "bucket": "entry_slippage_failure",
    "count": 1,
    "direction_id": "live_entry_slippage_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 5.758139851660718e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "entry_slippage_risk_filter",
    "rank": 2,
    "sort_loss_bnb": 5.758139851660718e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit",
    "count": 48,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 48.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 48,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 40,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 40.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 40,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 23,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 23.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 23,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 657,
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
    "count": 174,
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
