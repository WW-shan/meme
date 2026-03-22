# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-10
**Branch:** `main`
**Commit:** `23d41ee`

## OVERVIEW

FourMeme Hybrid Trading System. Main path: collector -> dataset -> hybrid training -> bot.

This repo is a plain Python application repo, not a packaged library. `src` is the import root, and several entry scripts prepend the repo root to `sys.path`.

## PRECEDENCE

Nearest child `AGENTS.md` wins for files in its subtree. Use this root file for routing, global commands, and repo-wide constraints; use child files for local ownership and conventions.

## STRUCTURE

```text
./
├── config/        # env contract, RPC separation, trading knobs, ABI loading
├── docs/plans/    # dated design/implementation notes
├── scripts/       # thin CLIs for dataset build and hybrid training
├── src/           # import root; package map and training/runtime code
├── systemd/       # collector service deployment notes
├── tests/         # unittest contract and workflow coverage
└── tools/         # memectl, collector entrypoint, shell runtime helpers
```

## WHERE TO LOOK

| Task | Location | Notes |
|---|---|---|
| Env / RPC / trading config | `config/` | See `config/AGENTS.md` |
| Shared package map / training cluster | `src/` | See `src/AGENTS.md` |
| Listener / WS / transport | `src/core/` | See `src/core/AGENTS.md` |
| Live bot behavior | `src/trader/` | See `src/trader/AGENTS.md` |
| Lifecycle / dataset / features | `src/data/` | See `src/data/AGENTS.md` |
| Local service control / collector ops | `tools/` | See `tools/AGENTS.md` |
| Deployment install steps | `systemd/README.md` | Covered by `tools/AGENTS.md` |
| Historical design context | `docs/plans/` | Reference only; not the runtime source of truth |

## CONVENTIONS

- Dependency surface is `requirements.txt`.
- Test surface is `python -m unittest discover`.
- No `pyproject.toml`, `setup.py`, `tox.ini`, or pytest config.
- `src` is the import root; do not assume a `src/<package_name>/...` layout.
- `.env.example` is the env contract template.
- RPC roles are intentionally separated: listener WS, listener HTTP logs pool, trade HTTP RPC.
- `ENABLE_TRADING=false` is the safe default; treat real trading as opt-in.

## ANTI-PATTERNS

- Assuming pytest, tox, or packaging metadata drives the workflow.
- Mixing listener RPC endpoints and trade submission RPC endpoints.
- Repeating subtree rules here instead of moving them into a child file.
- Changing env-driven behavior without updating `.env.example` and relevant contract tests.
- Treating dated docs in `docs/plans/` as newer than code plus tests.

## UNIQUE STYLES

- `tests/core/` acts like infra contract coverage.
- `tests/model/` covers dataset, feature, training, and RL behavior.
- `docs/plans/` uses dated design/implementation files by topic.
- `tools/memectl` is the repo-supported Unix service wrapper; Windows work should prefer direct Python entrypoints unless editing the wrapper itself.

## COMMANDS

```bash
python -m venv .venv
pip install -r requirements.txt

python tools/collect_continuous.py
python scripts/build_dataset_new.py --lifecycle-dir data/training --output-dir data/datasets
python scripts/run_hybrid_training.py --output-dir data/models --lifecycle-dir data/training
python -m src.trader.bot

python -m unittest discover
python -m unittest tests.core.test_rpc_config
python -m unittest tests.model.test_run_hybrid_training_cli
```

## NOTES

- Root routes; children own details.
- For cross-cutting work, read every touched child file before editing.
- For config-sensitive runtime changes, trust code plus `tests/core/*` over assumptions.
