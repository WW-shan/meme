# 2026-06-08 Post-Boundary Continue-Hold Router

## Live State

- Bot and collector were running under `./tools/memectl` in `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and zero open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `BUY_ACTION_POLICY_ROUTER_ENABLED=false`, and `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`.
- Latest committed milestone before this work was `351a99b research: reject quick profit boundary replay`; GitHub Actions run `27145171827` passed.
- Active node state: not archived. This is a material shadow-only milestone inside the active round, not a live cutover.

Fresh no-switch reports:

- `data/replay_reports/live_trade_attribution_20260608_post_boundary_direction_refresh.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_audit_20260608_post_boundary_direction_refresh.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_path_attribution_20260608_post_boundary_direction_refresh.json` / `.md`

Live attribution since the `2026-06-07 12:25:39.499918` `苹果人生` close found `0` new closed trades and ranked rejected-path support as `fast_profit=39`, `fast_profit_then_collapse=51`, `slow_runner=15`, `flat_timeout=608`, and `stop_first=146`. Recorded post-audit shadow telemetry since `2026-06-08 15:02:20` had `3606` signal rows, `3526` rows with recorded shadow fields, `5` recorded shadow-used rows, `2` queued shadow-used rows, and `0` matched trades. Recorded `quick_take_profit` route precision fell to `23/157 = 0.1464968152866242`, reinforcing that broad quick-profit routing remains rejected.

## Prior Review

The immediate prior quick-profit boundary replay was rejected under strict replay: it improved validation headline profit but failed sealed final profit, win rate, drawdown, walk-forward, and stress. The recorded quick-profit route path attribution was also rejected twice because the route did not isolate quick-profit-shaped paths.

The surviving structural evidence is the accepted-action router. Its latest strict replay `Shadow Candidate` improved common accepted trades without added or removed entries. Inspecting `data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json` showed the selected candidate had `action_policy_router_quick_take_profit_entry_count=0`; its uplift came from `continue_hold` router activity and forced-hold exit behavior, not quick-profit entries.

## Research Reused

No new SmartSearch Deep Research was needed. This round reused committed research and replay evidence:

- `docs/research/20260608-router-shadow-next-direction/summary.md`
- `docs/research/20260608-recorded-shadow-path-attribution/summary.md`
- `docs/research/20260608-quick-profit-boundary-replay/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: recorded `quick_take_profit` route quality worsened, but the strict router's selected offline uplift did not require quick-profit entries. The smallest useful falsifier was to remove quick-profit overlay parameters from the selected router candidate and test whether the continue-hold-only version still passes strict replay and paired-delta uncertainty gates.

## Hypothesis Portfolio

1. Continue-hold-only accepted-action router: selected. Evidence strength is high because prior strict replay already passed, expected impact is positive because it preserves common-trade exit improvements, falsifiability is strong via one-candidate strict replay, and implementation cost is low because no code or runtime config change is required.
2. Direct paired-delta utility target/meta gate: deferred. It aligns with profit, but recent generic utility-label and reward selectors failed uncertainty or final gates; it needs a new training/tooling step.
3. Replay-compatible freshness/context propagation: deferred. The signal-context freshness alpha is promising, but strict replay context remains missing or degenerate for the current fields.
4. Rejected-entry quick-profit selector: rejected for now. Fresh live counts are large, but recorded route precision and strict quick-profit replays failed, so another micro-sweep would repeat a failing family.

## Hypothesis

If the accepted-action router's edge is genuinely continue-hold exit behavior rather than quick-profit routing, then the best selected router thresholds without any quick-profit overlay parameters should preserve validation/final net profit, walk-forward, stress, trade count, win rate, drawdown, and paired common-trade delta under strict 10 percent replay.

Falsification rule: reject if validation or final strict gates fail, if the candidate adds or removes trades, if any common trade worsens, if paired-delta uncertainty downgrades below `Shadow Candidate`, or if removing quick-profit parameters reduces the prior router uplift materially.

## Experiment

Candidate grid:

- `docs/research/20260608-post-boundary-continue-hold-router/continue_hold_only_grid.json`

Strict replay:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260608-post-boundary-continue-hold-router/continue_hold_only_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260608_continue_hold_only_post_boundary.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260608_continue_hold_only_post_boundary.json \
  --candidate-id continue_hold_only_router_20260608_post_boundary \
  --output data/replay_reports/replay_uncertainty_gate_20260608_continue_hold_only_post_boundary.json \
  --force
```

Selected candidate:

- `buy_action_policy_router_min_confidence=0.55`
- `buy_action_policy_continue_hold_activation_pct=0.40`
- `buy_action_policy_continue_hold_release_pct=0.85`
- No quick-profit overlay take-profit or max-hold parameters.

Strict assumptions stayed at 10 percent sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, no fixed stake.

## Results

Replay decision: `accept`. Uncertainty decision: `paired_delta_uncertainty_shadow_candidate`. Outcome tier: `Shadow Candidate`.

Validation baseline to selected:

- Net profit BNB: `0.012252343033424175 -> 0.012757683043646897`.
- Trades/win/max drawdown: unchanged at `23`, `73.91304347826086%`, and `-7.361964742920057%`.
- Walk-forward worst return: `2.8446315943470024% -> 10.73202124582493%`.
- Stress worst net profit BNB: `0.004609956337437153 -> 0.004695903033616375`.
- Router activity: `26` signals, `14` continue-hold entries, `0` quick-profit entries, `212` forced-hold events.
- Paired delta: `0` added, `0` removed, `23` common trades; common delta `+95.88960293988933%`, `3` improved, `20` unchanged, `0` worsened.
- Bootstrap positive probability: `0.96075`; top-1 and top-3 dependency blockers were both `false`.

Final baseline to selected:

- Net profit BNB: `0.0020282580548887895 -> 0.0022677955521744793`.
- Trades/win/max drawdown: unchanged at `24`, `54.166666666666664%`, and `-18.206422038627302%`.
- Walk-forward worst return: `5.791910318976479% -> 10.04441244002603%`.
- Stress worst net profit BNB: `-0.0005495624150332759 -> -0.00036872340204832914`.
- Stress worst max drawdown: `-26.925411157799616% -> -24.184914712689608%`.
- Router activity: `26` signals, `12` continue-hold entries, `0` quick-profit entries, `133` forced-hold events.
- Paired delta: `0` added, `0` removed, `24` common trades; common delta `+42.202744255605126%`, `7` improved, `17` unchanged, `0` worsened.
- Bootstrap positive probability: `0.99975`; final lower bound `+0.6972111473809277%`; top-1 and top-3 dependency blockers were both `false`.

This exactly preserves the prior strict router economics while removing live-risk ambiguity from quick-profit overlay parameters.

## Decision

Outcome tier: `Shadow Candidate` / material shadow-only evidence.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this changes the selected router interpretation: the best material shadow-only router evidence is now continue-hold-only at `0.55 / 0.40 / 0.85`, and quick-profit overlay parameters are unnecessary for the strict replay uplift.

Next highest-value direction: continue collecting in-process audit rows for the continue-hold-only path, and only consider live-risk review after matched queued/opened continue-hold evidence appears or a separate review accepts the no-entry-change forced-hold mechanism.
