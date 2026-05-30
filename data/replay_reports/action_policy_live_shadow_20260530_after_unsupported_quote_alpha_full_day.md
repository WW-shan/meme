# Action Policy Live Shadow Report

Generated: `2026-05-30T02:46:01.249451+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `13902`
- Queued signal count: `11`
- Matched signal rows: `32`
- Unique matched live trades: `7`
- Shadow-used signals: `85`
- Queued shadow-used signals: `11`
- Queued shadow-used matched trades: `7`
- Queued shadow-used unmatched signals: `4`
- Queued shadow-used matched net profit BNB: `0.00010067417568420197`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 11, 'rejected': 13891}`
- Signal reasons: `{'buy_model_reject': 4332, 'entry_price_volatility_below_min': 127, 'entry_volume_30s_below_min': 270, 'near_threshold_pred_return_below_min': 7179, 'near_threshold_volume_30s_below_min': 10, 'pred_return_below_min': 1973, 'queued': 11}`
- Shadow routes: `{'continue_hold': 85, 'skip': 13817}`
- Shadow reasons: `{'continue_hold': 85, 'non_continue_hold_route': 13817}`
- Matched trade reasons: `{'PPO_SELL100': 7, 'STOP_LOSS': 3, 'TIME_EXIT': 11, 'TRAILING_STOP': 11}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
