# Exit-State Attribution Diagnostic

Generated: `2026-05-25T18:21:44+08:00`

Contract: read-only diagnostic, not live-switch evidence. Active model remains `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% position sizing.

## Live Since Restart

- Restart anchor: `None`
- Closed trades: `1`; wins: `1`; losses: `0`
- Net profit: `3.7973257314077554e-05` BNB
- Failure labels: `{"profitable_exit": 1}`
- Close reasons: `{"ENTRY_SLIPPAGE_PROTECTION": 1}`

## Support Gate

| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |
|---|---:|---:|---:|---:|---|
| `post_target_collapse_or_live_mfe_giveback` | 5 | 0 | 4 | 0 | NO-GO |
| `dead_flow_timeout` | 0 | 0 | 0 | 7 | NO-GO |
| `entry_slippage_failure` | n/a | n/a | n/a | 0 | NO-GO |

## Decision

`NO_GO_FOR_LIVE_RULE`: validation_positives is 0, below the >=3 support gate. No candidate bucket has >=3 positives in validation, final, and live with a replay-equivalent label. The best-supported post-target direction has train=5, validation=0, final=4, live=0.

The next aligned step is a default-off replay-only feasibility probe or more live label accumulation, not a live config/model switch.

## Symbols

- Live `mfe_then_giveback`: ``
- Live `dead_flow_timeout`: ``
- Live `entry_slippage_failure`: ``
- Live `profitable_exit`: `尽调中心`
