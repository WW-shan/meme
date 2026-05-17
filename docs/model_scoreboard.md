# Model Scoreboard

This file records accepted and rejected model candidates for live FourMeme trading. Selection is based on live-sized replay with 10% position sizing, gas costs, current execution delay assumptions, walk-forward checks, and stress replay.

## Accepted Baseline

| Model | Status | Threshold | Trades | Net Return | Net Profit BNB | Win Rate | Max DD | WF Worst Return | WF Worst DD | Reason |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `data/models/20260516_v67_v65_thr9715_tr35_12` | accepted/live baseline | `0.9715` | `140` | `319.2357%` | `0.02248441` | `60.7143%` | `-17.0505%` | `77.7197%` | `-16.8768%` | Best accepted strict live-sized baseline so far. Strong final return, positive walk-forward worst segment, and positive harsh stress replay. |

## Rejected Candidates

| Date | Model | Status | Threshold | Trades | Net Return | Net Profit BNB | Win Rate | Max DD | WF Worst Return | Stress Summary | Decision |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2026-05-17 | `data/models/20260517_v75b_profit_path_hold60_screen` | rejected | `0.956` | `73` | `200.6989%` | `0.01413563` | `61.6438%` | `-14.9665%` | `15.9330%` | Final harsh stress stayed positive around `21%`, but validation harsh friction was `-0.0816%` and validation harsh execution was `-17.6282%`. | Do not switch live. Profit-path hold60 reduced drawdown and raised win rate slightly, but gave up too much return versus v67 and validation stress was unstable. |
| 2026-05-17 | `data/models/20260517_v76_quality30_v67exit_screen` | rejected | `0.9715` | `74` | `217.3068%` | `0.01530535` | `60.8108%` | `-11.8992%` | `18.9700%` | Final harsh friction was `-0.1385%` and harsh execution was `-11.3059%`; validation walk-forward worst was `-2.4786%`. | Do not switch live. Raising the delay-robust target to `30%` with v67-style exits improved drawdown but cut too many profitable trades and failed stress/walk-forward gates versus v67. |

## Notes

- v75b used `profit_path` behavior cloning, `min_policy_hold_seconds=60`, `trailing_start_pct=0.35`, `trailing_stop_pct=0.12`, `stop_loss=-0.25`, `entry_delay_seconds=1`, `exit_delay_seconds=4`, and 10% position sizing.
- v75b is useful evidence that simply forcing longer minimum hold is not enough. The next promising direction is conditional exit logic: keep runners longer only when path/flow features justify it, while preserving fast exits for collapsing tokens.
- v76 is useful evidence that making the buy label stricter is not enough. Recent near-miss analysis found a small runner subset among high `PredReturn` rejects, but most high `PredReturn` rejects still had large downside. The next direction should be a second-stage runner filter or conditional exit policy, not a global threshold relaxation.
