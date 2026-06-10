# Moonshot Token-Level Evaluation

Created: 2026-06-10

Purpose: replace snapshot-level moonshot baseline diagnostics with an honest token-level evaluation for the local `>=10x` proxy. This is an offline research probe only and does not change live trading behavior.

## Inputs

- Lifecycle dir: `data/training`
- Snapshot seconds: `30,60,300`
- Dedupe policy: `max_events`
- Report: `data/replay_reports/moonshot_token_level_eval_20260610.json`
- External API calls: `false`
- Prior Phase 0 raw label report remains a local-only large artifact; committed evidence uses `data/replay_reports/moonshot_label_truth_probe_20260609.summary.json` plus this token-level report.

## Dedupe Result

| Metric | Value |
|---|---:|
| Local label candidates scanned | 563,118 |
| Output tokens | 300,789 |
| Duplicate token groups | 60,928 |
| Conflict token groups | 30,807 |
| Rejects | 40,944 |
| Skipped selected labels | 0 |
| Future field violations | 0 |

Sensitivity by local duplicate policy:

| Policy | Token count | `>=10x` positives |
|---|---:|---:|
| `max_events` | 300,789 | 1,826 |
| `max_multiple` | 300,789 | 1,845 |
| `min_multiple` | 300,789 | 1,012 |

Interpretation: duplicate local lifecycle rows materially affect the positive set. `max_events` is a reasonable default because it prefers the lifecycle copy with the most observed trade events, but the conservative `min_multiple` sensitivity shows that local duplicate disagreement is still a real label-quality risk.

## Snapshot-Level Baseline Recheck

These are still snapshot-level diagnostics and can contain multiple checkpoints per token.

| Metric | Value |
|---|---:|
| Snapshot samples | 902,367 |
| Positive snapshots | 5,478 |
| Base positive rate | 0.0060707007 |
| Validation samples | 180,474 |
| Validation positives | 888 |
| `precision_at_10` | 0.60 |
| `precision_at_25` | 0.28 |
| `precision_at_50` | 0.26 |
| `precision_at_100` | 0.26 |

## Token-Level Result

Each token contributes only one selected checkpoint, and the validation split is group-disjoint by token.

| Metric | Value |
|---|---:|
| Tokens | 300,789 |
| Positive tokens | 1,826 |
| Base positive rate | 0.0060707007 |
| Train tokens | 240,631 |
| Validation tokens | 60,158 |
| Validation positives | 296 |
| Token overlap | 0 |
| `precision_at_10` | 0.40 |
| `precision_at_25` | 0.20 |
| `precision_at_50` | 0.20 |
| `precision_at_100` | 0.36 |
| `lift_at_10` | 81.2946 |
| `lift_at_100` | 73.1651 |

## Interpretation

- The honest token-level score remains far above base rate, so the local on-chain runner signal is real enough to keep developing.
- The headline `precision_at_10` drops from snapshot-level `0.60` to token-level `0.40`, confirming that the old snapshot-level metric was optimistic.
- `precision_at_100` is `0.36`, stronger than the old snapshot-level `0.26`, because one-token-per-candidate ranking removes duplicated weaker checkpoints and changes the validation candidate pool.
- This is still local `>=10x` proxy evidence only. It is not evidence for true `20x/50x/100x` labels or exits.
- This does not justify live runtime changes, model promotion, threshold changes, sizing changes, or a bot restart.

## Next Work

1. Use this token-level table as the join target for future external Bitquery/CoinGecko/Codex label exports.
2. Keep external attention features separate until historical label truth is available or a bounded live/recent shadow collection is approved.
3. Do not run `10x/20x/50x/100x` exit-policy grids until true high-multiple labels exist.

## Scoreboard Closeout

`docs/model_scoreboard.md` was updated because this round changes the moonshot model direction: continue from the token-level local `>=10x` ranker gate, not from the old snapshot-level baseline.
