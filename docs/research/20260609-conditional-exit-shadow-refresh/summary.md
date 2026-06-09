# 2026-06-09 Conditional-Exit Recorded Shadow Refresh

## Live State

- Fresh work started after the preserve-base utility-label current-data rerun was rejected by uncertainty gates.
- Bot and collector stayed running under `./tools/memectl`; no restart was performed.
- Active live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, max positions `8`, and action-policy router live enablement remained off.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions during the preceding health check.
- There were still no new real trades after the `2026-06-07 12:25:39.499918` close.
- Current node state entering this boundary: not archived; prior milestone `715ea5c` was committed, pushed, and GitHub Actions passed.

## Question

After the utility-label branch failed the paired-delta uncertainty gate, does fresh in-process action-policy shadow telemetry support a structural conditional-exit direction, especially live enablement of the continue-hold or quick-profit router paths?

## Research Reused

No new web research was needed. This boundary reused the already committed conditional-exit and continue-hold evidence:

- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260609-continue-hold-router-robustness/summary.md`
- `docs/research/20260609-preserve-base-utility-label-current-data/summary.md`

Prior evidence made the strongest structural branch a no-entry-change continue-hold forced-hold effect. Quick-profit route precision was already weak, and the latest continue-hold robustness note explicitly required matched in-process shadow support before any live-risk review.

## Experiments

Recorded shadow audit:

```bash
venv/bin/python scripts/probe_action_policy_recorded_shadow_audit.py \
  --since "2026-06-08 15:20:22" \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/action_policy_recorded_shadow_audit_20260609_after_utility_label_reject.json \
  --output-md data/replay_reports/action_policy_recorded_shadow_audit_20260609_after_utility_label_reject.md \
  --force
```

Recorded route path attribution:

```bash
venv/bin/python scripts/probe_action_policy_recorded_shadow_path_attribution.py \
  --since "2026-06-08 15:20:22" \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 36 \
  --output-json data/replay_reports/action_policy_recorded_shadow_path_attribution_20260609_after_utility_label_reject.json \
  --output-md data/replay_reports/action_policy_recorded_shadow_path_attribution_20260609_after_utility_label_reject.md \
  --force
```

Activation-aware shadow attribution using the conservative continue-hold parameterization:

```bash
venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since "2026-06-08 15:20:22" \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 36 \
  --router-min-confidence 0.55 \
  --activation-pct 40 \
  --release-pct 85 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260609_after_utility_label_reject.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260609_after_utility_label_reject.md \
  --force
```

All reports are read-only. Their contracts set `live_switch_evidence=false` and `safe_for_live_switch=false`.

The signal-row counts differ slightly across the three reports because the live bot and collector kept appending to `data/signal_audit.jsonl` between the sequential probe runs. Each report is interpreted independently against its own generated timestamp and input slice.

## Results

Recorded shadow audit:

- Decision: `insufficient_recorded_shadow_support`.
- Signal rows since `2026-06-08 15:20:22`: `4848`.
- Recorded shadow rows: `4848`; missing recorded fields: `0`.
- Queued signals: `2`.
- Recorded shadow-used rows: `10`.
- Queued recorded shadow-used rows: `2`.
- Queued recorded shadow-used matched trades: `0`.
- Recorded routes: `continue_hold=13`, `quick_take_profit=218`, `skip=4617`.

Recorded route path attribution:

- Decision: `rejected_recorded_quick_take_profit_path_precision`.
- Signal rows: `4853`; path-evaluable rows: `4853`; missing paths: `0`.
- Overall barrier classes: `fast_profit=376`, `fast_profit_then_collapse=339`, `flat_timeout=2260`, `slow_runner=189`, `stop_first=1689`.
- Quick-profit route support: `218` path-evaluable rows, `37` quick-profit candidates, precision `0.16972477064220184`, below the `0.60` support threshold.
- Continue-hold recorded route paths: `13` rows, with `1` fast-profit-then-collapse, `11` flat-timeout, and `1` stop-first; quick-profit precision `0.07692307692307693`.
- Skip route quick-profit precision was also weak at `0.14647338814366076`.

Activation-aware shadow attribution:

- Decision: `insufficient_activation_shadow_support`.
- Conservative continue-hold runtime scoring saw `17` shadow-used rows but only `2` queued shadow-used rows.
- Queued shadow-used matched trades: `0`.
- Activation hits: `0`; release hits: `0`; activated-then-stop: `0`.

## Decision

Outcome tier: `Rejected` as live-enable / live-risk-review evidence; useful only as a read-only direction refresh.

Fresh recorded telemetry does not support live enablement of either structural path. The continue-hold router remains the strongest offline `Shadow Candidate`, but it still has no matched live shadow-used trade support in this post-enable window. Quick-profit remains rejected as a structural direction because route precision stayed far below the support threshold despite a larger path-evaluable sample.

No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live behavior changed. `docs/model_scoreboard.md` was updated because this changes the active interpretation: do not prepare a continue-hold live-risk review or reopen quick-profit activation work from current recorded-shadow evidence. The next optimization branch should pivot to a direct paired trade-delta / utility objective or another replay-compatible structural gate, while continuing to collect matched in-process continue-hold shadow evidence passively.
