# 2026-05-22 Live Watchpoint: 温州队长

## Context

This round continued the live v95 canary evidence review after `16:36 +0800` and kept the bot, collector, thresholds, sizing, and `.env` unchanged.

## Live Evidence

- Signal audit since `2026-05-22 16:36:00`: `166` `SIGNAL_DECISION` rows, `0` queued buys, `0` opened buys.
- Paper trades since `16:36`: `0`.
- Latest real trade is still the `2026-05-22 13:42:48` open for `吃饱饱赚饱饱`.
- Bot and collector remained healthy during the observation window.

### Main Watchpoint

`温州队长` (`0xeC1491941AB68dbEC4e3055C95cEc38af0124444`) was the strongest new live candidate:

- First signal: `2026-05-22 16:43:31.699353`
- First signal prob / PredReturn: `0.9848170688295238` / `4.558862752960975`
- First-signal reason: `entry_volume_30s_below_min`
- Price at or before first signal: `7.087449570393333e-09`
- Peak after first signal: `1.5276123267083143e-08` (`+115.54%` from first-signal price)
- Latest observed price by `16:48`: `5.74711319935697e-09`
- Latest from peak: about `-62.38%`

The max-prob signal for the same token was later:

- Max-prob time: `2026-05-22 16:43:36.227719`
- Max-prob prob / PredReturn: `0.9902015387357727` / `-6.624934944561912`
- Reason: `pred_return_below_min`

Later signals for the same token continued to reject on `pred_return_below_min`, `near_threshold_pred_return_below_min`, `buy_model_reject`, and `entry_volume_30s_below_min`.

## Decision

No model, threshold, sizing, runtime, or restart change is justified from this round.

`docs/model_scoreboard.md` was updated with a no-change live watchpoint note so this round is recorded in the public scoreboard instead of only in local `.ccg` state.

## Verification

- `python` summary checks on `data/signal_audit.jsonl`, `data/paper_trades.jsonl`, `data/bot_state.json`, `data/training/collector_runtime_state.json`, and `logs/bot.log`
- `gh run list --limit 5` latest CI remained green
- Bot status: running
- Collector status: running
