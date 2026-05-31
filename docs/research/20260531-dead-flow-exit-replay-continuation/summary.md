# Dead-Flow Exit Replay Continuation

Generated: 2026-05-31

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction with `max_open_positions=8`.
- This is replay-only research evidence, not live-switch evidence.
- No `.env`, `.env.example`, model artifact, threshold, bot process, collector process, buy/sell logic, or runtime behavior changed.

## Live-First Note

- Bot and collector were running through `memectl`; `data/bot_state.json` had zero open positions and balance `0.002183078348474941` BNB.
- Fresh read-only attribution since `2026-05-31 12:37:23` found `0` new closed trades, `5701` signal decisions, and `430` per-token rejected candidates.
- Rejected-path classes were `fast_profit=11`, `fast_profit_then_collapse=23`, `flat_timeout=305`, `missing_path=1`, `slow_runner=8`, and `stop_first=82`.
- The attribution decision remained `NO_GO_FOR_LIVE_SWITCH`.

## Direction Selection

The latest useful alpha before this run was the accepted-trade freshness/dead-flow proxy in `docs/research/20260531-freshness-deadflow-structural-refresh/summary.md`: it selected `signal_volume_30s >= 3.73949` and skipped only losses in train, validation, and final proxy splits. That evidence was still blocked from shadow/live because it lacked replay-integrated drawdown, walk-forward, stress, and paired-delta support.

Chosen direction: test whether an existing replay-compatible dead-flow exit overlay can reproduce that accepted-trade proxy under strict live-sized replay gates.

Falsification rule: reject if no validation candidate passes the strict acceptance gate, if final confirmation fails, or if the rule is inactive on final.

## Commands

Fresh live attribution:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-31 12:37:23' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 80 \
  --output-json data/replay_reports/live_trade_attribution_20260531_after_freshness_alpha_continue.json \
  --output-md data/replay_reports/live_trade_attribution_20260531_after_freshness_alpha_continue.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Replay:

```bash
venv/bin/python scripts/run_dead_flow_exit_replay.py \
  --output data/replay_reports/dead_flow_exit_replay_20260531_freshness_deadflow_continue.json \
  --force
```

An initial broader `scripts/run_flow_abstention_replay.py` attempt was stopped before it produced a report because it ran more than 14 minutes with no artifact and was broader than the selected dead-flow/freshness replay hypothesis.

## Result

Reports:

- `data/replay_reports/live_trade_attribution_20260531_after_freshness_alpha_continue.json`
- `data/replay_reports/live_trade_attribution_20260531_after_freshness_alpha_continue.md`
- `data/replay_reports/dead_flow_exit_replay_20260531_freshness_deadflow_continue.json`

Replay result: `Rejected`.

Validation baseline:

- net profit: `0.022842003299308057` BNB
- trades: `38`
- win rate: `0.8157894736842105`
- max drawdown: `-10.187954315383251%`
- walk-forward worst return: `101.88310806253628%`
- stress worst net profit: `0.011661288085332917` BNB
- dead-flow exits: `0`

Selected validation candidate:

- params: `buy_dead_flow_exit_min_hold_seconds=180.0`, `buy_dead_flow_exit_max_mfe_pct=0.08`
- net profit: `0.022842003299308057` BNB, unchanged from baseline
- trades: `38`, unchanged
- win rate: `0.8157894736842105`, unchanged
- dead-flow exits: `1`
- failed gates: no required `+0.0005` BNB validation improvement, lower stress worst net profit, and lower stress worst return

Final confirmation:

- params: `buy_dead_flow_exit_min_hold_seconds=180.0`, `buy_dead_flow_exit_max_mfe_pct=0.08`
- baseline and candidate both had net profit `0.0018096462830015873` BNB, `20` trades, `0.6` win rate, and max drawdown `-16.256141287806237%`
- candidate dead-flow exits: `0`
- failed gates: no dead-flow exit activity and no required net-profit improvement

All `12` bounded candidates failed acceptance. Most `max_mfe_pct=0.03` and `0.05` variants were no-ops. The active `max_mfe_pct=0.08` variants fired only once in validation and did not improve validation profit or stress; the selected candidate became inactive in final.

## Decision

Outcome tier: `Rejected`.

The freshness/dead-flow proxy remains useful `Research Alpha`, but this specific dead-flow exit overlay does not convert it into deployable replay evidence. It is neither a `Shadow Candidate` nor a `Live Switch Candidate`.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: do not continue bounded dead-flow min-hold / max-MFE exit sweeps without new population evidence. Use the zero-winner signal-context alpha for a direct replay-compatible abstention or paired-delta utility target, or continue collecting queued/opened freshness shadow support.
