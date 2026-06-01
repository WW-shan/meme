# 2026-06-01 Post-Router Never-Activated Selector Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in the expected tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.002026614705196296` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, no fixed stake, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Recent bot and collector log tails had no fatal traceback; the collector still showed bounded catch-up lag.
- Latest real trade before this round remained `QIFY`, closed at `2026-06-01 14:16:20.125260`.

## Live Attribution

Artifacts:

- `data/replay_reports/live_trade_attribution_20260601_after_post_router_shadow_boundary.json`
- `data/replay_reports/live_trade_attribution_20260601_after_post_router_shadow_boundary.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 14:16:21' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 96 \
  --output-json data/replay_reports/live_trade_attribution_20260601_after_post_router_shadow_boundary.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_after_post_router_shadow_boundary.md \
  --max-trade-sample 80 \
  --max-candidate-sample 320 \
  --force
```

Result:

- Decision: `NO_GO_FOR_LIVE_SWITCH`.
- Closed trades after `2026-06-01 14:16:21`: `0`.
- Rejected signal decisions: `971`; per-token candidates: `79`.
- Barrier classes: `fast_profit=2`, `fast_profit_then_collapse=4`, `flat_timeout=54`, `stop_first=19`.
- Quick-profit-shaped rejected candidates: `6`, still below the same-shape support gate and mostly negative-PredReturn. This does not reopen a quick-profit rescue replay.

## Prior Review

The immediately prior post-router shadow refresh showed four fresh timeout losses joining the `never_activated_loss` cohort, while `UP` remained the counterexample `never_activated_win`. That made a simple never-activated skip unsafe and made another scalar activation-threshold sweep low value.

Recent committed evidence checked:

- `docs/research/20260601-post-router-freshness-activation-shadow-refresh/summary.md`
- `docs/research/20260601-never-activated-utility-negative-selector/summary.md`
- `docs/research/20260531-direct-paired-delta-utility-ranker/summary.md`
- `docs/research/20260601-post-selector-conditional-exit-router-refresh/summary.md`
- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md`
- `docs/research/20260601-signal-flow-parity-reward-probe/summary.md`

No new SmartSearch pass was opened. This round reused the committed SmartSearch-backed meta-label, action-policy, dead-flow, and freshness research.

## Direction Selection

Ranked directions:

1. Current-lifecycle dead-flow exit replay refresh. Selected because the prior post-router boundary added four fresh never-activated timeout losses, which is new population evidence relative to the earlier dead-flow overlay rejection.
2. Direct reward/meta-label support refresh using the new rejected-signal boundary. Selected because the latest attribution adds `79` rejected candidates, so the right question is whether support is now sufficient rather than whether to replay-expand immediately.
3. Conditional-exit router live enablement. Deferred because it is already a `Shadow Candidate`; runtime enablement is live-risk work requiring explicit switch review and a controlled restart.
4. Activation45/freshness live-shadow accumulation. Useful but passive until another queued trade closes.

Hypothesis: if the fresh no-upside never-activated losses are replay-compatible, a current-lifecycle dead-flow exit replay or direct reward/meta-label support refresh should pass validation/final support without damaging walk-forward, stress, drawdown, or protected winner rows.

Falsification rule: reject if the candidate is inactive, selected support is accepted-only, final support is missing, strict replay gates fail, or selected rejected rows mix opportunity candidates with stop-first losses.

## Experiment 1: Dead-Flow Exit Replay

Artifact:

- `data/replay_reports/dead_flow_exit_replay_20260601_post_router_never_activated_losses.json`

Command:

```bash
venv/bin/python scripts/run_dead_flow_exit_replay.py \
  --output data/replay_reports/dead_flow_exit_replay_20260601_post_router_never_activated_losses.json \
  --force
```

Result:

- Decision: `reject`.
- Candidate grid: `12` bounded dead-flow exit variants.
- Best validation candidate: `buy_dead_flow_exit_min_hold_seconds=180.0`, `buy_dead_flow_exit_max_mfe_pct=0.08`.
- Validation dead-flow exits: `1`.
- Validation net profit tied baseline at `0.022842003299308057` BNB, failing the required `+0.0005` BNB improvement gate.
- Validation stress worsened: worst net profit `0.011661288085 -> 0.010936617415` BNB, and worst return `229.584409706% -> 215.317281853%`.
- Final confirmation failed because the selected candidate had `0` dead-flow exits and tied baseline at `0.002130506358905197` BNB.
- Entry set stayed frozen and profitable baseline trades were not worsened, but activity/profit/stress/final gates were not enough.

Interpretation: the fresh never-activated losses did not convert the bounded dead-flow min-hold / max-MFE overlay into strict replay evidence.

## Experiment 2: Direct Reward / Meta-Label Support Refresh

Artifact:

- `data/replay_reports/action_policy_reward_probe_20260601_post_router_rejected_boundary.json`

Command:

```bash
venv/bin/python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260601_after_post_router_shadow_boundary.json \
  --final-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --output data/replay_reports/action_policy_reward_probe_20260601_post_router_rejected_boundary.json \
  --force
```

Result:

- Decision: `shadow_only_support_limited`.
- Support failure: `validation_rejected_selection_below_min`.
- Train rows: `194` (`100` accepted, `94` rejected).
- Validation rows: `70` (`32` accepted, `38` rejected); selected rows: `31`, all accepted.
- Final rows: `100` (`21` accepted, `79` rejected); selected rows: `26`, with `20` accepted and `6` rejected.
- The six selected final rejected rows were mixed: two quick-profit candidates and four stop-first losses, so the fresh rejected boundary does not form a clean deployable support pocket.
- The model still mostly learns accepted continuation support from `pred_return`, `prob`, and flow-volume fields rather than reliable rejected-signal opportunity selection.

## Tier

Classification: `Rejected` for the dead-flow exit overlay refresh and `Research Alpha diagnostic / support-limited` for the direct reward/meta-label refresh.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

This round reinforces the current next-direction constraints:

- Do not continue bounded dead-flow min-hold / max-MFE sweeps from this population.
- Do not replay-promote the direct reward/meta-label branch until validation selects rejected-signal support and final selected rejected rows are not mixed with stop-first losses.
- The strongest current no-switch candidate remains the accepted-action conditional-exit router `Shadow Candidate`; live enablement is a separate live-risk task.
- Otherwise, continue collecting activation45/freshness live-shadow evidence until new queued trades close.

## Scoreboard

`docs/model_scoreboard.md` was updated because this boundary rejects the current-lifecycle dead-flow refresh and keeps the direct reward/meta-label branch support-limited after the latest post-router rejected-signal evidence.
