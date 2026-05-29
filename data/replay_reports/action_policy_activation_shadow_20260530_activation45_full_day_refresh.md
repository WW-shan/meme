# Action Policy Activation Shadow Report

Generated: `2026-05-29T17:12:02.541578+00:00`

Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Parameters

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Activation pct: `45.0`
- Release pct: `75.0`
- Stop loss pct: `-18.0`

## Summary

- Queued shadow-used matched trades: `7`
- Matched net profit BNB: `0.00010067417568420197`
- Activation hits: `2`
- Release hits: `2`
- Activated then stop: `0`
- Stop before activation: `0`
- Outcomes: `{'activated_released': 2, 'never_activated_loss': 5}`
- Unemitted outcomes: `0`

## Decision

`activation_shadow_support`: Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
