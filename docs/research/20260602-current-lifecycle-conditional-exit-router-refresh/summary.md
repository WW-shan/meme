# 2026-06-02 Current-Lifecycle Conditional-Exit Router Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.001857812463585878` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `5028d13db7ee6861e5cfa606ebf0bc47f22bf1c0`, pushed to `origin/main`, with GitHub Actions `CI` run `26775578956` passing.

## Fresh Live Attribution

Fresh watch artifacts after the rejected freshness-volatility replay boundary:

- `data/replay_reports/live_trade_attribution_20260602_post_replay_veto_commit_watch.json`
- `data/replay_reports/live_trade_attribution_20260602_post_replay_veto_commit_watch.md`
- `data/replay_reports/action_policy_live_shadow_20260602_post_replay_veto_commit_watch.json`
- `data/replay_reports/action_policy_live_shadow_20260602_post_replay_veto_commit_watch.md`
- `data/replay_reports/action_policy_activation_shadow_20260602_post_replay_veto_commit_watch.json`
- `data/replay_reports/action_policy_activation_shadow_20260602_post_replay_veto_commit_watch.md`

Since the last closed-trade boundary at `2026-06-01 21:38:26`, live attribution found `0` new closed trades, `1032` signal decisions, and `119` rejected per-token candidates. Barrier classes were `fast_profit=5`, `fast_profit_then_collapse=5`, `flat_timeout=93`, `slow_runner=2`, and `stop_first=14`; recommended policies were `quick_take_profit=10`, `conditional_slow_hold=2`, and `skip=107`.

Action-policy live shadow scored all `1032` production decisions as rejected, with `14` read-only `continue_hold` shadow routes, `0` queued rows, and `0` matched trades. Activation45 shadow had `0` matched rows and stayed insufficient support.

This keeps rejected-entry rescue below replay promotion and leaves accepted-action conditional exit as the highest-value structural branch.

## Prior Research Reused

No new SmartSearch pass was opened because this is a current-lifecycle refresh of the already researched conditional-exit / accepted-action router:

- `docs/research/20260601-post-selector-conditional-exit-router-refresh/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260520-conditional-profit-lock-exit/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260602-replay-compatible-freshness-volatility-veto/summary.md`

New live-derived angle: after the strict freshness-volatility veto failed and the post-boundary watch still found no queued live support, retest whether the accepted-position conditional-exit router remains a material replay/shadow candidate on the current lifecycle set.

## Hypothesis Portfolio

1. **Current-lifecycle conditional-exit router refresh**. Selected because it is structural, preserves entries and 10% sizing, and directly targets realized exit quality through accepted-action routing rather than another hard entry veto.
2. **Trade-delta-trained accepted-action meta gate**. Deferred because the existing router already emits paired trade-delta attribution and can be uncertainty-gated immediately; a new learned gate should come after this refresh if live shadow remains mixed.
3. **Rejected-entry quick-profit / slow-runner rescue**. Rejected for this boundary because fresh support remains mixed and below promotion: only `10` quick-profit-shaped policies, `2` slow-runner policies, and no queued rows.
4. **Direct live enablement of the router**. Deferred because live activation evidence is mixed and runtime enablement is a separate live-risk task requiring explicit switch review, open-position check, config diff, and controlled restart.

## Hypothesis

If the accepted-action `continue_hold` router still improves realized exits on the current lifecycle data, strict replay should improve validation and final net profit without adding or removing trades, without worsening win rate/drawdown/walk-forward/stress, and with positive paired trade deltas that are not top-winner dependent.

Falsification rule: reject if validation or final fails any replay acceptance gate, if added/removed trades rather than common-trade deltas drive the result, if common trades worsen, if bootstrap positive probability falls below the shadow threshold, or if top-winner dependency blocks shadow promotion.

## Experiment

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260602_current_lifecycle_structural_refresh.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260602_current_lifecycle_structural_refresh.json \
  --candidate-id current_lifecycle_structural_router_20260602 \
  --output data/replay_reports/replay_uncertainty_gate_20260602_current_lifecycle_structural_router.json \
  --force
```

Selected candidate:

- Candidate index: `17` of `18`.
- `buy_action_policy_router_min_confidence=0.55`.
- `buy_action_policy_continue_hold_activation_pct=0.35`.
- `buy_action_policy_continue_hold_release_pct=0.75`.
- `buy_quick_profit_overlay_take_profit_pct=0.25`.
- `buy_quick_profit_overlay_max_hold_seconds=120`.

## Results

Replay decision: `accept`.

Validation baseline to selected:

- Net profit BNB: `0.022842003299308057 -> 0.023052473017855603`.
- Trades: `38 -> 38`.
- Win rate: unchanged at `0.8157894736842105`.
- Max drawdown: unchanged at `-10.187954315383251%`.
- Walk-forward worst return: `101.88310806253628% -> 103.01533998554144%`.
- Stress worst net profit BNB: `0.011661288085332917 -> 0.012392324169094096`.
- Stress worst return: `229.58440970567636% -> 243.9768581672623%`.
- Router activity: `49` signals, `24` continue-hold entries, `161` forced holds, `0` quick-profit entries.

Final baseline to selected:

- Net profit BNB: `0.002130506358905197 -> 0.002637064337252893`.
- Trades: `21 -> 21`.
- Win rate: unchanged at `0.6190476190476191`.
- Max drawdown: `-16.256141287806237% -> -15.315648358960388%`.
- Walk-forward worst return: `1.1443686694029065% -> 5.183643607072308%`.
- Walk-forward worst drawdown: `-12.826715376991016% -> -12.788948638069087%`.
- Stress worst net profit BNB: `-0.00008990912085104011 -> 0.00010799932032521092`.
- Stress worst return: `-1.7701074089495061% -> 2.1262625555631187%`.
- Stress worst max drawdown: `-31.51190976920992% -> -28.92186120577952%`.
- Router activity: `23` signals, `12` continue-hold entries, `240` forced holds, `0` quick-profit entries.

Paired trade-delta:

- Validation added trades: `0`; removed trades: `0`; common trades: `38`.
- Validation common-trade delta: `+39.9371855268287%`, with `3` improved, `35` unchanged, and `0` worsened.
- Final added trades: `0`; removed trades: `0`; common trades: `21`.
- Final common-trade delta: `+96.12071561162495%`, with `3` improved, `18` unchanged, and `0` worsened.

Uncertainty gate:

- Outcome tier: `Shadow Candidate`.
- Decision: `paired_delta_uncertainty_shadow_candidate`.
- Validation positive probability: `0.956`; observed paired delta `+39.9371855268287%`; top-1 dependency `false`; top-3 dependency `false`.
- Final positive probability: `0.963`; observed paired delta `+96.12071561162495%`; top-1 dependency `false`; top-3 dependency `false`.
- Shadow blockers: `[]`.
- Rejection reasons: `[]`.

## Strict Evaluation

This is material shadow-only evidence for the accepted-action conditional-exit router under current lifecycle data. It keeps the entry set fixed, keeps live 10% sizing assumptions, improves validation and final net profit, improves or ties drawdown/walk-forward/stress, and improves only common-trade exit outcomes rather than adding risky entries or removing baseline winners.

The result is not live-switch evidence. Fresh live shadow still has no queued/matched post-boundary rows, and prior cumulative activation45 live attribution is mixed. Runtime enablement remains a separate live-risk task.

## Decision

`Shadow Candidate` / material shadow-only evidence, not `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this changes the current structural state: the conditional-exit router remains the strongest accepted-action candidate after the failed freshness-volatility replay bridge and current-lifecycle refresh.

Next direction: keep collecting activation-aware live shadow, and if pursuing a future improvement instead of live-risk review, train or probe a trade-delta accepted-action meta gate that preserves the three improved common-trade cases while avoiding live no-activation losses.
