# 2026-06-09 Continue-Hold Router Robustness

## Live State

- Bot and collector were running under `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `BUY_ACTION_POLICY_ROUTER_ENABLED=false`, and `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`.
- Latest committed boundary before this work was `77df1a6 research: reject continue hold reward lcb replay`; GitHub Actions run `27150718305` passed.
- Active node state: not archived, committed, and pushed through the prior boundary.

Fresh health/log review found no new real trades after the `2026-06-07 12:25:39` `苹果人生` close. Recent live signal rows were rejected by the buy model or near-threshold PredReturn floor, and recorded shadow support still lacked matched continue-hold live trades.

## Prior Review

The current material evidence remains the continue-hold-only accepted-action router from `docs/research/20260608-post-boundary-continue-hold-router/summary.md`.

The 2026-06-08 reward-LCB refresh improved read-only LCB but failed strict replay because the candidate gate no-oped or under-traded. That result ruled out another path-state score-floor micro-sweep.

Quick-profit routing remains rejected because recorded quick-take-profit precision and strict quick-profit replays are weak. This robustness check therefore keeps quick-profit overlay parameters out of the grid.

## Research Reused

No new SmartSearch run was needed. This boundary reused already committed conditional-exit / action-router research:

- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260608-post-boundary-continue-hold-router/summary.md`
- `docs/research/20260608-continue-hold-shadow-reward-lcb-refresh/summary.md`

New live-derived angle: because in-process matched shadow support is still absent, the safest next falsifier was not live-risk review. It was a stricter offline robustness check to see whether the continue-hold-only edge survives neighboring activation/release thresholds without adding or removing entries.

## Hypothesis Portfolio

1. Continue-hold-only robustness grid: selected. Expected impact is medium because it can strengthen or falsify the only current Shadow Candidate; evidence is strong; falsifiability is direct via strict replay and uncertainty; implementation cost is low.
2. Continue-hold live-risk review: deferred. Offline evidence is strongest, but recorded in-process support is only `2` queued shadow-used rows and `0` matched trades in the latest audit.
3. Direct trade-delta-trained meta gate: deferred. It aligns with the profit objective, but the latest reward-to-replay bridge failed to change candidate economics.
4. Quick-profit route selector: rejected for now due repeated weak recorded precision and strict replay failures.

## Hypothesis

If the continue-hold-only router edge is structural rather than a single-threshold artifact, nearby activation/release settings at the same router confidence should pass strict validation and final gates while preserving trade count, win rate, drawdown, walk-forward, stress, and paired common-trade delta under unchanged 10 percent sizing.

Falsification rule: reject robustness if only the prior single point passes, if any selected candidate relies on added/removed trades, if win rate/drawdown/walk-forward/stress worsens, or if paired-delta uncertainty downgrades the result.

## Experiment

Candidate grid:

- `docs/research/20260609-continue-hold-router-robustness/continue_hold_only_robustness_grid.json`

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260609-continue-hold-router-robustness/continue_hold_only_robustness_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260609_continue_hold_only_robustness.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260609_continue_hold_only_robustness.json \
  --candidate-id continue_hold_conf055_act050_rel085 \
  --output data/replay_reports/replay_uncertainty_gate_20260609_continue_hold_only_robustness.json \
  --force
```

Strict assumptions stayed at 10 percent sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and no fixed stake.

## Results

Replay decision: `accept`. Uncertainty decision: `paired_delta_uncertainty_shadow_candidate`. Outcome tier: `Shadow Candidate`.

All six continue-hold-only candidates passed the strict validation acceptance gate:

- `0.55 / 0.35 / 0.75`: validation net profit `0.012635376578461251` BNB, WF worst return `8.40850488379996%`, stress worst profit `0.004695903033616375` BNB, forced holds `213`.
- `0.55 / 0.35 / 0.85`: validation net profit `0.012757683043646897` BNB, WF worst return `10.73202124582493%`, stress worst profit `0.004695903033616375` BNB, forced holds `222`.
- `0.55 / 0.40 / 0.75`: validation net profit `0.012635376578461251` BNB, WF worst return `8.40850488379996%`, stress worst profit `0.004695903033616375` BNB, forced holds `203`.
- `0.55 / 0.40 / 0.85`: validation net profit `0.012757683043646897` BNB, WF worst return `10.73202124582493%`, stress worst profit `0.004695903033616375` BNB, forced holds `212`.
- `0.55 / 0.45 / 0.85`: validation net profit `0.012757683043646897` BNB, WF worst return `10.73202124582493%`, stress worst profit `0.004695903033616375` BNB, forced holds `203`.
- `0.55 / 0.50 / 0.85`: validation net profit `0.012757683043646897` BNB, WF worst return `10.73202124582493%`, stress worst profit `0.004609956337437153` BNB, forced holds `192`.

The replay-selected candidate was `continue_hold_conf055_act050_rel085`. It improved validation net profit `0.012252343033424175 -> 0.012757683043646897` BNB, tied trades/win/max drawdown (`23`, `0.7391304347826086`, `-7.361964742920057%`), improved WF worst return `2.8446315943470024% -> 10.73202124582493%`, and did not worsen stress worst profit (`0.004609956337437153` BNB).

Final confirmation improved net profit `0.0020282580548887895 -> 0.0022677955521744793` BNB, tied trades/win/max drawdown (`24`, `0.5416666666666666`, `-18.206422038627302%`), and improved WF worst return `5.791910318976479% -> 10.04441244002603%`. Final stress worst profit and stress worst drawdown were tied to baseline for this selected point; the earlier `0.40 / 0.85` shadow point remains the more conservative preferred interpretation because it improved final stress in the 2026-06-08 one-candidate replay.

Paired trade delta remained no-entry-change:

- Validation: `0` added, `0` removed, `23` common trades, `3` improved, `20` unchanged, `0` worsened, common return delta `+95.88960293988933%`.
- Final: `0` added, `0` removed, `24` common trades, `7` improved, `17` unchanged, `0` worsened, common return delta `+42.202744255605126%`.
- Uncertainty: validation positive probability `0.96075`; final positive probability `0.99975`; final lower bound `+0.6972111473809277%`; no rejection reasons or shadow blockers.

## Decision

Outcome tier: `Shadow Candidate` / robustness evidence, not live switch.

This strengthens the continue-hold-only router as material shadow-only evidence because the no-entry-change forced-hold effect survives neighboring activation/release thresholds. It does not authorize live enablement: recorded in-process support still has no matched continue-hold live trades, and no `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this changes the evidence strength for the current best shadow-only branch. Next work should either keep collecting matched in-process continue-hold shadow evidence or prepare a separate live-risk review focused on the no-entry-change forced-hold mechanism, with the 2026-06-08 `0.55 / 0.40 / 0.85` point retained as the preferred conservative shadow parameterization unless later evidence supersedes it.
