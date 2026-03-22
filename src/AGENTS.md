# SRC PACKAGE GUIDE

## OVERVIEW

`src` is the import root. This file covers shared package layout and the training/model cluster; deeper child files own `core`, `trader`, and `data`.

## STRUCTURE

```text
src/
├── core/       # listener, websocket manager, trade transport
├── data/       # lifecycle state, dataset builder, feature extraction
├── trader/     # live bot orchestration
├── pipeline/   # hybrid training orchestration
├── model/      # buy model and hybrid inference
├── rl/         # PPO, BC, trading env, reward logic
├── backtest/   # impact / execution simulation
├── features/   # feature validity helpers
└── utils/      # support helpers, not a second domain layer
```

## WHERE TO LOOK

| Task | Location | Notes |
|---|---|---|
| Transport / listener behavior | `core/` | See `src/core/AGENTS.md` |
| Live bot workflow | `trader/` | See `src/trader/AGENTS.md` |
| Lifecycle and dataset logic | `data/` | See `src/data/AGENTS.md` |
| Hybrid training flow | `pipeline/` | Covered here |
| Buy model / hybrid inference | `model/` | Covered here |
| PPO / BC / env / reward | `rl/` | Covered here |
| Execution simulation | `backtest/` | Covered here |
| Feature validity helpers | `features/` | Covered here |

## CONVENTIONS

- `src` is the import root used by runtime commands like `python -m src.trader.bot`.
- Several scripts prepend the repo root to `sys.path`; keep imports compatible with that pattern.
- Keep package roles separated:
  - `pipeline` orchestrates training,
  - `model` owns model implementations and load/save surfaces,
  - `rl` owns training env and sell-policy learning,
  - `backtest` owns offline execution simulation,
  - `features` owns feature-level helpers.
- `scripts/build_dataset_new.py` and `scripts/run_hybrid_training.py` are thin CLI surfaces over this tree, not independent domain layers.

## ANTI-PATTERNS

- Moving transport or bot orchestration into training packages.
- Turning `utils/` into a catch-all for domain behavior.
- Creating a second training pipeline outside `pipeline/`.
- Duplicating data-prep heuristics outside `src/data/`.

## NOTES

- For `core`, `trader`, or `data`, switch to the deeper child file.
- For training/model changes spanning `pipeline`, `model`, `rl`, `backtest`, and `features`, this file is the shared owner.
