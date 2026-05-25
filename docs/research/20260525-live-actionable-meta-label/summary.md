# Live-Actionable Candidate Meta-Label Probe

## Question

Can the rejected-signal candidate-level meta-label probe improve when narrowed to candidates that are closer to live-actionable entry conditions, instead of training over every rejected time-to-barrier candidate?

## Research Reuse

This round reused the committed SmartSearch Deep Research artifact `docs/research/20260525-candidate-meta-label-research/summary.md`. The new angle is not a new literature claim; it is a local falsification of that artifact's next-step recommendation: narrow the candidate universe before replay integration and require source-split risk coverage.

## Live Evidence

Fresh live health at `2026-05-25T15:13:36+08:00`:

- bot running under `./tools/memectl bot status`, PID `2953`;
- collector running under `./tools/memectl collector status`, PID `2898`;
- tmux sessions `meme-bot` and `meme-collector` present;
- `data/bot_state.json` balance `0.00313902491330702`, open positions `0`;
- `data/paper_trades.jsonl` still had `196` rows, with no new paper trade after the prior `DRIPDOGE` close;
- latest signal audit remained a rejected-signal regime, with recent high-probability `House`/`Genmoji` rows rejected mostly for low or negative `PredReturn`.

The live-derived failure tag remains `missed_runner_vs_fast_collapse_candidate_selection`, not live execution, sizing, or exit timing.

## Implementation

Added reusable decision-time candidate filters to the read-only meta-label probe:

- `src/pipeline/candidate_meta_label_probe.py`
- `scripts/probe_candidate_meta_label.py`
- `tests/model/test_candidate_meta_label_probe.py`
- `tests/model/test_candidate_meta_label_probe_cli.py`

The filters accept repeated numeric conditions such as `prob>=0.94`, validate that fields are in the decision-time feature set, and record both the filter list and pre/post-filter candidate counts in the JSON report. This avoids token-specific or timestamp-specific experiment code.

TDD evidence:

- RED: `python -m unittest tests.model.test_candidate_meta_label_probe tests.model.test_candidate_meta_label_probe_cli` failed because `candidate_filters` and `--candidate-filter` did not exist.
- GREEN: the same command passed after implementation, `6` tests OK.

## Experiment

Input reports:

- `data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json`
- `data/replay_reports/time_to_barrier_probe_20260523_2250_since_221344_correct_abstention.json`
- `data/replay_reports/time_to_barrier_probe_20260524_negative_return_reject_option_since_1546.json`
- `data/replay_reports/time_to_barrier_probe_20260524_new_direction_since_1851.json`
- `data/replay_reports/time_to_barrier_probe_20260525_generic_since_restart.json`
- `data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json`

Live-actionable candidate filters:

- `prob>=0.94`
- `entry_volume_30s>=1.25`
- `entry_price_volatility>=0.08`

The filters reduced the candidate universe from `4015` to `1209` rows, with `181` positives.

Reports:

- `data/replay_reports/candidate_meta_label_probe_20260525_live_actionable_thr020.json`
- `data/replay_reports/candidate_meta_label_probe_20260525_live_actionable_two_window_thr020.json`
- `data/replay_reports/candidate_meta_label_probe_20260525_live_actionable_two_window_d2_l3_thr040.json`
- `data/replay_reports/candidate_meta_label_probe_20260525_live_actionable_grid_summary.json`

## Result

Fixed latest-window probe (`validation_report_count=1`, `threshold=0.20`, `max_depth=3`, `min_samples_leaf=20`):

- train `1199` candidates, base precision `14.7623%`, selected `313`, precision `46.9649%`;
- latest validation `10` candidates, base precision `40.0000%`, selected `4`, positives `1`, precision `25.0000%`.

Fixed two-window probe (`validation_report_count=2`, `threshold=0.20`, `max_depth=3`, `min_samples_leaf=3`):

- validation `1142` candidates, base precision `14.4483%`, selected `349`, positives `88`, precision `25.2149%`.

Best grid point with at least `10` selected validation candidates:

- `validation_report_count=2`, `max_depth=2`, `min_samples_leaf=3`, `probability_threshold=0.40`;
- train selected `5/5` positives;
- validation selected `37`, positives `22`, precision `59.4595%`, lift `4.1153x` over validation base.

## Decision

Reject live/runtime use for this round and keep the result as shadow-only evidence.

The filtered universe is materially better than the broad learned probe's strict two-window `13.0856%` precision, but the evidence is not robust enough for replay integration or live overlay:

- the fixed latest-window setting underperformed the filtered base rate (`25.0000%` vs `40.0000%`);
- single-window top grid points selected only one latest token;
- the best two-window point was trained from only `5` selected samples, making the `59.4595%` validation result high-overfit-risk;
- there was no live replay integration, no stress replay, and no live switch procedure.

No `.env`, threshold, sizing, model artifact, or bot process changed.

Next viable direction: require source-window stability or add a replay-integrated risk-coverage gate before considering any runtime overlay from this filtered meta-label signal.
