# Late Pump Exhaustion Veto Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether a replay-only late-pump exhaustion veto can skip TSG-like high-score chase entries without increasing live risk.

**Architecture:** Keep the live bot untouched and add optional replay parameters to the existing `train_hybrid._run_eval_replay` path. The veto only applies when a candidate already passed the existing v95 entry stack and then also matches age, pre-signal price-extension, volume, and volatility exhaustion guards. A thin CLI runs a validation grid, confirms the selected rule on final, and rejects the idea unless it beats current v95 strict baseline under the existing acceptance gate.

**Tech Stack:** Python `unittest`, existing `src.pipeline.train_hybrid`, existing `src.pipeline.model_replay`, and JSON replay reports under `data/replay_reports/`.

---

### Task 1: Replay Veto Contract

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Create: `tests/model/test_late_pump_exhaustion_veto.py`

- [ ] **Step 1: Write failing tests**

Add tests that call `_run_eval_replay` directly. The first test should build one token episode where the candidate has `age=210`, `volume_30s=3.2`, `price_volatility=0.24`, and a 30-second price extension above 100%; with veto params enabled it must produce `total_trades=0` and `late_pump_veto_reject_count=1`. The second test should build a younger/less-extended candidate and prove it still opens normally.

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_veto
```

Expected: fail because `_run_eval_replay` does not yet accept `buy_late_pump_veto_*` parameters.

- [ ] **Step 3: Implement minimal replay support**

Add optional parameters:

- `buy_late_pump_veto_min_age_seconds`
- `buy_late_pump_veto_extension_window_seconds`
- `buy_late_pump_veto_min_price_extension_pct`
- `buy_late_pump_veto_min_entry_volume_30s`
- `buy_late_pump_veto_min_entry_price_volatility`

Compute the per-sample price extension from earlier samples in the same episode, apply the veto only after the normal entry filters have passed, and record `late_pump_veto_signal_count`, `late_pump_veto_reject_count`, and the configured values in replay output.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_veto
```

Expected: OK.

### Task 2: Replay Grid CLI

**Files:**
- Create: `scripts/run_late_pump_exhaustion_replay.py`
- Create: `tests/model/test_late_pump_exhaustion_replay_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Test that the CLI parser enforces 10% sizing, exact `max_open_positions=8`, safe report output, and that the candidate grid contains only replay-only veto params.

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_replay_cli
```

Expected: fail because the CLI does not exist.

- [ ] **Step 3: Implement CLI**

Use `run_model_replay` with `split=validation` for the grid and `split=final` for the selected validation candidate. The output path is `data/replay_reports/late_pump_exhaustion_replay_20260519_v95.json`. The report must include strict assumptions, baseline summaries, candidate summaries, final confirmation, and `decision` set to `accept` only if the final candidate beats v95 on profit, drawdown, win rate, walk-forward, stress, and does not materially shrink or expand trade count.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_replay_cli
```

Expected: OK.

### Task 3: Execute Experiment And Record Decision

**Files:**
- Modify: `docs/model_scoreboard.md`
- Modify: `docs/research/20260519-late-pump-exhaustion-veto/summary.md`
- Output: `data/replay_reports/late_pump_exhaustion_replay_20260519_v95.json`

- [ ] **Step 1: Run targeted tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_late_pump_exhaustion_veto tests.model.test_late_pump_exhaustion_replay_cli tests.model.test_low_volume_rescue_replay tests.model.test_model_replay
```

- [ ] **Step 2: Run replay grid**

Run:

```bash
venv/bin/python scripts/run_late_pump_exhaustion_replay.py --output data/replay_reports/late_pump_exhaustion_replay_20260519_v95.json --force
```

- [ ] **Step 3: Record accept/reject**

Append the report result to `docs/model_scoreboard.md`. If the candidate fails any gate, explicitly reject it and state that no live switch is allowed.

- [ ] **Step 4: Final verification and reviews**

Run targeted tests, `py_compile` for changed Python files, JSON parse for the report, `git diff --check`, and two strict review passes after the final edit. If both reviews pass and the node is meaningful, commit and push.
