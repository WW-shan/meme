# Review

## Result

- No live switch.
- No model artifact change.
- No trading config change.
- Current dead-flow support gate remains `NO_GO_FOR_DEAD_FLOW_RULE`.
- Integrated feasibility gate remains `NO_GO_FOR_LIVE_RULE`.

## Evidence

- Dead-flow support report:
  - train positives: `0`
  - validation positives: `0`
  - final positives: `0`
  - live matched positives: `7`
  - live recall: `7/7`
  - source scope: `existing_post_target_replay_reports_only`
- The live shape is real, but the frozen post-target replay reports do not provide a deployable replay-equivalent dead-flow support row.
- The result is diagnostic only; the next useful node is a lifecycle replay surface for dead-flow candidates, not a live rule.

## Codex Local Review

- Critical: none.
- Warning fixed: future passing dead-flow diagnostics no longer produce a contradictory no-support `go_no_go.reason`.
- Warning fixed: support report now documents source scope and live/replay sell-pressure parity caveat.
- Warning fixed: live shape matches are separated from dead-flow-label recall.
- Warning fixed: malformed passing dead-flow support reports cannot pass feasibility integration if required counts are missing.
- Warning fixed: new CLI now mirrors the protected exact path guard used by the sibling feasibility CLI.

## Claude Review

- Session: `f3cb4ce7-457f-4bc0-8086-9e4f7b8fe3fe`
- Critical: none.
- Warnings:
  - Document live/replay sell-pressure parity caveat.
  - Separate live shape-matched rows from label-filtered recall.
  - Harden missing-key handling for supplied dead-flow support gates.
  - Align protected path checks between the two CLIs.
- All actionable warnings were fixed.

## Verification

```bash
venv/bin/python -m unittest tests.model.test_dead_flow_timeout_probe tests.model.test_dead_flow_timeout_probe_cli tests.model.test_conditional_exit_feasibility_probe tests.model.test_conditional_exit_feasibility_probe_cli
venv/bin/python scripts/probe_dead_flow_timeout_support.py --force
venv/bin/python scripts/probe_conditional_exit_feasibility.py --force
venv/bin/python -m unittest discover -q
python -m json.tool .ccg/tasks/live-model-optimization-20260522-dead-flow-support/task.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/dead-flow-support.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json >/dev/null
test -s docs/research/20260521-conditional-exit-flow-state/dead-flow-support.md
test -s docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Observed:

- Focused probe tests: `16` tests, `OK`.
- Full project tests: `696` tests, `OK`.
- `docs/goals/` checks produced no output.
