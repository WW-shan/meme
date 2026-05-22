# Plan

1. Inspect replay code paths and prior active-flow script to identify the narrowest default-off dead-flow exit hook.
2. Run external Claude analyzer with a long wait and strict no-write/no-spawn instructions.
3. If analysis supports the direction, write focused TDD tests for the default-off replay exit behavior.
4. Implement the minimal default-off replay parameters and a bounded replay script/report.
5. Run a small validation grid, then sealed final confirmation if validation has a candidate.
6. Write `docs/research/20260522-conditional-dead-flow-exit-replay/summary.md` and update `docs/model_scoreboard.md`.
7. Run local review + external Claude review, fix Critical/Warning findings.
8. Run focused tests, full `python -m unittest discover`, `git diff --check`, docs/goals guard.
9. Archive this task, force-add ignored CCG archive, commit, and push.
