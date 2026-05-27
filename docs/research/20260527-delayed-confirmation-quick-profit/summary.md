# 2026-05-27 Delayed-Confirmation Quick-Profit Replay

## Question

Can a short post-signal confirmation delay separate rejected fast-profit breakouts from immediate stop-first/fakeout paths without reopening the previously rejected broad quick-profit overlay?

## Evidence

- Live state was healthy: bot and collector were running; no open position; no 2026-05-27 paper trades at the time of analysis.
- Fresh TTB probe since `2026-05-27 00:00:00` found `99` per-token candidates: `fast_profit=10`, `fast_profit_then_collapse=4`, `slow_runner=8`, `flat_timeout=60`, `stop_first=17`.
- SmartSearch research supported waiting for confirmation rather than entering on the first tick. The fetched Bookmap and OrderflowHQ pages both emphasize order-flow/volume/continuation confirmation; the arXiv memecoin manipulation paper supports treating ultra-short memecoin breakouts as manipulation-prone. The CPD paper supports short-window regime/change confirmation but warns that too-short windows can be noisy and transaction costs can dominate.

## Implementation

Replay-only support was added for:

- `buy_quick_profit_overlay_confirmation_delay_seconds`
- `buy_quick_profit_overlay_max_confirmation_drawdown_pct`
- `buy_quick_profit_overlay_max_confirmation_chase_pct`

These parameters only affect `quick_profit_overlay_used` entries. Baseline primary and near-threshold entries keep their normal replay delay. A new strict replay CLI, `scripts/run_delayed_confirmation_quick_tp_replay.py`, tests the previous support-rule quick-profit pocket with `3s/5s` extra confirmation delay and price-hold/chase filters.

## Command

```bash
python scripts/run_delayed_confirmation_quick_tp_replay.py \
  --output data/replay_reports/delayed_confirmation_quick_tp_replay_20260527.json \
  --force
```

## Result

Decision: `reject`, `safe_for_live_switch=false`.

Validation baseline:

- trades `32`
- net profit `0.021094872146` BNB
- win rate `0.7500`
- max drawdown `-9.8821%`
- WF worst return `87.2942%`
- stress worst profit `0.011148541484` BNB

Best validation candidate:

- params: `5s` confirmation delay, max drawdown `3%`, max chase `20%`, take profit `35%`
- trades `36`
- quick-profit overlay entries `5`
- confirmation rejects `5`
- net profit `0.021132514471` BNB
- win rate `0.7500`
- max drawdown worsened to `-11.4110%`
- WF worst return worsened to `82.5080%`
- stress worst profit worsened to `0.011119044925` BNB

Final confirmation:

- baseline net profit `0.005174515325` BNB, trades `21`, win rate `0.5238`
- candidate net profit `0.004629167773` BNB, trades `23`, win rate `0.5217`
- candidate quick-profit overlay entries `3`, confirmation rejects `1`
- failed net profit, max drawdown, win rate, walk-forward return/drawdown, and stress profit gates

## Decision

No live switch. No `.env`, threshold, sizing, model artifact, or bot restart change.

The switch gate is not too strict here. The delayed-confirmation idea reduced activity enough to avoid the prior trade explosion, but the remaining admitted overlay trades still weakened final profit and robustness. Do not continue static short-delay quick-profit tuning as the next main branch. The next direction should focus on richer decision-time separation, such as a learned early-collapse toxicity classifier, a replacement-only oracle upper bound, or a wider same-token replacement label with support checks.

Scoreboard updated: yes.
