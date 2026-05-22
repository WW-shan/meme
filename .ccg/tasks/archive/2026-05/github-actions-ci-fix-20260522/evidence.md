# Evidence

## Failure Reproduction

- Latest failed GitHub Actions run: `https://github.com/WW-shan/meme/actions/runs/26261566877`
- Root cause reproduced locally with `TZ=UTC` on the affected model tests before the fix.

## Final Verification

- `TZ=UTC python -m unittest tests.model.test_collect_continuous_cleanup`
  - Passed: `Ran 11 tests in 0.004s`
- `TZ=UTC python -m unittest discover`
  - Passed: `Ran 739 tests in 1.302s`
- `python -m unittest discover`
  - Passed: `Ran 739 tests in 1.320s`
- `git diff --check`
  - Clean
- `docs/goals` guard
  - No changes

## Notes

- Production `src.pipeline.reentry_probe.parse_time()` was left unchanged.
- CI workflow now sets `TZ: UTC` explicitly to make the runner contract obvious.
