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

## Preserve-Base VolCeil008 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_volceil008_grid.json`

Adding `buy_runner_retention_rescue_max_entry_price_volatility=0.08` under `--preserve-base-candidates` was rejected because it was too strict and became a no-op versus baseline:

- Validation net profit: `0.0192544647942539 -> 0.0192544647942539` BNB
- Validation trades: `32 -> 32`
- Validation win rate: `0.84375 -> 0.84375`
- Final net profit: `0.006994210572241049 -> 0.006994210572241049` BNB
- Final trades: `24 -> 24`
- Final win rate: `0.6666666666666666 -> 0.6666666666666666`
- Scored rescue candidates: `108770 -> 6110` versus the no-ceiling preserve-base run

The risk gates recovered because the replay selected only baseline trades, but net profit did not improve. This keeps the hot-extension ceiling direction alive while falsifying the `0.08` setting. The next experiment should loosen the ceiling to `0.10`, which is closer to the attribution boundary where final stop-loss added rows started (`~0.0605-0.1022`) while validation stop-loss rows mostly sat above `~0.097`.

## Preserve-Base VolCeil010 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_volceil010_grid.json`

Loosening the volatility ceiling to `buy_runner_retention_rescue_max_entry_price_volatility=0.10` was still rejected as a no-op versus baseline:

- Validation net profit: `0.0192544647942539 -> 0.0192544647942539` BNB
- Validation trades: `32 -> 32`
- Validation win rate: `0.84375 -> 0.84375`
- Final net profit: `0.006994210572241049 -> 0.006994210572241049` BNB
- Final trades: `24 -> 24`
- Final win rate: `0.6666666666666666 -> 0.6666666666666666`
- Scored rescue candidates: `6110 -> 12856` versus volceil008, still far below the no-ceiling `108770`

The setting is still too strict for any expanded rescue to become an actual replay entry. The next experiment should loosen the ceiling again to `0.12` before abandoning volatility ceilings.

## Preserve-Base VolCeil012 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_volceil012_grid.json`

Loosening the volatility ceiling again to `buy_runner_retention_rescue_max_entry_price_volatility=0.12` was still rejected as a no-op versus baseline:

- Validation net profit: `0.0192544647942539 -> 0.0192544647942539` BNB
- Validation trades: `32 -> 32`
- Final net profit: `0.006994210572241049 -> 0.006994210572241049` BNB
- Final trades: `24 -> 24`
- Scored rescue candidates: `12856 -> 20514` versus volceil010, still below the no-ceiling `108770`

The replay still selected only baseline trades. The next experiment should stop single-stepping and use a wider volatility-ceiling grid (`0.15`, `0.20`, `0.30`) to locate where expanded rescue trades start reappearing.

## Preserve-Base VolCeil015/020/030 Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_volceil015_020_030_grid.json`

A wider volatility-ceiling grid found the first active region. `0.15` and `0.30` were no-ops versus the regenerated report baseline, while `0.20` selected expanded rescue trades and was the best candidate:

- Validation net profit: `0.021094872145773796 -> 0.023328161474807346` BNB
- Validation trades: `32 -> 35`
- Validation win rate: `0.75 -> 0.8`
- Validation max drawdown: `-9.882063701276877% -> -10.629430038254872%`
- Validation walk-forward worst net return: `87.29422785362748% -> 114.31996385582126%`
- Validation stress worst net profit: `0.011148541483943297 -> 0.013079793200217672` BNB
- Final net profit: `0.005685226969249181 -> 0.005991960022322411` BNB
- Final trades: `24 -> 25`
- Final win rate: `0.5833333333333334 -> 0.56`
- Final max drawdown: `-18.22920277638137% -> -18.089417548633513%`
- Final stress worst net profit: `0.0016694143812187997 -> 0.002026417643520605` BNB

Result: rejected, but materially more promising than the no-op ceilings. Validation failed drawdown gates (`max_drawdown_pct` and `walk_forward_worst_max_drawdown_pct`), while final confirmation improved profit/drawdown/stress but failed the win-rate gate. No live switch, no `.env`, model artifact, threshold, sizing, or bot restart change. The next experiment should write selected trade-delta attribution for the `0.20` candidate and then search a second condition that removes the final losing added trade without giving up the profit/stress gain.

## Preserve-Base VolCeil020 Trade-Delta Attribution

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260528_train_boundary_soft_feature_preserve_base_volceil020_trade_delta.json`

The single-point `0.20` run reproduced the active volatility-ceiling result and wrote selected trade-delta attribution.

- Validation added candidate trades: `7`, with `6` wins / `1` loss, return sum `+673.8993255323189%`
- Validation removed baseline trades: `4`, with `2` wins / `2` losses, return sum `+258.2272394338749%`
- Final added candidate trades: `3`, with `1` win / `2` losses, return sum `+141.5242869252002%`
- Final removed baseline trades: `2`, with `1` win / `1` loss, return sum `+83.32087917450748%`

The final net-profit gain comes from one large added winner (`+186.68527822325188%`) and improving one existing stop-loss path (`-47.46496070300593%` baseline to `-33.4009224076938%` candidate), but the extra final added loss (`-11.760068890357907%`) pulls win rate below the strict gate. The final stop-loss added row is a hot-extension shape with higher `price_volatility`, `price_momentum`, `price_change_pct`, `trade_frequency`, `early_buy_volume`, and `early_volume_ratio`; the extra episode-end loss is harder to separate from the winner with the current hard-coded ceiling knobs.

Conclusion: no live switch. The next implementation should replace the growing list of hard-coded rescue ceiling knobs with a generic decision-time feature-bound parser, then test `0.20` plus a second rescue-side feature bound chosen from this attribution. Treat symbol/name length as diagnostic only unless it survives replay, because validation winners also include long symbols/names.

## Preserve-Base VolCeil020 Generic Second-Condition Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_generic_second_condition_grid.json`

After adding the generic rescue feature-bound parser, a six-candidate attribution-driven grid tested `volatility<=0.20` plus second conditions on `price_momentum`, `price_change_pct`, `time_since_launch`, and `early_volume_ratio`. All six candidates were rejected as no-ops versus the regenerated baseline:

- Validation net profit stayed `0.021094872145773796` BNB for every candidate.
- Validation trades stayed `32`, win rate stayed `0.75`, and max drawdown stayed `-9.882063701276877%`.
- Final selected candidate also stayed at its baseline metrics: net profit `0.005084036893262802` BNB, trades `26`, win rate `0.5384615384615384`, and max drawdown `-18.22920277638137%`.
- The generic parser was active; scored rescue candidates ranged from `457` to `46700`, but none survived into actual selected replay entries.

Result: rejected/no-op. The second-condition direction was too restrictive when applied as hard rescue eligibility. The next direction should stop hard-filtering the attribution features and instead test a softer ranking/selection mechanism, such as a rescue top-rank cap or score calibration that can keep only the highest runner-retention rescues after `volatility<=0.20`.

## Preserve-Base VolCeil020 RankCap Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_rankcap_grid.json`

After adding `buy_runner_retention_rescue_max_rank_per_episode`, a six-candidate grid tested the prior active `volatility<=0.20` preserve-base candidate with no rank cap and caps of `1`, `2`, `3`, `5`, and `8` expanded rescues per episode.

Result: rejected.

- The no-cap control stayed the best validation candidate: net profit `0.021094872145773796 -> 0.023328161474807346` BNB, trades `32 -> 35`, win rate `0.75 -> 0.8`, but max drawdown worsened to `-10.629430038254872%` and walk-forward worst max drawdown worsened to `-20.69504321270199%`.
- `rank_cap=1` cut scored rescue candidates from `55275` to `2873`, but validation still failed the same drawdown gates and net profit fell to `0.0225566486558376` BNB.
- `rank_cap=2` cut scored rescue candidates to `5562`, but validation still failed the same drawdown gates and net profit fell to `0.022950605291799292` BNB.
- `rank_cap=3`, `5`, and `8` produced the same validation trade metrics as the no-cap control.
- The selected no-cap final confirmation improved net profit `0.005084036893262802 -> 0.005390769946336032` BNB, max drawdown `-18.22920277638137% -> -18.089417548633513%`, and stress worst net profit `0.0010162439781012198 -> 0.001373247240403025` BNB, but failed win rate (`0.5384615384615384 -> 0.5185185185185185`).

Conclusion: the rescue rank cap works mechanically, but it is not the missing optimization. The drawdown-heavy rescue is already in the top-ranked set, so cutting tail rescues reduces profit before it fixes risk. The next direction should change the runner-retention scoring target itself, for example by adding a drawdown/risk-aware negative label or utility target, rather than applying more post-score rank caps.

## Preserve-Base VolCeil020 Label-MAE Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_label_mae_grid.json`

After adding `buy_runner_retention_label_min_mae_pct`, a four-candidate grid tested the no-risk-label control plus `min_mae_pct=-18`, `-15`, and `-12` while keeping the prior active `volatility<=0.20` preserve-base setup and `buy_path_state_meta_gate_min_score=0.75`.

Result: rejected.

- The no-risk-label control again stayed the best validation candidate: net profit `0.021094872145773796 -> 0.023328161474807346` BNB and win rate `0.75 -> 0.8`, but failed max-drawdown and walk-forward-drawdown gates.
- `min_mae_pct=-18` relabeled `170` raw train positives as risk-rejected, changing raw train labels from `2011` positives to `1841`; validation then selected only baseline trades, with net profit unchanged at `0.021094872145773796` BNB.
- `min_mae_pct=-15` relabeled `513` raw train positives as risk-rejected and also selected only baseline trades.
- `min_mae_pct=-12` relabeled `821` raw train positives as risk-rejected and also selected only baseline trades.
- Because these risk-aware candidates tied the baseline exactly, they failed the strict net-profit improvement gate.

Conclusion: the risk-aware label works, but the old `0.75` score floor is miscalibrated after label tightening. The next experiment should keep `min_mae_pct=-18/-15` and sweep lower path-state score floors, rather than treating this no-op as a failure of the risk-label direction itself.

## Preserve-Base VolCeil020 Label-MAE Score-Floor Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_label_mae_scorefloor_grid.json`

A 15-candidate score-floor calibration grid tested no-risk-label controls at score floors `0.75`, `0.65`, and `0.55`, plus `buy_runner_retention_label_min_mae_pct=-18` and `-15` at score floors `0.70`, `0.65`, `0.60`, `0.55`, `0.50`, and `0.45`.

Result: rejected.

- The no-risk-label `0.75` control remained the best validation candidate: net profit `0.021094872145773796 -> 0.023328161474807346` BNB, trades `32 -> 35`, win rate `0.75 -> 0.8`, and stress worst net profit `0.011148541483943297 -> 0.013079793200217672` BNB. It still failed validation drawdown gates.
- The no-risk-label `0.65` control was slightly worse than `0.75`: net profit `0.023267999703650462` BNB with `36` trades and win rate `0.7777777777777778`.
- `min_mae_pct=-18` became active at score floors `0.60` and lower, but all those floors selected the same weaker trade set: net profit `0.022979692081619485` BNB, `39` trades, win rate `0.717948717948718`, and max drawdown `-18.023403740152833%`.
- `min_mae_pct=-15` also became active at `0.60` and lower and produced the same validation metrics as `-18`, so the stronger risk relabel did not improve selection.
- At `0.70` and `0.65`, both risk-label settings still selected only baseline trades.
- The selected no-risk-label `0.75` final confirmation improved net profit `0.005084036893262802 -> 0.005390769946336032` BNB and stress worst net profit `0.0010162439781012198 -> 0.001373247240403025`, but failed the final win-rate gate (`0.5384615384615384 -> 0.5185185185185185`).

Conclusion: lowering the score floor after MAE relabeling does not rescue this branch. The risk-aware labels can make the scorer active, but the active set is worse than the original `volceil020` control and reintroduces the same drawdown-heavy rescue profile. Next work should stop using a binary relabel plus score-floor calibration as the main lever and instead test a utility-weighted runner-retention target or trade-delta-driven target that directly penalizes low-MAE/high-drawdown rescues while preserving the large winner.

## Preserve-Base VolCeil020 Utility-Label Follow-Up

Report: `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json`

A 13-candidate utility-label grid tested the prior active `volatility<=0.20` preserve-base setup with train-only utility relabeling. The utility label used `mfe_pct + mae_penalty * min(mae_pct, 0)` and swept `buy_runner_retention_label_min_utility_score` across `35`, `45`, `55`, and `65`, MAE penalties `0.5`, `1.0`, and `1.5`, and score floors `0.75` and `0.65`.

Result: utility-label hypothesis rejected; no live switch.

- The selected and best validation candidate was still candidate `0`, the no-utility-label control: validation net profit improved `0.021094872145773796 -> 0.023328161474807346` BNB, trades `32 -> 35`, win rate `0.75 -> 0.8`, walk-forward worst net return `87.29422785362748% -> 114.31996385582126%`, and stress worst net profit `0.011148541483943297 -> 0.013079793200217672` BNB. It still failed validation drawdown gates.
- The best utility-label candidates (`min_utility=55, mae_penalty=0.5` and `min_utility=35, mae_penalty=1.0`) reached only `0.023111078098197922` BNB validation net profit with `37` trades and `0.7567567567567568` win rate, below the no-utility control.
- Other active utility candidates either tied baseline/no-op or reintroduced the weaker drawdown-heavy set, for example `min_utility=45, mae_penalty=0.5` selected `39` trades with `0.717948717948718` win rate and `-18.023403740152833%` max drawdown.
- Final confirmation for the selected no-utility control improved net profit `0.0059171187479749796 -> 0.006223851801048209` BNB, max drawdown `-18.22920277638137% -> -18.089417548633513%`, and stress worst net profit `0.0016816345683702428 -> 0.002038637830672048` BNB, but failed the final win-rate guardrail (`0.5555555555555556 -> 0.5357142857142857`).
- Paired trade-delta still shows outlier dependence: final added trades were `1/3` winners with return sum `+141.5242869252002%`, while removed baseline trades were `1/2` winners with return sum `+83.32087917450748%`. The final paired return delta was only `+58.203407750692705%`; removing the top added winner (`+186.68527822325188%`) makes the paired delta negative at `-128.4818704725592%`.

Tier classification: the utility-label branch is `Rejected`. The older no-utility `volceil020` control remains useful `Research Alpha` evidence under the tiered workflow because it repeatedly improves validation/final net profit and stress, but this utility-label experiment did not create a stronger alpha and did not reduce top-winner dependence. Per the current goal rule, stop runner-retention parameter/label micro-sweeps here and pivot to a structural direction, starting with conditional exit / early-profit harvest.
