# 2026-05-23 Live Flow Support Refresh

## Context

Active live model remained `data/models/20260519_v95_v84_selective_nearmiss_gate` with primary threshold `0.98`, near-rescue threshold `0.94`, 10% sizing, and `max_open_positions=8`.

Fresh live attribution during this round produced two closed trades:

- `加密永存` opened with `prob=0.9860838731398268`, high entry slippage of about `18.214%`, then closed by `TIME_EXIT` for `+0.00020415720266439525` BNB. Its path reached about `+68.959%` MFE from entry and did not hit the `-18%` or `-25%` barriers after entry.
- `BinancePizza` opened with `prob=0.9842774305758827`, high entry slippage of about `11.416%`, then closed by `STOP_LOSS` for `-0.0001080618494564743` BNB. Its path reached only about `+9.429%` MFE before hitting `-18%` and `-25%` about `23.456s` after entry.

The live evidence was mixed: high slippage alone is not a reliable veto because one high-slippage trade became a strong winner while another stopped quickly. The round therefore tested whether recent rejected-signal flow/support evidence could justify a narrow default-off replay candidate.

## Reports

- `data/replay_reports/time_to_barrier_probe_20260523_1422_since_141200.json`
- `data/replay_reports/reentry_retention_probe_20260523_1422_live_trades.json`
- `data/replay_reports/low_volume_breakout_probe_20260523_1422_since_141200_prob94.json`
- `data/replay_reports/support_action_policy_20260523_1422_since_141200.json`
- `data/replay_reports/support_action_policy_pool_20260523_0825_1422.json`

An attempted fresh delayed-profit-lock replay command was stopped after roughly 45 minutes because it was still CPU-bound and had not produced an output report:

```bash
venv/bin/python scripts/run_delayed_profit_lock_replay.py \
  --output data/replay_reports/delayed_profit_lock_replay_20260523_live_round.json \
  --force
```

No partial 2026-05-23 delayed-profit-lock JSON artifact was produced or committed.

The earlier sealed replay result in `docs/research/20260521-delayed-profit-lock-event-exit/summary.md` remains the applicable decision for that direction: blanket delayed full-position profit-lock is rejected because it reduces net profit and stress profitability even when it improves drawdown and win rate.

## Evidence

Fresh time-to-barrier since `2026-05-23 14:12:00` emitted `15` per-token candidates:

- Class counts: `fast_profit=2`, `fast_profit_then_collapse=1`, `stop_first=2`, `flat_timeout=10`.
- Policy counts: `quick_take_profit=3`, `skip=12`.
- `BinancePizza` appeared as a fast-profit candidate in the rejected-signal probe, but this is replay/support evidence only, not proof to loosen live stop-loss behavior.
- `PIZZA` was a fast-profit-then-collapse case: it reached `+25%` quickly but then hit the negative barrier, which is exactly the risk that prevents a broad quick-profit rescue.

The stop-loss/reentry probe found `2` stop-loss reentry candidates and accepted both, including `BinancePizza`, but the sample is too small and remains ex-post support evidence.

The low-volume breakout probe found `0` candidates in this window, so there was no fresh support for relaxing volume gates.

The single-window support-action report had only two eligible rules. Both selected `3` candidates with `1` positive and `2` negatives, for `33.33%` precision:

- `high_prob_volume_volatility`
- `high_prob_low_toxic_overlap`

The pooled support-action report across 11 May 23 windows had `181` candidates: `33` positives and `148` negatives. The target flow rule, `high_prob_low_toxic_overlap`, selected `40` candidates with `18` positives and `22` negatives, for `45%` precision. It met the raw count floor (`selected>=30`, `positives>=12`) but still failed the evidence gate:

- Decision: `missing_flow_feature_parity`
- `flow_event_count_30s`: finite for `181/181`
- `flow_buy_sell_overlap_ratio_60s`: finite for `139/181`
- `flow_recent_seller_reentry_ratio_30s`: finite for `128/181`

Because the replay/runtime feature surface does not yet have complete parity for the flow fields, the apparent support cannot be treated as deployable policy evidence.

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

Do not change `.env`, `MODEL_DIR`, primary/near thresholds, `MIN_ENTRY_VOLUME_30S`, position sizing, model artifacts, or bot runtime state. Do not restart the bot for this round.

The next aligned research direction is to fix flow missingness/parity and then convert the support shape into a replay-integrated candidate-level gate with strict trade-count, walk-forward, and stress constraints. Do not widen quick-profit entries, do not relax volume globally, and do not add a blanket delayed profit-lock or stop-loss reentry rule from this evidence.

## Scoreboard

`docs/model_scoreboard.md` was updated for this round as a rejected/probe-only model note. No accepted model metrics changed.
