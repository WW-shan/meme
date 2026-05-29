# Action Policy Live Shadow Report

Generated: `2026-05-29T15:07:24.064318+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `12761`
- Queued signal count: `9`
- Matched signal rows: `32`
- Unique matched live trades: `7`
- Shadow-used signals: `76`
- Queued shadow-used signals: `9`
- Queued shadow-used matched trades: `7`
- Queued shadow-used unmatched signals: `2`
- Queued shadow-used matched net profit BNB: `0.00010067417568420197`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 9, 'rejected': 12752}`
- Signal reasons: `{'buy_model_reject': 3622, 'entry_price_volatility_below_min': 123, 'entry_volume_30s_below_min': 262, 'near_threshold_pred_return_below_min': 6842, 'near_threshold_volume_30s_below_min': 8, 'pred_return_below_min': 1895, 'queued': 9}`
- Shadow routes: `{'continue_hold': 76, 'skip': 12685}`
- Shadow reasons: `{'continue_hold': 76, 'non_continue_hold_route': 12685}`
- Matched trade reasons: `{'PPO_SELL100': 7, 'STOP_LOSS': 3, 'TIME_EXIT': 11, 'TRAILING_STOP': 11}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
