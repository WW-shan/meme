# Requirements

## User Workflow Contract

- This is one full business/research/experiment/cutover round, not a micro task.
- Do not open another CCG task while this one is active.
- Complete the loop before ending the round: analysis, plan, implementation/evidence, review, verification, research report, scoreboard update, archive, commit, push.
- Give external Claude enough time; do not treat a slow response as a failed round, and do not open a new task while waiting.
- Do not edit `docs/goals/**` in this round.
- Do not change `.env`, live services, position sizing, or model artifacts unless strict replay/live-switch gates pass.

## Current Objective

Continue optimizing the v95 live-trading stack toward real-money profitability by grounding the next experiment in the newest live trade outcomes and current live state.

## This Round's Hypothesis

Recent real trades after the previous conditional-exit attribution window added more timeout/stop/slippage losses. Before another replay rule, create or refresh a reproducible read-only live trade attribution artifact that classifies real v95 trades into failure buckets and identifies which bucket has enough live support to justify the next replay-integrated experiment.

## Gates

- Evidence-only reports remain `live_switch_evidence=false` and `safe_for_live_switch=false`.
- No live switch, `.env` change, restart, or position sizing change is allowed from attribution alone.
- If live/support evidence is insufficient for a replay-integrated rule, stop as `NO_GO_FOR_LIVE_SWITCH` and document the next most defensible research direction.
