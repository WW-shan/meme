# Recorded Shadow Audit Report

Generated: `2026-06-08T11:54:54.837516+00:00`

Contract: read-only recorded audit evidence; `live_switch_evidence=false`; no live config changed.

## Summary

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Signal count: `2229`
- Rows with recorded shadow fields: `2149`
- Rows missing recorded shadow fields: `80`
- Queued signal count: `1`
- Matched signal rows: `0`
- Recorded shadow-used signals: `4`
- Queued recorded shadow-used signals: `1`
- Queued recorded shadow-used matched trades: `0`
- Queued recorded shadow-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 1, 'rejected': 2228}`
- Signal reasons: `{'buy_model_reject': 825, 'entry_price_volatility_below_min': 8, 'entry_volume_30s_below_min': 51, 'near_threshold_pred_return_below_min': 1094, 'pred_return_below_min': 250, 'queued': 1}`
- Recorded shadow routes: `{'continue_hold': 4, 'quick_take_profit': 104, 'skip': 2041}`
- Recorded shadow reasons: `{'continue_hold': 4, 'non_continue_hold_route': 2145}`
- Recorded shadow used counts: `{'False': 2145, 'True': 4}`
- Matched trade reasons: `{}`

## Decision

`insufficient_recorded_shadow_support`: Recorded shadow audit evidence is read-only; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
