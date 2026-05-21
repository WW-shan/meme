# Review

## Local Codex Review

### Scope Reviewed

- `src/pipeline/train_hybrid.py`
- `src/pipeline/model_replay.py`
- `scripts/run_active_flow_quick_profit_replay.py`
- `tests/model/test_low_volume_rescue_replay.py`
- `tests/model/test_model_replay.py`
- `tests/model/test_active_flow_quick_profit_replay_cli.py`
- `data/replay_reports/active_flow_quick_profit_replay_20260522_v95.json`
- `docs/research/20260522-active-flow-quick-profit-replay/summary.md`
- `docs/model_scoreboard.md`

### Findings

- Critical: none.
- Warning: none after review fixes.
- Info: `buy_quick_profit_overlay_min_total_buys` intentionally remains replay/default-off and is not added to `LIVE_RUNTIME_PARAM_KEYS`; no `.env` or live service wiring was changed.

### Verification

- TDD red check: new active-flow tests initially failed because `_run_eval_replay()` did not accept `buy_quick_profit_overlay_min_total_buys`, the new CLI script did not exist, `parse_args("--out")` reset output to the default, and the replay report lacked `safe_for_live_switch`.
- Focused tests after fixes: `venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_model_replay tests.model.test_active_flow_quick_profit_replay_cli tests.model.test_primary_score_scalp_replay_cli tests.model.test_ultrashort_runner_replay_cli` -> `96` tests OK.
- Full suite after fixes: `venv/bin/python -m unittest discover` -> `724` tests OK.
- `git diff --check` passed.
- `docs/goals/**` status and diffs are clean.

## External Claude Review

### Analysis Pass

External Claude analysis completed after a longer wait (about 220 seconds). Log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-29548.log`.

Key recommendations adopted:

- narrow this round to the active-flow count proxy only;
- add only `buy_quick_profit_overlay_min_total_buys`;
- defer overlap/reentry filters until missing-flow semantics match support-probe semantics;
- keep the replay grid to `min_total_buys in {6, 10, 14}`.

### Review Pass

External Claude review was given an extended wait. Log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-30025.log`.

Review findings before fixes:

- Critical: none.
- Warning: `scripts/run_active_flow_quick_profit_replay.py` reset argparse-abbreviated output flags like `--out` back to the script default.
- Info: add a positive-control boundary test for `total_buys >= floor`.
- Info: scoreboard said `safe_for_live_switch=false`, but the report artifact did not emit that field.

Actions taken:

- Added `_has_output_flag()` so abbreviated `--out` is respected when base argparse accepts it.
- Added positive-control coverage for the inclusive `total_buys` floor boundary.
- Added `safe_for_live_switch=false` to the script report and patched the generated report artifact.
- Re-ran focused and full tests after the fixes.

Note: the external Claude review process internally attempted a recursive Codex review despite the current project rule not to call external Codex. No further recursive result is used as an independent required gate; the actionable final Claude findings above were still reviewed and fixed locally.
