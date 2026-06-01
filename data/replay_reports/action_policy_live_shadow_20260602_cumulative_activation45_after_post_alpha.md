# Action Policy Live Shadow Report

Generated: `2026-06-01T17:37:36.239757+00:00`

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

- Signal count: `11613`
- Queued signal count: `18`
- Matched signal rows: `26`
- Unique matched live trades: `13`
- Shadow-used signals: `89`
- Queued shadow-used signals: `17`
- Queued shadow-used matched trades: `13`
- Queued shadow-used unmatched signals: `4`
- Queued shadow-used matched net profit BNB: `-1.0049028392099149e-05`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 18, 'rejected': 11595}`
- Signal reasons: `{'buy_model_reject': 4242, 'entry_price_volatility_below_min': 133, 'entry_volume_30s_below_min': 221, 'near_threshold_pred_return_below_min': 5258, 'near_threshold_volume_30s_below_min': 6, 'pred_return_below_min': 1735, 'queued': 18}`
- Shadow routes: `{'continue_hold': 89, 'skip': 11524}`
- Shadow reasons: `{'continue_hold': 89, 'non_continue_hold_route': 11524}`
- Matched trade reasons: `{'PPO_SELL100': 1, 'STOP_LOSS': 1, 'TIME_EXIT': 22, 'TRAILING_STOP': 2}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
