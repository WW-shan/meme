# 2026-06-06 Post-Flow Accepted-Action Router Shadow Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `1de29765b9897e44d7418554325c2ec3abfbff45`, pushed to `origin/main`, with GitHub Actions `CI` run `27057862063` passing.
- Recent logs showed recurring listener catch-up lag and provider fallback warnings, but no sampled fatal traceback, failed buy/sell loop, or open-position risk requiring restart.

## Live Attribution

Fresh current-stream artifacts reused from the 20260606 flow-activation boundary:

- `data/replay_reports/live_trade_attribution_20260606_current_stream_refresh.json`
- `data/replay_reports/live_trade_attribution_20260606_current_stream_refresh.md`
- `data/replay_reports/action_policy_live_shadow_20260606_current_stream_refresh.json`
- `data/replay_reports/action_policy_live_shadow_20260606_current_stream_refresh.md`
- `data/replay_reports/action_policy_activation_shadow_20260606_current_stream_refresh.json`
- `data/replay_reports/action_policy_activation_shadow_20260606_current_stream_refresh.md`

The attribution window had `0` new closed live trades after the previous boundary. The last paper-trade close remained the `2026-06-02 21:27:41` `ENTRY_SLIPPAGE_PROTECTION` close. The signal stream had `1985` rejected signal decisions and `288` per-token candidates. Barrier classes were `fast_profit=4`, `fast_profit_then_collapse=5`, `flat_timeout=258`, `slow_runner=2`, and `stop_first=19`; recommended policies were `quick_take_profit=9`, `conditional_slow_hold=2`, and `skip=277`.

Action-policy live shadow found `1` queued signal, `1985` rejected signals, `19` read-only `continue_hold` routes, and `0` matched trades. Activation-aware shadow had `0` matched rows, `0` activation hits, and `0` release hits.

This made live enablement inappropriate. The useful live-derived angle was to retest the existing accepted-action router after the hard flow-activation structure failed, because the router changes common accepted exits instead of adding rejected entries or vetoing accepted entries.

## Prior Research Reused

No new SmartSearch pass was opened because this is a refresh of the already researched conditional-exit / accepted-action router line:

- `docs/research/20260602-current-lifecycle-conditional-exit-router-refresh/summary.md`
- `docs/research/20260606-flow-activation-structural-refresh/summary.md`
- `docs/research/20260601-post-selector-conditional-exit-router-refresh/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: after the 20260606 current stream showed no matched activation support and the hard flow-activation replay rejected, retest whether the accepted-action router still improves common accepted trades on the current lifecycle without changing entries or 10 percent sizing.

## Hypothesis Portfolio

1. **Accepted-action conditional-exit router paired-delta refresh**. Selected because it is structural, keeps the entry set fixed, keeps the 10 percent live-sizing assumptions, and can produce material shadow-only evidence without a live-risk runtime change.
2. **Signal-time freshness / accepted-action trade-delta tooling for original proxy fields**. High long-term value, but larger implementation cost because strict replay still lacks the original live freshness fields.
3. **Rejected-entry quick-profit / slow-runner rescue**. Deferred because fresh same-shape support was small (`9` quick-profit-shaped hints and `2` slow runners), and prior runner-retention sweeps failed strict gates.
4. **Direct live enablement of the router**. Deferred because fresh live shadow still has no matched activation/release support; runtime enablement is a separate live-risk review.

## Hypothesis

If the post-flow accepted-action router still improves realized exits on current lifecycle data, strict replay should improve validation and final net profit, walk-forward, stress, and paired common-trade delta without adding or removing trades, worsening win rate, or increasing live sizing.

Falsification rule: reject or downgrade if validation or final fails the strict replay acceptance gate, paired common-trade delta is not positive and stable, top-winner dependency appears, or the result requires added/removed trades rather than improving common accepted-action exits.

## Experiment

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260606_post_flow_activation_reject_current_lifecycle.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260606_post_flow_activation_reject_current_lifecycle.json \
  --candidate-id post_flow_activation_router_20260606 \
  --output data/replay_reports/replay_uncertainty_gate_20260606_post_flow_activation_router.json \
  --force
```

Selected candidate:

- Candidate index: `17` of `18`.
- `buy_action_policy_router_min_confidence=0.55`.
- `buy_action_policy_continue_hold_activation_pct=0.35`.
- `buy_action_policy_continue_hold_release_pct=0.75`.
- `buy_quick_profit_overlay_take_profit_pct=0.25`.
- `buy_quick_profit_overlay_max_hold_seconds=120`.

Strict assumptions were `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, no fixed stake, and `buy_action_policy_router_skip_passthrough=true`.

## Results

Replay decision: `accept`. Live-switch evidence: `false`.

Validation baseline to selected:

- Net profit BNB: `0.012252343033424175 -> 0.012635376578461251`.
- Trades: unchanged at `23`.
- Win rate: unchanged at `0.7391304347826086`.
- Max drawdown: unchanged at `-7.361964742920057%`.
- Walk-forward worst return: `2.8446315943470024% -> 8.40850488379996%`.
- Walk-forward worst drawdown: `-14.377134762904564% -> -14.329703059730136%`.
- Stress worst net profit BNB: `0.004609956337437153 -> 0.004695903033616375`.
- Stress worst return: `90.75962250093363% -> 92.45171872255753%`.
- Stress worst max drawdown: unchanged at `-12.245451556163134%`.
- Router activity: `26` signals, `14` continue-hold entries, `213` forced holds, and `0` quick-profit entries.

Final baseline to selected:

- Net profit BNB: `0.001960790463800862 -> 0.0022003279610865517`.
- Trades: unchanged at `22`.
- Win rate: unchanged at `0.5454545454545454`.
- Max drawdown: unchanged at `-18.206422038627302%`.
- Walk-forward worst return: `-3.927696685669879% -> -0.010208960142532586%`.
- Walk-forward worst drawdown: unchanged at `-18.206422038627302%`.
- Stress worst net profit BNB: `-0.0003650458326306498 -> -0.0001781748282776198`.
- Stress worst return: `-7.186927497780982% -> -3.507859721429718%`.
- Stress worst max drawdown: `-26.925411157799616% -> -24.184914712689608%`.
- Router activity: `24` signals, `11` continue-hold entries, `112` forced holds, and `0` quick-profit entries.

Paired trade-delta:

- Validation added trades: `0`; removed trades: `0`; common trades: `23`.
- Validation common-trade delta: `+72.6816278213862%`, with `3` improved, `20` unchanged, and `0` worsened.
- Final added trades: `0`; removed trades: `0`; common trades: `22`.
- Final common-trade delta: `+42.202744255605126%`, with `7` improved, `15` unchanged, and `0` worsened.

Uncertainty gate:

- Outcome tier: `Shadow Candidate`.
- Decision: `paired_delta_uncertainty_shadow_candidate`.
- Validation positive probability: `0.96075`; observed paired delta `+72.6816278213862%`; top-1 dependency `false`; top-3 dependency `false`.
- Final positive probability: `1.0`; observed paired delta `+42.202744255605126%`; top-1 dependency `false`; top-3 dependency `false`.
- Final lower confidence bound stayed positive at `+0.7349307328836847%`; validation lower bound was `0.0%`.
- Shadow blockers: `[]`.
- Rejection reasons: `[]`.

## Strict Evaluation

This is material shadow-only evidence for the accepted-action conditional-exit router. It keeps the entry set fixed, keeps 10 percent sizing, improves validation and final net profit, improves or ties drawdown, walk-forward, and stress, and improves common accepted-action exits without added trades, removed trades, or worsened common trades.

It is not a live-switch candidate. Fresh live shadow still has no matched activation/release support in the current stream, and runtime enablement would be a live-risk change requiring a separate zero-position live-switch review, config diff, restart plan, and post-switch canary.

## Decision

`Shadow Candidate` / material shadow-only evidence, not `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this result changes the active round conclusion: after the utility-label, freshness-volume, and flow-activation rejections, the post-flow accepted-action router remains the strongest structural candidate and is material enough to close this business round as shadow-only evidence.

Next direction: do not continue runner-retention or hard flow/freshness micro-sweeps. The next highest-value work is either a live-risk review for default-off/audit-only router shadow instrumentation, or a learned accepted-action trade-delta selector that preserves the common-trade improvements while filtering live no-activation losses.
