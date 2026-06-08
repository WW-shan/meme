# Recorded Shadow Path Attribution Report

Generated: `2026-06-08T12:06:41.930625+00:00`

Contract: read-only recorded route path attribution; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `2325`
- Rows with recorded shadow fields: `2245`
- Rows missing recorded shadow fields: `80`
- Path-evaluable recorded rows: `2245`
- Missing path count: `0`

## Counts

- Decisions: `{'queued': 1, 'rejected': 2324}`
- Signal reasons: `{'buy_model_reject': 868, 'entry_price_volatility_below_min': 10, 'entry_volume_30s_below_min': 56, 'near_threshold_pred_return_below_min': 1138, 'pred_return_below_min': 252, 'queued': 1}`
- Recorded shadow routes: `{'continue_hold': 4, 'quick_take_profit': 108, 'skip': 2133}`
- Barrier classes: `{'fast_profit': 96, 'fast_profit_then_collapse': 187, 'flat_timeout': 1054, 'slow_runner': 86, 'stop_first': 822}`
- Recommended policies: `{'conditional_slow_hold': 86, 'quick_take_profit': 283, 'skip': 1876}`

## Route Path Summary

```json
{
  "continue_hold": {
    "barrier_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 3
    },
    "missing_path_count": 0,
    "path_evaluable_count": 4,
    "quick_take_profit_candidate_count": 1,
    "quick_take_profit_precision": 0.25,
    "recommended_policy_counts": {
      "quick_take_profit": 1,
      "skip": 3
    },
    "signal_count": 4
  },
  "quick_take_profit": {
    "barrier_class_counts": {
      "fast_profit": 10,
      "fast_profit_then_collapse": 12,
      "flat_timeout": 25,
      "slow_runner": 8,
      "stop_first": 53
    },
    "missing_path_count": 0,
    "path_evaluable_count": 108,
    "quick_take_profit_candidate_count": 22,
    "quick_take_profit_precision": 0.2037037037037037,
    "recommended_policy_counts": {
      "conditional_slow_hold": 8,
      "quick_take_profit": 22,
      "skip": 78
    },
    "signal_count": 108
  },
  "skip": {
    "barrier_class_counts": {
      "fast_profit": 86,
      "fast_profit_then_collapse": 174,
      "flat_timeout": 1026,
      "slow_runner": 78,
      "stop_first": 769
    },
    "missing_path_count": 0,
    "path_evaluable_count": 2133,
    "quick_take_profit_candidate_count": 260,
    "quick_take_profit_precision": 0.12189404594467886,
    "recommended_policy_counts": {
      "conditional_slow_hold": 78,
      "quick_take_profit": 260,
      "skip": 1795
    },
    "signal_count": 2133
  }
}
```

## Decision

`rejected_recorded_quick_take_profit_path_precision`: Recorded route path attribution is read-only direction evidence. Live enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
- quick_take_profit_path_count: `108`
- quick_take_profit_precision: `0.2037037037037037`
