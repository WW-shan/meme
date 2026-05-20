# Delayed Profit-Lock Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether a delayed, event-driven full-position profit-lock can improve realized profit for accepted v95 primary positions without increasing position size, entries, or live risk.

**Architecture:** Reuse the existing replay-only `profit_lock_take_profit_pct` and `profit_lock_max_hold_seconds` runtime overrides. Add a bounded CLI that sweeps delayed windows beyond the rejected `30-120s` fast-profit range because the live CMC trade reached +25% around 225s and +35% around 459s before a STOP_LOSS. The experiment is default-off and can only become live-switch evidence if validation and sealed final strictly beat the current best v95 baseline under the existing strict gates.

**Tech Stack:** Python stdlib CLI, `unittest`, `src.pipeline.model_replay.run_model_replay`, existing live-sized replay metrics.

---

### Task 1: Add Delayed Profit-Lock Replay CLI

**Files:**
- Create: `scripts/run_delayed_profit_lock_replay.py`
- Test: `tests/model/test_delayed_profit_lock_replay_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/model/test_delayed_profit_lock_replay_cli.py` with tests that load `scripts/run_delayed_profit_lock_replay.py` by path and verify:

```python
def test_candidate_grid_uses_delayed_windows_only(self):
    cli = _load_cli()
    candidates = list(cli.candidate_grid())
    self.assertEqual(len(candidates), 16)
    self.assertEqual(candidates[0], {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": 180.0})
    self.assertEqual(candidates[-1], {"profit_lock_take_profit_pct": 0.60, "profit_lock_max_hold_seconds": 480.0})
    for candidate in candidates:
        self.assertEqual(set(candidate), {"profit_lock_take_profit_pct", "profit_lock_max_hold_seconds"})
        self.assertGreater(candidate["profit_lock_max_hold_seconds"], 120.0)
```

Also test strict risk parsing rejects `--position-fraction 0.2`, `--max-position-fraction 0.05`, and `--max-open-positions 9`.

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_delayed_profit_lock_replay_cli
```

Expected: failure because `scripts/run_delayed_profit_lock_replay.py` does not exist.

- [ ] **Step 3: Implement minimal CLI**

Create `scripts/run_delayed_profit_lock_replay.py` by reusing the structure of `scripts/run_fast_profit_lock_replay.py`, with these intentional differences:

```python
DEFAULT_OUTPUT = "data/replay_reports/delayed_profit_lock_replay_20260521_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.003957285747499339

def candidate_grid():
    profit_targets = [0.25, 0.35, 0.45, 0.60]
    max_windows = [180.0, 240.0, 360.0, 480.0]
    for target, window in itertools.product(profit_targets, max_windows):
        yield {
            "profit_lock_take_profit_pct": target,
            "profit_lock_max_hold_seconds": window,
        }
```

The CLI must preserve:
- strict `position_fraction == 0.1`
- strict `max_position_fraction == 0.1`
- strict `max_open_positions == 8`
- `fixed_stake_bnb=None`
- `skip_all_in_replay=True`
- validation selection first, sealed final confirmation second
- no writes to model artifacts
- no `.env` or live bot changes

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_delayed_profit_lock_replay_cli
```

Expected: OK.

### Task 2: Run The Bounded Replay

**Files:**
- Create: `data/replay_reports/delayed_profit_lock_replay_20260521_v95.json`

- [ ] **Step 1: Run delayed replay**

Run:

```bash
venv/bin/python scripts/run_delayed_profit_lock_replay.py --force
```

Expected: report JSON is written. The decision may be `accept` or `reject`; do not infer live readiness without the report gates.

- [ ] **Step 2: Inspect report gates**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("data/replay_reports/delayed_profit_lock_replay_20260521_v95.json")
r = json.loads(p.read_text())
print("decision", r.get("decision"))
print("selected", r.get("selected_candidate"))
print("live_switch_evidence", r.get("live_switch_evidence"))
print("best_validation_candidate", r.get("best_validation_candidate"))
print("final_confirmation", r.get("final_confirmation"))
PY
```

Expected: strict gate evidence is visible. If `decision != "accept"` or `live_switch_evidence` is false, do not switch live.

### Task 3: Record Research And Scoreboard Evidence

**Files:**
- Create/modify: `docs/research/20260521-delayed-profit-lock-event-exit/summary.md`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Write research summary**

Create `docs/research/20260521-delayed-profit-lock-event-exit/summary.md` with:
- live trigger: CMC primary v95 trade hit delayed profit then STOP_LOSS
- history check: short-window fast profit-lock and blanket exits were already rejected
- fetched sources and SmartSearch commands
- hypothesis: delayed event-driven TP may harvest primary slow profit without expanding entries
- falsification rule: reject if validation/final/stress do not beat v95 or if improvement is outlier-only

- [ ] **Step 2: Update scoreboard**

Add one row near the top of `docs/model_scoreboard.md` under Rejected Candidates or Accepted Baseline depending on report decision. The row must include:
- report path
- model path
- exact candidate if selected
- validation/final summary
- `10%` sizing and `max_open_positions=8`
- decision and next action

Do not edit `docs/goals/live-model-optimization-goal.md`.

### Task 4: Verify And Review

**Files:**
- All files touched in Tasks 1-3

- [ ] **Step 1: Run focused tests**

```bash
venv/bin/python -m unittest tests.model.test_delayed_profit_lock_replay_cli tests.model.test_fast_profit_lock_replay_cli tests.model.test_fast_profit_lock_replay tests.model.test_model_replay
```

- [ ] **Step 2: Compile CLI scripts**

```bash
venv/bin/python -m py_compile scripts/run_delayed_profit_lock_replay.py scripts/run_fast_profit_lock_replay.py
```

- [ ] **Step 3: Review pass 1**

```bash
git diff -- docs/goals/live-model-optimization-goal.md .env .env.example config src/trader
git diff -- scripts/run_delayed_profit_lock_replay.py tests/model/test_delayed_profit_lock_replay_cli.py docs/model_scoreboard.md docs/research/20260521-delayed-profit-lock-event-exit/summary.md
```

Expected: no goal/env/live runtime diffs; code/doc diffs match the plan.

- [ ] **Step 4: Review pass 2**

Run a second independent review focusing on:
- no risk expansion
- no live switch unless accepted
- no protected model artifact writes
- delayed windows are all `>120s`
- report decision matches scoreboard language

- [ ] **Step 5: Commit and push**

Only after verification and two review passes:

```bash
git add scripts/run_delayed_profit_lock_replay.py tests/model/test_delayed_profit_lock_replay_cli.py docs/superpowers/plans/2026-05-21-delayed-profit-lock-replay.md docs/research/20260521-delayed-profit-lock-event-exit docs/model_scoreboard.md data/replay_reports/delayed_profit_lock_replay_20260521_v95.json
git commit -m "test: evaluate delayed profit lock replay"
git push
```
