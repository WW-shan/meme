# Action Policy Live Shadow Report

Generated: `2026-05-29T00:24:24.141699+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `568`
- Queued signal count: `3`
- Matched signal rows: `6`
- Unique matched live trades: `2`
- Shadow-used signals: `14`
- Queued shadow-used signals: `3`
- Queued shadow-used matched trades: `2`
- Queued shadow-used unmatched signals: `1`
- Queued shadow-used matched net profit BNB: `0.00012139439972800572`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 3, 'rejected': 565}`
- Signal reasons: `{'buy_model_reject': 278, 'entry_price_volatility_below_min': 6, 'entry_volume_30s_below_min': 7, 'near_threshold_pred_return_below_min': 218, 'near_threshold_volume_30s_below_min': 7, 'pred_return_below_min': 49, 'queued': 3}`
- Shadow routes: `{'continue_hold': 14, 'skip': 554}`
- Shadow reasons: `{'continue_hold': 14, 'non_continue_hold_route': 554}`
- Matched trade reasons: `{'PPO_SELL100': 3, 'STOP_LOSS': 3}`

## Decision

`has_matched_shadow_route`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
