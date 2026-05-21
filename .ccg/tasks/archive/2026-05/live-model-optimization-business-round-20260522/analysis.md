# Business Round Analysis - 2026-05-22

## Current Live State

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- `.env` has `ENABLE_TRADING=true`.
- `bot` and `collector` are running under `tools/memectl`.
- `data/bot_state.json` has no open positions.
- Latest 2026-05-22 signal decisions are mostly rejects for `pred_return_below_min`, `entry_volume_30s_below_min`, and `near_threshold_pred_return_below_min`.
- No new clear missed-runner or new failure shape was found in the latest signal audit tail.

## Existing No-Go Evidence

`docs/research/20260521-conditional-exit-flow-state/summary.md` remains decisive for exit-rule ideas:

- `post_target_collapse_or_live_mfe_giveback`: train `5`, validation `0`, final `4`, live `3`, so validation support is missing.
- `dead_flow_timeout`: live `7`, but replay train/validation/final support is `0`.
- Result: `NO_GO_FOR_LIVE_RULE`. Do not change live exit logic from this node.

## Execution Calibration Check

Command:

```bash
python scripts/calibrate_execution_costs.py --since '2026-05-19 04:02:23'
```

Key result:

- `open_count=18`
- `post_fill_protection_exit_count=2`
- `protection_skip_count=2`
- `observed_entry_execution_failure_rate=0.18181818181818182`
- `p95_positive_entry_slippage_pct=0.13988759185875`
- recommended `entry_price_protection_pct=0.15988759185874998`

This supports researching entry execution and slippage risk, but the sample is too small to justify a live parameter change.

## Entry Protection Replay Sweep

Validation sweep over `entry_price_protection_pct`:

| pct | trades | skip count | net profit BNB | net return | win rate | max DD | WF worst return | stress worst return | rolling |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `0.05` | `27` | `14` | `0.01613373` | `269.0492%` | `85.1852%` | `-31.5133%` | `58.8561%` | `69.1161%` | fail |
| `0.08` | `32` | `0` | `0.01926804` | `321.3175%` | `81.25%` | `-31.5133%` | `63.5561%` | `154.7870%` | fail |
| `0.10` | `32` | `0` | `0.01926804` | `321.3175%` | `81.25%` | `-31.5133%` | `63.5561%` | `151.4379%` | fail |
| `0.12` | `32` | `0` | `0.01926804` | `321.3175%` | `81.25%` | `-31.5133%` | `63.5561%` | `175.1885%` | fail |
| `0.16` | `32` | `0` | `0.01926804` | `321.3175%` | `81.25%` | `-31.5133%` | `63.5561%` | `185.9775%` | fail |
| `0.25` | `32` | `0` | `0.01926804` | `321.3175%` | `81.25%` | `-31.5133%` | `63.5561%` | `221.3099%` | fail |

Decision:

- Do not change `entry_price_protection_pct`.
- `0.08` through `0.25` have no validation main-scenario separation.
- `0.05` is active but cuts profit and stress robustness.
- The direct parameter path is `NO_GO` for this round.

## External Claude Second View

Claude agreed that a live change is not justified and warned against using the 18-trade calibration percentile as a deployable rule. It recommended a falsifiable protection sweep; the local sweep above rejects simple protection tuning.

## Next Action

Plan a default-off replay-only candidate-level `entry_slippage_risk_veto` rather than another global parameter sweep.

Minimum design requirements:

- Keep v95 primary and near-threshold candidate generation unchanged.
- Use only causal pre-entry fields available at signal time.
- Candidate features should focus on pre-entry extension, drawdown from recent peak, recent price jump, volume/volatility ramp, probability and PredReturn deltas, and live fill-lag exposure.
- Output must include validation and final replay, walk-forward, stress replay, drawdown, trade-count discipline, and evidence that at least one risky candidate is actually rejected.
- No `.env`, `data/models/**`, or `docs/goals/**` change is allowed before replay gates pass.

## Entry Slippage Risk Veto Implementation Evidence

Files added/changed for the default-off replay branch:

- `src/pipeline/train_hybrid.py`
- `scripts/run_entry_slippage_risk_veto_replay.py`
- `tests/model/test_entry_slippage_risk_veto.py`
- `tests/model/test_entry_slippage_risk_veto_replay_cli.py`

Focused RED/GREEN result:

```bash
venv/bin/python -m unittest tests.model.test_entry_slippage_risk_veto tests.model.test_entry_slippage_risk_veto_replay_cli
```

Result: `OK` after implementation.

Adjacent regression check:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_veto tests.model.test_late_pump_exhaustion_replay_cli tests.model.test_conditional_volume_pump_risk_replay_cli
```

Result: `OK`.

Full 64-candidate replay command was attempted:

```bash
venv/bin/python scripts/run_entry_slippage_risk_veto_replay.py --output data/replay_reports/entry_slippage_risk_veto_replay_20260522_v95.json
```

It ran for about 30 minutes with high CPU and no final report. Per plan runtime guard, it was stopped and replaced with bounded diagnostic probes.

Limited 8-candidate report:

- Path: `data/replay_reports/entry_slippage_risk_veto_replay_20260522_v95_limited8.json`
- Decision: `reject`
- Candidate count: `8`
- Baseline validation: `32` trades, `0.016149475023616806` BNB net profit, `-31.769381949238507%` max drawdown, `81.25%` win rate.
- Best limited candidate was identical to baseline and had `entry_slippage_risk_veto_reject_count=0`.
- Failed gates: `net_profit_bnb`, `entry_slippage_risk_veto_reject_count`.

Single `drawdown=0.0` probe:

- Path: `data/replay_reports/entry_slippage_risk_veto_probe_drawdown0_20260522_v95.json`
- Result: `0` veto rejects, unchanged profit/trades/drawdown.
- Failed gates: `net_profit_bnb`, `entry_slippage_risk_veto_reject_count`.

Loose triggerability probe:

- Path: `data/replay_reports/entry_slippage_risk_veto_probe_loose_trigger_20260522_v95.json`
- Result: `127` veto rejects, only `5` trades, `0.0007549373864733479` BNB net profit, `-27.501862356933316%` max drawdown, `80%` win rate.
- Failed gates: `net_profit_bnb`, `total_trades_not_materially_lower`, `win_rate`, `walk_forward_worst_net_return_pct`, `stress_worst_net_return_pct`, `stress_worst_net_profit_bnb`.

Small targeted sweep:

- Path: `data/replay_reports/entry_slippage_risk_veto_probe_small_sweep_20260522_v95.json`
- Candidate `extension=0.5`, `jump=0.0`: `40` rejects, `24` trades, `0.012455451397` BNB profit, `-33.057700%` max drawdown.
- Candidate `extension=0.5`, `jump=0.02`: `31` rejects, `26` trades, `0.013733768180` BNB profit, `-33.057700%` max drawdown.
- Candidate `extension=0.5`, `jump=0.05`: `20` rejects, `27` trades, `0.014500786592` BNB profit, `-33.057700%` max drawdown.
- Candidate `extension=1.0`, `jump=0.0`: `12` rejects, `29` trades, `0.015320002866` BNB profit, `-31.769382%` max drawdown.

Decision from this branch:

- `entry_slippage_risk_veto` is useful as a default-off replay experiment but is `NO_GO_FOR_LIVE_RULE` in the tested forms.
- Strict planned thresholds do not reject any actual v95 validation entries.
- Looser thresholds reject real entries but reduce profit and/or worsen drawdown.
- Do not change `.env`, `data/models/**`, or live runtime parameters from this evidence.

## Latest Live Reject Time-To-Barrier Probe

Timestamp: `2026-05-22T04:13:20+08:00`

Live services:

- Bot is running under `tools/memectl`, PID `2100`.
- Collector is running under `tools/memectl`, PID `2281`.
- `data/bot_state.json` has no open positions and balance `0.003471730065131376` BNB.
- `data/paper_trades.jsonl` has no trades with `time >= 2026-05-22`.

Current-day signal audit since `2026-05-22`:

- `679` `near_threshold_pred_return_below_min`
- `306` `pred_return_below_min`
- `247` `buy_model_reject`
- `18` `entry_volume_30s_below_min`
- `4` `entry_price_volatility_below_min`
- `1` `near_threshold_volume_30s_below_min`

Read-only probe:

```bash
venv/bin/python scripts/probe_time_to_barrier.py --since '2026-05-22 00:00:00' --recent-lifecycle-files 1 --output data/replay_reports/time_to_barrier_probe_20260522_latest_rejects.json
```

Report summary:

- `1205` signal decisions processed.
- `1167` duplicate signal decisions dropped.
- `38` per-token candidates.
- Barrier classes: `26` `flat_timeout`, `4` `stop_first`, `4` `fast_profit`, `4` `fast_profit_then_collapse`.
- Recommended policies: `30` `skip`, `8` `quick_take_profit`.

Useful examples:

- Quick-profit pocket:
  - `小龙人`: `prob=0.9824`, `PredReturn=0.8330`, `volume_30s=3.1372`, `volatility=0.1986`, class `fast_profit`, MFE `75.55%`, MAE `-9.57%`.
  - `4lpha agent`: `prob=0.9838`, `PredReturn=13.1624`, `volume_30s=0.9802`, `volatility=0.0836`, class `fast_profit_then_collapse`, MFE `509.83%`, MAE `-28.26%`.
  - `PNP`: `prob=0.9829`, `PredReturn=-15.3192`, `volume_30s=6.0054`, `volatility=0.2904`, class `fast_profit`, MFE `432.45%`, MAE `-2.44%`.
- Correct-skip high-probability examples:
  - `PIZZA Chain`: `prob=0.9856`, `PredReturn=31.1641`, `volume_30s=2.2806`, `volatility=0.1827`, class `flat_timeout`.
  - `PNP`: `prob=0.9864`, `PredReturn=25.8513`, `volume_30s=3.0180`, `volatility=0.1439`, class `flat_timeout`, MFE `-1.75%`, MAE `-7.08%`.
  - `DRAWIFY`: `prob=0.9694`, `PredReturn=48.2964`, `volume_30s=0.0`, `volatility=0.3515`, class `flat_timeout`.

Interpretation:

- Raw high probability and high `PredReturn` are still not enough. Several very strong-looking rejects are correctly skipped.
- The new useful pocket is not "lower threshold and buy more"; it is a narrow `quick_take_profit` action problem on rejected candidates that often have low/negative `PredReturn`, low volume, or short-lived spikes.
- Because several quick-profit examples are `fast_profit_then_collapse`, the next experiment must be replay-integrated and support-constrained, with explicit fast take-profit / fast invalidation behavior. It should not repeat broad static slippage thresholds or global threshold lowering.

Next in-round action:

- Plan a replay-integrated support-constrained quick-profit/skip experiment over v95 rejected candidates.
- Keep v95 primary and near-threshold entry generation unchanged.
- Keep 10% sizing and require validation/final/walk-forward/stress gates before any live change.
- Do not archive this CCG task yet.

## Decision Gate Clarification

Timestamp: `2026-05-22T04:19:09+08:00`

The `entry_slippage_risk_veto` branch itself is failed and should be treated as a completed `NO-GO` experiment.

The remaining process decision is whether the May 22 business round should:

- close now with the `entry_slippage_risk_veto` NO-GO evidence, then archive/commit/push; or
- explicitly continue in the same CCG task with the next support-constrained quick-profit experiment.

No new replay or implementation should start until that decision is explicit.

## Same-Round Quick-Profit Direction Analysis

Timestamp: `2026-05-22T04:26:33+08:00`

User continuation resumed the same May 22 business round. The `entry_slippage_risk_veto` branch remains a completed `NO-GO`; this section analyzes whether the next experiment should continue in the same task.

External Claude second-view attempt:

```bash
~/.claude/bin/codeagent-wrapper --progress --backend claude - "$(pwd)"
```

Result:

- Wrapper PID `24158`, Claude PID `24160`, log `/Users/ww/.claude/logs/codeagent-wrapper-shim-24158.log`.
- Claude inspected scoped task/report files and did not start external Codex.
- It did not return a final Critical/Warning/Info/Recommendation answer after about five minutes, so the process was terminated.
- Treat this as a second-view tooling gap, not as approval for the next experiment.

Local Codex analysis:

- Existing 2026-05-22 support report: `data/replay_reports/support_action_policy_probe_20260522_latest_rejects.json`.
- Candidate scope: `38` rejected per-token candidates, with `8` positive oracle quick-profit labels and `30` skips.
- Old static high-score buckets weakened in the latest live window:
  - `v95_like_pred_rescue`: `0/1` positive.
  - `high_prob_positive_pred`: `1/5` positive.
  - `young_high_prob_positive_pred`: `1/4` positive.
  - `high_prob_volume_volatility`: `2/7` positive.
- The only support bucket with usable but still small evidence is flow-aware:
  - `high_prob_low_toxic_overlap`: `4` selected, `3` positives, `1` negative, precision `0.75`.
  - Positives: `冰箱人`, `PIZZAPERSONAS`, `Pizza`.
  - Negative: `Blobby`.

Decision:

- Do not run the existing `run_primary_score_scalp_replay.py` / `run_ultrashort_runner_replay.py` grid as-is as the next serious experiment. Their current gates are mainly probability / PredReturn / volume / volatility / age, while today's support evidence says those buckets are weak.
- The next same-round experiment, if continued, should be a new default-off replay-only flow-aware support-constrained quick-profit overlay.
- This is not live-switch evidence. The live probe labels use ex-post paths and must only guide replay design.

Proposed design gate:

- Entry universe: keep v95 primary and near-threshold candidate generation unchanged.
- Overlay eligibility: rejected candidates only; start from a bounded flow-aware rule family around `prob>=0.985`, `flow_event_count_30s>=2`, `flow_buy_sell_overlap_ratio_60s<=0.5`, and `flow_recent_seller_reentry_ratio_30s<=0.5`.
- Negative control: explicitly test broader score/volume buckets and require them to fail or underperform before selecting a flow-aware rule.
- Action: quick-profit only, with fixed 10% sizing, fast take-profit, and short max hold; no global threshold lowering and no live config/model artifact changes.
- Acceptance gates: validation profit above v95 baseline; drawdown, win rate, walk-forward, stress, and trade-count discipline not worse; final confirmation passes the same gate; overlay entry count must be nonzero.
- Process gate: write a new plan section before implementation and do not code until the design is accepted.

## Claude Second View - Quick-Profit Direction

Timestamp: `2026-05-22T04:29:27+08:00`

External Claude second-view rerun:

```bash
~/.claude/bin/codeagent-wrapper --progress --backend claude - "$(pwd)"
```

Result:

- Wrapper log: `/Users/ww/.claude/logs/codeagent-wrapper-shim-24919.log`.
- Claude returned a usable analysis and did not edit files.
- Claude recommendation: choose option `C`, but fold in option `D` as a required pre-step.

Claude conclusions:

- Do not close/archive the round immediately just because `entry_slippage_risk_veto` is NO-GO; the May 22 live reject data produced one still-useful flow-aware hypothesis.
- Do not run existing `run_primary_score_scalp_replay.py` or `run_ultrashort_runner_replay.py` as-is as the next serious experiment; those tools mostly use probability, PredReturn, volume, volatility, and age, while the only latest support bucket with non-trivial precision depends on flow features.
- The flow-aware low-toxic-overlap bucket is still only `3/4` positive, so it is hypothesis evidence, not edge evidence.
- The next branch must guard against:
  - `n=4` overfit;
  - in-sample rule selection bias;
  - treating oracle quick-profit labels as realized P&L;
  - mixing `fast_profit` and `fast_profit_then_collapse` without explicit exit handling;
  - replay/live flow-feature parity drift.

Updated design gate:

- First expand or hold out the evidence set before implementation. Use additional days/cohorts of reject probes, or a held-out token cohort, before treating the flow rule as stable.
- Pre-register the current flow thresholds as the hypothesis, not a fit target:
  - `prob >= 0.985`
  - `flow_event_count_30s >= 2`
  - `flow_buy_sell_overlap_ratio_60s <= 0.5`
  - `flow_recent_seller_reentry_ratio_30s <= 0.5`
- Compare against the existing primary-score/ultrashort replay gates on the same expanded sample, but do not use those existing gates as the main next experiment.
- Measure expected P&L or realized quick-exit return, not only oracle-label precision.
- Decide how `fast_profit_then_collapse` is handled before replay: include only with a quick-exit rule or exclude and report recall loss.
- Define NO-GO conditions before running this branch so the May 22 round can close cleanly if the flow-aware quick-profit overlay fails.

Next action:

- Present a design gate for user confirmation before writing implementation code.
- If accepted, write the plan under the current CCG task and keep the task unarchived until the full same-round experiment reaches accept/reject evidence.

## Flow-Aware Quick-Profit Pooled Evidence Gate

Timestamp: `2026-05-22T05:00:17+08:00`

Implementation completed for Task 1 only:

- `src/pipeline/support_action_policy_probe.py`
- `scripts/probe_support_action_policy_pool.py`
- `tests/model/test_support_action_policy_probe.py`
- `tests/model/test_support_action_policy_pool_cli.py`

Focused TDD evidence:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_pool_cli
```

Result: RED first with missing `build_pooled_support_report` and missing CLI, then GREEN with `21` tests `OK`.

Regression check:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_probe_cli tests.model.test_support_action_policy_pool_cli
```

Result: `25` tests `OK`.

Pooled support report command:

```bash
venv/bin/python scripts/probe_support_action_policy_pool.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260521_flow_fields_live.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_latest_rejects.json \
  --output data/replay_reports/support_action_policy_pool_20260522_flow.json \
  --min-pooled-selected 30 \
  --min-pooled-positive 12 \
  --force
```

Report:

- Path: `data/replay_reports/support_action_policy_pool_20260522_flow.json`
- Decision: `missing_flow_feature_parity`
- Input reports: `2`
- Input candidates: `104`
- Positive oracle candidates: `22`
- Negative oracle candidates: `82`
- Target rule: `high_prob_low_toxic_overlap`
- Target selected: `13`
- Target positives: `9`
- Target negatives: `4`
- Target precision: `0.6923076923076923`
- Required evidence gate: at least `30` selected and at least `12` positives.
- Required flow fields complete: `false`

Flow-field completeness:

- `flow_event_count_30s`: finite `103/104`
- `flow_buy_sell_overlap_ratio_60s`: finite `80/104`
- `flow_recent_seller_reentry_ratio_30s`: finite `71/104`

Negative controls:

- `young_high_prob_clean_flow`: `4` selected, `3` positives, precision `0.75`, still too small.
- `high_prob_volume_volatility`: `15` selected, `7` positives, precision `0.4666666666666667`.
- `young_high_prob_positive_pred`: `7` selected, `3` positives, precision `0.42857142857142855`.
- `high_prob_positive_pred`: `9` selected, `3` positives, precision `0.3333333333333333`.
- `v95_like_pred_rescue`: `3` selected, `1` positive, precision `0.3333333333333333`.

Decision:

- Stop the flow-aware quick-profit runtime-overlay branch before Tasks 2-4.
- Do not implement replay/live flow aliases from this evidence.
- Do not implement `buy_flow_quick_profit_overlay_*` runtime params.
- Do not run a flow quick-profit replay grid.
- Do not change `.env`, `data/models/**`, or live services.
- Treat this as `NO_GO_FOR_RUNTIME_OVERLAY` for the May 22 round unless a future separate business round collects materially larger and complete flow evidence.

Useful lesson:

- The flow-aware bucket still dominates static score/PredReturn/volume controls by precision, so the direction remains useful research evidence.
- It is not stable enough for runtime/replay overlay work in this round because the expanded support is only `13/9`, below the pre-registered `30/12` gate, and required flow fields are not complete across pooled candidates.
