# Flow Volume Abstention Freshness Proxy

Date: 2026-06-01
Status: Rejected

## Question

Can the zero-winner accepted-trade freshness proxy be made replay-compatible by abstaining from otherwise eligible v95 entries when the signal is young/high-confidence but `volume_30s` is above a toxic floor?

The test is deliberately narrower than a new live rule. It keeps the current v95/v84 generator, 10% position sizing, `max_open_positions=8`, one entry per token, walk-forward, stress replay, and a final confirmation split. It only adds a default-off flow-abstention veto field:

- `buy_flow_abstention_min_toxic_entry_volume_30s`

## Artifacts

- Live attribution refresh: `data/replay_reports/live_trade_attribution_20260531_after_dead_flow_exit_reject.json`
- Live attribution markdown: `data/replay_reports/live_trade_attribution_20260531_after_dead_flow_exit_reject.md`
- Strict replay report: `data/replay_reports/flow_volume_abstention_replay_20260531_freshness_proxy.json`
- CLI: `scripts/run_flow_volume_abstention_replay.py`

## Live Attribution Context

The fresh attribution window after the dead-flow exit rejection produced no new closed trades, but enough rejected signal-path support to keep structural replay work useful:

- Closed trades: `0`
- Per-token rejected candidates: `457`
- Barrier buckets: `fast_profit=15`, `fast_profit_then_collapse=24`, `slow_runner=9`, `flat_timeout=323`, `stop_first=85`, `missing_path=1`
- Read-only decision: `NO_GO_FOR_LIVE_SWITCH`

## Replay Result

The bounded 12-candidate grid was rejected.

Validation baseline:

- Net profit: `0.022842003299308057` BNB
- Trades: `38`
- Win rate: `0.8157894736842105`
- Max drawdown: `-10.187954315383251%`
- WF worst return: `101.88310806253628%`
- Stress worst net profit: `0.011661288085332917` BNB

The selected raw validation candidate used:

- `buy_flow_abstention_min_prob=0.94`
- `buy_flow_abstention_max_age_seconds=60.0`
- `buy_flow_abstention_min_entry_volume_30s=1.5`
- `buy_flow_abstention_min_entry_price_volatility=0.0`
- `buy_flow_abstention_min_toxic_entry_volume_30s=3.73949`

It was effectively a no-op on validation with `0` flow-abstention vetoes and therefore failed the activity and net-profit improvement gates. Lower toxic floors did veto trades, but they reduced validation profit, win rate, walk-forward quality, and stress robustness.

Final confirmation made the rejection clearer:

| Split | Net Profit BNB | Trades | Win Rate | WF Worst Return | Stress Worst Net Profit | Flow Vetoes |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | `0.0018096462830015873` | `20` | `0.6` | `-3.927696685669879%` | `-0.00028851104372550496` | `0` |
| Candidate | `0.0017190498904131758` | `19` | `0.5789473684210527` | `-5.576361956610565%` | `-0.00032188481087637097` | `1` |

Final candidate gates failed on net profit, win rate, walk-forward worst return, stress worst net profit, stress worst return, and stress drawdown.

## Decision

Reject high-volume flow abstention as a replay-compatible freshness proxy.

No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live switch changed. The scoreboard was updated because this records a direct negative result for converting the zero-winner freshness proxy into a simple flow-volume abstention rule.

Next work should not continue bounded high-volume flow-abstention sweeps without new population evidence. Prefer paired-delta integration of signal-context freshness fields, a structurally different accepted-loss abstention selector, or continued queued/opened freshness shadow accumulation.
