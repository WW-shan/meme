# Live Trade Attribution Refresh

Generated: `2026-05-30 17:23:50.863046`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Live Since Restart

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Restart anchor: `None`
- Closed trades: `1`; wins: `0`; losses: `1`
- Net profit: `-0.0001639087430183287` BNB
- Failure labels: `{"stop_first_after_entry": 1}`
- Close reasons: `{"STOP_LOSS": 1}`
- Lifecycle price paths: `1/1` with missing path count `0`
- Bucket net profit: `{"stop_first_after_entry": -0.0001639087430183287}`

## Near Threshold Split

- Near trades: `1`; labels: `{"stop_first_after_entry": 1}`
- Near net profit: `-0.0001639087430183287` BNB
- Primary trades: `0`; labels: `{}`
- Primary net profit: `0` BNB

## Symbols

- Symbols by label: `{"stop_first_after_entry": ["帕鲁"]}`

## Rejected Signal Paths

- Signal decisions: `93`; per-token candidates: `8`
- Barrier classes: `{"flat_timeout": 5, "slow_runner": 1, "stop_first": 2}`
- Recommended policies: `{"conditional_slow_hold": 1, "skip": 7}`
- Missing/unemitted candidates: `0`

## Ranked Directions

- Ranked directions total: `4`

```json
[
  {
    "bucket": "stop_first_after_entry",
    "count": 1,
    "direction_id": "live_stop_first_risk_replay",
    "evidence_unit": "bnb_loss",
    "evidence_value": 0.0001639087430183287,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "pre_entry_stop_risk_filter",
    "rank": 1,
    "sort_loss_bnb": 0.0001639087430183287,
    "sort_opportunity_count": 1,
    "source": "live_trade_failure"
  },
  {
    "bucket": "slow_runner",
    "count": 1,
    "direction_id": "rejected_slow_runner_conditional_slow_hold_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 1.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "conditional_slow_hold",
    "rank": 2,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 1,
    "source": "rejected_signal_path"
  },
  {
    "bucket": "flat_timeout",
    "count": 5,
    "direction_id": "rejected_flat_timeout_skip_replay",
    "evidence_unit": "candidate_count",
    "evidence_value": 0.0,
    "meets_minimum_same_shape_count": false,
    "policy_hint": "skip",
    "rank": 3,
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
    "rank": 4,
    "sort_loss_bnb": 0.0,
    "sort_opportunity_count": 0,
    "source": "rejected_signal_path"
  }
]
```

## Decision

`NO_GO_FOR_LIVE_SWITCH`: Read-only live attribution is diagnostic evidence only; same-shape count can trigger a future replay, but live runtime/model changes still require causal, replay-equivalent support.

Next action: Keep live config unchanged; only a future replay task may test a conditional dead-flow exit or candidate-level meta gate if causal support improves.
