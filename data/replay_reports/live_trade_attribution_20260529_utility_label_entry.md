# Live Trade Attribution Refresh

Generated: `2026-05-29 05:49:27.122923`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `2`; wins: `1`; losses: `1`
- Net profit: `0.00012139439972800572` BNB
- Failure labels: `{"mfe_then_giveback": 1, "profitable_exit": 1}`
- Close reasons: `{"PPO_SELL100": 1, "STOP_LOSS": 1}`
- Lifecycle price paths: `2/2` with missing path count `0`
- Bucket net profit: `{"mfe_then_giveback": -0.00015238787562031852, "profitable_exit": 0.00027378227534832425}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `2`; labels: `{"mfe_then_giveback": 1, "profitable_exit": 1}`
- Primary net profit: `0.00012139439972800572` BNB

## Symbols

- Symbols by label: `{"mfe_then_giveback": ["Binance light source"], "profitable_exit": ["币安光源"]}`

## Rejected Signal Paths

- Signal decisions: `431`; per-token candidates: `31`
- Barrier classes: `{"fast_profit": 2, "fast_profit_then_collapse": 2, "flat_timeout": 24, "slow_runner": 1, "stop_first": 2}`
- Recommended policies: `{"conditional_slow_hold": 1, "quick_take_profit": 4, "skip": 26}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `6`

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
    "bucket": "fast_profit",
    "count": 2,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 2.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 2,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 2,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 2.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "quick_take_profit",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 2,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 1,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 1.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 1,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 24,
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
    "count": 2,
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
