# BUY_NOT_READY Outcome Probe

Generated: `2026-06-01 18:23:50.061782`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Parameters

```json
{
  "horizon_seconds": 10800.0,
  "max_hold_seconds": 560.0,
  "max_sample": 100,
  "min_support": 3,
  "reason_contains": "Unsupported quote asset",
  "since": "2026-06-01 18:00:00",
  "until": null
}
```

## Summary

```json
{
  "event_count": 1,
  "extended_label_counts": {
    "extended_stop_first": 1
  },
  "extended_last_return_pct_avg": -31.103059819284717,
  "extended_last_return_pct_median": -31.103059819284717,
  "missing_path_count": 0,
  "reason_counts": {
    "Unsupported quote asset: 0x55d398326f99059fF775485246999027B3197955": 1
  },
  "supports_quote_universe_research_count": 0,
  "timeout_return_pct_avg": -31.103059819284717,
  "timeout_return_pct_median": -31.103059819284717,
  "token_quote_counts": {
    "0x55d398326f99059fF775485246999027B3197955": 1
  },
  "with_path_count": 1,
  "within_hold_label_counts": {
    "guarded_stop_first_within_hold": 1
  }
}
```

## Decision

```json
{
  "outcome_tier": "Rejected",
  "reason": "Unsupported-quote BUY_NOT_READY outcomes did not show enough +25% before stop within the current hold window. Keep the runtime quote guard unchanged.",
  "safe_for_live_switch": false,
  "status": "reject_unsupported_quote_no_within_hold_support"
}
```

## Sample

```json
[
  {
    "anchor_price": 5.591630236976381e-06,
    "anchor_price_source": "signal_price",
    "buy_fast_status_used": false,
    "event_time": "2026-06-01 18:03:46.227150",
    "extended_label": "extended_stop_first",
    "extended_last_point": {
      "kind": "sell",
      "price": 3.852462139496405e-06,
      "return_pct": -31.103059819284717,
      "seconds_after_event": 65.77285,
      "time": "2026-06-01 18:04:52"
    },
    "extended_metrics": {
      "first_barrier": "-18",
      "mae_pct": -31.103059819284717,
      "mfe_pct": -31.103059819284717,
      "time_to_minus_18_seconds": 5.77285,
      "time_to_minus_25_seconds": 5.77285,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "hold_metrics": {
      "first_barrier": "-18",
      "mae_pct": -31.103059819284717,
      "mfe_pct": -31.103059819284717,
      "time_to_minus_18_seconds": 5.77285,
      "time_to_minus_25_seconds": 5.77285,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_path_point_count": 2,
    "horizon_seconds": 10800.0,
    "lifecycle_price_current": null,
    "lifecycle_price_from_peak_pct": null,
    "lifecycle_status_chain_lag_seconds": 22.078747987747192,
    "lifecycle_status_staleness_seconds": null,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 3.852462139496405e-06,
      "return_pct": -31.103059819284717,
      "seconds_after_event": 5.77285,
      "time": "2026-06-01 18:03:52"
    },
    "min_point": {
      "kind": "buy",
      "price": 3.852462139496405e-06,
      "return_pct": -31.103059819284717,
      "seconds_after_event": 5.77285,
      "time": "2026-06-01 18:03:52"
    },
    "path_point_count": 2,
    "pred_return": 33.05533657120386,
    "primary_score_rescue_used": false,
    "prob": 0.9472593174067286,
    "reason": "Unsupported quote asset: 0x55d398326f99059fF775485246999027B3197955",
    "signal_price": 5.591630236976381e-06,
    "supports_quote_universe_research": false,
    "symbol": "5.25",
    "timeout_point": {
      "kind": "sell",
      "price": 3.852462139496405e-06,
      "return_pct": -31.103059819284717,
      "seconds_after_event": 65.77285,
      "time": "2026-06-01 18:04:52"
    },
    "token": "0x97208c83b55127ad060df9cd262bde2c5ac94444",
    "token_quote": "0x55d398326f99059fF775485246999027B3197955",
    "within_hold_label": "guarded_stop_first_within_hold"
  }
]
```
