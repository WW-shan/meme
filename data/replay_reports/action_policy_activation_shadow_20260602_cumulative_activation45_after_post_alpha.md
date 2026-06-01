# Action Policy Activation Shadow Report

Generated: `2026-06-01T17:38:37.378259+00:00`

Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Parameters

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Activation pct: `35.0`
- Release pct: `75.0`
- Stop loss pct: `-18.0`
- Runtime params: `{'buy_threshold': 0.98, 'min_entry_score': 35.0, 'min_entry_volume_30s': 1.5, 'min_entry_price_volatility': 0.1, 'buy_near_threshold_min_prob': 0.94, 'buy_near_min_pred_return': 32.0, 'buy_near_min_entry_volume_30s': 1.25, 'buy_near_min_entry_price_volatility': 0.08, 'buy_near_min_age_seconds': 0.0}`

## Summary

- Queued shadow-used matched trades: `13`
- Matched net profit BNB: `-1.0049028392099149e-05`
- Activation hits: `2`
- Release hits: `1`
- Activated then stop: `0`
- Stop before activation: `0`
- Outcomes: `{'activated_profitable_no_release': 1, 'activated_released': 1, 'never_activated_loss': 10, 'never_activated_win': 1}`
- Unemitted outcomes: `0`

## Decision

`activation_shadow_support`: Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
