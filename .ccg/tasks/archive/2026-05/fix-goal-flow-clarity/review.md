# Review

## Critical

- None.

## Warning

- None.

## Info

- Added a root `AGENTS.md` phase gate so future goal work must close pending completed nodes before opening follow-up tasks.
- Confirmed this change does not modify protected `docs/goals/` files.

## Verification

- `venv/bin/python -m unittest discover -q` passed: 696 tests.
- JSON validation passed for active task metadata and generated research artifacts.
