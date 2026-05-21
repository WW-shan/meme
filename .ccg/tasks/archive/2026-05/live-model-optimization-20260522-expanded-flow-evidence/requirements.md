# Requirements

## User Workflow Contract

- This is one full business/research/experiment/cutover round, not a micro task.
- Do not open another CCG task while this one is active.
- Before ending the round, explicitly finish the loop: analysis, plan, implementation/probe, review, verification, research report, scoreboard update, archive, commit, push.
- Do not edit `docs/goals/**` in this round.
- Do not change `.env`, live services, position sizing, or model artifacts unless replay evidence passes the documented live-switch gates.

## Current Objective

Continue optimizing the active v95 model/live-trading stack toward better real-money performance. The previous round rejected both a static entry-slippage veto and a flow quick-profit runtime overlay because the support evidence was too small and flow fields were incomplete.

## This Round's Hypothesis

Before another runtime overlay, collect a larger and more complete rejected-signal support set. The immediate falsifiable question is whether the existing `high_prob_low_toxic_overlap` flow rule still fails once `time_to_barrier` evidence can emit all candidates rather than only the first 100 sample rows.

## Gates

- Evidence-only reports remain `live_switch_evidence=false` and `safe_for_live_switch=false`.
- A runtime/replay overlay is allowed only if the expanded pooled support gate passes pre-registered support and flow parity checks.
- If the gate fails, stop the round as `NO_GO`, document the reason, and archive/commit/push.
