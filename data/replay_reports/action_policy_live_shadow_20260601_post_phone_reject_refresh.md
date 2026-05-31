# Action Policy Live Shadow Report

Generated: `2026-05-31T17:16:55.224216+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `56`
- Queued signal count: `0`
- Matched signal rows: `0`
- Unique matched live trades: `0`
- Shadow-used signals: `0`
- Queued shadow-used signals: `0`
- Queued shadow-used matched trades: `0`
- Queued shadow-used unmatched signals: `0`
- Queued shadow-used matched net profit BNB: `0`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'rejected': 56}`
- Signal reasons: `{'buy_model_reject': 37, 'near_threshold_pred_return_below_min': 19}`
- Shadow routes: `{'skip': 56}`
- Shadow reasons: `{'non_continue_hold_route': 56}`
- Matched trade reasons: `{}`

## Decision

`insufficient_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
