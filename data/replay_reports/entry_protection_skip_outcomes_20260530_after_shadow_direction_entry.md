# Entry Protection Skip Outcome Probe

Generated: `2026-05-30 08:01:27.846761`

Contract: read-only diagnostic evidence; `live_switch_evidence=false`; `safe_for_live_switch=false`.

## Parameters

```json
{
  "horizon_seconds": 10800.0,
  "max_hold_seconds": 560.0,
  "max_sample": 0,
  "min_support": 7,
  "since": "2026-05-29 21:19:42",
  "until": null
}
```

## Summary

```json
{
  "extended_label_counts": {
    "late_profit_after_hold": 1
  },
  "extended_last_return_pct_avg": -70.7896372732952,
  "extended_last_return_pct_median": -70.7896372732952,
  "missing_path_count": 0,
  "signal_to_candidate_jump_pct_median": 126.42364142205085,
  "skip_count": 1,
  "supports_relaxing_entry_protection_count": 0,
  "timeout_return_pct_avg": 3.9453389652795323,
  "timeout_return_pct_median": 3.9453389652795323,
  "with_path_count": 1,
  "within_hold_label_counts": {
    "protected_flat_timeout": 1
  }
}
```

## Decision

```json
{
  "outcome_tier": "Rejected",
  "reason": "Entry-protection skip outcomes did not show enough +25% before stop within the current hold window. Do not loosen live entry protection from this evidence.",
  "safe_for_live_switch": false,
  "status": "reject_relaxation_no_within_hold_support"
}
```

## Sample

```json
[
  {
    "candidate_price": 1.9950613022e-08,
    "entry_price_protection_pct": 0.25,
    "extended_label": "late_profit_after_hold",
    "extended_last_point": {
      "kind": "sell",
      "price": 5.827646429927401e-09,
      "return_pct": -70.7896372732952,
      "seconds_after_skip": 18302.643365,
      "time": "2026-05-30 07:12:07"
    },
    "extended_metrics": {
      "first_barrier": "+25",
      "mae_pct": -71.05780491090866,
      "mfe_pct": 89.2711611385804,
      "time_to_minus_18_seconds": 10589.643365,
      "time_to_minus_25_seconds": 10589.643365,
      "time_to_plus_25_seconds": 882.643365,
      "time_to_plus_60_seconds": 4988.643365
    },
    "hold_metrics": {
      "first_barrier": null,
      "mae_pct": -3.2431589267389094,
      "mfe_pct": 3.9453389652795323,
      "time_to_minus_18_seconds": null,
      "time_to_minus_25_seconds": null,
      "time_to_plus_25_seconds": null,
      "time_to_plus_60_seconds": null
    },
    "horizon_seconds": 10800.0,
    "max_hold_seconds": 560.0,
    "max_point": {
      "kind": "buy",
      "price": 3.776075692100423e-08,
      "return_pct": 89.2711611385804,
      "seconds_after_skip": 10576.643365,
      "time": "2026-05-30 05:03:21"
    },
    "min_point": {
      "kind": "sell",
      "price": 5.774145342296904e-09,
      "return_pct": -71.05780491090866,
      "seconds_after_skip": 10613.643365,
      "time": "2026-05-30 05:03:58"
    },
    "path_point_count": 570,
    "pred_return": 85.43009813900393,
    "prob": 0.9871236046862742,
    "reported_entry_slippage_fraction": 1.2642364142205085,
    "reported_entry_slippage_pct": 126.42364142205085,
    "signal_price": 8.811188132431943e-09,
    "signal_to_candidate_jump_pct": 126.42364142205085,
    "skip_time": "2026-05-30 02:07:04.356635",
    "supports_relaxing_entry_protection": false,
    "symbol": "BTC",
    "timeout_point": {
      "kind": "buy",
      "price": 2.07377323313691e-08,
      "return_pct": 3.9453389652795323,
      "seconds_after_skip": 558.643365,
      "time": "2026-05-30 02:16:23"
    },
    "token": "0x0c3e642757effd7797439ba33be6e228a6664444",
    "within_hold_label": "protected_flat_timeout"
  }
]
```
