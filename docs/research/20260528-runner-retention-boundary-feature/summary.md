# Runner-Retention Boundary Soft Feature

## Research Basis

SmartSearch evidence under this directory supports a train-only, validation-held-out treatment of boundary/meta-label signals:

- Meta-labeling evidence supports a secondary act/pass model over primary trading opportunities instead of lowering the primary model threshold directly.
- Reject-option/selective classification evidence supports abstention or confidence gating when error cost is asymmetric.
- Cost-sensitive threshold evidence supports optimizing decision thresholds against business utility rather than raw accuracy.
- Conformal risk / OPE evidence supports conservative holdout checks before promotion.
- Data-leakage evidence supports fitting any selector on train-only data and evaluating it on separate replay splits.

## Implementation

Codex added two train-only soft features for the runner-retention candidate gate:

- `runner_retention_train_boundary_match`
- `runner_retention_train_boundary_condition_fraction`

The boundary report is fitted only on balanced train rows, then the selected rule is used as a soft model input for full train/eval scoring. It is not used as a hard replay filter. Because full train boundary search was too slow, the implementation now supports `buy_runner_retention_train_boundary_max_rows`, which caps only the boundary-rule search rows and records `source_row_count`, `search_row_count`, and `max_rows` in the report.

## Experiment

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_sampled_single_grid.json`

Sampled single-candidate config:

- `buy_path_state_meta_gate_min_score=0.45`
- `buy_runner_retention_train_boundary_loss_cost=3.0`
- `buy_runner_retention_train_boundary_max_conditions=1`
- `buy_runner_retention_train_boundary_beam_width=4`
- `buy_runner_retention_train_boundary_max_rows=600`

Result: rejected.

- Validation baseline net profit: `0.0192544647942539` BNB
- Candidate net profit: `0.019166146977559965` BNB
- Delta: `-0.00008831781669393565` BNB
- Trades: `32 -> 40`
- Max drawdown: `-8.18251735324681% -> -18.439271563032666%`
- Walk-forward worst return: `79.59654474223983% -> 95.72652671065272%`
- Stress worst net profit: `0.010166721706927569 -> 0.010971179311315297` BNB

The learned train boundary selected `time_since_launch >= 226.5` from `600` sampled train rows out of `5531` balanced train rows. The soft feature was active and meaningful in the scorer: `runner_retention_train_boundary_match` had feature importance `0.25325615354770065`, second only to `flow_buy_volume_60s`.

## Conclusion

No live switch, no `.env`, threshold, sizing, model artifact, or bot restart change.

The sampled train-boundary soft feature is not an accepted optimization in this configuration: it slightly lowered net profit and materially worsened drawdown. However, it did improve walk-forward worst return and stress worst net profit, and the feature had high model importance. The next experiment should keep the sampled soft-feature mechanism but use a stricter path-state/meta score gate or calibrated score gate to retain the stress/walk-forward gain while rejecting the added drawdown-heavy trades.
