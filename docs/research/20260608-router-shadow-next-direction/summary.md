# 2026-06-08 Router Shadow Next Direction

## Live State

- Bot and collector were running under `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions during the experiment.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Fresh attribution since the `2026-06-07 12:25:39.499918` `苹果人生` close found `0` new closed trades. Recent high-score log rows remained mostly rejected by negative or insufficient `PredReturn`.

Fresh no-switch reports:

- `data/replay_reports/live_trade_attribution_20260608_router_shadow_next_direction_entry.json` / `.md`
- `data/replay_reports/action_policy_live_shadow_20260608_router_shadow_next_direction_entry.json` / `.md`
- `data/replay_reports/action_policy_activation_shadow_20260608_router_shadow_next_direction_entry.json` / `.md`

Live attribution ranked rejected-path opportunities as `fast_profit=28`, `fast_profit_then_collapse=27`, `slow_runner=12`, `flat_timeout=353`, and `stop_first=84`. Live shadow still had insufficient support: `7333` signals, `35` `continue_hold` shadow routes, `2` queued shadow-used rows, and `0` matched queued shadow-used trades. Activation shadow had `0` matched rows.

## Prior Review

The scoreboard already rejects runner-retention utility/volceil micro-sweeps, broad quick-profit overlays, scalar flow/freshness threshold bridges, direct-delta shadow-ranker grids, replacement-pair selectors, generic action-policy reward pivots, and generic positive meta-label classifiers. The surviving structural evidence is the accepted-action router: it changes common accepted exits without adding or removing entries and has repeatedly passed strict replay, paired-delta, and uncertainty gates.

The signal-context freshness rule remains useful `Research Alpha`, but strict replay samples currently lack `lifecycle_status_chain_lag_seconds`, blocking strict replay promotion.

## Research Reused

No new SmartSearch Deep Research was needed because this round reused committed SmartSearch-backed methods:

- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260521-conservative-action-policy-from-oracle-labels/summary.md`

New live-derived angle: with no fresh matched live shadow rows, test whether a stricter custom router grid can improve the existing strict-replay common-trade mechanism before any live-risk runtime enablement discussion.

## Hypothesis Portfolio

1. Strict custom accepted-action router grid: selected. It has high evidence, low implementation cost, strict replay support, and no live-risk change.
2. Learned accepted-action trade-delta / utility selector: deferred. It could filter no-activation losses, but recent generic reward/meta selectors failed and fresh matched shadow support is zero.
3. Replay-compatible freshness field propagation: deferred. The proxy is useful, but strict replay cannot compute its lifecycle freshness field yet.
4. Rejected-entry fast-profit / fast-profit-then-collapse selector: deferred. Fresh counts are visible, but broad quick-profit and scalar selectors already failed.

## Hypothesis

Because repeated strict replay showed the accepted-action router improves common accepted trades but the current live window has no matched activation rows, a narrow stricter router grid should preserve or improve validation/final net profit, walk-forward, stress, and paired common-trade delta without changing entries, sizing, runtime config, or live behavior.

Falsification rule: reject or downgrade if validation/final strict gates fail, if the candidate adds or removes trades, if any common trade worsens, if paired delta weakens below the prior router evidence, or if drawdown, walk-forward, stress, win rate, or uncertainty regresses.

## Experiment

Grid artifact:

- `docs/research/20260608-router-shadow-next-direction/router_strict_confidence_grid.json`

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260608-router-shadow-next-direction/router_strict_confidence_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json \
  --candidate-id strict_confidence_router_20260608 \
  --output data/replay_reports/replay_uncertainty_gate_20260608_strict_confidence_router.json \
  --force
```

Selected candidate:

- Candidate index: `10` of `13`.
- `buy_action_policy_router_min_confidence=0.55`.
- `buy_action_policy_continue_hold_activation_pct=0.40`.
- `buy_action_policy_continue_hold_release_pct=0.85`.
- `buy_quick_profit_overlay_take_profit_pct=0.25`.
- `buy_quick_profit_overlay_max_hold_seconds=120.0`.

Strict assumptions stayed at 10 percent sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, no fixed stake.

## Results

Replay decision: `accept`. Uncertainty decision: `paired_delta_uncertainty_shadow_candidate`. Outcome tier: `Shadow Candidate`.

Validation baseline to selected:

- Net profit BNB: `0.012252343033424175 -> 0.012757683043646897`.
- Trades/win/max drawdown: unchanged at `23`, `73.9130%`, and `-7.361964742920057%`.
- Walk-forward worst return: `2.8446315943470024% -> 10.73202124582493%`.
- Stress worst net profit BNB: `0.004609956337437153 -> 0.004695903033616375`.
- Paired delta: `0` added, `0` removed, `23` common trades; common delta `+95.88960293988933%`, `3` improved, `20` unchanged, `0` worsened.
- Bootstrap positive probability: `0.96075`; top-1 removal delta `+21.01258060545925%`; top-3 removal delta `0.0%`.

Final baseline to selected:

- Net profit BNB: `0.0020282580548887895 -> 0.0022677955521744793`.
- Trades/win/max drawdown: unchanged at `24`, `54.1667%`, and `-18.206422038627302%`.
- Walk-forward worst return: `5.791910318976479% -> 10.04441244002603%`.
- Stress worst net profit BNB: `-0.0005495624150332759 -> -0.00036872340204832914`.
- Stress worst max drawdown: `-26.925411157799616% -> -24.184914712689608%`.
- Paired delta: `0` added, `0` removed, `24` common trades; common delta `+42.202744255605126%`, `7` improved, `17` unchanged, `0` worsened.
- Bootstrap positive probability: `0.99975`; final lower bound `+0.6972111473809277%`; top-1 removal delta `+1.4925900784794948%`; top-3 removal delta `+0.7558032659916165%`.

Compared with the previous `0.35 / 0.75` selected control, this stricter release candidate improves validation net profit and walk-forward while preserving the same final net-profit, paired-delta, and risk improvements. It remains shadow-only because fresh live shadow has no matched activation/release support and runtime enablement would be a separate live-risk/config/restart action.

## Decision

Outcome tier: `Shadow Candidate` / stronger material shadow-only evidence.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because the strict custom grid changes the selected router parameters and strengthens the material shadow-only evidence.

Next highest-value direction after this boundary: either perform a separate live-risk review for default-off audit-only in-process router shadow instrumentation while zero positions remain, or continue offline with a learned accepted-action trade-delta/no-activation selector if fresh matched shadow rows remain unavailable.
