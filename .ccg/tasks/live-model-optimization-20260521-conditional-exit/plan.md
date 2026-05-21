# Conditional Exit Flow-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Advance live model optimization without overfitting by turning conditional-exit research into read-only support gates before any replay or live change.

**Architecture:** Keep live runtime unchanged. Use frozen v95 replay reports plus live attribution to decide whether a conditional exit has enough support to become a default-off replay candidate. If support is missing, emit a no-go report instead of changing model or trading config.

**Tech Stack:** Plain Python scripts/modules, JSON diagnostics, `python -m unittest discover`, existing v95 replay reports, CCG task artifacts.

---

### Task 1: Freeze Current Evidence

**Files:**
- Create: `docs/research/20260521-conditional-exit-flow-state/live_attribution.json`
- Create: `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json`
- Create: `docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md`
- Create: `docs/research/20260521-conditional-exit-flow-state/summary.md`

- [x] **Step 1: Attribute live failures**

Input: real closed trades since `2026-05-19 04:02:23` and lifecycle paths from current collector/training files.

Expected output:

```json
{
  "trade_count": 18,
  "win_count": 2,
  "loss_count": 16,
  "net_profit_bnb": -0.001256566335,
  "failure_label_counts": {
    "dead_flow_timeout": 7,
    "entry_slippage_failure": 2,
    "mfe_then_giveback": 3,
    "profitable_exit": 2,
    "stop_first_after_entry": 1,
    "unprofitable_other": 3
  }
}
```

- [x] **Step 2: Compare support across train, validation, final, and live**

Use:

```text
data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json
data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json
data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json
docs/research/20260521-conditional-exit-flow-state/live_attribution.json
```

Expected decision:

```json
{
  "status": "NO_GO_FOR_LIVE_RULE",
  "reason": "No candidate bucket has >=3 positives in validation, final, and live with a replay-equivalent label. The best-supported post-target direction has train=5, validation=0, final=4, live=3."
}
```

- [x] **Step 3: Summarize fetched research**

Write `summary.md` with:

- triple-barrier/path-dependent label relevance,
- MFE/MAE exit diagnostic relevance,
- pump-and-dump microstructure relevance,
- Zhipu/Exa provider gaps,
- no live-switch decision.

- [ ] **Step 4: Verify JSON and docs**

Run:

```bash
python -m json.tool docs/research/20260521-conditional-exit-flow-state/live_attribution.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json >/dev/null
test -s docs/research/20260521-conditional-exit-flow-state/summary.md
test -s docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md
```

Expected: all commands exit `0`.

### Task 2: Decide Whether To Build A Replay Candidate

**Files:**
- Read: `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json`
- Read: `docs/model_scoreboard.md`
- Modify only if support later passes: `src/pipeline/train_hybrid.py`, `src/pipeline/model_replay.py`, focused tests under `tests/model/`

- [ ] **Step 1: Enforce the support gate**

Do not implement a conditional exit replay candidate unless one bucket has:

```text
validation_positives >= 3
final_positives >= 3
live_positives >= 3
```

Current state:

```text
post_target_collapse_or_live_mfe_giveback:
  train=5
  validation=0
  final=4
  live=3
```

Expected current decision: `NO-GO`.

- [ ] **Step 2: If support remains missing, stop at diagnostic status**

Update the task review with:

```text
No live switch. No replay implementation. Continue collecting live labels or design a read-only probe for dead_flow_timeout support.
```

- [ ] **Step 3: If support later passes, write tests first**

Minimum tests:

```bash
python -m unittest tests.model.test_model_replay
python -m unittest tests.model.test_train_hybrid_pipeline
```

The new tests must prove:

- conditional exit defaults to disabled,
- runtime replay records candidate counts,
- selected candidate cannot pass with zero validation positives,
- live sizing remains 10%.

### Task 3: Review And Close This Node

**Files:**
- Modify: `.ccg/tasks/live-model-optimization-20260521-conditional-exit/review.md`
- Modify: `.ccg/tasks/live-model-optimization-20260521-conditional-exit/task.json`

- [ ] **Step 1: Run focused verification**

Run:

```bash
python -m json.tool .ccg/tasks/live-model-optimization-20260521-conditional-exit/task.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/live_attribution.json >/dev/null
python -m json.tool docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json >/dev/null
```

Expected: all commands exit `0`.

- [ ] **Step 2: Confirm protected files are untouched**

Run:

```bash
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Expected: no output.

- [ ] **Step 3: Record review**

Write `review.md` with:

- Gemini analysis status: failed locally because `gemini` command was not available in `PATH`.
- Claude analysis status: recommended bundled read-only research summary plus live/replay attribution before any conditional-exit implementation.
- Decision: no live switch and no model artifact change from this node.

- [ ] **Step 4: Keep task active unless archived by a verified follow-up**

Only archive this task after verification, review, and a commit requested by the workflow. Do not archive while the broader optimization goal is still mid-node.
