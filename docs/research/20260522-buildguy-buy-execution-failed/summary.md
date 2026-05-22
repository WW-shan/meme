# 2026-05-22 BUILDGUY Buy Execution Failed

## Context

This round continued the live v95 canary review after the previous post-`17:05` abstention/cleanup node had already been archived, committed, pushed, and verified green in CI.

The user reported another new trade. Local evidence showed this was not a successful new open: it was a queued BUILDGUY buy attempt that failed at transaction submission.

## Live Evidence

- Signal audit since `2026-05-22 17:05:00`: `606` `SIGNAL_DECISION` rows through the `17:55:30.980978 +0800` snapshot.
- Decisions in that window: `605` rejected, `1` queued.
- Non-decision audit rows in that window: `1` `BUY_EXECUTION_FAILED`.
- Since the previous closeout snapshot at `17:40:54.307910 +0800`: `349` signal decisions, `348` rejected and `1` queued, plus `1` `BUY_EXECUTION_FAILED`.

## BUILDGUY Attribution

- Token: `0x18C412942775bff9523B29752A08444986654444`.
- Symbol: `BUILDGUY`.
- Queued at `2026-05-22 17:46:18.174736`.
- Signal features:
  - `prob=0.9829137733278135`
  - `PredReturn=47.50809044519591`
  - `token_age_seconds=145.0`
  - `volume_30s=1.6957425722970296`
  - `price_volatility=0.146165426354468`
- The bot used lifecycle fast status at `17:46:18.919`, with price `9.381203198410017e-09`, staleness `0.018s`, and chain lag `2.176s`.
- The bot attempted a real buy at `17:46:18.920` for about `0.000294 BNB`.
- `src.core.trader` rejected the submission at `17:46:19.143` with `nonce too low: next nonce 869, tx nonce 867`.
- `data/signal_audit.jsonl` recorded `BUY_EXECUTION_FAILED` at `17:46:19.143430`.
- `data/paper_trades.jsonl` stayed at `184` rows and had `0` BUILDGUY rows.
- `data/bot_state.json` still had `positions_count=0` and `positions={}`.
- No later BUILDGUY `BUY SIGNAL` or open-position audit row appeared.

## Price Path

`data/training/collector_runtime_state.json` still contained BUILDGUY as an active lifecycle in the `17:55:56 +0800` snapshot.

- First observed price: `6.01636694221724e-09` at `17:43:51`.
- Signal/audit price: `9.381203198410017e-09`, `+55.93%` from first observed price.
- Lifecycle peak: `9.797425565826684e-09` at `17:46:20`, only `+4.44%` over the signal price.
- Runtime snapshot current price: `6.817968030570905e-09`, `-27.32%` versus the signal price.
- After the failed buy, the model quickly re-rejected the token:
  - `17:46:22`: `PredReturn=2.7276`, rejected by `pred_return_below_min`.
  - `17:46:24`: `PredReturn=-1.0651`, rejected.
  - Later BUILDGUY rows stayed negative or low through `17:48:38`.

## Decision

Classify BUILDGUY as a transient execution-layer nonce-staleness failure, not a successful trade and not a model threshold miss.

No model artifact, `.env`, threshold, sizing, trading-logic, or restart change is justified from this single event. `src/core/trader.py` resets `local_nonce=None` after a buy exception, so the next transaction re-syncs from chain. `src/trader/bot.py` does not blindly resubmit the original buy after the `1.5s` cooldown; the candidate must still pass model gates, and BUILDGUY no longer did.

The residual risk is operational: nonce staleness can recur if rapid or overlapping transactions advance the chain nonce ahead of the local cache. A proactive per-buy chain nonce read would add latency to the buy path, so this remains a watchpoint rather than an immediate code change.

`docs/model_scoreboard.md` was updated because this round changes the public live interpretation from pure post-`17:05` abstention to one queued signal that failed at execution and quickly faded.

## Verification

- `python` summary checks on `data/signal_audit.jsonl`, `data/paper_trades.jsonl`, `data/bot_state.json`, `data/training/collector_runtime_state.json`, and `logs/bot.log`
- Code inspection of `src/core/trader.py` nonce cache/reset behavior and `src/trader/bot.py` failed-buy cooldown behavior
- External Claude second perspective: session `126dcebd-6c94-4e43-996f-00b38a1d122f`
- Bot status: running
- Collector status: running
