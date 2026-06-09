# Recorded Shadow Path Attribution Report

Generated: `2026-06-09T02:01:07.330675+00:00`

Contract: read-only recorded route path attribution; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `4853`
- Rows with recorded shadow fields: `4853`
- Rows missing recorded shadow fields: `0`
- Path-evaluable recorded rows: `4853`
- Missing path count: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 4851}`
- Signal reasons: `{'buy_model_reject': 1978, 'entry_price_volatility_below_min': 19, 'entry_volume_30s_below_min': 99, 'near_threshold_pred_return_below_min': 2240, 'near_threshold_price_volatility_below_min': 3, 'pred_return_below_min': 512, 'queued': 2}`
- Recorded shadow routes: `{'continue_hold': 13, 'quick_take_profit': 218, 'skip': 4622}`
- Barrier classes: `{'fast_profit': 376, 'fast_profit_then_collapse': 339, 'flat_timeout': 2260, 'slow_runner': 189, 'stop_first': 1689}`
- Recommended policies: `{'conditional_slow_hold': 189, 'quick_take_profit': 715, 'skip': 3949}`

## Route Path Summary

```json
{
  "continue_hold": {
    "barrier_class_counts": {
      "fast_profit_then_collapse": 1,
      "flat_timeout": 11,
      "stop_first": 1
    },
    "missing_path_count": 0,
    "path_evaluable_count": 13,
    "quick_take_profit_candidate_count": 1,
    "quick_take_profit_precision": 0.07692307692307693,
    "recommended_policy_counts": {
      "quick_take_profit": 1,
      "skip": 12
    },
    "signal_count": 13
  },
  "quick_take_profit": {
    "barrier_class_counts": {
      "fast_profit": 22,
      "fast_profit_then_collapse": 15,
      "flat_timeout": 62,
      "slow_runner": 7,
      "stop_first": 112
    },
    "missing_path_count": 0,
    "path_evaluable_count": 218,
    "quick_take_profit_candidate_count": 37,
    "quick_take_profit_precision": 0.16972477064220184,
    "recommended_policy_counts": {
      "conditional_slow_hold": 7,
      "quick_take_profit": 37,
      "skip": 174
    },
    "signal_count": 218
  },
  "skip": {
    "barrier_class_counts": {
      "fast_profit": 354,
      "fast_profit_then_collapse": 323,
      "flat_timeout": 2187,
      "slow_runner": 182,
      "stop_first": 1576
    },
    "missing_path_count": 0,
    "path_evaluable_count": 4622,
    "quick_take_profit_candidate_count": 677,
    "quick_take_profit_precision": 0.14647338814366076,
    "recommended_policy_counts": {
      "conditional_slow_hold": 182,
      "quick_take_profit": 677,
      "skip": 3763
    },
    "signal_count": 4622
  }
}
```

## Decision

`rejected_recorded_quick_take_profit_path_precision`: Recorded route path attribution is read-only direction evidence. Live enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
- quick_take_profit_path_count: `218`
- quick_take_profit_precision: `0.16972477064220184`
