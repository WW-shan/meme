# Recorded Shadow Audit Report

Generated: `2026-06-08T08:00:03.530165+00:00`

Contract: read-only recorded audit evidence; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `614`
- Rows with recorded shadow fields: `534`
- Rows missing recorded shadow fields: `80`
- Queued signal count: `0`
- Matched signal rows: `0`
- Recorded shadow-used signals: `0`
- Queued recorded shadow-used signals: `0`
- Queued recorded shadow-used matched trades: `0`
- Queued recorded shadow-used matched net profit BNB: `0`

## Counts

- Decisions: `{'rejected': 614}`
- Signal reasons: `{'buy_model_reject': 218, 'entry_price_volatility_below_min': 1, 'entry_volume_30s_below_min': 21, 'near_threshold_pred_return_below_min': 312, 'pred_return_below_min': 62}`
- Recorded shadow routes: `{'quick_take_profit': 36, 'skip': 498}`
- Recorded shadow reasons: `{'non_continue_hold_route': 534}`
- Recorded shadow used counts: `{'False': 534}`
- Matched trade reasons: `{}`

## Decision

`insufficient_recorded_shadow_support`: Recorded shadow audit evidence is read-only; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
