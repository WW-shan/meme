# Requirements

Fix the GitHub Actions CI failure before continuing model research.

## Constraints

- Keep this as the only active CCG task until archived, committed, and pushed.
- Do not modify `docs/goals/**`.
- Do not change live trading config, `.env`, model artifacts, thresholds, or position sizing.
- Identify the CI root cause from GitHub Actions logs before changing code.
- Reproduce the failure locally where possible.
- Prefer the narrowest deterministic fix that makes CI and local tests agree.

## Acceptance

- The previously failing GitHub Actions unittest class failures are reproduced locally with a UTC timezone.
- The fix removes the system-timezone dependency.
- Focused failing tests pass under `TZ=UTC`.
- Full `python -m unittest discover` passes locally.
- Task is archived, committed, pushed, and CI is rechecked.
