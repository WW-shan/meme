# Action Policy Activation Shadow Report

Generated: `2026-05-30T09:01:44.363607+00:00`

Contract: read-only activation-aware counterfactual evidence; `live_switch_evidence=false`; no live config changed.

## Parameters

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Activation pct: `45.0`
- Release pct: `75.0`
- Stop loss pct: `-18.0`

## Summary

- Queued shadow-used matched trades: `0`
- Matched net profit BNB: `0`
- Activation hits: `0`
- Release hits: `0`
- Activated then stop: `0`
- Stop before activation: `0`
- Outcomes: `{}`
- Unemitted outcomes: `0`

## Decision

`insufficient_activation_shadow_support`: Read-only activation-aware shadow attribution. Treat as live-alignment evidence only; runtime enablement still requires replay, stress, walk-forward, sufficient support, and live-switch review.
