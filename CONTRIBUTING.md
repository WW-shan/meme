# Contributing

This repository is a plain Python application for the FourMeme collector, dataset, hybrid training, and bot workflow.

## Before Editing

- Read root `AGENTS.md` before making changes.
- Treat `AGENTS.md` as the canonical repo guidance; `CLAUDE.md` mirrors practical workflow notes for Claude Code.
- If you edit inside `config/`, `src/`, `src/core/`, `src/data/`, `src/trader/`, or `tools/`, also read the nearest child `AGENTS.md`.
- Do not edit `docs/goals/` unless the current task explicitly asks for goal-document changes.
- Treat real trading behavior as high risk. Keep `ENABLE_TRADING=false` unless the task explicitly covers live trading.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with local RPC and wallet values. Never commit `.env`, private keys, wallet files, or paid RPC credentials.

## Validation

Use `unittest` commands:

```bash
python -m unittest discover
python -m unittest tests.core.test_rpc_config
python -m unittest tests.model.test_run_hybrid_training_cli
python -m unittest tests.smoke.test_surviving_workflow_imports
```

For narrow changes, run the most relevant targeted test first, then run broader coverage when the change affects shared behavior.

## Artifact Policy

- Generated lifecycle data, datasets, logs, pid files, local caches, and virtualenvs stay untracked.
- Curated replay and model JSON/JSONL reports are reviewable evidence and may be tracked.
- Model binaries under `data/models/` are ignored by default unless a reviewed run is intentionally force-added.
- Do not change `.env.example` without also updating config contract tests when behavior changes.

## Pull Request Checklist

- Tests or an explicit reason they could not be run.
- `git diff --check` passes.
- `git status --short --untracked-files=all` contains only intended changes.
- No secrets, wallet material, RPC credentials, or accidental large artifacts.
- Any config-sensitive runtime change updates `.env.example` and relevant docs/tests.
