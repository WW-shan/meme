# Action Policy Live Shadow Report

Generated: `2026-06-01T10:23:30.606726+00:00`

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

- Signal count: `1039`
- Queued signal count: `4`
- Matched signal rows: `5`
- Unique matched live trades: `3`
- Shadow-used signals: `8`
- Queued shadow-used signals: `3`
- Queued shadow-used matched trades: `3`
- Queued shadow-used unmatched signals: `0`
- Queued shadow-used matched net profit BNB: `-0.00011912908202403903`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 4, 'rejected': 1035}`
- Signal reasons: `{'buy_model_reject': 318, 'entry_price_volatility_below_min': 8, 'entry_volume_30s_below_min': 9, 'near_threshold_pred_return_below_min': 544, 'pred_return_below_min': 156, 'queued': 4}`
- Shadow routes: `{'continue_hold': 8, 'skip': 1031}`
- Shadow reasons: `{'continue_hold': 8, 'non_continue_hold_route': 1031}`
- Matched trade reasons: `{'PPO_SELL100': 1, 'STOP_LOSS': 1, 'TIME_EXIT': 3}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
