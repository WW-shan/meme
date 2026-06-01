# Action Policy Live Shadow Report

Generated: `2026-06-01T19:35:50.207056+00:00`

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

- Signal count: `1166`
- Queued signal count: `2`
- Matched signal rows: `6`
- Unique matched live trades: `2`
- Shadow-used signals: `18`
- Queued shadow-used signals: `2`
- Queued shadow-used matched trades: `2`
- Queued shadow-used unmatched signals: `0`
- Queued shadow-used matched net profit BNB: `-4.1226224496676e-05`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 1164}`
- Signal reasons: `{'buy_model_reject': 551, 'entry_price_volatility_below_min': 39, 'entry_volume_30s_below_min': 38, 'near_threshold_pred_return_below_min': 397, 'near_threshold_volume_30s_below_min': 5, 'pred_return_below_min': 134, 'queued': 2}`
- Shadow routes: `{'continue_hold': 18, 'skip': 1148}`
- Shadow reasons: `{'continue_hold': 18, 'non_continue_hold_route': 1148}`
- Matched trade reasons: `{'TIME_EXIT': 6}`

## Decision

`has_matched_shadow_route`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
