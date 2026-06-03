# Action Policy Live Shadow Report

Generated: `2026-06-03T05:50:08.291700+00:00`

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

- Signal count: `10708`
- Queued signal count: `7`
- Matched signal rows: `16`
- Unique matched live trades: `7`
- Shadow-used signals: `50`
- Queued shadow-used signals: `7`
- Queued shadow-used matched trades: `7`
- Queued shadow-used unmatched signals: `0`
- Queued shadow-used matched net profit BNB: `-0.00018803661607591775`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 7, 'rejected': 10701}`
- Signal reasons: `{'buy_model_reject': 4516, 'entry_price_volatility_below_min': 106, 'entry_volume_30s_below_min': 219, 'near_threshold_pred_return_below_min': 4630, 'near_threshold_volume_30s_below_min': 6, 'pred_return_below_min': 1224, 'queued': 7}`
- Shadow routes: `{'continue_hold': 50, 'skip': 10658}`
- Shadow reasons: `{'continue_hold': 50, 'non_continue_hold_route': 10658}`
- Matched trade reasons: `{'ENTRY_SLIPPAGE_PROTECTION': 1, 'TIME_EXIT': 15}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
