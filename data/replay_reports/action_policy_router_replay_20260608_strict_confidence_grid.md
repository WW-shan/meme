# Action-Policy Router Strict Confidence Grid

Generated from `data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json`.

## Commands

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260608-router-shadow-next-direction/router_strict_confidence_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json \
  --write-selected-trade-delta \
  --force

venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260608_strict_confidence_grid.json \
  --candidate-id strict_confidence_router_20260608 \
  --output data/replay_reports/replay_uncertainty_gate_20260608_strict_confidence_router.json \
  --force
```

## Selected Candidate

- Decision: `accept`.
- Outcome tier: `Shadow Candidate`.
- Candidate index: `10` of `13`.
- `buy_action_policy_router_min_confidence=0.55`.
- `buy_action_policy_continue_hold_activation_pct=0.40`.
- `buy_action_policy_continue_hold_release_pct=0.85`.
- `buy_quick_profit_overlay_take_profit_pct=0.25`.
- `buy_quick_profit_overlay_max_hold_seconds=120.0`.

Strict assumptions stayed at 10 percent sizing: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and no fixed stake.

## Validation

Baseline to selected:

- Net profit BNB: `0.012252343033424175 -> 0.012757683043646897`.
- Trades: `23 -> 23`.
- Win rate: `0.7391304347826086 -> 0.7391304347826086`.
- Max drawdown pct: `-7.361964742920057 -> -7.361964742920057`.
- Walk-forward worst net return pct: `2.8446315943470024 -> 10.73202124582493`.
- Walk-forward worst max drawdown pct: `-14.377134762904564 -> -14.329703059730136`.
- Stress worst net profit BNB: `0.004609956337437153 -> 0.004695903033616375`.
- Stress worst net return pct: `90.75962250093363 -> 92.45171872255753`.
- Stress worst max drawdown pct: unchanged at `-12.245451556163134`.
- Router activity: `26` signals, `14` continue-hold entries, `212` forced holds, `0` quick-profit entries.

Paired delta:

- Added trades: `0`; removed trades: `0`; common trades: `23`.
- Common-trade delta: `+95.88960293988933%`.
- Improved/unchanged/worsened common trades: `3 / 20 / 0`.
- Bootstrap positive probability: `0.96075`; non-negative probability: `1.0`; lower bound: `0.0%`.
- Top-1 removal delta: `+21.01258060545925%`; top-3 removal delta: `0.0%`; no top-winner dependency blocker.

## Final

Baseline to selected:

- Net profit BNB: `0.0020282580548887895 -> 0.0022677955521744793`.
- Trades: `24 -> 24`.
- Win rate: `0.5416666666666666 -> 0.5416666666666666`.
- Max drawdown pct: unchanged at `-18.206422038627302`.
- Walk-forward worst net return pct: `5.791910318976479 -> 10.04441244002603`.
- Walk-forward worst max drawdown pct: unchanged at `-18.206422038627302`.
- Stress worst net profit BNB: `-0.0005495624150332759 -> -0.00036872340204832914`.
- Stress worst net return pct: `-10.819642026555643 -> -7.2593305288810805`.
- Stress worst max drawdown pct: `-26.925411157799616 -> -24.184914712689608`.
- Router activity: `26` signals, `12` continue-hold entries, `133` forced holds, `0` quick-profit entries.

Paired delta:

- Added trades: `0`; removed trades: `0`; common trades: `24`.
- Common-trade delta: `+42.202744255605126%`.
- Improved/unchanged/worsened common trades: `7 / 17 / 0`.
- Bootstrap positive probability: `0.99975`; non-negative probability: `1.0`; lower bound: `+0.6972111473809277%`.
- Top-1 removal delta: `+1.4925900784794948%`; top-3 removal delta: `+0.7558032659916165%`; no top-winner dependency blocker.

## Decision

This is stronger material shadow-only evidence for the accepted-action router, not live-switch evidence. The stricter activation/release candidate improves validation net profit and walk-forward versus the previous `0.35 / 0.75` control while preserving the final common-trade improvement. It keeps the entry set fixed, keeps 10 percent sizing, adds no trades, removes no trades, and worsens no common trades.

No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.
