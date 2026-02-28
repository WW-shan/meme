# Backtest Staged Search Acceleration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce backtest auto-tuning time by replacing full 6D Cartesian search with a staged search that preserves parameter coverage and existing scoring semantics.

**Architecture:** Keep `MemeModelTrainer._select_backtest_thresholds` as the single backtest-threshold selection entry point, but add a strategy switch (`full` vs `staged`). In `staged`, first rank entry parameter triples with fixed exit defaults (Stage A), then run exit-grid expansion only on Stage A Top-N entries (Stage B). Reuse existing `_selection_score`, priority logic, and best-candidate tie-break order to avoid strategy drift.

**Tech Stack:** Python 3.12, pandas/numpy/joblib, unittest (`python3 -m unittest`), existing `src/model/trainer.py` pipeline.

---

Execution discipline for every task: follow @superpowers:test-driven-development (write failing test → verify fail → minimal code → verify pass → commit).

### Task 1: Lock behavior with failing tests for staged search cardinality

**Files:**
- Modify: `tests/model/test_trainer_backtest_gate.py`

**Step 1: Write the failing test**

Add a test that proves staged search evaluates fewer unique combinations than full Cartesian search while still returning full selected parameters:

```python
def test_select_backtest_thresholds_staged_limits_combinations(self):
    df = pd.DataFrame([
        {
            "f1": 1.0,
            "token_address": "A",
            "sample_time": 1,
            "time_since_launch": 20,
            "unique_buyers": 6,
            "total_buys": 12,
            "is_moon_200": 0,
            "min_return_pct": -5.0,
            "max_return_pct": 120.0,
            "final_return_pct": 20.0,
        }
    ])

    thresholds = self.trainer._gate_thresholds()
    bt = thresholds["backtest"]
    bt["auto_tune_entry"] = True
    bt["auto_tune_strategy"] = "staged"
    bt["entry_stage_top_n"] = 1
    bt["prob_threshold_candidates"] = [0.70, 0.85]
    bt["reg_min_return_candidates"] = [60.0, 90.0]
    bt["max_age_seconds_candidates"] = [90]
    bt["first_take_profit_candidates"] = [1.0, 2.0]
    bt["first_exit_ratio_candidates"] = [0.5, 0.6]
    bt["drawdown_stop_candidates"] = [0.20]

    with tempfile.TemporaryDirectory() as d:
        model_dir = Path(d)
        (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
        (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
        fake_clf = _FakeClf({1.0: 0.95})
        fake_reg = _FakeReg({1.0: 80.0})

        evaluated = []

        def fake_gate(df, probs, pred_returns, threshold, reg_min_return, backtest_thresholds):
            combo = (
                round(float(threshold), 2),
                float(reg_min_return),
                int(backtest_thresholds["max_age_seconds"]),
                float(backtest_thresholds["first_take_profit"]),
                float(backtest_thresholds["first_exit_ratio"]),
                float(backtest_thresholds["drawdown_stop"]),
            )
            evaluated.append(combo)
            return {
                "return_pct": float(threshold * 100.0 - reg_min_return * 0.1),
                "max_drawdown_pct": 8.0,
                "trades": 12,
            }

        with patch("joblib.load", side_effect=[fake_clf, fake_reg]), patch.object(
            self.trainer,
            "_run_backtest_gate_precomputed",
            side_effect=fake_gate,
        ):
            _, selected = self.trainer._select_backtest_thresholds(
                model_dir=model_dir,
                test_df=df,
                feature_cols=["f1"],
                gate_thresholds=thresholds,
            )

    # StageA=4 entry combos, StageB=1*4 exit combos => 8 unique evaluations
    self.assertEqual(len(set(evaluated)), 8)
    self.assertIn("first_take_profit", selected)
    self.assertIn("first_exit_ratio", selected)
    self.assertIn("drawdown_stop", selected)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_limits_combinations -v`

Expected: FAIL (current code runs full 6D search regardless of strategy).

**Step 3: Add a second failing test for full-mode compatibility**

```python
def test_select_backtest_thresholds_full_strategy_keeps_cartesian(self):
    # same candidate setup as staged test, but auto_tune_strategy="full"
    # expected unique combos: 2*2*1*2*2*1 = 16
    ...
    self.assertEqual(len(set(evaluated)), 16)
```

**Step 4: Run both tests together**

Run: `python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_limits_combinations tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_full_strategy_keeps_cartesian -v`

Expected: both FAIL before implementation.

**Step 5: Commit**

```bash
git add tests/model/test_trainer_backtest_gate.py
git commit -m "test: lock staged vs full backtest search behavior"
```

---

### Task 2: Add staged-search config defaults and strategy switch

**Files:**
- Modify: `src/model/trainer.py`
- Test: `tests/model/test_trainer_metadata.py`

**Step 1: Write the failing metadata test**

Add to `test_build_metadata_contains_gate_and_format_priority`:

```python
self.assertEqual(meta["gate_thresholds"]["backtest"]["auto_tune_strategy"], "staged")
self.assertEqual(meta["gate_thresholds"]["backtest"]["entry_stage_top_n"], 10)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_trainer_metadata.TestTrainerMetadata.test_build_metadata_contains_gate_and_format_priority -v`

Expected: FAIL (new keys not present).

**Step 3: Write minimal implementation**

In `MemeModelTrainer.DEFAULT_GATE_THRESHOLDS["backtest"]` add:

```python
"auto_tune_strategy": "staged",
"entry_stage_top_n": 10,
```

In `_select_backtest_thresholds`, read strategy with safe fallback:

```python
strategy = str(backtest_thresholds.get("auto_tune_strategy", "full")).strip().lower()
if strategy not in {"full", "staged"}:
    strategy = "full"
```

Keep current full-grid path under `strategy == "full"` unchanged.

**Step 4: Run metadata test to verify it passes**

Run: `python3 -m unittest tests.model.test_trainer_metadata.TestTrainerMetadata.test_build_metadata_contains_gate_and_format_priority -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/trainer.py tests/model/test_trainer_metadata.py
git commit -m "feat: add staged backtest strategy config defaults"
```

---

### Task 3: Implement Stage A + Stage B candidate evaluation flow

**Files:**
- Modify: `src/model/trainer.py`
- Test: `tests/model/test_trainer_backtest_gate.py`

**Step 1: Confirm failing staged/full tests are still red**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_limits_combinations tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_full_strategy_keeps_cartesian -v`

Expected: FAIL on staged cardinality assertion.

**Step 2: Implement minimal staged engine inside `_select_backtest_thresholds`**

Refactor candidate evaluation into one local helper to avoid duplication:

```python
def _evaluate_candidate(prob, reg_min, age, first_tp, first_ratio, drawdown):
    tuned_thresholds = copy.deepcopy(gate_thresholds)
    tuned_thresholds["backtest"]["max_age_seconds"] = int(age)
    tuned_thresholds["backtest"]["first_take_profit"] = float(first_tp)
    tuned_thresholds["backtest"]["first_exit_ratio"] = float(first_ratio)
    tuned_thresholds["backtest"]["drawdown_stop"] = float(drawdown)

    selection_result = self._run_backtest_gate_precomputed(...)
    validation_result = self._run_backtest_gate_precomputed(...)
    full_result = self._run_backtest_gate_precomputed(...)

    selection_score = self._selection_score(selection_result, backtest_thresholds)
    validation_score = self._selection_score(validation_result, backtest_thresholds)
    full_score = self._selection_score(full_result, backtest_thresholds)

    validation_viable = _is_viable(validation_result)
    full_viable = _is_viable(full_result)
    priority = 2 if validation_viable else (1 if full_viable else 0)

    if priority == 2:
        score = 0.6 * validation_score + 0.3 * full_score + 0.1 * selection_score
    elif priority == 1:
        score = 0.7 * full_score + 0.2 * validation_score + 0.1 * selection_score
    else:
        score = 0.8 * full_score + 0.2 * validation_score

    return {
        "prob_threshold": float(prob),
        "reg_min_return": float(reg_min),
        "max_age_seconds": int(age),
        "first_take_profit": float(first_tp),
        "first_exit_ratio": float(first_ratio),
        "drawdown_stop": float(drawdown),
        "selection_result": selection_result,
        "validation_result": validation_result,
        "full_result": full_result,
        "priority": int(priority),
        "score": float(score),
    }
```

Implement strategy branches:

```python
if strategy == "full":
    # existing 6D loops (same behavior)
else:
    # Stage A: entry loops only, fixed exit defaults
    stage_a_candidates = []
    for prob in prob_candidates:
        for reg_min in reg_candidates:
            for age in age_candidates:
                stage_a_candidates.append(
                    _evaluate_candidate(
                        prob, reg_min, age,
                        backtest_thresholds["first_take_profit"],
                        backtest_thresholds["first_exit_ratio"],
                        backtest_thresholds["drawdown_stop"],
                    )
                )

    stage_a_sorted = sorted(
        stage_a_candidates,
        key=lambda c: (
            int(c["priority"]),
            float(c["score"]),
            float(c["full_result"].get("return_pct", -1e9)),
            -float(c["full_result"].get("max_drawdown_pct", 999.0)),
            float(c["validation_result"].get("return_pct", -1e9)),
            -float(c["validation_result"].get("max_drawdown_pct", 999.0)),
        ),
        reverse=True,
    )

    requested_top_n = int(backtest_thresholds.get("entry_stage_top_n", 10))
    top_n = min(max(1, requested_top_n), len(stage_a_sorted))
    stage_a_top = stage_a_sorted[:top_n]

    candidates = []
    for entry in stage_a_top:
        for first_tp in first_take_profit_candidates:
            for first_ratio in first_exit_ratio_candidates:
                for drawdown in drawdown_stop_candidates:
                    candidates.append(
                        _evaluate_candidate(
                            entry["prob_threshold"],
                            entry["reg_min_return"],
                            entry["max_age_seconds"],
                            first_tp,
                            first_ratio,
                            drawdown,
                        )
                    )

    if not candidates:
        candidates = [stage_a_sorted[0]]
```

Keep `best = max(candidates, key=...)` and `selected = {...}` format unchanged.

**Step 3: Re-run staged/full tests**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_limits_combinations tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_full_strategy_keeps_cartesian -v`

Expected: PASS.

**Step 4: Add clamp test for oversized `entry_stage_top_n`**

```python
def test_select_backtest_thresholds_staged_clamps_top_n(self):
    # entry combos = 4, exit combos = 4, top_n requested = 999
    # expected unique combos = 4 + (4*4) = 20
    ...
    self.assertEqual(len(set(evaluated)), 20)
```

Run this test:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_clamps_top_n -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/trainer.py tests/model/test_trainer_backtest_gate.py
git commit -m "feat: implement staged backtest auto-tuning with entry top-n"
```

---

### Task 4: Persist staged search metadata to trial outputs

**Files:**
- Modify: `src/model/trainer.py`
- Modify: `tests/model/test_trainer_backtest_gate.py`

**Step 1: Write failing test for search metadata in selected output**

```python
def test_select_backtest_thresholds_staged_returns_search_meta(self):
    ...
    _, selected = self.trainer._select_backtest_thresholds(...)

    self.assertIn("search_meta", selected)
    self.assertEqual(selected["search_meta"]["strategy"], "staged")
    self.assertIn("stageA_total", selected["search_meta"])
    self.assertIn("stageB_total", selected["search_meta"])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_returns_search_meta -v`

Expected: FAIL.

**Step 3: Write minimal implementation**

In `_select_backtest_thresholds`, append search metadata to selected result:

```python
selected["search_meta"] = {
    "strategy": strategy,
    "stageA_total": int(stage_a_total),
    "stageA_top_n": int(stage_a_top_n),
    "stageB_total": int(stage_b_total),
    "evaluated_candidates_total": int(evaluated_total),
    "estimated_reduction_ratio": float(reduction_ratio),
}
```

In `train(...)` trial assembly (`model_meta["trial_summary"]` and `trial_results` row), persist:

```python
"backtest_search_meta": selected_backtest_thresholds.get("search_meta", {})
```

In final `selection_summary.json` row assembly, include same field:

```python
"backtest_search_meta": r.get("backtest_search_meta", {}),
```

**Step 4: Re-run targeted tests**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_returns_search_meta tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_staged_limits_combinations -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/trainer.py tests/model/test_trainer_backtest_gate.py
git commit -m "feat: persist staged backtest search metadata"
```

---

### Task 5: Final regression and verification

**Files:**
- Verify: `src/model/trainer.py`
- Verify: `tests/model/test_trainer_backtest_gate.py`
- Verify: `tests/model/test_trainer_metadata.py`

**Step 1: Run full backtest-threshold test module**

Run: `python3 -m unittest tests.model.test_trainer_backtest_gate -v`

Expected: PASS.

**Step 2: Run metadata module**

Run: `python3 -m unittest tests.model.test_trainer_metadata -v`

Expected: PASS.

**Step 3: Run combined focused regression**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate tests.model.test_trainer_metadata -v`

Expected: PASS.

**Step 4: Optional smoke check with reduced candidate grid**

Run:
`TRAINER_PROFILES=balanced TRAINER_TARGET_THRESHOLDS=100 python3 scripts/run_full_training.py`

Expected:
- training finishes
- auto-tune logs show staged strategy and reduced evaluated count
- generated `selection_summary.json` contains `backtest_search_meta`

**Step 5: Commit**

```bash
git add src/model/trainer.py tests/model/test_trainer_backtest_gate.py tests/model/test_trainer_metadata.py
git commit -m "perf: speed up backtest parameter tuning via staged search"
```

---

Use @superpowers:verification-before-completion before claiming final success.
