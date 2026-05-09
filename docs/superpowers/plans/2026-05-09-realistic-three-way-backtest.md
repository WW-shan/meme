# Realistic Three-Way Backtest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a credible train/validation/final-test model-selection flow and more live-like replay execution failure controls.

**Architecture:** Extend the existing `src/pipeline/train_hybrid.py` flow instead of creating a second pipeline. Replay gets bounded delayed-fill behavior and execution quality metrics; training gets an optional three-way chronological split where validation tunes thresholds and final test remains held out. The CLI stays thin and only passes new config fields.

**Tech Stack:** Python 3.12, `unittest`, CatBoost buy model, Stable-Baselines PPO sell policy, existing `scripts/run_hybrid_training.py` CLI.

---

## File Map

- Modify `src/pipeline/train_hybrid.py`: add replay fill-wait/protection controls, execution metrics, three-way file split, validation risk tuning, validation manifest output.
- Modify `scripts/run_hybrid_training.py`: expose split and execution realism flags; apply live-profile defaults.
- Modify `tests/model/test_train_hybrid_pipeline.py`: TDD coverage for replay controls and three-way data flow.
- Modify `tests/model/test_run_hybrid_training_cli.py`: CLI parsing and config propagation tests.

## Task 1: Replay Entry/Exit Execution Controls

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing replay tests**

Add tests proving:

```python
def test_run_eval_replay_entry_fill_times_out_after_max_wait(self):
    # token A signal at t=0, due at t=3, next sample at t=10.
    # entry_max_fill_wait_seconds=3 means the buy is skipped.
    out = m._run_eval_replay(..., entry_delay_seconds=3, entry_max_fill_wait_seconds=3)
    self.assertEqual(out["total_trades"], 0)
    self.assertEqual(out["entry_timeout_count"], 1)
```

```python
def test_run_eval_replay_entry_price_protection_skips_chase(self):
    # signal price 1.0, delayed fill price 1.4, protection 25%.
    out = m._run_eval_replay(..., entry_price_protection_pct=0.25)
    self.assertEqual(out["entry_price_protection_skip_count"], 1)
```

```python
def test_run_eval_replay_exit_fill_timeout_is_reported(self):
    # exit due at t=3, first later fill at t=10, max wait 3.
    out = m._run_eval_replay(..., exit_delay_seconds=3, exit_max_fill_wait_seconds=3)
    self.assertGreaterEqual(out["exit_timeout_count"], 1)
    self.assertGreaterEqual(out["max_exit_wait_seconds"], 7)
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline
```

Expected: failures for missing keyword args and metrics.

- [ ] **Step 3: Implement replay controls**

Extend `_run_eval_replay` signature:

```python
entry_max_fill_wait_seconds=None,
exit_max_fill_wait_seconds=None,
entry_price_protection_pct=None,
```

Store pending entry signal price and due time. If delayed fill wait exceeds the max, skip and count timeout. If delayed price exceeds the protection limit, skip and count price-protection. Record entry/exit wait arrays and timeout counters.

- [ ] **Step 4: Verify replay tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline
```

- [ ] **Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Add realistic delayed fill replay controls"
```

## Task 2: CLI Controls

**Files:**
- Modify: `tests/model/test_run_hybrid_training_cli.py`
- Modify: `scripts/run_hybrid_training.py`

- [ ] **Step 1: Write failing CLI tests**

Add assertions for:

```python
self.assertEqual(args.validation_split_ratio, 0.0)
self.assertEqual(args.min_validation_files, 1)
self.assertIsNone(args.entry_max_fill_wait_seconds)
self.assertIsNone(args.exit_max_fill_wait_seconds)
self.assertIsNone(args.entry_price_protection_pct)
```

Add extended-config assertions for explicit values and live-profile defaults:

```python
self.assertEqual(cfg["validation_split_ratio"], 0.2)
self.assertEqual(cfg["min_validation_files"], 3)
self.assertEqual(cfg["entry_max_fill_wait_seconds"], 4)
self.assertEqual(cfg["exit_max_fill_wait_seconds"], 7)
self.assertEqual(cfg["entry_price_protection_pct"], 0.2)
```

- [ ] **Step 2: Implement CLI args and live defaults**

Add parser flags and config fields. In live profile, default missing values to `3`, `6`, and `0.25`.

- [ ] **Step 3: Verify CLI tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_run_hybrid_training_cli
```

- [ ] **Step 4: Commit**

```bash
git add scripts/run_hybrid_training.py tests/model/test_run_hybrid_training_cli.py
git commit -m "Expose realistic replay training controls"
```

## Task 3: Three-Way Split

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing three-way training test**

Patch training helpers and `_load_samples` to prove:

```python
result = m.run_hybrid_training({
    "lifecycle_paths": files,
    "train_split_ratio": 0.6,
    "validation_split_ratio": 0.2,
    "min_validation_files": 1,
    "min_eval_files": 1,
})
self.assertEqual(result["three_way_split"]["enabled"], True)
self.assertIn("validation_evaluation", result)
```

Also assert the risk tuning call receives validation samples, while final `evaluation` receives final-test samples.

- [ ] **Step 2: Implement helper and pipeline flow**

Add `_split_lifecycle_files_three_way(files, train_split_ratio, validation_split_ratio, min_validation_files, min_eval_files)`.

When enabled:

- train model on train files
- load validation samples excluding train raw tokens
- set `buy_artifact["calibration_samples"]` to validation samples before `_tune_buy_threshold_by_replay`
- load final test samples excluding train and validation raw tokens
- emit `three_way_split` and `validation_evaluation`

- [ ] **Step 3: Verify pipeline tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline
```

- [ ] **Step 4: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Add three-way validation split for model selection"
```

## Task 4: Full Verification and Training

**Files:**
- No code edits expected.
- Output: `data/models/20260509_realistic_three_way_v29/`

- [ ] **Step 1: Run full verification**

Run:

```bash
venv/bin/python -m unittest discover
git diff --check
```

- [ ] **Step 2: Train v29**

Run:

```bash
venv/bin/python scripts/run_hybrid_training.py \
  --output-dir data/models/20260509_realistic_three_way_v29 \
  --lifecycle-dir data/training \
  --train-split-ratio 0.6 \
  --validation-split-ratio 0.2 \
  --min-validation-files 3 \
  --min-eval-files 3 \
  --sample-mode trade_event \
  --max-sample-age-seconds 300 \
  --future-windows 300 \
  --max-hold-seconds 300 \
  --min-policy-hold-seconds 5 \
  --max-samples-per-token 20 \
  --target-label-column live_risk_adjusted_return_pct \
  --target-threshold-value 10 \
  --label-live-downside-penalty-weight 1.0 \
  --total-timesteps 12000 \
  --stop-loss -0.30 \
  --initial-equity-bnb 1.0 \
  --fixed-stake-bnb 0.1 \
  --position-fraction 0.10 \
  --max-position-fraction 0.10 \
  --include-trade-log \
  --fee-bps 100 \
  --slippage-bps 200 \
  --one-entry-per-token \
  --max-trades-per-token 1 \
  --trailing-start-pct 0.25 \
  --trailing-stop-pct 0.15 \
  --rug-sell-pressure 0.92 \
  --live-replay-profile \
  --risk-tune-max-trades 6000 \
  --risk-tune-max-drawdown-pct -30 \
  --risk-tune-min-win-rate 0.30 \
  --risk-tune-target-entry-rate 0.20 \
  --risk-tune-entry-rate-penalty 0.02 \
  --risk-tune-candidate-entry-rates 0.02,0.05,0.10,0.15,0.20,0.30,0.45,0.60,0.80 \
  --risk-tune-probability-threshold-count 120 \
  --risk-tune-drawdown-penalty 0.0 \
  --catboost-iterations 260 \
  --catboost-depth 5
```

- [ ] **Step 3: Report final status**

Report final-test multiple, net BNB, drawdown, walk-forward, stress replay, and execution quality metrics. Do not call the model credible unless validation and final test are directionally consistent.

## Self-Review

- Spec coverage: replay controls, CLI controls, three-way split, validation/final manifest, and training verification are covered.
- Placeholder scan: no placeholder sections remain.
- Type consistency: config keys use the same names across CLI, replay, tests, and manifest.
