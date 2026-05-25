# Source-Window Stability Meta-Label Probe

## Question

Does the live-actionable candidate meta-label signal remain stable when the same parameter grid is evaluated across rolling chronological source windows?

## Research Reuse

This round reused `docs/research/20260525-candidate-meta-label-research/summary.md` and `docs/research/20260525-live-actionable-meta-label/summary.md`. The new angle is local validation methodology: instead of trusting one aggregate split, test each parameter setting across rolling source-window folds and require support in every fold.

## Live Evidence

Fresh live state at `2026-05-25T15:35:06+08:00`:

- bot running under `memectl`, PID `2953`;
- collector running under `memectl`, PID `2898`;
- tmux sessions `meme-bot` and `meme-collector` present;
- `data/bot_state.json` balance `0.00313902491330702`, open positions `0`;
- `data/paper_trades.jsonl` remained at `196` rows, latest still `DRIPDOGE` close by `ENTRY_SLIPPAGE_PROTECTION`;
- recent high-probability rejects such as `人民币6900`, `仅向上`, and `赵舔鹏` were rejected mostly by low or negative `PredReturn`.

The live-derived failure tag is still `missed_runner_vs_fast_collapse_candidate_selection`, but the previous round identified the immediate blocker as source/support instability.

## Implementation

Added a reusable rolling stability analyzer:

- core: `src/pipeline/candidate_meta_stability_probe.py`
- CLI: `scripts/probe_candidate_meta_stability.py`
- tests: `tests/model/test_candidate_meta_stability_probe.py`, `tests/model/test_candidate_meta_stability_probe_cli.py`

The analyzer takes any chronological list of time-to-barrier reports, candidate filters, and a small parameter grid. For each configuration it trains the existing decision-time meta-label model on rolling prefixes, validates on the newest source window(s), and records fold count, eligible fold count, all-fold eligibility, minimum fold precision, pooled precision, selected counts, and errors.

## Experiment

Inputs:

- `data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json`
- `data/replay_reports/time_to_barrier_probe_20260523_2250_since_221344_correct_abstention.json`
- `data/replay_reports/time_to_barrier_probe_20260524_negative_return_reject_option_since_1546.json`
- `data/replay_reports/time_to_barrier_probe_20260524_new_direction_since_1851.json`
- `data/replay_reports/time_to_barrier_probe_20260525_generic_since_restart.json`
- `data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json`

Live-actionable filters:

- `prob>=0.94`
- `entry_volume_30s>=1.25`
- `entry_price_volatility>=0.08`

Grid:

- `validation_report_count`: `1`, `2`
- `probability_threshold`: `0.20`, `0.40`
- `max_depth`: `2`, `3`
- `min_samples_leaf`: `3`, `20`

Reports:

- `data/replay_reports/candidate_meta_stability_probe_20260525_source_stability_thr040.json`
- `data/replay_reports/candidate_meta_stability_probe_20260525_source_stability_thr020.json`
- `data/replay_reports/candidate_meta_stability_probe_20260525_source_stability_thr020_relaxed045.json`

## Result

Strict gate (`min_validation_selected=3`, `min_train_selected=10`, `min_stable_precision=0.50`):

- stable results: `0/16`.
- best-ranked config: `validation_report_count=2`, `probability_threshold=0.40`, `max_depth=3`, `min_samples_leaf=3`;
- only `2/4` folds were eligible, minimum eligible-fold precision `48.4848%`, pooled precision `50.1992%`.

Support-relaxed gate (`min_validation_selected=3`, `min_train_selected=5`, `min_stable_precision=0.50`):

- stable results: `0/16`.
- a fully eligible config existed, but its minimum fold precision was only `25.0000%` with pooled precision `47.8571%`.

Precision-relaxed gate (`min_validation_selected=3`, `min_train_selected=5`, `min_stable_precision=0.45`):

- stable results: `0/16`.
- the same fully eligible config remained below the relaxed precision floor because its minimum fold precision was `25.0000%`.

## Decision

Reject the filtered meta-label stability direction for runtime or replay integration in its current form. It is useful shadow evidence, but not a model improvement candidate:

- the configurations with about `50%` pooled precision did not cover all rolling folds;
- the all-fold eligible configurations fell to `25%` worst-fold precision;
- the result confirms the prior concern that the apparent `22/37` two-window precision came from unstable source support.

No `.env`, threshold, sizing, model artifact, or bot process changed.

Next viable direction: move away from shallow decision-tree source-window stability on rejected candidates and test either a replay-integrated risk/coverage gate on primary v95/v84 trade candidates or a conditional exit/retention model that uses actual live trade path failures rather than only rejected-signal TTB rows.
