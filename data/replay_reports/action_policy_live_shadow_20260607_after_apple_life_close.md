# Action Policy Live Shadow Report

Generated: `2026-06-07T08:56:14.908306+00:00`

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

- Signal count: `12415`
- Queued signal count: `2`
- Matched signal rows: `6`
- Unique matched live trades: `1`
- Shadow-used signals: `124`
- Queued shadow-used signals: `2`
- Queued shadow-used matched trades: `1`
- Queued shadow-used unmatched signals: `1`
- Queued shadow-used matched net profit BNB: `5.553972801680855e-05`
- Queued shadow-not-used matched net profit BNB: `0`

## Counts

- Decisions: `{'queued': 2, 'rejected': 12413}`
- Signal reasons: `{'buy_model_reject': 5487, 'entry_price_volatility_below_min': 98, 'entry_volume_30s_below_min': 247, 'near_threshold_pred_return_below_min': 5242, 'near_threshold_volume_30s_below_min': 5, 'pred_return_below_min': 1334, 'queued': 2}`
- Shadow routes: `{'continue_hold': 124, 'skip': 12291}`
- Shadow reasons: `{'continue_hold': 124, 'non_continue_hold_route': 12291}`
- Matched trade reasons: `{'TRAILING_STOP': 6}`

## Decision

`has_matched_shadow_route`: Read-only shadow evidence; promote only after enough matched live shadow routes and replay/stress evidence support the same route.
