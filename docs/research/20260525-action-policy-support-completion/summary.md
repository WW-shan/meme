# Action-Policy Support Completion Research

Date: 2026-05-25

## Question

For the live v95 action-policy reward probes, how should we handle sparse final-holdout support gaps when accepted and rejected candidate families are missing, and what conservative diagnostic should prevent deployment of an action-policy overlay?

## SmartSearch Commands

```bash
smart-search doctor --format json
smart-search deep "For offline policy evaluation in sparse trading data, how should we handle support/positivity gaps when accepted and rejected candidate families are missing from a final holdout, and what conservative lower-bound diagnostic should prevent deploying an action-policy overlay?" --budget deep --format json --output docs/research/20260525-action-policy-support-completion/01-plan.json
smart-search search "offline policy evaluation positivity support overlap assumption sparse data off-policy evaluation" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-action-policy-support-completion/02-search-ope-support.json
smart-search search "conservative off-policy evaluation lower confidence bound offline policy learning deployment support overlap" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-action-policy-support-completion/03-search-conservative-lcb.json
smart-search search "offline reinforcement learning extrapolation error out-of-distribution actions support conservative Q learning" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-action-policy-support-completion/04-search-offline-rl-support.json
smart-search fetch "https://openreview.net/forum?id=kLo4TKh0OP" --format markdown --output docs/research/20260525-action-policy-support-completion/05-fetch-ceopl-openreview.md
smart-search fetch "https://proceedings.mlr.press/v235/khan24b.html" --format markdown --output docs/research/20260525-action-policy-support-completion/06-fetch-ope-beyond-overlap.md
smart-search fetch "https://proceedings.neurips.cc/paper/2020/hash/0d2b2061826a5df3221116a5085a6052-Abstract.html" --format markdown --output docs/research/20260525-action-policy-support-completion/07-fetch-cql-neurips.md
smart-search fetch "https://proceedings.mlr.press/v216/rothfuss23a.html" --format markdown --output docs/research/20260525-action-policy-support-completion/08-fetch-hambo-conservative-control.md
```

`02-search-ope-support.json` recorded an `xAI Responses 返回空结果` failure. The round did not use that failed search for claims. The useful evidence came from the successful searches and fetched pages.

The raw `smart-search doctor` output was not saved because it includes masked API-key fragments. `00-doctor-sanitized.json` records the usable capability state without credential material.

## Fetched Sources

- CEOPL OpenReview page: offline policy learning needs a pre-deployment evaluation method; CEOPL estimates a lower bound on the offline policy using OPE with bootstrap confidence intervals and deploys only when overestimation risk is controlled.
- Khan, Saveski, and Ugander 2024 PMLR page: standard OPE usually assumes overlap between logging and target policies; absent overlap, evaluation needs extra assumptions or conservative bounds.
- Kumar et al. 2020 NeurIPS CQL page: offline RL can fail from distribution shift between dataset and learned policy; CQL uses conservative value estimates that lower-bound policy value to reduce overoptimistic out-of-distribution action selection.
- Rothfuss et al. 2023 PMLR page: conservative OPE seeks a lower bound on policy performance before real-world deployment; uncertainty-aware pessimistic trajectories are one way to make deployment criteria conservative.

## What Applies To This Bot

- A fresh final holdout containing only rejected candidates is not enough to accept a live action-policy overlay. The final holdout must have selected accepted-family and rejected-family support, or the round must explicitly downgrade to shadow-only / support-limited evidence.
- Support-completion is the right next experiment because the prior reward probes failed mainly on final accepted-family absence, not because the reward framing was useless.
- If final selected support is complete, still require a conservative diagnostic: positive validation and final reward, no selected-family collapse dominated by stop-loss, and a lower-bound/proxy stress rule that refuses deployment when selected count is too small or family coverage is missing.
- Because this repo's probe is not a full replay-integrated live policy, even support-complete reward evidence should remain no-switch unless it is later integrated into strict replay, walk-forward, stress, and live execution assumptions.

## What We Reject

- Reject treating rejected-only fresh final reward as deployable OPE evidence.
- Reject using broad threshold or volume relaxation to create support; local live evidence shows many high-probability rejected paths are `PredReturn`-negative, stop-first, or flat.
- Reject using post-decision path labels as decision-time features. Accepted reports may provide labels/rewards, but selected features must remain decision-time fields such as `prob`, `pred_return`, `near_threshold_rescue_used`, and available flow features.
- Reject any live switch from this research node alone.

## Next Experiment

Run a support-completion action-policy reward probe:

- Generate a feature-rich accepted train post-target report if the existing train accepted report lacks decision-time features.
- Use existing feature-rich validation and final accepted reports.
- Use prior rejected path reports for train/validation and the fresh `support_completion_round` live attribution report as the final rejected holdout.
- Run `scripts/probe_action_policy_reward.py` with accepted and rejected reports present in train, validation, and final.
- Reject unless final selected support includes both families and reward quality survives a conservative threshold/stress check.

## Experiment Result

The support-completion experiment was run after generating a feature-rich train accepted report:

- Train accepted report: `data/replay_reports/post_target_exit_state_probe_20260525_support_completion_train_features.json`
- Main reward report: `data/replay_reports/action_policy_reward_probe_20260525_support_completion_final_support.json`
- Threshold stress reports:
  - `data/replay_reports/action_policy_reward_probe_20260525_support_completion_final_support_thr04.json`
  - `data/replay_reports/action_policy_reward_probe_20260525_support_completion_final_support_thr06.json`
  - `data/replay_reports/action_policy_reward_probe_20260525_support_completion_final_support_thr08.json`

The train accepted support report produced `201` accepted candidates with decision-time fields (`prob`, `pred_return`, `near_threshold_rescue_used`), including `155` post-target continuations and `12` post-target collapses.

At reward threshold `0.2`, the support gate passed:

- Validation selected `49` candidates: `31` accepted and `18` rejected; selected reward `+2899.4735%`.
- Final selected `29` candidates: `20` accepted and `9` rejected; selected reward `+1354.2610%`.
- Final selected policy mix: `continue_hold=13`, `lock_profit=4`, `no_action=3`, `quick_take_profit=2`, `stop_loss=5`, `timeout_or_skip=2`.

Threshold stress:

- `0.4`: same selected set as `0.2`; support gate still passed.
- `0.6`: failed support with `validation_rejected_selection_below_min`; validation selected accepted-only.
- `0.8`: failed support with both `validation_rejected_selection_below_min` and `final_rejected_selection_below_min`.

## Decision

Shadow-only / no live switch.

The round successfully fixed the previous final accepted-support blocker, so the action-policy reward idea remains useful. However, this is still a direct reward/support probe, not strict replay, walk-forward, stress, or live-execution evidence. Stricter thresholds drop rejected-family support rather than forming a conservative deployable subset. No `.env`, threshold, sizing, model artifact, or bot process changed.

Next highest-value direction: turn the support-complete reward evidence into a replay-integrated action-policy candidate or a reusable support/LCB diagnostic that automatically rejects reward probes when support disappears under conservative thresholding.
