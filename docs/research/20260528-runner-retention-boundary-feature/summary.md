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

## Score060 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_sampled_score060_grid.json`

Changing only `buy_path_state_meta_gate_min_score` from `0.45` to `0.60` was still rejected but moved closer to baseline:

- Validation baseline net profit: `0.0192544647942539` BNB
- Candidate net profit: `0.019229300894133685` BNB
- Delta: `-0.00002516390012021613` BNB
- Trades: `32 -> 39`
- Win rate: `0.84375 -> 0.7692307692307693`
- Max drawdown: `-8.18251735324681% -> -17.802076304174253%`
- Walk-forward worst return: `79.59654474223983% -> 96.96988460997562%`
- Stress worst net profit: `0.010166721706927569 -> 0.011061044311076237` BNB

The selected rule and feature importances were unchanged (`time_since_launch >= 226.5`, `runner_retention_train_boundary_match` importance `0.25325615354770065`). This means the path-state score floor alone is not filtering enough drawdown-heavy added trades. The next experiment should narrow the rescue eligibility itself, starting with a higher `buy_near_threshold_min_prob`.

## Prob090 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_sampled_prob090_score060_grid.json`

Raising `buy_near_threshold_min_prob` from `0.875` to `0.9` did not help:

- Validation baseline net profit: `0.0192544647942539` BNB
- Candidate net profit: `0.019166146977559965` BNB
- Delta: `-0.00008831781669393565` BNB
- Trades: `32 -> 40`
- Win rate: `0.84375 -> 0.75`
- Max drawdown: `-8.18251735324681% -> -18.439271563032666%`
- Walk-forward worst return: `79.59654474223983% -> 95.72652671065272%`
- Stress worst net profit: `0.010166721706927569 -> 0.010971179311315297` BNB

The selected rule tightened only slightly to `time_since_launch >= 222.5`, but the soft feature remained high-importance (`0.19234740448717838`). This suggests the problem is not the boundary signal itself; it is that the rescue universe still contains too many drawdown-heavy entries. The next experiment should keep the sampled soft feature but preserve only the base-approved entries as default and score rescue candidates separately with `--preserve-base-candidates`.

## Preserve-Base Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_score060_grid.json`

Running the score060 sampled soft feature with `--preserve-base-candidates` was still rejected by the strict gate, but it is the first train-boundary follow-up in this sequence that improved both validation and final net profit:

- Validation net profit: `0.0192544647942539 -> 0.020696672022367666` BNB (`+0.001442207228113765`)
- Validation trades: `32 -> 40`
- Validation win rate: `0.84375 -> 0.775`
- Validation max drawdown: `-8.18251735324681% -> -17.802076304174253%`
- Validation walk-forward worst return: `79.59654474223983% -> 96.96988460997562%`
- Validation stress worst net profit: `0.010166721706927569 -> 0.011356736725930728` BNB
- Final net profit: `0.006994210572241049 -> 0.007545463282348655` BNB (`+0.0005512527101076067`)
- Final trades: `24 -> 26`
- Final win rate: `0.6666666666666666 -> 0.6153846153846154`
- Final max drawdown: `-12.90811269409964% -> -14.76389731964588%`
- Final walk-forward worst return: `-7.064527500103712% -> -3.7982228328361956%`
- Final stress worst net profit: `0.0028749898853279235 -> 0.0035171020438556806` BNB

The acceptance gate failed on win rate and drawdown (`max_drawdown_pct`, `walk_forward_worst_max_drawdown_pct`, and `stress_worst_max_drawdown_pct`) despite net-profit, walk-forward-return, and stress-profit improvements. The runner-retention scorer preserved `351` base candidates and scored `108770` rescue candidates; the train-only boundary feature stayed active with `runner_retention_train_boundary_match` importance `0.25325615354770065`.

This changes the next direction: preserve-base is promising, but the rescue side is still too broad. The next experiment should keep `--preserve-base-candidates` and raise the rescue/path score floor, starting with `buy_path_state_meta_gate_min_score=0.75`, to try to keep the net-profit and stress gains while removing enough added losers to pass win-rate and drawdown gates.

## Preserve-Base Score075 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_score075_grid.json`

Raising `buy_path_state_meta_gate_min_score` from `0.60` to `0.75` under `--preserve-base-candidates` did not change the selected trade set. The replay stayed rejected with the same metrics as preserve-base score060:

- Validation net profit: `0.0192544647942539 -> 0.020696672022367666` BNB
- Validation trades: `32 -> 40`
- Validation win rate: `0.84375 -> 0.775`
- Validation max drawdown: `-8.18251735324681% -> -17.802076304174253%`
- Final net profit: `0.006994210572241049 -> 0.007545463282348655` BNB
- Final trades: `24 -> 26`
- Final win rate: `0.6666666666666666 -> 0.6153846153846154`
- Final max drawdown: `-12.90811269409964% -> -14.76389731964588%`

This falsifies score-floor tightening in the `0.60 -> 0.75` band: the rescue candidates that survive the train-boundary scorer already clear the higher path-state score. The next experiment should constrain a different axis that can actually reduce the added set, such as `buy_near_min_pred_return`, `buy_near_min_entry_volume_30s`, or a direct rescue-probability/rank cap, while keeping `--preserve-base-candidates`.

## Preserve-Base Trade-Delta Attribution

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_score075_trade_delta.json`

The selected trade-delta attribution explains why preserve-base improved net profit but failed win-rate and drawdown gates:

- Validation added candidate trades: `13`, with `8` wins / `5` losses, return sum `+736.1336009685672%`
- Validation removed baseline trades: `5`, with `4` wins / `1` loss, return sum `+470.5714349546618%`
- Final added candidate trades: `7`, with `1` win / `6` losses, return sum `+57.17388004163721%`
- Final removed baseline trades: `5`, with `1` win / `4` losses, return sum `-47.427779083788764%`

So preserve-base can raise net profit by replacing several final baseline losers, but the added final rescue set is too loss-heavy (`1/7` win rate) and creates drawdown. The feature contrast points away from a simple low-volume rescue constraint: final added stop-loss rows had higher `early_buy_volume`, `volume_30s`, `price_volatility`, `total_buy_volume`, and `trade_frequency` than the non-stop-loss added rows. The next implementation should add parameterized rescue-side ceiling filters for hot-extension features, then test a preserve-base replay with a maximum entry volatility / momentum / volume-style ceiling instead of another minimum volume or score-floor sweep.
