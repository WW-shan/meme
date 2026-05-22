# 2026-05-22 Support-Rule Quick-TP Validation

## Context

This follow-up validation took the wide-window rejected-signal support gate and tried to turn the strongest rule shape into a replay-integrated quick-TP candidate.

The goal was narrower than the earlier active-flow overlay: keep the live v95 primary profile unchanged and test only the best support-rule quick-TP shape without reintroducing the rejected `total_buys` proxy.

## Run

- Script: `scripts/run_support_rule_quick_tp_replay.py`
- Test coverage: `tests/model/test_support_rule_quick_tp_replay_cli.py`
- Report: `data/replay_reports/support_rule_quick_tp_replay_20260522_v95.json`
- Mode used for this node: `--validation-only`

## Candidate Grid

- `buy_quick_profit_overlay_min_prob=0.985`
- `buy_quick_profit_overlay_min_pred_return=30.0`
- `buy_quick_profit_overlay_max_pred_return=35.0`
- `buy_quick_profit_overlay_min_entry_volume_30s=1.25`
- `buy_quick_profit_overlay_min_entry_price_volatility=0.08`
- `buy_quick_profit_overlay_max_age_seconds=60.0`
- `buy_quick_profit_overlay_take_profit_pct in {0.25, 0.35}`
- `buy_quick_profit_overlay_max_hold_seconds in {60.0, 120.0}`

## Validation Result

Baseline validation:

- net profit: `0.018493796819` BNB
- total trades: `32`
- win rate: `75.0%`
- max drawdown: `-27.4492%`
- WF worst net return: `60.4110%`
- stress worst profit: `0.012948788502` BNB

Best validation candidate (`take_profit=0.35`, `max_hold=120s`):

- net profit: `0.018357345313` BNB
- total trades: `37`
- win rate: `72.9730%`
- max drawdown: `-27.4492%`
- WF worst net return: `42.6177%`
- stress worst profit: `0.011936707553` BNB
- quick-profit overlay entries: `7`

This candidate lost to baseline on net profit, trade count, win rate, walk-forward return, and stress profit. It is therefore rejected as a live or replay improvement.

## Decision

- Do not update `docs/model_scoreboard.md`.
- Do not change `.env`, model artifacts, thresholds, sizing, runtime, or bot restart state.
- Keep the next direction as research-only; this candidate shape is not strong enough to promote.
