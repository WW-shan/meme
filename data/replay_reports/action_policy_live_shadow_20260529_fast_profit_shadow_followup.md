# Action Policy Live Shadow Report

Generated: `2026-05-29T15:00:08.560291+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `1527`
- Queued signal count: `0`
- Matched signal rows: `0`
- Unique matched live trades: `0`
- Shadow-used signals: `18`
- Queued shadow-used signals: `0`
- Queued shadow-used matched trades: `0`
- Queued shadow-used unmatched signals: `0`
- Queued shadow-used matched net profit BNB: `0`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'rejected': 1527}`
- Signal reasons: `{'buy_model_reject': 387, 'entry_price_volatility_below_min': 16, 'entry_volume_30s_below_min': 39, 'near_threshold_pred_return_below_min': 828, 'near_threshold_volume_30s_below_min': 1, 'pred_return_below_min': 256}`
- Shadow routes: `{'continue_hold': 18, 'skip': 1509}`
- Shadow reasons: `{'continue_hold': 18, 'non_continue_hold_route': 1509}`
- Matched trade reasons: `{}`

## Decision

`insufficient_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
