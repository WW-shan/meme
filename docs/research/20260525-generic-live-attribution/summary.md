# Generic Live Attribution Refresh

Date: 2026-05-25

## Decision

No live switch. Keep `data/models/20260519_v95_v84_selective_nearmiss_gate`, current thresholds, 10% sizing, `.env`, model artifacts, and running bot unchanged.

This round upgraded the live attribution tooling so future rounds can analyze real trades and rejected signals without hard-coded output roots, token names, or one-off windows. The new report is diagnostic only: `live_switch_evidence=false` and `safe_for_live_switch=false`.

`docs/model_scoreboard.md` was updated with the no-switch result.

## Attribution Report

Report:

- `data/replay_reports/live_trade_attribution_20260525_generic.json`
- `data/replay_reports/live_trade_attribution_20260525_generic.md`

Scope:

- `paper_trades`: `data/paper_trades.jsonl`
- `signal_audit`: `data/signal_audit.jsonl`
- `since`: `2026-05-19 04:02:23`
- `until`: `2026-05-25 13:25:41`
- `active_model`: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- `recent_lifecycle_files=3`

Live trade attribution since the v95 restart:

- closed trades: `27`
- wins/losses: `5/22`
- net profit: `-0.00129134586789572` BNB
- failure labels: `dead_flow_timeout=9`, `entry_slippage_failure=2`, `mfe_then_giveback=1`, `profitable_exit=5`, `stop_first_after_entry=4`, `unprofitable_other=6`
- lifecycle price paths: `12/27`, with `15` missing paths
- near-threshold trades: `12`, all `dead_flow_timeout` or `unprofitable_other`, net `-0.0004773102883302226` BNB

Rejected signal path attribution:

- signal decisions: `90459`
- per-token candidates: `3734`
- classes: `fast_profit=130`, `fast_profit_then_collapse=162`, `slow_runner=38`, `flat_timeout=1273`, `stop_first=339`, `missing_path=1792`
- policies: `quick_take_profit=292`, `conditional_slow_hold=38`, `skip=3404`

Ranked directions from the generic report:

1. `stop_first_after_entry`: highest live loss bucket (`4` trades, `-0.0007549268195000331` BNB) but below the same-shape support threshold.
2. `entry_slippage_failure`: only `2` loss trades and below support threshold.
3. `dead_flow_timeout`: `9` trades and enough same-shape count, but the static dead-flow exit replay was already rejected on 2026-05-22.
4. rejected-signal quick-take-profit paths: many candidates, but still require feature separation and replay.

## Experiment

To avoid promoting a hard-coded quick-TP rule, this round reran generic rejected-signal probes over the same live window:

```bash
python scripts/probe_time_to_barrier.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 3 \
  --since '2026-05-19 04:02:23' \
  --until '2026-05-25 13:25:41' \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260525_generic_since_restart.json

python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260525_generic_since_restart.json \
  --output data/replay_reports/support_action_policy_20260525_generic_since_restart.json \
  --min-selected 7 \
  --force
```

TTB result:

- per-token candidates: `3734`
- policies: `quick_take_profit=292`, `conditional_slow_hold=38`, `skip=3404`

Support rule result:

- total positive candidates: `330`
- total negative candidates: `3404`
- best built-in rule was `high_prob_low_toxic_overlap`: `283` selected, `107` positive, `176` negative, precision `37.8092%`
- `young_high_prob_clean_flow`: `110` selected, `33` positive, `77` negative, precision `30.0000%`
- `v95_like_pred_rescue`: `23` selected, only `2` positive, precision `8.6957%`

## Interpretation

The live report surfaces real opportunities, but the static decision-time rules still do not separate runners cleanly enough:

- `dead_flow_timeout` has enough live count, but the previous static replay failed; rerunning that unchanged would be circular.
- `stop_first_after_entry` and `entry_slippage_failure` have larger loss impact but too few same-shape live examples for a replay-directed change.
- rejected quick-TP opportunities are numerous, but the best current built-in decision-time rule still admits too many negative candidates.

The next model-improvement direction should be a learned candidate-level segment/meta-label probe over rejected and accepted signal candidates, with purged validation, risk/coverage reporting, and strict live-sized replay. It should mine decision-time features generically instead of using token names, fixed time windows, or hand-picked static thresholds.

No live configuration change is justified from this round.

## Round Step Closeout

- Startup/health check: completed earlier in the active goal round; no live switch or restart was performed in this node.
- Live attribution: completed with `data/replay_reports/live_trade_attribution_20260525_generic.json`.
- Prior experiment review: completed against `docs/model_scoreboard.md`; static dead-flow, quick-TP, broad path-state, global threshold, and static support-rule directions remain rejected.
- SmartSearch Deep Research: skipped only for this round by explicit user instruction in the current session; no external research evidence is used to justify this no-switch decision. The next round must run or explicitly record SmartSearch Deep Research before selecting its experiment direction.
- Direction selection: completed; strongest next direction is learned candidate-level segment/meta-labeling over accepted and rejected candidates.
- Hypothesis/experiment: completed as a falsification of static support rules over the fixed live window.
- Scoreboard/research update: completed; `docs/model_scoreboard.md` was updated.
- Live switch handling: completed as `NO_GO_FOR_LIVE_SWITCH`; `.env`, thresholds, sizing, model artifacts, and bot process are unchanged.
- Review/verification: completed with two Codex self-review passes after the final code/report edit, targeted tests, `git diff --check`, and full unittest discovery.

## Verification

- `python -m unittest tests.model.test_live_trade_attribution_probe tests.model.test_live_trade_attribution_probe_cli tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_probe_cli` -> 67 tests OK.
- `git diff --check` -> OK.
- `python -m unittest discover` -> 781 tests OK, 1 skipped.
