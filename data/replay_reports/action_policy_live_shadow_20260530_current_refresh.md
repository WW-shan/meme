# Action Policy Live Shadow Report

Generated: `2026-05-29T20:51:36.282563+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `2128`
- Queued signal count: `1`
- Matched signal rows: `0`
- Unique matched live trades: `0`
- Shadow-used signals: `22`
- Queued shadow-used signals: `1`
- Queued shadow-used matched trades: `0`
- Queued shadow-used unmatched signals: `1`
- Queued shadow-used matched net profit BNB: `0`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 1, 'rejected': 2127}`
- Signal reasons: `{'buy_model_reject': 645, 'entry_price_volatility_below_min': 22, 'entry_volume_30s_below_min': 44, 'near_threshold_pred_return_below_min': 1073, 'near_threshold_volume_30s_below_min': 3, 'pred_return_below_min': 340, 'queued': 1}`
- Shadow routes: `{'continue_hold': 22, 'skip': 2106}`
- Shadow reasons: `{'continue_hold': 22, 'non_continue_hold_route': 2106}`
- Matched trade reasons: `{}`

## Decision

`insufficient_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
