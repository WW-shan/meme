# Review Notes

## Result

- No critical issues.
- No live-switch evidence was found.
- The no-go decision is supported by validation scarcity.

## Addressed Review Items

- Added explicit bucket definitions to `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json`.
- Added a leakage clause to `docs/research/20260521-conditional-exit-flow-state/summary.md`.
- Annotated `gemini-analysis.md` as a failed backend run.
- Added a near-threshold split to `live_attribution.json` for sharper attribution.

## Verification

```bash
python scripts/probe_conditional_exit_feasibility.py --force
venv/bin/python -m unittest tests.model.test_conditional_exit_feasibility_probe tests.model.test_conditional_exit_feasibility_probe_cli
venv/bin/python -m unittest discover -q
python -m json.tool .ccg/tasks/live-model-optimization-20260521-conditional-exit/task.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/live_attribution.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json >/dev/null
test -s docs/research/20260521-conditional-exit-flow-state/summary.md
test -s docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

## Review Sources

- Claude reviewer: request changes, non-blocking.
- Gemini reviewer: failed locally because `gemini` is not on `PATH`; this predates the current CCG rule that disables Gemini usage.
- `python -m unittest discover -q` with system Python failed because `web3` is not installed in that interpreter.
- `venv/bin/python -m unittest discover -q` passed 685 tests with one skipped test in the project runtime environment.
- Reproducible feasibility probe now exists at `scripts/probe_conditional_exit_feasibility.py` and successfully regenerated `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json` and `11-exit-state-attribution.md` with `support_gate=NO_GO_FOR_LIVE_RULE`.
- No live switch. No replay implementation. Continue collecting live labels or design a read-only probe for `dead_flow_timeout` support.
