# Action Policy Live Shadow Report

Generated: `2026-06-06T17:30:43.889764+00:00`

Contract: read-only counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Runtime

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Router enabled for scoring: `True`
- Route names: `['conditional_slow_hold', 'continue_hold', 'lock_profit', 'quick_take_profit', 'skip']`
- Feature count: `28`
- Min confidence: `0.4`
- Min live features: `2`
- Runtime params: `{'buy_threshold': 0.98, 'min_entry_score': 10.0, 'min_entry_volume_30s': 0.0, 'min_entry_price_volatility': 0.0, 'buy_near_threshold_min_prob': 0.94, 'buy_near_min_pred_return': 32.0, 'buy_near_min_entry_volume_30s': 1.25, 'buy_near_min_entry_price_volatility': 0.08, 'buy_near_min_age_seconds': 0.0}`

## Summary

- Signal count: `284439`
- Queued signal count: `182`
- Matched signal rows: `383`
- Unique matched live trades: `139`
- Shadow-used signals: `2003`
- Queued shadow-used signals: `121`
- Queued shadow-used matched trades: `94`
- Queued shadow-used unmatched signals: `27`
- Queued shadow-used matched net profit BNB: `-0.004918239711871068`
- Queued shadow-not-used matched net profit BNB: `-0.0029292665081616437`

## Counts

- Decisions: `{'queued': 182, 'rejected': 284257}`
- Signal reasons: `{'buy_model_reject': 86076, 'entry_price_volatility_below_min': 1443, 'entry_volume_30s_below_min': 4243, 'near_threshold_pred_return_below_min': 96479, 'near_threshold_price_volatility_below_min': 13, 'near_threshold_volume_30s_below_min': 63, 'pred_return_below_min': 95940, 'queued': 182}`
- Shadow routes: `{'continue_hold': 2003, 'skip': 282436}`
- Shadow reasons: `{'continue_hold': 2003, 'non_continue_hold_route': 282436}`
- Matched trade reasons: `{'APP_STOP_LIQUIDATION': 1, 'ENTRY_SLIPPAGE_PROTECTION': 28, 'PPO_SELL100': 114, 'STOP_LOSS': 81, 'TIME_EXIT': 118, 'TRAILING_STOP': 41}`

## Decision

`candidate_shadow_support`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
