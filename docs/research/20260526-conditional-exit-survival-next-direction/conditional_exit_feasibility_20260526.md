# Exit-State Attribution Diagnostic

Generated: `2026-05-26T05:47:28+08:00`

Contract: read-only diagnostic, not live-switch evidence. Active model remains `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% position sizing.

## Live Since Restart

- Restart anchor: `None`
- Closed trades: `0`; wins: `0`; losses: `0`
- Net profit: `0` BNB
- Failure labels: `{}`
- Close reasons: `{}`

## Support Gate

| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |
|---|---:|---:|---:|---:|---|
| `post_target_collapse_or_live_mfe_giveback` | 12 | 0 | 4 | 0 | NO-GO |
| `dead_flow_timeout` | n/a | n/a | n/a | 0 | NO-GO |
| `entry_slippage_failure` | n/a | n/a | n/a | 0 | NO-GO |

## Decision

`NO_GO_FOR_LIVE_RULE`: validation_positives is 0, below the >=3 support gate. No candidate bucket has >=3 positives in validation, final, and live with a replay-equivalent label. The best-supported post-target direction has train=12, validation=0, final=4, live=0.

The next aligned step is a default-off replay-only feasibility probe or more live label accumulation, not a live config/model switch.

## Symbols

- Live `mfe_then_giveback`: ``
- Live `dead_flow_timeout`: ``
- Live `entry_slippage_failure`: ``
- Live `profitable_exit`: ``
