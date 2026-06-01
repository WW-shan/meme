# Action Policy Live Shadow Report

Generated: `2026-06-01T17:24:05.891795+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`
- Runtime params: `{'buy_threshold': 0.98, 'min_entry_score': 35.0, 'min_entry_volume_30s': 1.5, 'min_entry_price_volatility': 0.1, 'buy_near_threshold_min_prob': 0.94, 'buy_near_min_pred_return': 32.0, 'buy_near_min_entry_volume_30s': 1.25, 'buy_near_min_entry_price_volatility': 0.08, 'buy_near_min_age_seconds': 0.0}`

## Summary

- Signal count: `3290`
- Queued signal count: `5`
- Matched signal rows: `5`
- Unique matched live trades: `3`
- Shadow-used signals: `30`
- Queued shadow-used signals: `5`
- Queued shadow-used matched trades: `3`
- Queued shadow-used unmatched signals: `2`
- Queued shadow-used matched net profit BNB: `7.267236041361662e-05`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 5, 'rejected': 3285}`
- Signal reasons: `{'buy_model_reject': 1324, 'entry_price_volatility_below_min': 73, 'entry_volume_30s_below_min': 59, 'near_threshold_pred_return_below_min': 1408, 'near_threshold_volume_30s_below_min': 5, 'pred_return_below_min': 416, 'queued': 5}`
- Shadow routes: `{'continue_hold': 30, 'skip': 3260}`
- Shadow reasons: `{'continue_hold': 30, 'non_continue_hold_route': 3260}`
- Matched trade reasons: `{'TIME_EXIT': 4, 'TRAILING_STOP': 1}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
