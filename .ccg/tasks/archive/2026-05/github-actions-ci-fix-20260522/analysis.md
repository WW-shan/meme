# Analysis

## Current State

- Active branch: `main`.
- Latest commit before this CI task: `b40655c research: reject dead flow exit replay`.
- Worktree was clean before task creation.
- No active non-archive CCG task existed before this task.
- Bot and collector are running; this task does not change live services.

## GitHub Actions Failure

Latest failed run:

- Workflow: `CI`
- Event: `push`
- Branch: `main`
- Commit: `b40655ccf3575244582f4a33d116576b95ad6997`
- Run: `https://github.com/WW-shan/meme/actions/runs/26261566877`
- Job: `Python unittest`
- Failing step: `Run tests`
- Command: `python -m unittest discover`

CI failure summary:

- `tests.model.test_time_to_barrier_probe` expected causal flow fields such as `flow_buy_volume_10s` but got `0.0`.
- `tests.model.test_time_to_barrier_probe` expected class counts such as `fast_profit_then_collapse`, but the class was missing.
- `tests.model.test_low_volume_breakout_probe` expected `low_volume_runner`, but the class was missing.
- `tests.model.test_post_target_exit_state_probe` expected post-target classes but saw `target_not_hit` / missing counts.
- `tests.model.test_reentry_probe` expected accepted stop-loss reentry count `1` but got `0`.

## Root Cause

These failures reproduce locally when forcing the process timezone to UTC:

```bash
TZ=UTC python -m unittest tests.model.test_time_to_barrier_probe.TestTimeToBarrierProbe.test_score_signal_adds_causal_signal_time_flow_fields_from_lifecycle -v
TZ=UTC python -m unittest tests.model.test_time_to_barrier_probe.TestTimeToBarrierProbe.test_build_probe_report_passes_lifecycle_to_signal_flow_scoring -v
TZ=UTC python -m unittest tests.model.test_post_target_exit_state_probe.TestPostTargetExitStateProbe.test_uses_lifecycle_path_and_reports_post_target_window_returns_and_flow -v
```

The failing tests build synthetic lifecycle timestamps with `naive_datetime.timestamp()`. That call interprets a naive datetime in the process local timezone. On the dev machine the local timezone is Asia/Shanghai, matching `reentry_probe.ANALYSIS_TZ`. On GitHub Actions the runner timezone is UTC, so the synthetic timestamps are shifted by eight hours when `parse_time()` converts numeric epoch values back into the analysis timezone. The price/flow points therefore land outside the expected window and the probes classify them as missing/target-not-hit/zero-flow.

This is a deterministic test fixture timezone bug, not a model/runtime cutover issue.

## Candidate Fixes

1. Recommended: add a small test helper that converts naive fixture datetimes to epoch seconds using `reentry_probe.ANALYSIS_TZ`, then update the affected tests to use it.
   - Pro: preserves production `parse_time()` semantics for real epoch timestamps.
   - Pro: directly fixes the fragile fixtures causing CI failure.
   - Con: touches several test files.

2. Alternative: change `reentry_probe.parse_time()` numeric timestamp handling to use the process local timezone.
   - Pro: fewer test edits.
   - Con: makes production timestamp parsing depend on runner host timezone; this is unsafe for replay/research reproducibility.

Recommendation: use option 1.
