# 2026-05-22 Live Abstention And Cleanup Audit

## Context

This round extended the live v95 canary review after `17:05 +0800` and kept the bot, collector, thresholds, sizing, and `.env` unchanged.

The user reported a new trade during the round. Local evidence showed this was not a new model entry: it was the earlier `吃饱饱赚饱饱` position being cleaned up at `13:52:09 +0800` after `TIME_EXIT` found on-chain token balance `0`.

## Live Evidence

- Signal audit since `2026-05-22 16:48:00`: `791` `SIGNAL_DECISION` rows through the `17:40:54.307910 +0800` closeout snapshot, all rejected, with `0` queued buys and `0` opened buys.
- Signal audit since `2026-05-22 17:05:00`: `258` additional `SIGNAL_DECISION` rows through the same closeout snapshot, all rejected, still `0` queued buys and `0` opened buys.
- Paper trades since `16:48`: `0`.
- Latest `paper_trades.jsonl` row is still the `2026-05-22 13:42:48` open for `吃饱饱赚饱饱`.
- Bot log shows a `TIME_EXIT` sell attempt for `吃饱饱赚饱饱` at `13:52:09`, then `Token balance is 0 ... removing position` at `13:52:11`; `data/bot_state.json` has no open positions and includes the token in `closed_tokens`.
- The running bot process started at `13:28:59`, before commit `6142cee` (`fix: persist zero-balance sell cleanup`) existed for that process. Current source already records future zero-balance removals in `signal_audit`, but this live event is a pre-fix data-integrity gap: no `POSITION_ZERO_BALANCE_REMOVED` audit row and no synthetic `CLOSE` row were written.
- Bot and collector remained healthy during the observation window.

### Main Watchpoints

`AIBNB` (`0x373EF7E0EAb228bD40eAc58158A1d1a3DDe64444`) was the most useful borderline case:

- First signal: `2026-05-22 16:51:02.961794`
- First-signal prob / PredReturn: `0.985306342258131` / `10.95131852432386`
- First-signal reason: `entry_volume_30s_below_min`
- Price at first signal: `7.3055151606688435e-09`
- Peak after first signal: `1.2096073521639627e-08` (`+65.57%`)
- Closeout snapshot current price: `5.830277350312941e-09`
- Closeout from first signal: about `-20.19%`
- Closeout from peak: about `-51.80%`

Other notable candidates did not change the conclusion:

- `🤣` peaked about `+9.08` PredReturn but ended about `-35.18%` from peak.
- `以太坊思维` only reached about `+2.08` PredReturn and remained below the actionable gate.
- `TER` became the dominant later reject stream after `17:20`, but its PredReturn oscillated below the actionable gate and never produced a buy.
- `请自行做好研究`, `NNB`, `田螺姑娘`, and `J8` were the newest later rejects in the closeout snapshot, all rejected by the same model/near-threshold gates rather than forming a new entry.
- `108` stayed below the signal-price peak and never crossed into actionable territory.
- `币安黑奴` reached about `+11.82` PredReturn but remained a border case, not a model change.
- `EHD1000` appeared only as a later reject, not as a buy candidate.
- `祖国人` stayed a sub-threshold/borderline reject and did not produce a runner path.

## Decision

No model artifact, threshold, sizing, runtime, or restart change is justified from this round.

No code change is needed in this round for the zero-balance cleanup case. The current source already has the intended guard from `6142cee`, and writing a retroactive synthetic `CLOSE` row would mix an operational cleanup with a real economic close.

`docs/model_scoreboard.md` was updated with an abstention plus cleanup-audit note so this round is recorded in the public scoreboard instead of only in local `.ccg` state.

## Verification

- `python` summary checks on `data/signal_audit.jsonl`, `data/paper_trades.jsonl`, `data/bot_state.json`, `data/training/collector_runtime_state.json`, and `logs/bot.log`
- `gh run list --limit 5` latest CI remained green
- `gh pr view` confirmed PR `#2` is open and draft
- Bot status: running
- Collector status: running
