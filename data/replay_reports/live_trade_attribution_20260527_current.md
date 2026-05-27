# Live Trade Attribution Refresh

Generated: `2026-05-27 19:28:42.635385`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `1`; wins: `1`; losses: `0`
- Net profit: `3.440599202236182e-05` BNB
- Failure labels: `{"profitable_exit": 1}`
- Close reasons: `{"PPO_SELL100": 1}`
- Lifecycle price paths: `1/1` with missing path count `0`
- Bucket net profit: `{"profitable_exit": 3.440599202236182e-05}`

## Near Threshold Split

- Near trades: `0`; labels: `{}`
- Near net profit: `0` BNB
- Primary trades: `1`; labels: `{"profitable_exit": 1}`
- Primary net profit: `3.440599202236182e-05` BNB

## Symbols

- Symbols by label: `{"profitable_exit": ["小鑫"]}`

## Rejected Signal Paths

- Signal decisions: `5589`; per-token candidates: `210`
- Barrier classes: `{"fast_profit": 18, "fast_profit_then_collapse": 11, "flat_timeout": 130, "slow_runner": 9, "stop_first": 42}`
- Recommended policies: `{"conditional_slow_hold": 9, "quick_take_profit": 29, "skip": 172}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `5`

```json
[
  {
    "bucket": "fast_profit",
    "count": 18,
    "direction_id": "rejected_fast_profit_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 18.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 1,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 18,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "fast_profit_then_collapse",
    "count": 11,
    "direction_id": "rejected_fast_profit_then_collapse_quick_take_profit_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 11.0,
    "meets_minimum_same_shape_count": true,
    "policy_hint": "quick_take_profit",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 11,
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
    "rank": 3,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 9,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 130,
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
    "count": 42,
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
