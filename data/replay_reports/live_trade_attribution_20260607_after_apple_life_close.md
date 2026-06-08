# Live Trade Attribution Refresh

Generated: `2026-06-07 16:56:04.104757`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `1`; wins: `1`; losses: `0`
- Net profit: `5.553972801680855e-05` BNB
- Failure labels: `{"profitable_exit": 1}`
- Close reasons: `{"TRAILING_STOP": 1}`
- Lifecycle price paths: `1/1` with missing path count `0`
- Bucket net profit: `{"profitable_exit": 5.553972801680855e-05}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `1`; labels: `{"profitable_exit": 1}`
- Primary net profit: `5.553972801680855e-05` BNB

## Symbols

- Symbols by label: `{"profitable_exit": ["苹果人生"]}`

## Rejected Signal Paths

- Signal decisions: `12407`; per-token candidates: `1122`
- Barrier classes: `{"fast_profit": 46, "fast_profit_then_collapse": 40, "flat_timeout": 821, "slow_runner": 29, "stop_first": 186}`
- Recommended policies: `{"conditional_slow_hold": 29, "quick_take_profit": 86, "skip": 1007}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `5`

```json
[
  {
    "bucket": "fast_profit",
    "count": 46,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 46.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 1,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 46,
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
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 40,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "slow_runner",
    "count": 29,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 29.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "conditional_slow_hold",
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 29,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 821,
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
    "count": 186,
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
