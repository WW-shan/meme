# Action Policy Activation Shadow Report

Generated: `2026-06-07T08:56:56.248816+00:00`

Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Parameters

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Activation pct: `35.0`
- Release pct: `75.0`
- Stop loss pct: `-18.0`
- Runtime params: `{'buy_threshold': 0.98, 'min_entry_score': 35.0, 'min_entry_volume_30s': 1.5, 'min_entry_price_volatility': 0.1, 'buy_near_threshold_min_prob': 0.94, 'buy_near_min_pred_return': 32.0, 'buy_near_min_entry_volume_30s': 1.25, 'buy_near_min_entry_price_volatility': 0.08, 'buy_near_min_age_seconds': 0.0}`

## Summary

- Queued shadow-used matched trades: `1`
- Matched net profit BNB: `5.553972801680855e-05`
- Activation hits: `1`
- Release hits: `0`
- Activated then stop: `0`
- Stop before activation: `0`
- Outcomes: `{'activated_profitable_no_release': 1}`
- Unemitted outcomes: `0`

## Decision

`insufficient_activation_shadow_support`: Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
