# Action Policy Live Shadow Report

Generated: `2026-05-29T10:27:11.519033+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`

## Summary

- Signal count: `9950`
- Queued signal count: `8`
- Matched signal rows: `30`
- Unique matched live trades: `6`
- Shadow-used signals: `55`
- Queued shadow-used signals: `8`
- Queued shadow-used matched trades: `6`
- Queued shadow-used unmatched signals: `2`
- Queued shadow-used matched net profit BNB: `0.00012579707233376005`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 8, 'rejected': 9942}`
- Signal reasons: `{'buy_model_reject': 2774, 'entry_price_volatility_below_min': 96, 'entry_volume_30s_below_min': 208, 'near_threshold_pred_return_below_min': 5429, 'near_threshold_volume_30s_below_min': 7, 'pred_return_below_min': 1428, 'queued': 8}`
- Shadow routes: `{'continue_hold': 55, 'skip': 9895}`
- Shadow reasons: `{'continue_hold': 55, 'non_continue_hold_route': 9895}`
- Matched trade reasons: `{'PPO_SELL100': 7, 'STOP_LOSS': 3, 'TIME_EXIT': 9, 'TRAILING_STOP': 11}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
