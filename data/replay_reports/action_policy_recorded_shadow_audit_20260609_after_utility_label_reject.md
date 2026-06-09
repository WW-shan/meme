# Recorded Shadow Audit Report

Generated: `2026-06-09T02:00:13.629870+00:00`

Contract: read-only recorded audit evidence; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `4848`
- Rows with recorded shadow fields: `4848`
- Rows missing recorded shadow fields: `0`
- Queued signal count: `2`
- Matched signal rows: `0`
- Recorded shadow-used signals: `10`
- Queued recorded shadow-used signals: `2`
- Queued recorded shadow-used matched trades: `0`
- Queued recorded shadow-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 4846}`
- Signal reasons: `{'buy_model_reject': 1973, 'entry_price_volatility_below_min': 19, 'entry_volume_30s_below_min': 99, 'near_threshold_pred_return_below_min': 2240, 'near_threshold_price_volatility_below_min': 3, 'pred_return_below_min': 512, 'queued': 2}`
- Recorded shadow routes: `{'continue_hold': 13, 'quick_take_profit': 218, 'skip': 4617}`
- Recorded shadow reasons: `{'continue_hold': 10, 'non_continue_hold_route': 4835, 'route_below_min_confidence': 3}`
- Recorded shadow used counts: `{'False': 4838, 'True': 10}`
- Matched trade reasons: `{}`

## Decision

`insufficient_recorded_shadow_support`: Recorded shadow audit evidence is read-only; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
