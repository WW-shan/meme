# TRADER BOT GUIDE

## OVERVIEW

Owns the live bot orchestrator: async queues, background tasks, position state, model loading, and exit behavior.

## WHERE TO LOOK

| Topic | Location | Notes |
|---|---|---|
| Main bot runtime | `bot.py` | largest orchestrator in repo |
| Persisted bot state | `data/bot_state.json` | runtime resumption surface |
| Model artifacts | `data/models/` | buy model, threshold, BC, PPO policy |
| Trading config dependency | `config/trading_config.py` | see `config/AGENTS.md` |

## CONVENTIONS

- `bot.py` owns queue topology and background-task coordination.
- Position state persists in `data/bot_state.json`; preserve compatibility if fields change.
- Model artifacts load from `data/models`.
- Hard stop-loss is always enforced.
- Time-based exits are part of the contract, not an optional optimization.
- Shutdown flow includes emergency liquidation behavior.
- Route env and risk-parameter semantics to `config/AGENTS.md`.
- Route shared training/model semantics to `src/AGENTS.md`.

## ANTI-PATTERNS

- Splitting queue ownership across unrelated modules.
- Introducing alternate state-file layouts without migration logic.
- Making stop-loss optional because the model prefers to hold.
- Skipping liquidation/cleanup for a cleaner shutdown path.
- Hardcoding one-off model artifact paths outside `data/models`.

## NOTES

- This subtree orchestrates; it should not absorb listener transport internals or dataset heuristics.
- For transport bugs, read `src/core/AGENTS.md`. For training/model behavior, read `src/AGENTS.md`.
