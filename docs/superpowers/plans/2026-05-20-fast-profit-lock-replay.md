# Fast Profit-Lock Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether a default-off fast profit-lock exit for existing v95 primary positions improves strict live-sized replay without adding entries, increasing position size, or touching the live bot.

**Architecture:** Add replay-only `profit_lock_*` exit knobs to the evaluation engine, then build a bounded replay runner that sweeps profit-lock threshold/window candidates against the current v95 baseline. Live `.env`, `src/trader/bot.py`, and `config/` stay unchanged unless a later accepted candidate passes the live-switch gate.

**Tech Stack:** Python 3.12, `unittest`, existing `src.pipeline.train_hybrid._run_eval_replay`, `src.pipeline.model_replay.run_model_replay`, JSON replay reports under `data/replay_reports/`.

---

## Live Evidence

- Current best/live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Current live risk: 10% sizing only.
- Current state at plan creation: bot running, collector running, `data/bot_state.json` has zero open positions.
- Live failure shape: a v95 `FENGSHUI` trade reached strong post-entry MFE quickly, hit both `+25%` and `+60%`, then fell through the stop zone before the current trailing/PPO stack captured profit.
- Probe evidence: `data/replay_reports/time_to_barrier_probe_20260520_140854_profit_lock_trigger.json` found `14/49` per-token candidates with `quick_take_profit` policy, including `10` fast-profit-then-collapse paths.

## Research Reuse

Use `docs/research/20260520-conditional-profit-lock-exit/summary.md`.

The research supports MFE/MAE-based exit analysis, triple-barrier first-touch labels, conditional profit locking, and meta-labeling. This plan deliberately starts with the smallest falsifiable no-new-entry replay before training or deploying a larger conditional-exit model.

## Hypothesis

Because live v95 can already buy tokens that hit fast favorable barriers but collapse before the existing exit stack realizes profit, a fast profit-lock exit for existing positions may improve realized profit without increasing entry risk.

## Falsification Rule

Reject this direction if validation or sealed final replay fails to beat the current v95 baseline on strict live-sized metrics: net profit, win rate, max drawdown, walk-forward worst return/drawdown, stress replay, and trade-count discipline. Also reject if `profit_lock_take_profit_count == 0`, if gains depend on one outlier, or if the exit cuts durable runners enough to weaken stress/walk-forward.

## File Responsibilities

- Modify `src/pipeline/train_hybrid.py`: add replay-only `profit_lock_take_profit_pct`, `profit_lock_max_hold_seconds`, exit reason `PROFIT_LOCK_TAKE_PROFIT`, counters, config echo, runtime/stress propagation, and top-level metrics.
- Modify `src/pipeline/model_replay.py`: default the new profit-lock overrides to `None` and allow explicit replay overrides; keep them out of live selected-runtime defaults until a later live-alignment node.
- Create `tests/model/test_fast_profit_lock_replay.py`: unit tests for `_run_eval_replay` profit-lock behavior.
- Create `scripts/run_fast_profit_lock_replay.py`: strict 10% replay grid against v95 with validation selection and final confirmation.
- Create `tests/model/test_fast_profit_lock_replay_cli.py`: CLI/report/risk-gate contract tests.
- Update `docs/model_scoreboard.md`: only after running the real report, record accept/reject and why.
- Do not modify `docs/goals/live-model-optimization-goal.md`.
- Do not modify live `.env`, `.env.example`, `src/trader/bot.py`, or `config/` in this replay-only plan.

## Subagent Ownership

- Worker A owns `tests/model/test_fast_profit_lock_replay.py` and the minimal `src/pipeline/train_hybrid.py` replay changes.
- Worker B owns `scripts/run_fast_profit_lock_replay.py`, `tests/model/test_fast_profit_lock_replay_cli.py`, and `src/pipeline/model_replay.py` propagation tests.
- Parent owns integration, real replay run, scoreboard update, two strict code-review passes, commit, and push.

## Task 1: Replay Profit-Lock Hook

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Create: `tests/model/test_fast_profit_lock_replay.py`

- [ ] **Step 1: Write failing default-off test**

Create `tests/model/test_fast_profit_lock_replay.py` with a tiny `_run_eval_replay` fixture. The default-off case should open a position, reach `+35%` inside `30s`, then fall to `-18%`. Without `profit_lock_*` params, expected exit reason is the existing baseline reason, not `PROFIT_LOCK_TAKE_PROFIT`, and `profit_lock_take_profit_count == 0`.

- [ ] **Step 2: Write failing fast-profit exit test**

In the same file, enable:

```python
profit_lock_take_profit_pct=0.25
profit_lock_max_hold_seconds=60
stop_loss=-0.18
position_fraction=0.1
include_trade_log=True
```

Use a path with prices `1.00 -> 1.26 -> 0.82`. Expected:

```python
self.assertEqual(result["trade_log"][0]["exit_reason"], "PROFIT_LOCK_TAKE_PROFIT")
self.assertEqual(result["profit_lock_take_profit_count"], 1)
self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)
```

- [ ] **Step 3: Write failing window and validation tests**

Add tests proving:

- no profit-lock exit fires when `+25%` happens after `profit_lock_max_hold_seconds`;
- invalid negative, `nan`, or infinite profit-lock values raise `ValueError`;
- specifying only one of `profit_lock_take_profit_pct` and `profit_lock_max_hold_seconds` raises `ValueError`.

- [ ] **Step 4: Run red tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_fast_profit_lock_replay
```

Expected: fail because `_run_eval_replay` does not accept `profit_lock_*`.

- [ ] **Step 5: Implement minimal replay hook**

In `_run_eval_replay`, add parameters:

```python
profit_lock_take_profit_pct=None
profit_lock_max_hold_seconds=None
```

Normalize them with `_optional_nonnegative_finite`. Enable the rule only when both are present. Raise `ValueError` if exactly one is set.

Before normal PPO/trailing exits, if:

```python
sample_time - position["entry_time"] <= profit_lock_max_hold_seconds
and pnl_pct >= profit_lock_take_profit_pct
```

set `exit_reason = "PROFIT_LOCK_TAKE_PROFIT"` for a full exit. Count `profit_lock_take_profit_count` only after `_execute_exit(...)` returns true, including delayed-exit paths.

- [ ] **Step 6: Echo metrics**

Return:

```python
"profit_lock_take_profit_pct": profit_lock_take_profit,
"profit_lock_max_hold_seconds": profit_lock_max_hold,
"profit_lock_take_profit_count": int(profit_lock_take_profit_count),
```

and include the exit reason in trade logs naturally via existing `_record_exit`.

- [ ] **Step 7: Run focused tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_fast_profit_lock_replay
```

Expected: OK.

## Task 2: Replay Propagation

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Modify: `tests/model/test_model_replay.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

- [ ] **Step 1: Add failing propagation tests**

Add tests proving explicit `profit_lock_*` overrides reach `run_ab_evaluation` / `_run_eval_replay` through `run_model_replay`, while default manifest-derived live config keeps both as `None`.

- [ ] **Step 2: Add config extraction**

In `run_ab_evaluation`, extract:

```python
profit_lock_params = {
    "profit_lock_take_profit_pct": config.get("profit_lock_take_profit_pct"),
    "profit_lock_max_hold_seconds": config.get("profit_lock_max_hold_seconds"),
}
```

Pass `**profit_lock_params` to runtime replay and stress replay calls.

- [ ] **Step 3: Add evaluation fields**

Add the new fields to the top-level evaluation result near the other replay-only overlay metrics:

```python
"profit_lock_take_profit_pct": runtime_replay.get("profit_lock_take_profit_pct"),
"profit_lock_max_hold_seconds": runtime_replay.get("profit_lock_max_hold_seconds"),
"profit_lock_take_profit_count": int(runtime_replay.get("profit_lock_take_profit_count", 0)),
```

- [ ] **Step 4: Add model replay defaults**

In `model_replay.live_replay_config_from_manifest`, set:

```python
"profit_lock_take_profit_pct": None,
"profit_lock_max_hold_seconds": None,
```

Do not add these keys to `LIVE_RUNTIME_PARAM_KEYS` yet.

- [ ] **Step 5: Run propagation tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_train_hybrid_pipeline tests.model.test_fast_profit_lock_replay
```

Expected: OK.

## Task 3: Strict Replay Runner

**Files:**
- Create: `scripts/run_fast_profit_lock_replay.py`
- Create: `tests/model/test_fast_profit_lock_replay_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create tests that verify:

- default model dir is `data/models/20260519_v95_v84_selective_nearmiss_gate`;
- default output is `data/replay_reports/fast_profit_lock_replay_20260520_v95.json`;
- `--position-fraction`, `--max-position-fraction`, and `--max-open-positions` only accept `0.1`, `0.1`, and `8`;
- protected model artifact names inside the model dir cannot be used as output;
- mocked `run_model_replay` receives strict overrides: `position_fraction=0.1`, `max_position_fraction=0.1`, `fixed_stake_bnb=None`, `skip_all_in_replay=True`, `max_open_positions=8`.

- [ ] **Step 2: Write failing selection test**

Mock `run_model_replay` so validation has:

- baseline;
- one higher-profit candidate that worsens drawdown/stress and must be rejected;
- one lower-profit but gate-passing candidate selected for final.

Assert final confirmation only runs baseline plus selected candidate, and `decision="accept"` only when final passes all gates and `profit_lock_take_profit_count > 0`.

- [ ] **Step 3: Implement bounded grid**

Use the `scripts/run_primary_score_scalp_replay.py` pattern, but the grid contains only:

```python
profit_targets = [0.25, 0.35, 0.60]
max_windows = [30.0, 60.0, 90.0, 120.0]
```

Each candidate override contains:

```python
{
    "profit_lock_take_profit_pct": target,
    "profit_lock_max_hold_seconds": window,
}
```

Acceptance gate:

- current v95 strict live-sized baseline;
- profit strictly above baseline;
- win rate not lower;
- max drawdown not worse;
- walk-forward worst return/drawdown not worse;
- stress worst return/profit/drawdown not worse;
- `profit_lock_take_profit_count > 0`;
- total trades not materially changed, because this plan must not add entries.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_fast_profit_lock_replay_cli
```

Expected: OK.

## Task 4: Real Replay And Decision

**Files:**
- Write report: `data/replay_reports/fast_profit_lock_replay_20260520_v95.json`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run focused test suite**

Run:

```bash
venv/bin/python -m unittest \
  tests.model.test_fast_profit_lock_replay \
  tests.model.test_fast_profit_lock_replay_cli \
  tests.model.test_model_replay \
  tests.model.test_train_hybrid_pipeline
```

- [ ] **Step 2: Run real replay**

Run:

```bash
venv/bin/python scripts/run_fast_profit_lock_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output data/replay_reports/fast_profit_lock_replay_20260520_v95.json \
  --position-fraction 0.1 \
  --max-position-fraction 0.1 \
  --max-open-positions 8
```

- [ ] **Step 3: Record accept/reject**

Update `docs/model_scoreboard.md` with:

- candidate grid and selected candidate;
- baseline vs candidate validation/final metrics;
- walk-forward and stress results;
- `profit_lock_take_profit_count`;
- accept/reject decision.

If accepted, this still does not switch live in this plan. A separate live-alignment node must add bot/config support, verify zero positions, commit/push, restart via `./tools/memectl bot restart`, and confirm logs.

## Task 5: Review, Commit, Push

**Files:**
- All files changed in this plan.

- [ ] **Step 1: First strict review**

Parent reviews the full diff for:

- replay/live boundary;
- 10% sizing;
- no hidden live bot changes;
- correct counters under delayed exit;
- no protected artifact overwrite risk;
- no repeat of rejected quick-profit overlay entry expansion.

- [ ] **Step 2: Second strict review**

Dispatch an independent reviewer subagent focused on bugs, replay/live mismatch, data leakage, missing tests, missing artifacts, and pull-and-run readiness.

- [ ] **Step 3: Rerun tests after review fixes**

If any review causes code edits, rerun the focused tests and repeat both review passes.

- [ ] **Step 4: Commit and push important node**

When report and scoreboard are complete:

```bash
git status --short
git add docs/research/20260520-conditional-profit-lock-exit/summary.md \
  docs/superpowers/plans/2026-05-20-fast-profit-lock-replay.md \
  src/pipeline/train_hybrid.py src/pipeline/model_replay.py \
  scripts/run_fast_profit_lock_replay.py \
  tests/model/test_fast_profit_lock_replay.py \
  tests/model/test_fast_profit_lock_replay_cli.py \
  tests/model/test_model_replay.py tests/model/test_train_hybrid_pipeline.py \
  docs/model_scoreboard.md \
  data/replay_reports/fast_profit_lock_replay_20260520_v95.json
git commit -m "test fast profit-lock replay against v95"
git push
```

If the report rejects the direction, keep the commit because the falsification result prevents future repeated work.
