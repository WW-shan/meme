# Post-Target Exit-State Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only probe that scores accepted v95 replay trades after they first hit a profit target, so the next live-profit iteration can distinguish "lock profit now" cases from durable runners without increasing 10% position risk or adding new entries.

**Architecture:** Reuse existing replay and lifecycle helpers to reconstruct the price and flow path for trades the current v95 strategy already enters. The probe is diagnostic only: it classifies post-target states and writes a report, but it must not edit `.env`, `config/`, `src/trader/`, model artifacts, or `docs/goals/live-model-optimization-goal.md`.

**Tech Stack:** Python stdlib, `unittest`, `src.pipeline.reentry_probe`, `src.pipeline.flow_activation_probe`, `src.pipeline.model_replay.run_model_replay`.

---

### Task 1: Add Post-Target Exit-State Scoring

**Files:**
- Create: `src/pipeline/post_target_exit_state_probe.py`
- Test: `tests/model/test_post_target_exit_state_probe.py`

- [ ] **Step 1: Write failing unit tests**

Create `tests/model/test_post_target_exit_state_probe.py` with tests for:

```python
def test_scores_hit_then_collapse_as_lock_profit():
    anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
    path = [
        reentry_probe.PricePoint(anchor, 1.00, "buy"),
        reentry_probe.PricePoint(anchor + dt.timedelta(seconds=225), 1.26, "buy"),
        reentry_probe.PricePoint(anchor + dt.timedelta(seconds=240), 1.18, "sell"),
        reentry_probe.PricePoint(anchor + dt.timedelta(seconds=260), 0.82, "sell"),
    ]
    result = p.score_trade_post_target_exit_state(
        {"token": "0xA", "symbol": "CMC", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
        {"token_address": "0xA", "price_history": []},
        path=path,
        target_pct=0.25,
        continuation_pct=0.60,
        collapse_pct=-0.18,
    )
    self.assertEqual(result["classification"], "post_target_collapse")
    self.assertEqual(result["recommended_policy"], "lock_profit")
    self.assertTrue(result["target_hit"])
```

Also test:
- A path that hits `+25%` and later `+60%` before collapse is `post_target_continuation` / `continue_hold`.
- A path that never hits the target is `target_not_hit` / `no_action`.
- The report contract has `read_only=True`, `live_switch_evidence=False`, and `requires_replay_before_live_change=True`.

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe
```

Expected: failure because `src.pipeline.post_target_exit_state_probe` does not exist.

- [ ] **Step 3: Implement minimal scoring**

Implement:

```python
def score_trade_post_target_exit_state(
    trade: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    *,
    path: Sequence[reentry_probe.PricePoint] | None = None,
    target_pct: float = 0.25,
    continuation_pct: float = 0.60,
    collapse_pct: float = -0.18,
    horizon_seconds: float = 900.0,
    post_target_windows: Sequence[float] = (15.0, 30.0, 60.0, 120.0),
) -> dict[str, Any]:
    ...
```

Behavior:
- Anchor from `trade["entry_time"]` and `trade["entry_price"]`.
- Use passed `path` for tests; otherwise use `reentry_probe.price_path_from_lifecycle(lifecycle)`.
- Find first time return from entry reaches `target_pct`.
- After target hit, find first continuation hit at `continuation_pct` and first collapse hit at `collapse_pct`.
- Classify:
  - no path or invalid entry: `missing_path`, `recommended_policy="no_action"`
  - no target hit: `target_not_hit`, `recommended_policy="no_action"`
  - collapse before continuation: `post_target_collapse`, `recommended_policy="lock_profit"`
  - continuation before collapse or no collapse: `post_target_continuation`, `recommended_policy="continue_hold"`
- Include `post_target_window_returns_pct` for each configured window using the latest price at or before `target_hit_time + window`.
- Include flow metrics using events before target hit when lifecycle `buys`/`sells` are available.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe
```

Expected: OK.

### Task 2: Add Read-Only CLI

**Files:**
- Create: `scripts/probe_post_target_exit_state.py`
- Test: `tests/model/test_post_target_exit_state_probe_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/model/test_post_target_exit_state_probe_cli.py` that loads the script by path and verifies:
- Defaults:
  - `--model-dir data/models/20260519_v95_v84_selective_nearmiss_gate`
  - `--lifecycle-dir data/training`
  - `--output data/replay_reports/post_target_exit_state_probe_20260521_v95.json`
  - `--target-pct 0.25`
  - `--continuation-pct 0.60`
  - `--collapse-pct -0.18`
  - `--position-fraction 0.10`
  - `--max-open-positions 8`
- Parser rejects any `--position-fraction` other than `0.10` and any `--max-open-positions` other than `8`.
- The CLI writes `probe_contract` and input fingerprints.

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe_cli
```

Expected: failure because `scripts/probe_post_target_exit_state.py` does not exist.

- [ ] **Step 3: Implement CLI**

Implement a CLI that:
- Imports `src.pipeline.post_target_exit_state_probe`.
- Runs `run_model_replay(... include_trade_log=True, write_report=False)` for the requested split.
- Loads lifecycles from `--lifecycle-dir` and optional lifecycle files.
- Builds a read-only report with:
  - `inputs`
  - `input_fingerprints`
  - `input_fingerprint_policy`
  - `probe_contract`
  - `parameters`
  - `candidate_counts`
  - `class_counts`
  - `policy_counts`
  - `candidate_sample`
- Writes only to `data/replay_reports/...` unless explicitly provided.
- Refuses protected model artifact output paths.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe_cli
```

Expected: OK.

### Task 3: Run The Probe And Record Evidence

**Files:**
- Create: `data/replay_reports/post_target_exit_state_probe_20260521_v95.json`
- Create: `docs/research/20260521-post-target-exit-state/summary.md`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run validation probe**

```bash
venv/bin/python scripts/probe_post_target_exit_state.py --split validation --force
```

Expected: report JSON is written; this is not live-switch evidence.

- [ ] **Step 2: Run final probe if validation has useful post-target cases**

```bash
venv/bin/python scripts/probe_post_target_exit_state.py --split final --force
```

Expected: report JSON is written; if the CLI overwrites by default, pass a split-specific `--output`.

- [ ] **Step 3: Write research summary**

Create `docs/research/20260521-post-target-exit-state/summary.md` with:
- Live evidence: CMC hit `+25%/+35%` then STOP_LOSS; no new trades after CMC at the start of this node.
- History check: delayed profit-lock rejected because blanket windows over-cut durable runners.
- SmartSearch evidence: trailing take-profit protects gains after activation; hybrid target+trail lets runners continue; momentum/volume confirmation should decide whether to cut.
- Hypothesis: a conditional post-target state can identify CMC-like collapses without cutting all winners.
- Experiment result: class counts, policy counts, and whether enough separable cases exist to justify a replay-integrated exit model.
- Decision: no live switch from this probe alone.

- [ ] **Step 4: Update scoreboard**

Add a concise rejected/supporting-evidence row or note to `docs/model_scoreboard.md`:
- Path to report.
- Class and policy counts.
- Whether the direction is promoted to a replay-integrated conditional exit model.
- Explicitly state `live_switch_evidence=false`.

Do not edit `docs/goals/live-model-optimization-goal.md`.

### Task 4: Review, Verify, Commit, Push

**Files:**
- All files touched in this plan.

- [ ] **Step 1: Focused verification**

```bash
venv/bin/python -m unittest tests.model.test_post_target_exit_state_probe tests.model.test_post_target_exit_state_probe_cli tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli
venv/bin/python -m py_compile src/pipeline/post_target_exit_state_probe.py scripts/probe_post_target_exit_state.py
```

- [ ] **Step 2: Review pass 1**

```bash
git diff -- docs/goals/live-model-optimization-goal.md .env .env.example config src/trader
git diff -- src/pipeline/post_target_exit_state_probe.py scripts/probe_post_target_exit_state.py tests/model/test_post_target_exit_state_probe.py tests/model/test_post_target_exit_state_probe_cli.py docs/model_scoreboard.md docs/research/20260521-post-target-exit-state
```

Expected: no goal/env/live runtime diffs; only read-only probe, tests, docs, and report artifacts.

- [ ] **Step 3: Review pass 2**

Run an independent strict review focused on:
- no risk expansion beyond 10% sizing and max 8 positions
- no live bot/config/model artifact mutation
- no live switch evidence claimed from a diagnostic probe
- no future leakage inside hit-time features
- report decision and scoreboard language match

- [ ] **Step 4: Commit and push**

```bash
git add src/pipeline/post_target_exit_state_probe.py scripts/probe_post_target_exit_state.py tests/model/test_post_target_exit_state_probe.py tests/model/test_post_target_exit_state_probe_cli.py docs/superpowers/plans/2026-05-21-post-target-exit-state-probe.md docs/research/20260521-post-target-exit-state docs/model_scoreboard.md
git add -f data/replay_reports/post_target_exit_state_probe_20260521_v95*.json
git commit -m "test: probe post-target exit states"
git push
```
