# Expanded Flow Evidence Gate Round Plan

## Goal

Determine whether the flow quick-profit direction has enough complete support evidence to justify a later runtime/replay overlay, without touching live settings unless gates pass.

## Flow

1. Analysis
   - Verify clean worktree, no active task, no `docs/goals` changes.
   - Re-read prior May 22 summaries and current support/probe scripts.
   - Do local Codex analysis and get external Claude analysis because this is M complexity.

2. Implementation / Evidence Collection
   - If current tooling cannot score all candidates, add a default-safe way to emit all candidates from `probe_time_to_barrier`.
   - Test the behavior before relying on it.
   - Generate an expanded read-only time-to-barrier report using more lifecycle files.
   - Pool it with the prior complete-flow live report and run the existing support gate.

3. Decision
   - If pooled evidence passes: stop before live change and plan a replay-integrated overlay in this same task only if time and gates warrant it.
   - If pooled evidence fails: record `NO_GO_FOR_RUNTIME_OVERLAY`, with concrete counts and next direction.

4. Verification and Closure
   - Run focused tests and the full unittest suite.
   - Run local review and external Claude review for code/report changes.
   - Update `docs/research/` and `docs/model_scoreboard.md`; do not edit `docs/goals/**`.
   - Archive the task, force-add `.ccg` archive if ignored, commit, and push.
