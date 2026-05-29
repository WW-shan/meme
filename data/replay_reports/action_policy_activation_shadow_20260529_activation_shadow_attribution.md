# Action Policy Activation Shadow Report

Generated: `2026-05-29T10:35:00.728186+00:00`

Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Parameters

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Activation pct: `35.0`
- Release pct: `75.0`
- Stop loss pct: `-18.0`

## Summary

- Queued shadow-used matched trades: `6`
- Matched net profit BNB: `0.00012579707233376005`
- Activation hits: `3`
- Release hits: `2`
- Activated then stop: `1`
- Stop before activation: `0`
- Outcomes: `{'activated_released': 2, 'activated_then_stop': 1, 'never_activated_loss': 3}`
- Unemitted outcomes: `0`

## Decision

`mixed_activation_shadow_support`: Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
