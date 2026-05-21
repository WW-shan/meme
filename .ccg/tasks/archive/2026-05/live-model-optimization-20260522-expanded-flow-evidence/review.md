# Review

## Local Codex Review

### Scope Reviewed

- `src/pipeline/time_to_barrier_probe.py`
- `scripts/probe_time_to_barrier.py`
- `tests/model/test_time_to_barrier_probe.py`
- `tests/model/test_time_to_barrier_probe_cli.py`
- `docs/research/20260522-expanded-flow-evidence-gate/summary.md`
- `docs/model_scoreboard.md`
- New replay report JSON artifacts under `data/replay_reports/`

### Findings

- Critical: none.
- Warning: none.
- Info: `--max-candidate-sample 0` can create larger report JSONs by design; this is explicit and default behavior remains capped at `100`.

### Verification

- Focused tests: `venv/bin/python -m unittest tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_pool_cli` -> `46` tests OK after review fixes.
- Full suite: `venv/bin/python -m unittest discover` -> `716` tests OK after review fixes.
- `git diff --check` passed.
- `docs/goals/**` status and diffs are clean.

## External Claude Review

Initial Claude analysis call hit repeated API `504 server_error` responses; review retry completed below.

### Claude Review Retry

Command log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-29103.log`.

Claude review returned no Critical findings. Warnings were test/readability gaps:

- add library and CLI coverage for negative `max_candidate_sample`;
- add explicit small non-zero sample limit coverage;
- cast `max_candidate_sample` once and reuse it;
- note additive report schema drift for archived consumers.

Actions taken:

- Added `test_build_probe_report_honors_explicit_candidate_sample_limit`.
- Added `test_build_probe_report_rejects_negative_candidate_sample_limit`.
- Added `test_parse_args_rejects_negative_candidate_sample_limit`.
- Changed `build_probe_report()` to cast `max_candidate_sample` once via `candidate_sample_limit`.
- Research summary and task analysis explicitly document the new optional report fields and default compatibility.
