# Hot-Market Moonshot Runner Phase 0/1

Created: 2026-06-09

Purpose: build the offline foundation for a hot-market BNB/FourMeme moonshot runner strategy. This round creates label truth diagnostics, point-in-time early-chain snapshots, and a pure on-chain `>=10x` runner baseline. It does not change live trading behavior.

## Artifacts

- Plan: `docs/superpowers/plans/2026-06-09-hot-market-moonshot-runner-phase0-1.md`
- Label summary report: `data/replay_reports/moonshot_label_truth_probe_20260609.summary.json`
- Raw label report: `data/replay_reports/moonshot_label_truth_probe_20260609.json` (local-only large artifact, not committed)
- Baseline report: `data/replay_reports/moonshot_local_runner_baseline_20260609.json`
- Tests:
  - `tests/model/test_moonshot_label_truth.py`
  - `tests/model/test_moonshot_feature_snapshot.py`
  - `tests/model/test_moonshot_local_runner_baseline.py`
  - `tests/model/test_moonshot_phase0_clis.py`

## Label Truth Result

The label truth probe scanned `data/training` lifecycle files with no external label exports.

| Metric | Value |
|---|---:|
| Lifecycle rows scanned | 598,457 |
| Local label rows before merge | 558,131 |
| Accepted unique labels after merge | 298,466 |
| Rejects | 40,326 |
| Merge warnings | 30,559 |

Threshold counts after merge:

| Threshold | Count |
|---|---:|
| `>=2x` | 20,025 |
| `>=5x` | 4,769 |
| `>=10x` | 1,837 |
| `>=20x` | 0 |
| `>=50x` | 0 |
| `>=100x` | 0 |

Interpretation:

- Local lifecycle data supports a `>=10x` runner proxy target.
- Local lifecycle data still does not contain usable `20x/50x/100x` truth.
- The `30,559` merge warnings are local duplicate-source max-multiple disagreements and should be treated as a data-quality signal for the next deduplication round, not external-source disagreement.
- External Bitquery/Codex exports remain required before claiming true long-hold moonshot label truth.
- The label report now includes `source_counts` and `reject_reason_counts` for export diagnostics.
- The external export normalizer accepts canonical rows plus Bitquery-style, Codex-style, and CMC-style historical export field aliases. This is offline file ingestion only; it does not call external APIs.

## Baseline Result

The local runner baseline used three point-in-time snapshots per accepted local label: `30s`, `60s`, and `300s` after launch.

| Metric | Value |
|---|---:|
| Snapshot samples | 895,398 |
| Positive `hit_10x` samples | 5,511 |
| Base positive rate | 0.0061548049 |
| Train split samples | 716,318 |
| Validation split samples | 179,080 |
| Validation positives | 891 |
| Skipped labels | 0 |
| Future field violations | 0 |

Validation top-k metrics:

| Metric | Value |
|---|---:|
| `precision_at_10` | 0.60 |
| `precision_at_25` | 0.28 |
| `precision_at_50` | 0.28 |
| `precision_at_100` | 0.25 |
| `lift_at_10` | 120.5926 |
| `lift_at_25` | 56.2765 |
| `lift_at_50` | 56.2765 |
| `lift_at_100` | 50.2469 |

Decision: `research_baseline_only`.

Interpretation:

- Early on-chain flow has strong ranking signal for local `>=10x` runners.
- The baseline is useful as a research floor and diagnostic, not as a deployable strategy.
- Top-k metrics are snapshot-level diagnostics and may include multiple snapshots for the same token; they are not token-level entry precision.
- The result is not evidence for `20x/50x/100x` exits because those labels remain absent locally.
- The current score is fixed-weight and should be replaced by a time-split ranker only after external label truth and duplicate-label reconciliation improve.

## Guardrails

- No `.env`, `.env.example`, runtime config, `src/trader`, `tools/memectl`, or live bot behavior changed.
- No external API calls are required by the new CLIs.
- No market-hot switch was introduced.
- No `docs/goals/**` files were changed.
- No model artifact was trained or promoted.
- No live switch, restart, threshold change, sizing change, or execution-path change was made.

Scoreboard update: not updated because Phase 0/1 produced offline foundation evidence only and did not accept or reject a live model candidate.

## Next Work

1. Add external historical label exports from Bitquery/Codex or another verified source to recover true `20x/50x/100x` labels with evidence URLs and source timestamps.
2. Reconcile duplicate local lifecycle labels so local merge warnings distinguish stale duplicate rows from genuine source disagreement.
3. Promote the fixed-weight baseline into a proper time-split ranking experiment only after label truth is cleaner.
4. Add external attention features separately from the pure on-chain baseline: DEX Screener profile/boost/CTO signals, X bounded mention counts, and optional GMGN smart-money/KOL counts.
5. Only after label truth and ranking validation improve, run exit-policy backtests for `10x/20x/50x/100x`, trailing exits, and first-sell timing.
