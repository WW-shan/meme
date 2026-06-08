# Live Trade Attribution Refresh

Generated: `2026-06-08 13:43:29.776215`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `0`; wins: `0`; losses: `0`
- Net profit: `0` BNB
- Failure labels: `{}`
- Close reasons: `{}`
- Lifecycle price paths: `0/0` with missing path count `0`
- Bucket net profit: `{}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `0`; labels: `{}`
- Primary net profit: `0` BNB

## Symbols

- Symbols by label: `{}`

## Rejected Signal Paths

- Signal decisions: `7228`; per-token candidates: `504`
- Barrier classes: `{"fast_profit": 28, "fast_profit_then_collapse": 27, "flat_timeout": 353, "slow_runner": 12, "stop_first": 84}`
- Recommended policies: `{"conditional_slow_hold": 12, "quick_take_profit": 55, "skip": 437}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `5`

```json
[
  {
    "bucket": "fast_profit",
    "count": 28,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 28.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 1,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 28,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 27,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 27.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 27,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 12,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 12.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 12,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 353,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "stop_first",
    "count": 84,
    "direction_id": "rejected_stop_first_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 5,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.
