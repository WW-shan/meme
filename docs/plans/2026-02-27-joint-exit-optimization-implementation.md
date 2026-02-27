# Joint Exit Take-Profit Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the training-time backtest selection to jointly optimize moon-branch exit settings (80%/100%/150%/200% first take-profit and related partial-exit params), then automatically choose the best-performing combination.

**Architecture:** Keep the existing trainer pipeline and gate evaluation flow, but parameterize moon exit logic and include exit dimensions in auto-tune search. Preserve existing entry filtering/scoring behavior and one-trade-per-token constraints, while persisting selected exit params into metadata and summary outputs for reproducible deployment.

**Tech Stack:** Python 3, pandas/numpy/joblib, existing `MemeModelTrainer`, unittest (`python3 -m unittest`), existing backtest/calibration modules.

---

Execution discipline for every task: follow @superpowers:test-driven-development (write failing test → run fail → minimal code → run pass → commit).

### Task 1: Parameterize moon-exit math in trainer backtest gate

**Files:**
- Modify: `tests/model/test_trainer_backtest_gate.py`
- Modify: `src/model/trainer.py`

**Step 1: Write the failing test**

Add test to prove first take-profit should be configurable and should depend on whether max return reaches TP threshold (instead of hard-coding `is_moon_200 == 1` + fixed `200%`):

```python
def test_backtest_gate_uses_configurable_first_take_profit_hit(self):
    df = pd.DataFrame([
        {
            "f1": 1.0,
            "token_address": "A",
            "sample_time": 1,
            "time_since_launch": 10,
            "unique_buyers": 4,
            "total_buys": 6,
            "is_moon_200": 0,
            "min_return_pct": -10.0,
            "max_return_pct": 120.0,
            "final_return_pct": 20.0,
        }
    ])

    thresholds = self.trainer._gate_thresholds()
    thresholds["backtest"]["first_take_profit"] = 1.0
    thresholds["backtest"]["first_exit_ratio"] = 0.5
    thresholds["backtest"]["drawdown_stop"] = 0.20

    with tempfile.TemporaryDirectory() as d:
        model_dir = Path(d)
        (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
        (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
        fake_clf = _FakeClf({1.0: 0.95})
        fake_reg = _FakeReg({1.0: 80.0})

        with patch("joblib.load", side_effect=[fake_clf, fake_reg]):
            result = self.trainer._run_backtest_gate(
                model_dir=model_dir,
                test_df=df,
                feature_cols=["f1"],
                threshold=0.8,
                gate_thresholds=thresholds,
            )

    expected_actual_return = 0.5 * 1.0 + 0.5 * (1.2 * (1 - 0.20))
    size = 0.1
    effective_entry = size / 1.2
    gross_value = effective_entry * (1 + expected_actual_return)
    net_value = gross_value * 0.95 * 0.98
    expected_return_pct = (net_value - size) * 100

    self.assertAlmostEqual(result["return_pct"], expected_return_pct, places=6)
```

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_backtest_gate_uses_configurable_first_take_profit_hit -v`

Expected: FAIL (current logic still hard-codes 200% moon branch path).

**Step 3: Write minimal implementation**

In `src/model/trainer.py`:

1. Extend `DEFAULT_GATE_THRESHOLDS["backtest"]` with:

```python
"first_take_profit": 2.0,
"first_exit_ratio": 0.6,
"drawdown_stop": 0.25,
"first_take_profit_candidates": [0.8, 1.0, 1.5, 2.0],
"first_exit_ratio_candidates": [0.5, 0.6, 0.7],
"drawdown_stop_candidates": [0.20, 0.25, 0.30],
```

2. In `_run_backtest_gate_precomputed`, replace moon hard-code block with parameterized logic:

```python
first_take_profit = float(backtest_thresholds.get("first_take_profit", 2.0))
first_exit_ratio = float(backtest_thresholds.get("first_exit_ratio", 0.6))
drawdown_stop = float(backtest_thresholds.get("drawdown_stop", 0.25))

max_ret = float(row.get("max_return_pct", 0.0)) / 100.0
final_ret = float(row.get("final_return_pct", row.get("max_return_pct", 0.0))) / 100.0
min_ret = float(row.get("min_return_pct", 0.0))

hit_first_tp = max_ret >= first_take_profit
if hit_first_tp:
    peak_from_entry = max(max_ret, first_take_profit)
    drawdown_exit_return = peak_from_entry * (1 - drawdown_stop)
    second_exit_ratio = 1.0 - first_exit_ratio
    second_exit_return = final_ret if final_ret >= drawdown_exit_return else drawdown_exit_return
    actual_return = first_exit_ratio * first_take_profit + second_exit_ratio * second_exit_return
elif min_ret <= -50.0:
    actual_return = -0.5
else:
    actual_return = final_ret
```

**Step 4: Run test to verify it passes**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_backtest_gate_uses_configurable_first_take_profit_hit -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_trainer_backtest_gate.py src/model/trainer.py
git commit -m "feat: parameterize trainer moon exit take-profit logic"
```

---

### Task 2: Add joint auto-tune search over exit parameter candidates

**Files:**
- Modify: `tests/model/test_trainer_backtest_gate.py`
- Modify: `src/model/trainer.py`

**Step 1: Write the failing test**

Add test ensuring `_select_backtest_thresholds` searches exit candidates and returns selected exit params:

```python
def test_select_backtest_thresholds_auto_tunes_exit_candidates(self):
    df = pd.DataFrame([
        {
            "f1": 1.0,
            "token_address": "A",
            "sample_time": 1,
            "time_since_launch": 20,
            "unique_buyers": 6,
            "total_buys": 12,
            "is_moon_200": 0,
            "min_return_pct": -10.0,
            "max_return_pct": 120.0,
            "final_return_pct": 20.0,
        }
    ])

    thresholds = self.trainer._gate_thresholds()
    bt = thresholds["backtest"]
    bt["auto_tune_entry"] = True
    bt["prob_threshold_candidates"] = [0.8]
    bt["reg_min_return_candidates"] = [60.0]
    bt["max_age_seconds_candidates"] = [120]
    bt["first_take_profit_candidates"] = [1.0, 2.0]
    bt["first_exit_ratio_candidates"] = [0.6]
    bt["drawdown_stop_candidates"] = [0.25]

    with tempfile.TemporaryDirectory() as d:
        model_dir = Path(d)
        (model_dir / "classifier_xgb.pkl").write_bytes(b"clf")
        (model_dir / "regressor_lgb.pkl").write_bytes(b"reg")
        fake_clf = _FakeClf({1.0: 0.95})
        fake_reg = _FakeReg({1.0: 80.0})

        with patch("joblib.load", side_effect=[fake_clf, fake_reg] * 6):
            _, selected = self.trainer._select_backtest_thresholds(
                model_dir=model_dir,
                test_df=df,
                feature_cols=["f1"],
                gate_thresholds=thresholds,
            )

    self.assertEqual(selected["first_take_profit"], 1.0)
    self.assertEqual(selected["first_exit_ratio"], 0.6)
    self.assertEqual(selected["drawdown_stop"], 0.25)
```

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_auto_tunes_exit_candidates -v`

Expected: FAIL (selected dict currently has only entry params).

**Step 3: Write minimal implementation**

In `src/model/trainer.py` inside `_select_backtest_thresholds`:

1. Load candidate lists:

```python
first_tp_candidates = backtest_thresholds.get("first_take_profit_candidates") or [backtest_thresholds["first_take_profit"]]
first_ratio_candidates = backtest_thresholds.get("first_exit_ratio_candidates") or [backtest_thresholds["first_exit_ratio"]]
drawdown_candidates = backtest_thresholds.get("drawdown_stop_candidates") or [backtest_thresholds["drawdown_stop"]]
```

2. Extend grid loops to include exit dimensions and set tuned thresholds before each `_run_backtest_gate_precomputed` call.

3. Include exit params in each candidate row and in final `selected` dict:

```python
selected = {
    "prob_threshold": ...,
    "reg_min_return": ...,
    "max_age_seconds": ...,
    "first_take_profit": ...,
    "first_exit_ratio": ...,
    "drawdown_stop": ...,
}
```

**Step 4: Run test to verify it passes**

Run:
`python3 -m unittest tests.model.test_trainer_backtest_gate.TestTrainerBacktestGate.test_select_backtest_thresholds_auto_tunes_exit_candidates -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_trainer_backtest_gate.py src/model/trainer.py
git commit -m "feat: add joint exit candidate search to backtest auto-tune"
```

---

### Task 3: Persist selected exit parameters into gate thresholds and trial outputs

**Files:**
- Modify: `tests/model/test_trainer_metadata.py`
- Modify: `src/model/trainer.py`

**Step 1: Write the failing test**

In `tests/model/test_trainer_metadata.py`, extend metadata expectations:

```python
self.assertEqual(meta["gate_thresholds"]["backtest"]["first_take_profit"], 2.0)
self.assertEqual(meta["gate_thresholds"]["backtest"]["first_exit_ratio"], 0.6)
self.assertEqual(meta["gate_thresholds"]["backtest"]["drawdown_stop"], 0.25)
self.assertEqual(meta["gate_thresholds"]["backtest"]["first_take_profit_candidates"], [0.8, 1.0, 1.5, 2.0])
```

Add/extend one test around trial summary payload assembly (if needed in existing trainer tests) to ensure selected rows include these keys.

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_trainer_metadata -v`

Expected: FAIL (new backtest fields missing).

**Step 3: Write minimal implementation**

In `src/model/trainer.py`:

1. After `_select_backtest_thresholds(...)`, assign selected exit params back into gate thresholds:

```python
gate_thresholds["backtest"]["first_take_profit"] = float(selected_backtest_thresholds["first_take_profit"])
gate_thresholds["backtest"]["first_exit_ratio"] = float(selected_backtest_thresholds["first_exit_ratio"])
gate_thresholds["backtest"]["drawdown_stop"] = float(selected_backtest_thresholds["drawdown_stop"])
```

2. Include selected exit params in trial result rows and final `selection_summary.json` result rows.

**Step 4: Run test to verify it passes**

Run:
`python3 -m unittest tests.model.test_trainer_metadata -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_trainer_metadata.py src/model/trainer.py
git commit -m "feat: persist selected exit parameters in trainer metadata"
```

---

### Task 4: Keep profit-first calibrator consistent with new exit parameter model

**Files:**
- Modify: `tests/model/test_profit_first_calibrator.py`
- Modify: `src/backtest/profit_first_calibrator.py`

**Step 1: Write the failing test**

Add test that calibrator can evaluate different first take-profit values and report them per candidate:

```python
def test_evaluate_single_config_supports_exit_params(self):
    module = _load_module(...)
    # build tiny df with max_return_pct=120 and final_return_pct=20
    # compare first_take_profit=1.0 vs 2.0
    low_tp = module._evaluate_single_config(..., first_take_profit=1.0, first_exit_ratio=0.6, drawdown_stop=0.25)
    high_tp = module._evaluate_single_config(..., first_take_profit=2.0, first_exit_ratio=0.6, drawdown_stop=0.25)

    self.assertGreater(low_tp["return_pct"], high_tp["return_pct"])
    self.assertEqual(low_tp["first_take_profit"], 1.0)
```

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_profit_first_calibrator.TestProfitFirstCalibrator.test_evaluate_single_config_supports_exit_params -v`

Expected: FAIL (function signature/logic not supporting new exit params).

**Step 3: Write minimal implementation**

In `src/backtest/profit_first_calibrator.py`:

1. Extend `_evaluate_single_config` signature to include:
- `first_take_profit`
- `first_exit_ratio`
- `drawdown_stop`

2. Reuse the same TP-hit based exit logic introduced in trainer.

3. Include exit params in returned candidate dict.

4. Extend `_evaluate_grid` and `run_profit_first_calibration` to accept optional candidate lists for these fields and iterate combinations.

**Step 4: Run test to verify it passes**

Run:
`python3 -m unittest tests.model.test_profit_first_calibrator -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_profit_first_calibrator.py src/backtest/profit_first_calibrator.py
git commit -m "feat: add exit-parameter evaluation to profit-first calibrator"
```

---

### Task 5: Keep simple backtest behavior aligned with trainer logic

**Files:**
- Create: `tests/model/test_simple_backtest_exit_logic.py`
- Modify: `src/backtest/simple_backtest.py`

**Step 1: Write the failing test**

Create a focused unit test using `SimpleBacktester.__new__` to bypass file loading and test `_execute_trade` directly with configurable exit params:

```python
def test_execute_trade_uses_configurable_exit_params_when_tp_hit():
    tester = SimpleBacktester.__new__(SimpleBacktester)
    tester.balance = 1.0
    tester.initial_balance = 1.0
    tester.position_size = 0.1
    tester.stop_loss = -0.5
    tester.take_profit = 999.0
    tester.prob_threshold = 0.8
    tester.first_take_profit = 1.0
    tester.first_exit_ratio = 0.6
    tester.drawdown_stop = 0.25
    tester.trades = []

    sample = {
        "label": {
            "is_moon_200": 0,
            "min_return_pct": -10.0,
            "max_return_pct": 120.0,
            "final_return_pct": 20.0,
        },
        "meta": {"symbol": "AAA", "sample_time": 0},
    }

    tester._execute_trade(sample, 0.95)
    self.assertEqual(len(tester.trades), 1)
    self.assertGreater(tester.trades[0]["actual_return"], 50.0)
```

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_simple_backtest_exit_logic -v`

Expected: FAIL (simple backtest still hard-coded to old moon branch behavior).

**Step 3: Write minimal implementation**

In `src/backtest/simple_backtest.py`:

1. Add optional init params with old defaults:
- `first_take_profit=2.0`
- `first_exit_ratio=0.6`
- `drawdown_stop=0.25`

2. Update `_execute_trade` to use the same TP-hit based logic as trainer/calibrator.

**Step 4: Run test to verify it passes**

Run:
`python3 -m unittest tests.model.test_simple_backtest_exit_logic -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_simple_backtest_exit_logic.py src/backtest/simple_backtest.py
git commit -m "feat: align simple backtest exit logic with trainer"
```

---

### Task 6: End-to-end verification through training entrypoint and artifacts

**Files:**
- Modify (if needed): `scripts/run_full_training.py`
- Verify artifacts under: `data/models/models_*/model_metadata.json`
- Verify artifacts under: `data/models/models_*_trials/selection_summary.json`

**Step 1: Run targeted regression tests**

Run:
```bash
python3 -m unittest tests.model.test_trainer_backtest_gate -v
python3 -m unittest tests.model.test_trainer_metadata -v
python3 -m unittest tests.model.test_profit_first_calibrator -v
python3 -m unittest tests.model.test_simple_backtest_exit_logic -v
```

Expected: PASS.

**Step 2: Run full training entrypoint**

Run:
`python3 scripts/run_full_training.py`

Expected:
- training completes without runtime errors
- logs show auto-selected backtest thresholds including exit params

**Step 3: Validate output metadata fields**

Check latest `model_metadata.json` and confirm:
- `gate_thresholds.backtest.first_take_profit`
- `gate_thresholds.backtest.first_exit_ratio`
- `gate_thresholds.backtest.drawdown_stop`

Check latest `selection_summary.json` and confirm each row includes selected exit params.

**Step 4: Sanity-check optimization outcome**

Acceptance checks:
- selected config includes one of `first_take_profit in [0.8, 1.0, 1.5, 2.0]`
- return/drawdown/trades are present
- no regressions in entry filtering behavior

**Step 5: Commit**

```bash
git add src/model/trainer.py src/backtest/profit_first_calibrator.py src/backtest/simple_backtest.py \
  tests/model/test_trainer_backtest_gate.py tests/model/test_trainer_metadata.py \
  tests/model/test_profit_first_calibrator.py tests/model/test_simple_backtest_exit_logic.py \
  scripts/run_full_training.py

git commit -m "feat: joint-optimize entry and moon exit take-profit in training backtests"
```

---

Use @superpowers:verification-before-completion before claiming final success.
