# Implementation Plan

Goal: complete one full read-only research/experiment round for live trade attribution refresh without opening another CCG task.

Files:
- Create `src/pipeline/live_trade_attribution_probe.py` for raw paper-trade/lifecycle attribution logic.
- Create `scripts/probe_live_trade_attribution.py` as a thin CLI that writes JSON + markdown under `docs/research/20260522-live-trade-attribution-refresh/`.
- Create `tests/model/test_live_trade_attribution_probe.py` and `tests/model/test_live_trade_attribution_probe_cli.py` first, then implement.
- Update `docs/research/20260522-live-trade-attribution-refresh/summary.md` and `live_attribution.json` from the CLI output.
- Update `docs/model_scoreboard.md` with a rejected/read-only note only after evidence is generated.
- Do not edit `.env`, `data/models/**`, `docs/goals/**`, or live runtime thresholds.

## TDD Steps

1. Write failing unit tests for:
   - OPEN/CLOSE real-trade pairing.
   - first-barrier-safe loss classification (`mfe_then_giveback` only if +25 before stop/loss).
   - `near_threshold_like` recomputation from prob/threshold rather than copying stale fields.
   - report contract flags: `read_only=true`, `live_switch_evidence=false`, `safe_for_live_switch=false`.
2. Run focused tests and verify they fail because the module does not exist yet.
3. Implement minimal probe module using existing `reentry_probe` helpers.
4. Run focused tests until green.
5. Add CLI test for output-path protection and fake-probe wiring.
6. Implement thin CLI.
7. Run focused tests, generate real report, inspect decision.
8. Run local Codex review + external Claude review if diff >30 lines.
9. Run focused tests, full `python -m unittest discover`, `git diff --check`, docs/goals guard checks.
10. Archive task, force-add ignored `.ccg` archive, commit, and push.
