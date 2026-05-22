# Post-CI Research Round

Generated: `2026-05-22 09:30:42 +0800`

Contract: read-only diagnostic evidence; no live model or runtime configuration change.

## Rejected-Signal Refresh

- Time-to-barrier report: `data/replay_reports/time_to_barrier_probe_20260522_post_ci_current_day_all_candidates.json`
- Support report: `data/replay_reports/support_action_policy_20260522_post_ci_current_day.json`
- Pooled report: `data/replay_reports/support_action_policy_pool_20260522_post_ci_current_plus_expanded.json`
- Current-day candidates: `66` per-token candidates from `2010` signal decisions; sample-limited: `false`
- Current-day labels: `fast_profit=11`, `fast_profit_then_collapse=4`, `slow_runner=1`, `flat_timeout=38`, `stop_first=12`
- Current-day support: `16` positives, `50` negatives
- Best current-day eligible rule: `high_prob_low_toxic_overlap`, selected `7`, positives `4`, precision `57.14%`; this is reported only as a diagnostic number because the slice misses the support floor
- Pooled candidates: `898`; positives `172`, negatives `726`
- Pooled target flow rule: selected `142`, positives `68`, precision `47.89%`
- Pooled decision: `missing_flow_feature_parity`; required flow fields are not complete across the pooled candidate set

Pre-registered criteria failed. The current-day slice is below the `150` candidate support floor, and the pooled target flow rule misses the `58%` precision target while still failing flow parity.

Eligibility note: current-day support uses `min_selected=3`; lower-support flow variants were not treated as evidence.

## Live-Loss Forensics

Source: `docs/research/20260522-live-trade-attribution-refresh/live_attribution.json`.

No newer closed real trade exists after `2026-05-21 20:42:26`; this table reuses the latest closed-trade attribution snapshot as a loss-only forensic view.

- Closed real trades since restart: `18`
- Losses: `16`
- Loss-only net: `-0.0016679114065155773` BNB
- Loss labels: `dead_flow_timeout=7`, `entry_slippage_failure=2`, `mfe_then_giveback=3`, `stop_first_after_entry=1`, `unprofitable_other=3`
- Loss close reasons: `TIME_EXIT=7`, `STOP_LOSS=4`, `PPO_SELL100=3`, `ENTRY_SLIPPAGE_PROTECTION=2`

| open_time | symbol | prob | pred_return | near | reason | label | net_bnb | hold_s | slip_pct | signal_open_s | MFE% | MAE% | first_barrier |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 2026-05-20 12:07:47.650455 | FENGSHUI | 0.9947 | 103.27 | N | ENTRY_SLIPPAGE_PROTECTION | entry_slippage_failure | -0.000402605 | 6.8 | 0.6604 | 2.62 | -1.82 | -76.04 | -18 |
| 2026-05-20 12:32:19.997588 | FENGSHUI | 0.9947 | 70.21 | N | STOP_LOSS | mfe_then_giveback | -0.000326840 | 90.6 | 0.0461 | 2.38 | 92.73 | -74.61 | +25 |
| 2026-05-21 02:10:09.761923 | CMC | 0.9885 | 43.32 | N | STOP_LOSS | mfe_then_giveback | -0.000228157 | 491.6 | 0.0522 | 2.23 | 37.18 | -51.63 | +25 |
| 2026-05-21 20:07:52.348972 | AUCA | 0.9842 | 93.62 | N | STOP_LOSS | mfe_then_giveback | -0.000165622 | 85.9 | 0.0987 | 2.54 | 102.90 | -39.44 | +25 |
| 2026-05-19 14:12:10.445957 | TSG | 0.9896 | 39.56 | N | STOP_LOSS | stop_first_after_entry | -0.000091868 | 93.4 | -0.0361 | 1.66 | 13.77 | -19.32 | -18 |
| 2026-05-21 12:00:50.559551 | domybest | 0.9849 | 56.75 | N | PPO_SELL100 | unprofitable_other | -0.000059947 | 89.4 | 0.1154 | 2.39 | -1.98 | -10.73 | None |
| 2026-05-21 14:43:14.970408 | 人间半夏小得盈满 | 0.9782 | 48.08 | Y | TIME_EXIT | dead_flow_timeout | -0.000057122 | 564.7 | 0.0524 | 1.29 | -1.98 | -9.48 | None |
| 2026-05-20 12:30:29.477678 | BNBGUY | 0.9553 | 52.87 | Y | PPO_SELL100 | unprofitable_other | -0.000054175 | 147.1 | 0.0933 | 3.48 | 10.05 | -9.88 | None |
| 2026-05-20 14:07:42.183647 | 饼小龙 | 0.9756 | 32.76 | Y | PPO_SELL100 | unprofitable_other | -0.000049018 | 69.5 | -0.0537 | 2.69 | -1.98 | -6.55 | None |
| 2026-05-20 20:00:29.078816 | BNA | 0.9676 | 38.20 | Y | TIME_EXIT | dead_flow_timeout | -0.000042795 | 566.2 | 0.0366 | 2.17 | -1.98 | -3.52 | None |
| 2026-05-20 19:00:42.537979 | 黄金夏日 | 0.9730 | 41.26 | Y | TIME_EXIT | dead_flow_timeout | -0.000041647 | 564.9 | 0.0367 | 1.35 | -1.98 | -3.52 | None |
| 2026-05-19 17:01:29.648115 | 币安 x402 | 0.9761 | 39.99 | Y | TIME_EXIT | dead_flow_timeout | -0.000031541 | 565.8 | -0.0555 | 1.25 | -1.98 | -1.98 | None |
| 2026-05-21 20:32:59.646364 | 币安队长 | 0.9763 | 37.45 | Y | TIME_EXIT | dead_flow_timeout | -0.000030418 | 563.9 | 0.0098 | 2.81 | -1.33 | -2.89 | None |
| 2026-05-20 17:37:51.388838 | 挠头 | 0.9828 | 58.58 | N | ENTRY_SLIPPAGE_PROTECTION | entry_slippage_failure | -0.000029599 | 5.7 | 0.3482 | 2.78 | -1.98 | -22.87 | -18 |
| 2026-05-21 16:52:56.643227 | 披风 | 0.9705 | 38.76 | Y | TIME_EXIT | dead_flow_timeout | -0.000028463 | 562.5 | -0.0556 | 1.72 | -1.98 | -2.12 | None |
| 2026-05-21 16:29:54.546046 | 🆙 | 0.9816 | 44.33 | N | TIME_EXIT | dead_flow_timeout | -0.000028094 | 562.6 | -0.0555 | 1.71 | -1.98 | -1.98 | None |

## Conclusion

Decision: `NO_GO_FOR_LIVE_SWITCH`.

This round falsifies the idea that the rejected-signal flow-support loop has become actionable after the CI interruption. The live-loss table points at two better future replay hypotheses: an entry-slippage veto/protection threshold for high positive slippage entries, and a giveback guard for trades that reached `+25%` MFE but later closed at STOP_LOSS. Both require a fresh pre-registered replay round before any live change.
