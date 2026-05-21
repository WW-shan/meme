# Active-Flow Quick-Profit Replay Round Plan

## Goal

Test whether a default-off quick-profit overlay with active-flow proxy filters can improve v95 live-sized replay without over-expanding trades or degrading risk.

## Flow

1. Analysis
   - Verify clean worktree, no active task, no `docs/goals` changes.
   - Re-read prior May 22 flow evidence and current replay/runtime quick-profit overlay code.
   - Complete local Codex analysis and wait longer for external Claude analysis.

2. TDD / Implementation
   - Add focused tests first for optional active-flow quick-profit filters.
   - Implement the minimal `train_hybrid` optional parameters while preserving default behavior.
   - Add a bounded replay script that passes active-flow overlay params into the existing v95 replay harness.

3. Evidence Collection
   - Run focused tests.
   - Run bounded validation/final replay with 10% sizing and strict max 8 positions.
   - Save the replay report under `data/replay_reports/`.

4. Decision
   - If gates pass: document replay evidence and stop before any live switch unless explicit live-change permission is given.
   - If gates fail: record `NO_GO_FOR_LIVE_SWITCH` with concrete validation/final/walk-forward/stress reasons.

5. Verification and Closure
   - Run focused tests, `git diff --check`, and full `python -m unittest discover` if feasible.
   - Run local review and external Claude review with a longer wait.
   - Update `docs/research/` and `docs/model_scoreboard.md`; do not edit `docs/goals/**`.
   - Archive the task, force-add ignored `.ccg` archive if needed, commit, and push.
