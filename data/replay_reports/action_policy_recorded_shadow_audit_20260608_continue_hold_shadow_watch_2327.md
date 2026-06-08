# Recorded Shadow Audit Report

Generated: `2026-06-08T15:27:54.353822+00:00`

Contract: read-only recorded audit evidence; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `3715`
- Rows with recorded shadow fields: `3635`
- Rows missing recorded shadow fields: `80`
- Queued signal count: `2`
- Matched signal rows: `0`
- Recorded shadow-used signals: `5`
- Queued recorded shadow-used signals: `2`
- Queued recorded shadow-used matched trades: `0`
- Queued recorded shadow-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 3713}`
- Signal reasons: `{'buy_model_reject': 1448, 'entry_price_volatility_below_min': 18, 'entry_volume_30s_below_min': 90, 'near_threshold_pred_return_below_min': 1730, 'pred_return_below_min': 427, 'queued': 2}`
- Recorded shadow routes: `{'continue_hold': 6, 'quick_take_profit': 162, 'skip': 3467}`
- Recorded shadow reasons: `{'continue_hold': 5, 'non_continue_hold_route': 3629, 'route_below_min_confidence': 1}`
- Recorded shadow used counts: `{'False': 3630, 'True': 5}`
- Matched trade reasons: `{}`

## Decision

`insufficient_recorded_shadow_support`: Recorded shadow audit evidence is read-only; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
