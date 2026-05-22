# 2026-05-22 Live Zero-Balance State Guard

## Context

This round reviewed the new v95 live canary trades after `2026-05-22 13:00` and kept the live model, `.env`, thresholds, and sizing unchanged. The actionable defect was runtime state persistence, not model selection.

## Live Evidence

| Token | Open | Close / event | Attribution |
|---|---|---|---|
| `华尔街瞎报` | `2026-05-22 13:20:56` | `2026-05-22 13:28:58`, `APP_STOP_LIQUIDATION` | Operational issue. The bot restart at `13:28:53` triggered emergency liquidation while the position was still open, so this close should not be counted as a model exit decision. |
| `FIGHT` | `2026-05-22 13:23:22` | `2026-05-22 13:28:03`, `PPO_SELL100` | Normal live loss / weak exit evidence. Helper status was used and the position closed before the restart. |
| `PORA` | `2026-05-22 13:37:54` | `2026-05-22 13:39:43`, `PPO_SELL100` | Late-entry evidence. Fast lifecycle attribution showed `lifecycle_price_from_peak_pct=-0.6311052905052421` at entry. |
| `吃饱饱赚饱饱` | `2026-05-22 13:42:48` | `2026-05-22 13:52:09` sell attempt, `13:52:11` zero token balance | Runtime state defect. Logs showed `Token balance is 0 ... removing position`, but no `CLOSE` / `POSITION_CLOSED` row was written and `data/bot_state.json` still listed the position. |

## Root Cause

`src/trader/bot.py` handled the zero-balance sell branch by removing the position from memory and returning `None`. `_close_position_inner()` then returned early because the position was already gone. That skipped `_save_state()`, so a later restart could resurrect a stale position from `data/bot_state.json`.

## Decision

Keep v95 live canary model, runtime thresholds, `.env`, and position sizing unchanged. Accept a runtime state-persistence guard: when `_do_sell()` sees zero token balance, it now writes a `POSITION_ZERO_BALANCE_REMOVED` signal-audit event, removes the position, records the token in `closed_tokens`, and saves state immediately.

`docs/model_scoreboard.md` was updated in this round because the live trade evidence changed runtime safety behavior, even though it did not justify a model or threshold change.

## Verification

- Red test before fix: `python -m unittest tests.core.test_hybrid_requirements_contract.TestPredReturnFilterStartupContract.test_do_sell_zero_balance_removes_position_and_saves_state` failed because `state.json` was not written.
- Green targeted test after fix: same command passed.
- Contract suite: `python -m unittest tests.core.test_hybrid_requirements_contract` passed, `82` tests OK.
- Full suite: `python -m unittest discover` passed, `739` tests OK, `1` skipped.
- Formatting: `git diff --check` passed.
