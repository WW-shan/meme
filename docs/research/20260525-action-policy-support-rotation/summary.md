# Action-Policy Support Rotation Research

Date: 2026-05-25

## Question

Can the replay-style action-policy reward probe be promoted by using fresher live rejected paths, accepted-source rotation, and a conservative support rule?

## SmartSearch Evidence

Deep Research plan:

- `docs/research/20260525-action-policy-support-rotation/01-plan.json`

Fetched evidence:

- `05-fetch-ope-review.md` and `09-fetch-ope-review-pdf.md`: Uehara, Shi, and Kallus' OPE review states that off-policy evaluation estimates a target/evaluation policy from historical behavior-policy data, and that weak positivity/support inclusion is an assumption for identification.
- `06-fetch-cql.md` and `10-fetch-cql-pdf.md`: Conservative Q-Learning frames offline RL's central risk as distribution shift from the dataset to the learned policy and uses conservative lower-bound value estimates to reduce overestimation.
- `07-fetch-conservative-eval.md`: Conservative Evaluation of Offline Policy Learning uses a train/test stream and lower-bound estimates with bootstrap confidence intervals to decide when deployment risk is acceptable.
- `08-fetch-purged-cv.md`: the finance CV source emphasizes purging/embargoing path-dependent labels to prevent leakage across folds.

Research implication for this repo:

- A reward probe without final support for both accepted and rejected families is not identifiable enough for live deployment.
- Fresh rejected-only final evidence can be used as a stress diagnostic, but not as a support-complete acceptance gate.
- Source rotation is useful only if it preserves family support and avoids using post-decision path labels as decision-time features.

## Live Trigger

Latest attribution report:

- `data/replay_reports/live_trade_attribution_20260525_next_research_round.json`

Since `2026-05-25 18:11:13`, there were no closed live trades. The attribution probe found `123` rejected per-token candidates from `3658` signal decisions:

- `fast_profit=8`
- `fast_profit_then_collapse=18`
- `flat_timeout=75`
- `slow_runner=1`
- `stop_first=21`

The live-derived direction stayed the same: rejected fast-profit / fast-collapse paths are the most plausible source of incremental action-policy value, but they need conservative reward and support checks.

## Experiment

Primary support-rotation command:

```bash
python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_2250_since_221344_correct_abstention.json \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260524_negative_return_reject_option_since_1546.json \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260525_action_policy_validation_features.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260525_path_state_replay.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260525_action_policy_final_features.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260525_next_research_round.json \
  --output data/replay_reports/action_policy_reward_probe_20260525_support_rotation_current_final.json \
  --probability-threshold 0.2 \
  --max-depth 3 \
  --min-samples-leaf 50 \
  --min-common-features 2 \
  --min-selected-per-family 1 \
  --force
```

Reports:

- `data/replay_reports/action_policy_reward_probe_20260525_support_rotation_current_final.json`
- `data/replay_reports/action_policy_reward_probe_20260525_support_rotation_swap_current_final.json`
- `data/replay_reports/action_policy_reward_probe_20260525_support_rotation_current_final_thr04.json`
- `data/replay_reports/action_policy_reward_probe_20260525_support_rotation_current_final_thr06.json`
- `data/replay_reports/action_policy_reward_probe_20260525_support_rotation_current_final_thr08.json`

Results:

| Report | Threshold | Decision | Validation selected / reward | Fresh final selected / reward | Final policy mix |
|---|---:|---|---:|---:|---|
| `support_rotation_current_final` | `0.2` | `shadow_only_support_limited` | `39`, `+1133.2594%` | `45`, `+312.0%`, avg `+6.9333%` | `quick_take_profit=24`, `stop_loss=16`, `timeout_or_skip=5` |
| `support_rotation_swap_current_final` | `0.2` | `shadow_only_support_limited` | `51`, `+2499.4985%` | `45`, `+262.0%`, avg `+5.8222%` | `quick_take_profit=22`, `stop_loss=16`, `timeout_or_skip=7` |
| `support_rotation_current_final_thr04` | `0.4` | `shadow_only_support_limited` | `27`, `+1141.2594%` | `24`, `+95.0%`, avg `+3.9583%` | `quick_take_profit=11`, `stop_loss=10`, `timeout_or_skip=3` |
| `support_rotation_current_final_thr06` | `0.6` | `shadow_only_support_limited` | `0`, `0` | `0`, `0` | none |
| `support_rotation_current_final_thr08` | `0.8` | `shadow_only_support_limited` | `0`, `0` | `0`, `0` | none |

The model used only decision-time fields: `near_threshold_rescue_used`, `pred_return`, and `prob`.

## Decision

Rejected / no live switch.

This round did not optimize the live model. The validation reward remains positive, but the fresh final holdout still has no accepted-family support and the selected rejected set remains mixed with too many stop-loss paths. Raising the selection threshold does not create a conservative subset: at `0.4`, final average reward falls, and at `0.6+` the policy selects nothing.

No `.env`, threshold, sizing, model artifact, or bot process changed.

Scoreboard updated: yes, in `docs/model_scoreboard.md`.

Next highest-value direction: build or mine a support-complete replay dataset for action-policy evaluation, especially accepted final/post-target paths with decision-time features, before attempting another policy overlay. If support cannot be completed, shift from deployment-oriented action policy to a reusable support/LCB diagnostic that rejects such probes automatically and guides data collection.
