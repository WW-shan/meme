# Review - 2026-05-22

## Critical

None.

## Warning

- `scripts/run_entry_slippage_risk_veto_replay.py` full 64-candidate replay is too slow for a practical live loop in this workspace. I added `--max-candidates` so bounded diagnostic runs can finish and produce evidence, but the default full sweep was not completed.
- External Claude review did not produce a usable final finding set. First attempt drifted into a forbidden external Codex call and was terminated. Second attempt stayed within Claude but did not return final findings after several minutes and was terminated. Treat this as an external-review tooling gap, not as a Claude approval.

## Info

- `src/pipeline/train_hybrid.py` correctly adds a default-off `entry_slippage_risk_veto` branch and threads the new params through runtime, stress, and walk-forward replay paths.
- Focused unit tests and adjacent replay tests pass.
- Full test suite passes: `venv/bin/python -m unittest discover` ran `711` tests with `OK`.
- `git diff --check` passes.
- Diagnostic probes show the planned sweep is a NO-GO for live use:
  - strict planned grid: no veto rejects, no profit improvement;
  - very loose trigger: veto triggers but profit and drawdown worsen;
  - targeted mid sweep: still loses profit and/or trade quality.
- Human-readable effect reports were written to `docs/research/20260522-entry-slippage-risk-veto/summary.md` and `docs/model_scoreboard.md`; `context.jsonl` remains an index only.

## Local Codex Review Notes

- Default-off behavior is preserved: all seven `buy_entry_slippage_risk_veto_*` params must be present before the veto can run.
- The veto uses causal replay sample fields only: current and prior episode prices within the configured lookback window, candidate age, `volume_30s`, and `price_volatility`.
- The new price-extension helper keeps late-pump and entry-slippage windows separate, which avoids coupling the new experiment to the existing late-pump veto.
- CLI live-risk controls are constrained by argument validation: 10% position fraction, 10% max position fraction, and max 8 open positions.
- Acceptance gates require profit improvement, no drawdown regression, win-rate discipline, walk-forward/stress robustness, trade-count discipline, and `entry_slippage_risk_veto_reject_count > 0`.

---

# Review - Flow Quick-Profit Pooled Support Gate

Timestamp: `2026-05-22T05:03:55+08:00`

## Critical

None.

## Warning

- The pooled flow-aware support branch is explicitly `NO_GO_FOR_RUNTIME_OVERLAY`: target support is only `13` selected and `9` positives, below the pre-registered `30/12` gate, and required flow fields are not complete. Tasks 2-4 must remain unimplemented in this round.

## Info

- Added `build_pooled_support_report` to `src/pipeline/support_action_policy_probe.py` as a read-only, ex-post-label support report. It does not change live logic, replay entry logic, model artifacts, `.env`, or position sizing.
- Added `scripts/probe_support_action_policy_pool.py` to combine multiple time-to-barrier reports and write only under `data/replay_reports/`.
- Added pooled support tests and CLI tests. RED was observed first for the missing function and missing CLI.
- Local review found and fixed a path-safety issue: the pooled CLI now refuses output paths that match any input report, including with `--force`.
- Generated `data/replay_reports/support_action_policy_pool_20260522_flow.json`; decision is `missing_flow_feature_parity`.
- Wrote human-readable report `docs/research/20260522-flow-quick-profit-overlay/summary.md` and scoreboard entry in `docs/model_scoreboard.md`.

## Verification

- `venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_pool_cli` -> `21` tests `OK`.
- `venv/bin/python -m unittest tests.model.test_support_action_policy_pool_cli tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_probe_cli` -> `25` tests `OK`.
- `venv/bin/python -m unittest discover` -> `711` tests `OK`.
- `git diff --check` -> pass.
- `jq empty .ccg/tasks/live-model-optimization-business-round-20260522/task.json` -> pass.
- `context.jsonl` JSONL parse check -> pass.
- `docs/goals` worktree, diff, and cached diff checks -> clean.

## Claude Review

Log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-26884.log`

Critical:

- None.

Major findings and fixes:

- Duplicate `currentPhase` keys in `task.json`: fixed by removing the stale `"implementation"` key and keeping `"review"`.
- Stale first review block test count `704`: fixed to `711`.

Minor findings handled:

- Added coverage for the `diagnostic_only_small_sample` pooled-report decision branch.
- Kept the CLI dual output-safety check; `test_main_refuses_to_overwrite_any_input_report_with_force` proves output cannot overwrite non-first inputs.

Claude summary:

- No critical findings.
- The pooled-support gate is read-only, path-safe, and correctly stops before runtime overlay Tasks 2-4.
- The earlier entry-slippage branch is a default-off replay experiment with no archive blocker.
