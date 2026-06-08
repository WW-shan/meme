# Recorded Shadow Path Attribution Report

Generated: `2026-06-08T15:28:11.378566+00:00`

Contract: read-only recorded route path attribution; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `3715`
- Rows with recorded shadow fields: `3635`
- Rows missing recorded shadow fields: `80`
- Path-evaluable recorded rows: `3635`
- Missing path count: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 3713}`
- Signal reasons: `{'buy_model_reject': 1448, 'entry_price_volatility_below_min': 18, 'entry_volume_30s_below_min': 90, 'near_threshold_pred_return_below_min': 1730, 'pred_return_below_min': 427, 'queued': 2}`
- Recorded shadow routes: `{'continue_hold': 6, 'quick_take_profit': 162, 'skip': 3467}`
- Barrier classes: `{'fast_profit': 237, 'fast_profit_then_collapse': 257, 'flat_timeout': 1744, 'slow_runner': 144, 'stop_first': 1253}`
- Recommended policies: `{'conditional_slow_hold': 144, 'quick_take_profit': 494, 'skip': 2997}`

## Route Path Summary

```json
{
  "continue_hold": {
    "barrier_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 4,
      "stop_first": 1
    },
    "missing_path_count": 0,
    "path_evaluable_count": 6,
    "quick_take_profit_candidate_count": 1,
    "quick_take_profit_precision": 0.16666666666666666,
    "recommended_policy_counts": {
      "quick_take_profit": 1,
      "skip": 5
    },
    "signal_count": 6
  },
  "quick_take_profit": {
    "barrier_class_counts": {
      "fast_profit": 14,
      "fast_profit_then_collapse": 12,
      "flat_timeout": 41,
      "slow_runner": 11,
      "stop_first": 84
    },
    "missing_path_count": 0,
    "path_evaluable_count": 162,
    "quick_take_profit_candidate_count": 26,
    "quick_take_profit_precision": 0.16049382716049382,
    "recommended_policy_counts": {
      "conditional_slow_hold": 11,
      "quick_take_profit": 26,
      "skip": 125
    },
    "signal_count": 162
  },
  "skip": {
    "barrier_class_counts": {
      "fast_profit": 223,
      "fast_profit_then_collapse": 244,
      "flat_timeout": 1699,
      "slow_runner": 133,
      "stop_first": 1168
    },
    "missing_path_count": 0,
    "path_evaluable_count": 3467,
    "quick_take_profit_candidate_count": 467,
    "quick_take_profit_precision": 0.13469858667435824,
    "recommended_policy_counts": {
      "conditional_slow_hold": 133,
      "quick_take_profit": 467,
      "skip": 2867
    },
    "signal_count": 3467
  }
}
```

## Decision

`rejected_recorded_quick_take_profit_path_precision`: Recorded route path attribution is read-only direction evidence. Live enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
- quick_take_profit_path_count: `162`
- quick_take_profit_precision: `0.16049382716049382`
