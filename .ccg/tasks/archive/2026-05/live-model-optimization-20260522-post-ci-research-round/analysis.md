# Analysis

## Current State

- Latest commit after CI fix: `60a6fb4 ci: fix timezone-dependent test fixtures`.
- GitHub Actions CI for `60a6fb4` completed with `success`.
- Worktree was clean before this research task.
- A stale empty `.ccg/tasks/fix-github-actions-unittest` directory existed without `task.json`; it was removed as a non-task leftover before creating this task.
- Current active task: `.ccg/tasks/live-model-optimization-20260522-post-ci-research-round`.
- `docs/goals/**` guard is clean.
- `.ccg/spec/` is absent.
- Bot is running, PID `2100`, uptime about `11h`.
- Collector is running, PID `2281`, uptime about `11h`.
- `data/paper_trades.jsonl` has no newer close after `2026-05-21 20:42:26` (`币安队长`, `TIME_EXIT`, net `-0.000030418340289465923` BNB).
- `data/signal_audit.jsonl` is live through at least `2026-05-22 09:20:16` with new rejected decisions.

## Where The Research Stopped

Recent completed rounds:

- `live-model-optimization-20260522-live-attribution-refresh`
  - Rebuilt live attribution from raw `paper_trades` and lifecycle files.
  - Closed real trades since restart anchor: `18`.
  - Wins/losses: `2/16`.
  - Net: `-0.001256566334920428` BNB.
  - Dominant failure: near-threshold `dead_flow_timeout` (`6` of `8` near trades).
  - Decision: `NO_GO_FOR_LIVE_SWITCH`.

- `live-model-optimization-20260522-expanded-flow-evidence`
  - Expanded all-candidate rejected-signal barrier report from `2026-05-21 00:00:00`.
  - `832` per-token candidates, `156` positives, `676` skips.
  - Pooled support gate failed with `decision=missing_flow_feature_parity`.
  - Post-hoc active-flow diagnostic looked better (`38` selected, `23` positives, `60.53%` precision) but was not live-switch evidence.
  - Decision: `NO_GO_FOR_RUNTIME_OVERLAY`.

- `live-model-optimization-20260522-active-flow-replay`
  - Tested replay-integrated active-flow quick-profit proxy.
  - Validation profit rose, but trades expanded from `32` to `136`, win rate fell, walk-forward/stress degraded.
  - Final confirmation also failed with trade expansion and worse stress.
  - Decision: `NO_GO_FOR_LIVE_SWITCH`.

- `live-model-optimization-20260522-conditional-dead-flow-exit-replay`
  - Tested dead-flow early exit grid.
  - Best validation improvement was too small and failed stress/materiality.
  - Final selected candidate had no dead-flow activity and failed gates.
  - Decision: `NO_GO_FOR_LIVE_SWITCH`.

## Local Interpretation

Direct live/runtime changes remain unjustified. The two strongest prior hypotheses were already falsified under replay gates:

- active-flow quick-profit rescue: too many extra trades and worse robustness;
- dead-flow early exit: too weak and not active on final.

Since there are no newer closed real trades, a fresh live-trade attribution refresh would not add much. The current new evidence is in rejected signal decisions after the previous reports. The lowest-risk next move is a read-only refresh of the latest rejected-signal barrier/flow report and support gate, using all emitted candidates so support counts are not sample-limited.

## Proposed Experiment

Run a fresh current-day read-only rejected-signal probe:

1. `probe_time_to_barrier.py` with `--since "2026-05-22 00:00:00"` and `--max-candidate-sample 0`.
2. Feed that output into `probe_support_action_policy.py`.
3. Optionally pool it with the existing expanded `2026-05-21` all-candidate report using `probe_support_action_policy_pool.py`.

Acceptance logic:

- This can produce research direction evidence only, not direct live-switch evidence.
- A live switch remains rejected unless a replay-integrated, pre-registered candidate later passes validation, final confirmation, walk-forward, and stress gates.

## External Claude Analysis

Claude agrees the rejected-signal refresh is safe and useful, but says it is low-value as the only experiment because previous rounds already showed rejected-signal support does not translate directly into live PnL. Claude recommends adding a read-only forensic pass on the actual losing live trades.

Pre-registered criteria for rejected-signal refresh:

- 2026-05-22-only candidate count >= `150`.
- Active-flow rule precision >= `55%` on the 2026-05-22-only slice.
- Pooled precision with the existing 2026-05-21 expanded report >= `58%` and not worse than the prior pooled/diagnostic baseline.
- Flow parity gate must pass on the new slice.
- If any miss, freeze this research direction instead of retrying the same rejected-signal support loop again.

Live-trade forensic pass:

- Output per-trade loss table only.
- Use it to generate hypotheses for a future pre-registered replay-integrated round.
- It is not live-switch evidence.

Decision for this round is pre-registered as `NO_GO_FOR_LIVE_SWITCH` regardless of read-only result, because neither experiment is a replay-integrated validation/final/walk-forward/stress gate.

## Experiment Result

The current-day rejected-signal refresh wrote:

- `data/replay_reports/time_to_barrier_probe_20260522_post_ci_current_day_all_candidates.json`
- `data/replay_reports/support_action_policy_20260522_post_ci_current_day.json`
- `data/replay_reports/support_action_policy_pool_20260522_post_ci_current_plus_expanded.json`

Result:

- Current-day candidates: `66`, below the pre-registered `150` support floor.
- Current-day best eligible rule: `high_prob_low_toxic_overlap`, selected `7`, positives `4`, precision `57.14%`; this is too small for action and fails by support insufficiency.
- Pooled target flow rule: selected `142`, positives `68`, precision `47.89%`, below the `58%` target.
- Pooled flow parity failed again with `decision=missing_flow_feature_parity`.

The live-loss forensic view is recorded in `docs/research/20260522-post-ci-research-round/summary.md`.
Loss-only evidence since the v95 restart:

- Losses: `16`.
- Loss-only net: `-0.0016679114065155773` BNB.
- Largest buckets: `dead_flow_timeout=7`, `mfe_then_giveback=3`, `entry_slippage_failure=2`.

Conclusion: `NO_GO_FOR_LIVE_SWITCH`. The rejected-signal flow-support loop should be frozen for now. The next useful research directions are replay-integrated tests for high-positive-slippage entry veto/protection and a giveback guard for trades that reach `+25%` MFE before later closing at STOP_LOSS.

Review note: future pre-registration must name the exact target active-flow rule string; this round used `high_prob_low_toxic_overlap` as the target pooled rule.
