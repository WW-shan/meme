# Live Trade Attribution Refresh

Generated: `2026-05-29 18:18:13.292998`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `6`; wins: `2`; losses: `4`
- Net profit: `0.00012579707233376005` BNB
- Failure labels: `{"dead_flow_timeout": 2, "mfe_then_giveback": 1, "profitable_exit": 2, "unprofitable_other": 1}`
- Close reasons: `{"PPO_SELL100": 2, "STOP_LOSS": 1, "TIME_EXIT": 2, "TRAILING_STOP": 1}`
- Lifecycle price paths: `6/6` with missing path count `0`
- Bucket net profit: `{"dead_flow_timeout": -7.612581567329163e-05, "mfe_then_giveback": -0.00015238787562031852, "profitable_exit": 0.00039943452436246886, "unprofitable_other": -4.512376073509866e-05}`

## Near Threshold Split

- Near trades: `1`; labels: `{"unprofitable_other": 1}`
- Near net profit: `-4.512376073509866e-05` BNB
- Primary trades: `5`; labels: `{"dead_flow_timeout": 2, "mfe_then_giveback": 1, "profitable_exit": 2}`
- Primary net profit: `0.0001709208330688587` BNB

## Symbols

- Symbols by label: `{"dead_flow_timeout": ["CHILLCAT", "CRY͏P͏TOM͏AXX͏ING"], "mfe_then_giveback": ["Binance light source"], "profitable_exit": ["币安光源", "TripleT"], "unprofitable_other": ["未来"]}`

## Rejected Signal Paths

- Signal decisions: `9860`; per-token candidates: `363`
- Barrier classes: `{"fast_profit": 23, "fast_profit_then_collapse": 34, "flat_timeout": 231, "slow_runner": 6, "stop_first": 69}`
- Recommended policies: `{"conditional_slow_hold": 6, "quick_take_profit": 57, "skip": 300}`
- Missing/unemitted candidates: `163`

## Ranked Directions

- Ranked directions total: `8`

```json
[
  {
    "bucket": "mfe_then_giveback",
    "count": 1,
    "direction_id": "live_mfe_giveback_exit_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.00015238787562031852,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "profit_lock_or_trailing_exit",
    "rank": 1,
    "sort_loss_bnb": 0.00015238787562031852,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "dead_flow_timeout",
    "count": 2,
    "direction_id": "live_dead_flow_exit_or_abstention_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 7.612581567329163e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_dead_flow_exit_or_entry_abstention",
    "rank": 2,
    "sort_loss_bnb": 7.612581567329163e-05,
    "sort_opportunity_count": 2,
    "source": "live_trade_failure"
  },
  {
    "bucket": "unprofitable_other",
    "count": 1,
    "direction_id": "live_unprofitable_other_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 4.512376073509866e-05,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "diagnostic_replay",
    "rank": 3,
    "sort_loss_bnb": 4.512376073509866e-05,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 34,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 34.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 34,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit",
    "count": 23,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 23.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 23,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 6,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 6.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 6,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 6,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 231,
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
    "count": 69,
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
