# 2026-06-08 Continue-Hold Shadow Reward LCB Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `BUY_ACTION_POLICY_ROUTER_ENABLED=false`, and `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`.
- Latest committed milestone before this work was `c284cde research: isolate continue hold router shadow`; GitHub Actions run `27147896985` passed.
- Active node state: not archived. The latest prior milestone was committed, pushed, and CI green.

Fresh no-switch reports:

- `data/replay_reports/live_trade_attribution_20260608_continue_hold_shadow_watch_2327.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_audit_20260608_continue_hold_shadow_watch_2327.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_path_attribution_20260608_continue_hold_shadow_watch_2327.json` / `.md`

Live attribution since the `2026-06-07 12:25:39` close found `0` new closed trades. Rejected-path support was `fast_profit=41`, `fast_profit_then_collapse=51`, `slow_runner=15`, `flat_timeout=614`, and `stop_first=147`. Recommended policies were `quick_take_profit=92`, `conditional_slow_hold=15`, and `skip=761`.

Recorded in-process shadow audit since `2026-06-08 15:02:20` had `3715` signal rows, `3635` rows with recorded shadow fields, `5` recorded shadow-used rows, `2` queued recorded shadow-used rows, and `0` matched trades. Recorded routes were `continue_hold=6`, `quick_take_profit=162`, and `skip=3467`. Recorded quick-take-profit precision stayed weak at `26/162 = 0.16049382716049382`.

## Prior Review

The current strongest material evidence remains the continue-hold-only accepted-action router from `docs/research/20260608-post-boundary-continue-hold-router/summary.md`. It improved common accepted trades with no added or removed entries, but it is not live-switch evidence because in-process matched shadow support is still absent.

The stale `volceil020` runner-retention utility-label branch is already resolved. `docs/research/20260606-preserve-base-utility-grid/summary.md` and `docs/model_scoreboard.md` record that it was rejected by the uncertainty gate and should not be reopened as another runner-retention parameter/label micro-sweep.

The prior structural reward selector in `docs/research/20260606-structural-reward-pivot/summary.md` was rejected because final reward LCB was negative and selected rejected rows were dominated by flat-timeout and stop-first contamination.

## Research Reused

No new SmartSearch run was needed. This boundary reused committed research and tooling:

- `docs/research/20260526-support-lcb-replay-gate/summary.md`
- `docs/research/20260606-structural-reward-pivot/summary.md`
- `docs/research/20260608-post-boundary-continue-hold-router/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: the latest rejected-path population reduced the reward selector's final selected rejected rows from the prior `339` to `38`, and the reward LCB turned positive. The smallest useful falsifier was to rerun the existing reward probe/LCB and then promote the positive LCB to strict candidate-gate replay.

## Hypothesis Portfolio

1. Current-data structural reward selector refresh: selected. Expected impact is medium because it can combine accepted-action continuation with rejected-entry opportunity selection; evidence improved because current final LCB may be positive; falsifiability is high via existing reward LCB and strict replay; implementation cost is low.
2. Continue-hold live-risk review: deferred. Offline evidence is strongest, but recorded in-process support is only `2` queued shadow-used rows and `0` matched trades.
3. Replay-compatible freshness propagation: deferred. Prior strict replay context was missing or degenerate for the selected freshness proxy.
4. Quick-profit route selector: rejected for now. Recorded quick-take-profit precision remains weak and strict quick-profit replays already failed.

## Hypothesis

If the current live rejected population makes the structural action-policy reward selector cleaner than the 2026-06-06 run, the `0.2` reward threshold should keep validation and final support, pass positive bootstrap LCB, then improve strict replay net profit or risk metrics under unchanged 10 percent sizing.

Falsification rule: reject if validation/final support disappears, final LCB is non-positive, strict replay fails validation or final gates, the gate only no-ops versus baseline, or it worsens trade count, win rate, drawdown, walk-forward, stress, or net profit.

## Experiment

Reward probes:

```bash
venv/bin/python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260608_continue_hold_shadow_watch_2327.json \
  --final-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --probability-threshold 0.2 \
  --output data/replay_reports/action_policy_reward_probe_20260608_continue_hold_shadow_watch_thr02.json \
  --force
```

The same command was rerun at thresholds `0.4`, `0.6`, and `0.8`.

LCB diagnostic:

```bash
venv/bin/python scripts/probe_action_policy_reward_lcb.py \
  --reward-report data/replay_reports/action_policy_reward_probe_20260608_continue_hold_shadow_watch_thr02.json \
  --output data/replay_reports/action_policy_reward_lcb_probe_20260608_continue_hold_shadow_watch_thr02.json \
  --bootstrap-samples 5000 \
  --force
```

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_candidate_gate_replay.py \
  --source-lcb-report data/replay_reports/action_policy_reward_lcb_probe_20260608_continue_hold_shadow_watch_thr02.json \
  --output data/replay_reports/action_policy_candidate_gate_replay_20260608_continue_hold_shadow_reward_lcb.json \
  --force
```

Strict assumptions stayed at 10 percent sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and no fixed stake.

## Results

Reward probe:

- Threshold `0.2`: `shadow_reward_positive_replay_required`.
- Thresholds `0.4`, `0.6`, and `0.8`: `shadow_only_support_limited`.
- Validation selected `38` rows: `32` accepted and `6` rejected, with selected reward `+2921.030679579%` and average `+76.86922840997369%`.
- Final selected `59` rows: `21` accepted and `38` rejected, with selected reward `+1446.7401432824%` and average `+24.521019377667795%`.
- Final selected classes were `fast_profit=5`, `fast_profit_then_collapse=6`, `flat_timeout=12`, `stop_first=15`, `post_target_continuation=14`, `post_target_collapse=4`, `post_target_unresolved=1`, and `target_not_hit=2`.

LCB:

- Decision: `shadow_reward_positive_lcb_replay_required`.
- Validation LCB: `+56.44340793263554%`.
- Final LCB: `+11.602487048429747%`.
- Support and stability gates both passed.

Strict replay:

- Decision: `reject`.
- Candidate count: `4`.
- Best validation candidate: `buy_path_state_meta_gate_min_score=0.2`.
- Validation baseline and selected net profit both `0.012252343033424175` BNB.
- Validation trades, win rate, max drawdown, walk-forward worst return, and stress worst net profit all tied baseline: `23`, `0.7391304347826086`, `-7.361964742920057%`, `2.8446315943470024%`, and `0.004609956337437153` BNB.
- The `0.2`, `0.4`, and `0.6` replay candidates were no-ops on strict validation economics and failed only the required net-profit-improvement gate.
- The `0.8` candidate reduced trades `23 -> 12`, cut validation net profit to `0.004312526665739055` BNB, lowered win rate to `0.6666666666666666`, worsened walk-forward worst return to `-3.8775606477391533%`, and reduced stress worst profit to `0.0020626013060232396` BNB.

## Decision

Outcome tier: `Rejected` as a strict replay candidate.

The positive current-data reward LCB is useful `Research Alpha` input evidence, but it did not become a strict replay candidate because the replay-integrated gate either no-oped versus baseline or under-traded and worsened risk/profit. No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this changes the structural reward selector interpretation: the current live slice makes the read-only LCB positive, but the existing replay integration still cannot translate it into profit improvement. Next work should avoid another path-state score-floor sweep and either keep collecting continue-hold in-process shadow evidence or design a structurally different reward-to-replay bridge that changes candidate economics instead of reproducing baseline trades.
