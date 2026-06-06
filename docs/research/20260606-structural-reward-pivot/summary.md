# 2026-06-06 Structural Reward Pivot

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- The preceding utility-label rejection was committed and pushed as `a8df601240d64c588c5cc8b53447cb16ebf98366`; GitHub Actions `CI` run `27066797922` passed.

## Live Attribution

Fresh structural-pivot artifacts:

- `data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json`
- `data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.md`
- `data/replay_reports/action_policy_live_shadow_20260606_structural_pivot_entry.json`
- `data/replay_reports/action_policy_live_shadow_20260606_structural_pivot_entry.md`
- `data/replay_reports/action_policy_activation_shadow_20260606_structural_pivot_entry.json`
- `data/replay_reports/action_policy_activation_shadow_20260606_structural_pivot_entry.md`

There were still no new closed trades since the `2026-06-02 21:27:41` close. The attribution report scanned `10098` signal decisions and found `1001` per-token rejected candidates. Barrier classes were `fast_profit=36`, `fast_profit_then_collapse=30`, `slow_runner=23`, `flat_timeout=753`, and `stop_first=159`; recommended policies were `quick_take_profit=66`, `conditional_slow_hold=23`, and `skip=912`.

The live-shadow report scored `10099` signals: `1` queued, `10098` rejected, `78` read-only `continue_hold` routes, `1` queued shadow-used row, and `0` matched trades. Activation-aware shadow had `0` matched rows, `0` activation hits, and `0` release hits.

This ruled out direct router enablement. The only safe structural pivot was a read-only accepted-action / rejected-action reward selector that could be falsified before any replay or runtime discussion.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment reused already researched and implemented action-policy reward/LCB tooling:

- `docs/research/20260526-support-lcb-replay-gate/summary.md`
- `docs/research/20260601-signal-flow-parity-reward-probe/summary.md`
- `docs/research/20260606-post-flow-accepted-action-router-shadow/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

The new live-derived angle was the current post-commit rejected-path population, where fast-profit-shaped support was large but stop-first and flat-timeout rows were also abundant.

## Hypothesis

If a structural action-policy reward selector can preserve the accepted-action continuation edge while safely selecting rejected-entry quick-profit opportunities, it should keep accepted/rejected support in validation and final splits and maintain a positive bootstrap lower confidence bound on reward.

Falsification rule: reject if validation or final support disappears, if final selected reward lower confidence bound is non-positive, or if the selected rejected population is dominated by stop-first / timeout rows instead of quick-profit rows.

## Experiment

The reward probe reused the support-complete accepted-action train/validation/final reports and the prior flow-parity rejected train/validation reports, then used the fresh `20260606_structural_pivot_entry` attribution as final rejected evidence.

Reward probes:

```bash
venv/bin/python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260606_structural_pivot_entry.json \
  --final-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --probability-threshold 0.2 \
  --output data/replay_reports/action_policy_reward_probe_20260606_structural_pivot_thr02.json \
  --force
```

The same command was rerun at thresholds `0.4`, `0.6`, and `0.8`, writing the corresponding `thr04`, `thr06`, and `thr08` reports.

LCB diagnostic:

```bash
venv/bin/python scripts/probe_action_policy_reward_lcb.py \
  --reward-report data/replay_reports/action_policy_reward_probe_20260606_structural_pivot_thr02.json \
  --output data/replay_reports/action_policy_reward_lcb_probe_20260606_structural_pivot_thr02.json \
  --bootstrap-samples 5000 \
  --force
```

## Results

- Threshold `0.2` was the only reward-probe variant that passed support.
- Thresholds `0.4`, `0.6`, and `0.8` were `shadow_only_support_limited` because validation selected no rejected-family rows.
- The `0.2` reward probe decision before LCB was `shadow_reward_positive_replay_required`, but this was downgraded by the LCB diagnostic.
- Model feature importances were dominated by `pred_return=0.8306789039018647`, then `prob=0.09568459219393464`, `flow_total_volume_30s=0.04672498546814197`, and `flow_buy_volume_10s=0.02691151843605868`.

Threshold `0.2` validation:

- Candidates: `70` total, `32` accepted and `38` rejected.
- Selected: `38` total, `32` accepted and `6` rejected.
- Selected reward: `+2921.030679579%`, average `+76.86922840997369%`.
- Selected rejected classes: `flat_timeout=4`, `stop_first=2`, and no quick-profit selections.
- LCB average reward: `+56.44340793263554%`.

Threshold `0.2` final:

- Candidates: `1022` total, `21` accepted and `1001` rejected.
- Selected: `360` total, `21` accepted and `339` rejected.
- Selected reward: `+577.7401432824%`, average `+1.60483373134%`.
- Selected rejected classes: `fast_profit=24`, `fast_profit_then_collapse=25`, `flat_timeout=162`, `slow_runner=5`, and `stop_first=123`.
- LCB average reward: `-0.9647304033557774%`.
- LCB decision: `shadow_reward_non_positive_rejected`, with stability reason `final_reward_lcb_non_positive`.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this structural pivot changes the next-direction constraints: current rejected-path fast-profit support is large, but this generic reward selector over-selects stop-first and flat-timeout rows and fails the final lower-confidence-bound gate.

Next direction: do not promote this action-policy reward selector and do not live-enable the router from current live shadow. The accepted-action router remains prior `Shadow Candidate` evidence, but current live shadow has `0` matched trades; future work needs a selector that explicitly avoids stop-first / timeout rejected rows, or continued audit-only shadow collection before a separate live-risk review.
