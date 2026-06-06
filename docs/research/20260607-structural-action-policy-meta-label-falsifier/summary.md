# 2026-06-07 Structural Action-Policy Meta-Label Falsifier

## Live State

- Bot and collector remained running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions at the entry check.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- The preceding stop/timeout flow falsifier was committed and pushed as `9b71d9091cd1e69ab8cf343380be0d96664df4a5`; GitHub Actions `CI` run `27068218176` passed.

## Trigger

The structural reward pivot failed because the selected rejected-entry final set over-selected `flat_timeout` and `stop_first` rows. The scalar stop/timeout flow falsifier then showed that a simple flow-threshold veto cannot isolate those rows without also selecting protected opportunity rows.

The next smallest structural question was whether the existing support-complete action-policy meta-label probe could learn a positive action-policy surface over accepted and rejected families on the fresh 2026-06-06 final rejected population.

This was a read-only support falsifier, not replay or live-switch evidence.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment reused already committed action-policy/meta-labeling and support-complete research:

- `docs/research/20260525-action-policy-meta-label/summary.md`
- `docs/research/20260526-support-complete-meta-label/summary.md`
- `docs/research/20260526-support-complete-replay-gate-spi/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260606-structural-reward-pivot/summary.md`
- `docs/research/20260607-structural-stop-timeout-flow-falsifier/summary.md`

The new live-derived angle was the current held-out final group: accepted support from `post_target_exit_state_probe_20260526_support_complete_entryflow_final.json` plus the fresh rejected-entry population from `live_trade_attribution_20260606_structural_pivot_entry.json`.

## Hypothesis

If a generic action-policy meta-label is worth replay escalation, then on the held-out final group it should select both accepted and rejected-family rows while materially concentrating positive action labels. It should not select a high-confidence bucket dominated by `flat_timeout` / `stop_first` rows whose recommended policy is `skip`.

Falsification rule: reject replay escalation if the selected final bucket has low positive precision or if selected rejected rows are mostly `flat_timeout` / `stop_first` skip rows, even when the generic family-support gate passes.

## Experiment

The probe used the same train/validation/final source split as the preceding reward pivot:

- Rejected train: `data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json`
- Rejected validation: `data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json`
- Rejected final: `data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json`
- Accepted train: `data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json`
- Accepted validation: `data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json`
- Accepted final: `data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json`

Command template:

```bash
venv/bin/python scripts/probe_action_policy_meta_label.py \
  --rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --rejected-report data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json \
  --accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --rejected-source-name train \
  --rejected-source-name validation \
  --rejected-source-name final \
  --accepted-source-name train \
  --accepted-source-name validation \
  --accepted-source-name final \
  --validation-source-count 1 \
  --probability-threshold 0.99 \
  --min-validation-selected 20 \
  --min-validation-selected-per-family 5 \
  --min-family-candidates 20 \
  --max-depth 3 \
  --min-samples-leaf 5 \
  --output data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr99.json \
  --force
```

The same command was run at thresholds `0.2`, `0.4`, `0.6`, `0.8`, `0.9`, `0.95`, and `0.99`.

Reports:

- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr02.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr04.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr06.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr08.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr90.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr95.json`
- `data/replay_reports/action_policy_meta_label_probe_20260607_structural_pivot_final_thr99.json`

## Results

All threshold reports returned `decision=probe_only_replay_required` with the generic support gate passing. That only means the diagnostic had enough accepted/rejected rows and shared decision-time features to train and score; it does not mean the selected policy is useful.

The train+validation source groups had `264` rows and the held-out final group had `1022` rows. The model used `28` shared decision-time features. Top feature importances were `flow_total_volume_60s=0.40777013209764196`, `pred_return=0.3989776652075275`, `flow_total_volume_30s=0.12061015998527395`, `flow_buy_volume_60s=0.05016004169171256`, and `flow_buy_volume_10s=0.022482001017844002`.

Held-out final threshold results:

| Threshold | Selected | Positive | Precision | Accepted | Rejected | Stop/Timeout | Skip |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `0.20` | `230` | `64` | `0.2782608695652174` | `21` | `209` | `163` | `163` |
| `0.40` | `53` | `21` | `0.39622641509433965` | `20` | `33` | `29` | `29` |
| `0.60` | `49` | `18` | `0.3673469387755102` | `17` | `32` | `28` | `28` |
| `0.80` | `49` | `18` | `0.3673469387755102` | `17` | `32` | `28` | `28` |
| `0.90` | `23` | `9` | `0.391304347826087` | `6` | `17` | `13` | `13` |
| `0.95` | `23` | `9` | `0.391304347826087` | `6` | `17` | `13` | `13` |
| `0.99` | `23` | `9` | `0.391304347826087` | `6` | `17` | `13` | `13` |

The high-confidence `0.99` bucket selected `17` rejected-family rows: `4` were `fast_profit_then_collapse` with `quick_take_profit`, while `13` were bad `flat_timeout` / `stop_first` rows with `skip`. No `fast_profit` or `slow_runner` rejected rows survived at this threshold.

This repeats the structural reward pivot's failure mode in classifier form: the generic positive-action surface cannot separate final opportunity rows from the stop/timeout mass well enough to justify replay escalation.

## Decision

`Rejected` for replay escalation, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this support-passing diagnostic narrows the next structural direction. Do not continue generic action-policy positive-label classifiers on the current accepted/rejected support set. Future work needs either a class-specific opportunity selector that treats `skip` as a negative for replay escalation, or more audit-only live shadow collection before another accepted/rejected replay attempt.
