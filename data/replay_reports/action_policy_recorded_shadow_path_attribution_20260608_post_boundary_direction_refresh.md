# Recorded Shadow Path Attribution Report

Generated: `2026-06-08T15:14:37.975672+00:00`

Contract: read-only recorded route path attribution; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `3606`
- Rows with recorded shadow fields: `3526`
- Rows missing recorded shadow fields: `80`
- Path-evaluable recorded rows: `3526`
- Missing path count: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 3604}`
- Signal reasons: `{'buy_model_reject': 1382, 'entry_price_volatility_below_min': 18, 'entry_volume_30s_below_min': 84, 'near_threshold_pred_return_below_min': 1700, 'pred_return_below_min': 420, 'queued': 2}`
- Recorded shadow routes: `{'continue_hold': 5, 'quick_take_profit': 157, 'skip': 3364}`
- Barrier classes: `{'fast_profit': 216, 'fast_profit_then_collapse': 257, 'flat_timeout': 1688, 'slow_runner': 133, 'stop_first': 1232}`
- Recommended policies: `{'conditional_slow_hold': 133, 'quick_take_profit': 473, 'skip': 2920}`

## Route Path Summary

```json
{
  "continue_hold": {
    "barrier_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 3,
      "stop_first": 1
    },
    "missing_path_count": 0,
    "path_evaluable_count": 5,
    "quick_take_profit_candidate_count": 1,
    "quick_take_profit_precision": 0.2,
    "recommended_policy_counts": {
      "quick_take_profit": 1,
      "skip": 4
    },
    "signal_count": 5
  },
  "quick_take_profit": {
    "barrier_class_counts": {
      "fast_profit": 11,
      "fast_profit_then_collapse": 12,
      "flat_timeout": 40,
      "slow_runner": 10,
      "stop_first": 84
    },
    "missing_path_count": 0,
    "path_evaluable_count": 157,
    "quick_take_profit_candidate_count": 23,
    "quick_take_profit_precision": 0.1464968152866242,
    "recommended_policy_counts": {
      "conditional_slow_hold": 10,
      "quick_take_profit": 23,
      "skip": 124
    },
    "signal_count": 157
  },
  "skip": {
    "barrier_class_counts": {
      "fast_profit": 205,
      "fast_profit_then_collapse": 244,
      "flat_timeout": 1645,
      "slow_runner": 123,
      "stop_first": 1147
    },
    "missing_path_count": 0,
    "path_evaluable_count": 3364,
    "quick_take_profit_candidate_count": 449,
    "quick_take_profit_precision": 0.13347205707491083,
    "recommended_policy_counts": {
      "conditional_slow_hold": 123,
      "quick_take_profit": 449,
      "skip": 2792
    },
    "signal_count": 3364
  }
}
```

## Decision

`rejected_recorded_quick_take_profit_path_precision`: Recorded route path attribution is read-only direction evidence. Live enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
- quick_take_profit_path_count: `157`
- quick_take_profit_precision: `0.1464968152866242`
