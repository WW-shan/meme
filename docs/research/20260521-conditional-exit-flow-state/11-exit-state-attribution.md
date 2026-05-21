# Exit-State Attribution Diagnostic

Generated: `2026-05-22T01:35:13+08:00`

Contract: read-only diagnostic, not live-switch evidence. Active model remains `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% position sizing.

## Live Since Restart

- Restart anchor: `2026-05-19 04:02:23`
- Closed trades: `18`; wins: `2`; losses: `16`
- Net profit: `-0.001256566335` BNB
- Failure labels: `{"dead_flow_timeout": 7, "entry_slippage_failure": 2, "mfe_then_giveback": 3, "profitable_exit": 2, "stop_first_after_entry": 1, "unprofitable_other": 3}`
- Close reasons: `{"ENTRY_SLIPPAGE_PROTECTION": 2, "PPO_SELL100": 5, "STOP_LOSS": 4, "TIME_EXIT": 7}`

## Support Gate

| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |
|---|---:|---:|---:|---:|---|
| `post_target_collapse_or_live_mfe_giveback` | 5 | 0 | 4 | 3 | NO-GO |
| `dead_flow_timeout` | 0 | 0 | 0 | 7 | NO-GO |
| `entry_slippage_failure` | n/a | n/a | n/a | 2 | NO-GO |

## Decision

`NO_GO_FOR_LIVE_RULE`: validation_positives is 0, below the >=3 support gate. No candidate bucket has >=3 positives in validation, final, and live with a replay-equivalent label. The best-supported post-target direction has train=5, validation=0, final=4, live=3.

The next aligned step is a default-off replay-only feasibility probe or more live label accumulation, not a live config/model switch.

## Symbols

- Live `mfe_then_giveback`: `FENGSHUI, CMC, AUCA`
- Live `dead_flow_timeout`: `币安 x402, 黄金夏日, BNA, 人间半夏小得盈满, 🆙, 披风, 币安队长`
- Live `entry_slippage_failure`: `FENGSHUI, 挠头`
- Live `profitable_exit`: `赵长娥, Bsc大金狗`
