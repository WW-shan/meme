# 2026-06-01 Post-Selector Conditional-Exit Router Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in the expected tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.002195742691061948` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, no fixed stake, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `51e0949`, pushed to `origin/main`, with GitHub Actions `CI` run `26737470395` passing.

## Live Attribution

Fresh entry artifacts:

- `data/replay_reports/live_trade_attribution_20260601_post_selector_ci.json`
- `data/replay_reports/live_trade_attribution_20260601_post_selector_ci.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 12:44:58' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 64 \
  --output-json data/replay_reports/live_trade_attribution_20260601_post_selector_ci.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_post_selector_ci.md \
  --max-trade-sample 40 \
  --max-candidate-sample 240 \
  --force
```

Result:

- Decision: `NO_GO_FOR_LIVE_SWITCH`.
- Closed trades after `UP`: `0`.
- Signal decisions: `330`; per-token candidates: `35`.
- Barrier classes: `fast_profit=1`, `fast_profit_then_collapse=1`, `slow_runner=3`, `flat_timeout=26`, `stop_first=4`.
- Same-shape rejected-signal support stayed below the replay gate, so the next experiment stayed on accepted-position routing rather than rejected-entry rescue.

## Prior Review

The immediately prior never-activated utility-negative selector was rejected, so activation-path selector expansion is no longer the best use of the current evidence. Direct utility shadow-ranker expansion is also already hard-rejected in `docs/research/20260531-direct-paired-delta-utility-ranker/summary.md` because it over-expanded trades and damaged risk.

The fresh live pair from the signal/flow parity round remains more relevant:

- `.bts` was a profitable accepted trade with post-entry continuation.
- `世界有无限可能` was a losing near-threshold accepted trade with no useful upside.
- `UP` was a profitable accepted trade after the activation45 refresh.

This points to accepted-position action routing / conditional continuation as a better structural branch than another entry-expansion or never-activated selector sweep.

Reused SmartSearch-backed research:

- `docs/research/20260521-post-target-exit-state/summary.md`
- `docs/research/20260520-conditional-profit-lock-exit/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260531-direct-paired-delta-utility-ranker/summary.md`

## Hypothesis Portfolio

Ranked directions:

1. Conditional-exit / accepted-action continuation router refresh. Selected because the recent live accepted-trade evidence and prior `Shadow Candidate` router branch target realized exit quality without adding entries, sizing, or threshold risk.
2. Replay-compatible signal-context freshness. Deferred because the latest strict signal/flow parity probe could not separate rejected-signal winners from losers and still selected too little rejected support.
3. Live-shadow accumulation for activation45/freshness. Useful but passive; no new queued trade closed after `UP` in this slice.
4. Direct paired-delta entry meta-gating. Deferred because the current direct utility shadow-ranker branch is already hard-rejected unless the target population changes.

Hypothesis: rerunning the existing action-policy router on the current lifecycle set will preserve the no-new-entry guarantee while improving realized return through release-only `continue_hold` behavior on common accepted trades.

Falsification rule: reject if validation or final fails net profit, drawdown, win-rate, walk-forward, stress, trade-count, router-activity, or paired-delta uncertainty gates; reject if the effect comes from added candidate trades, removed baseline trades, worsened common trades, or top-winner dependency.

## Experiment

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260601_post_selector_ci_current_lifecycle.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260601_post_selector_ci_current_lifecycle.json \
  --candidate-id post_selector_ci_conditional_exit_router_20260601 \
  --output data/replay_reports/replay_uncertainty_gate_20260601_post_selector_ci_conditional_exit_router.json \
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
- Win rate: `0.8157894736842105 -> 0.8157894736842105`.
- Max drawdown: unchanged at `-10.187954315383251%`.
- Walk-forward worst return: `101.88310806253628% -> 103.01533998554144%`.
- Stress worst net profit BNB: `0.011661288085332917 -> 0.012392324169094096`.
- Router activity: `49` signals, `24` continue-hold entries, `161` forced holds, `0` quick-profit entries.

Final baseline to selected:

- Net profit BNB: `0.002130506358905197 -> 0.002637064337252893`.
- Trades: `21 -> 21`.
- Win rate: `0.6190476190476191 -> 0.6190476190476191`.
- Max drawdown: `-16.256141287806237% -> -15.315648358960388%`.
- Walk-forward worst return: `1.1443686694029065% -> 5.183643607072308%`.
- Walk-forward worst drawdown: `-12.826715376991016% -> -12.788948638069087%`.
- Stress worst net profit BNB: `-0.00008990912085104011 -> 0.00010799932032521092`.
- Stress worst max drawdown: `-31.51190976920992% -> -28.92186120577952%`.
- Router activity: `23` signals, `12` continue-hold entries, `240` forced holds, `0` quick-profit entries.

Paired trade-delta:

- Validation added trades: `0`; removed trades: `0`; common trades: `38`.
- Validation common-trade delta: `+39.9371855268287%`, with `3` improved, `35` unchanged, `0` worsened.
- Final added trades: `0`; removed trades: `0`; common trades: `21`.
- Final common-trade delta: `+96.12071561162495%`, with `3` improved, `18` unchanged, `0` worsened.

Uncertainty gate:

- Outcome tier: `Shadow Candidate`.
- Decision: `paired_delta_uncertainty_shadow_candidate`.
- Validation positive probability: `0.956`; observed paired delta `+39.9371855268287%`; top-1 dependency `false`; top-3 dependency `false`.
- Final positive probability: `0.963`; observed paired delta `+96.12071561162495%`; top-1 dependency `false`; top-3 dependency `false`.
- Shadow blockers: `[]`.
- Rejection reasons: `[]`.

## Decision

Classification: `Shadow Candidate` / material shadow-only evidence.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

This is stronger than the earlier 2026-05-29 conditional-exit shadow result because the current lifecycle refresh still accepts under strict replay, emits selected trade-delta attribution, and passes uncertainty gating without added-trade expansion, removed baseline trades, worsened common trades, or top-winner dependency.

`docs/model_scoreboard.md` was updated because this changes the active best structural evidence: conditional-exit / accepted-action continuation is now a current `Shadow Candidate` again, while entry-expansion and activation-path selector directions remain rejected or blocked.

Live enablement remains a separate live-risk task. Any runtime activation would require explicit live-switch review, current open-position check, config diff, and a controlled bot restart.
