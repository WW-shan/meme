# Support-Complete Meta-Label

## What I checked

- `smart-search deep` plan: `01-deep-plan.json`
- Preflight: `smart-search doctor --format json`
- Broad searches: `02-ope-support-search.json`, `03-meta-labeling-search.json`
  - Both failed at the configured main-search provider with xAI 503 after the doctor had already reported xAI 429. I did not fall back to native web search.
- Fetches:
  - `04-fetch-hudson-thames-meta-labeling.md`
  - `05-fetch-doubly-robust-policy-eval.md`
  - `07-fetch-doubly-robust-rl-ope.md`
  - `08-fetch-counterfactual-risk-minimization.md`
  - `09-fetch-split-conformal.md`
  - `10-fetch-propensity-common-support.md`
  - `11-fetch-doubly-robust-estimation.md`

## Research takeaways

- Meta-labeling works as a second-stage filter on top of a strong primary signal.
- Support overlap / positivity matters. If accepted and rejected rows do not share a usable decision-time support set, OPE-style selection is just extrapolation.
- Doubly robust estimators are useful as a diagnostic lens because they reduce dependence on any single misspecified model, but they still need support.

## Experiment change

The earlier support-complete reward probe was still learning mostly from `prob` and `pred_return`. I changed the accepted post-target report generation so accepted rows now carry the same entry-time flow features as rejected signal rows.

New accepted/report evidence:

- `post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json`
- `post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json`
- `post_target_exit_state_probe_20260526_support_complete_entryflow_final.json`

New reward probe evidence:

- `action_policy_reward_probe_20260526_support_complete_entryflow.json`
- `action_policy_reward_probe_20260526_support_complete_entryflow_thr04.json`
- `action_policy_reward_probe_20260526_support_complete_entryflow_thr06.json`
- `action_policy_reward_probe_20260526_support_complete_entryflow_thr08.json`

## Result

- Main threshold `0.2`: support gate passed.
- Validation selected `32` accepted / `22` rejected, reward `3056.030679579`.
- Final selected `21` accepted / `15` rejected, reward `1422.7401432824`.
- Threshold `0.4`: same selected set as `0.2`, still passed.
- Threshold `0.6`: support-limited because rejected selections fell below minimum.
- Threshold `0.8`: support-limited on both validation and final.

Feature importances now include flow state, not just `prob` and `pred_return`. The top features were `pred_return`, `prob`, `flow_total_volume_60s`, `flow_buy_volume_10s`, `flow_buy_sell_ratio_30s`, and `flow_event_count_30s`.

## Decision

Shadow-only, no live switch.

This is better evidence than the previous support-complete probe because the accepted side now has the same entry-time flow vocabulary as the rejected side. The next highest-value direction is still a replay-integrated candidate gate or a reusable support/LCB diagnostic, not a live deployment.
