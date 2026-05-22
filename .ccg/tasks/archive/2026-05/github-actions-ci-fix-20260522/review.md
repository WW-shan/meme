# Review

## Codex Local Review

### Critical

- None.

### Warning

- None remaining.

### Info

- Scope is test/CI only. No production `src/` behavior changed.
- `docs/goals` guard stayed clean.

## Claude Review

### Critical

- None. Claude approved the direction: the CI failure was a deterministic timezone-dependent test fixture bug, and production `parse_time()` should remain unchanged.

### Warning

- `tests/model/timezone_helpers.py` aware-datetime branch was misleading.
  - Resolution: changed aware datetime handling to `value.timestamp()`.
- `tests/model/test_collect_continuous_cleanup.py` still had the same naive `.timestamp()` pattern.
  - Resolution: changed checkpoint tests to construct aware UTC datetimes and serialize them with `isoformat()`.
- A non-UTC CI matrix lane could catch future helper regressions.
  - Resolution: deferred. This task keeps CI cost and scope focused on restoring current main CI. Local verification ran both `TZ=UTC` and default process timezone.

### Info

- Helper location remains under `tests/model/` because this is test fixture infrastructure, not production API.
- No standalone helper test was added; the affected probe tests exercise the helper through the exact fixture paths that failed in CI.

## Result

- Approved after Warning fixes.
