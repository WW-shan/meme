# Live Stress Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add live-like stress replay to the hybrid evaluation so model reports include Base/Mild/Harsh execution assumptions instead of only ideal offline replay.

**Architecture:** Extend the existing chronological `_run_eval_replay` engine instead of adding a second simulator. Entry signals can be scheduled for delayed fills, exit signals can be scheduled for delayed sells, and evaluation can enforce a maximum number of simultaneously open positions. `run_ab_evaluation` will reuse precomputed buy probabilities and emit named stress scenarios in the manifest.

**Tech Stack:** Python `unittest`, existing `src/pipeline/train_hybrid.py`, existing thin CLI `scripts/run_hybrid_training.py`.

---

## File Map

- Modify `src/pipeline/train_hybrid.py`: add replay parameters `entry_delay_seconds`, `exit_delay_seconds`, `max_open_positions`; add stress scenario normalization; add `stress_replay` evaluation output.
- Modify `scripts/run_hybrid_training.py`: add CLI switch `--stress-replay` that enables default mild/harsh scenarios.
- Modify `tests/model/test_train_hybrid_pipeline.py`: add behavior tests for delayed entry, delayed exit, concurrent position caps, and stress scenario reporting.
- Modify `tests/model/test_run_hybrid_training_cli.py`: add parser/config/help coverage for the new CLI switch.

## Task 1: Replay Delay And Capacity Tests

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`

- [ ] **Step 1: Write failing tests**

Add tests inside `TestTrainHybridPipeline`:

```python
def test_run_ab_evaluation_entry_delay_uses_later_fill_price(self):
    m = _load_module()

    class _FakeBuyModel:
        def predict_proba(self, X):
            return [[0.1, 0.9] for _ in range(len(X))]

    class _SellAllPolicy:
        def predict(self, obs, deterministic=True):
            return 3, None

    def sample(sample_time, price, buy_volume=10.0, sell_volume=1.0):
        return {
            "features": {
                "current_price": price,
                "launch_fee": 0.5,
                "holder_count": 10,
                "total_buy_volume": buy_volume,
                "total_sell_volume": sell_volume,
            },
            "meta": {"token_address": "0xdelayentry", "sample_time": sample_time},
        }

    eval_samples = [
        sample(100, 1.0),
        sample(103, 2.0),
        sample(110, 3.0, buy_volume=1.0, sell_volume=9.0),
    ]

    out = m.run_ab_evaluation(
        {"eval_samples": eval_samples, "include_trade_log": True, "entry_delay_seconds": 2},
        {"model": _FakeBuyModel(), "threshold": 0.5},
        {"model": _SellAllPolicy()},
        {"bc_samples": 10},
    )

    self.assertEqual(out["trade_log"][0]["entry_time"], 103)
    self.assertEqual(out["trade_log"][0]["entry_index"], 1)
    self.assertAlmostEqual(out["trade_log"][0]["entry_price"], 2.0)
    self.assertAlmostEqual(out["trade_log"][0]["return_pct"], 50.0)
    self.assertEqual(out["runtime_replay"]["entry_delay_seconds"], 2)
```

```python
def test_run_ab_evaluation_exit_delay_uses_later_fill_price(self):
    m = _load_module()

    class _FakeBuyModel:
        def predict_proba(self, X):
            return [[0.1, 0.9] for _ in range(len(X))]

    class _SellAllPolicy:
        def predict(self, obs, deterministic=True):
            return 3, None

    def sample(sample_time, price):
        return {
            "features": {
                "current_price": price,
                "launch_fee": 0.5,
                "holder_count": 10,
                "total_buy_volume": 10.0,
                "total_sell_volume": 1.0,
            },
            "meta": {"token_address": "0xdelayexit", "sample_time": sample_time},
        }

    eval_samples = [sample(100, 1.0), sample(110, 2.0), sample(115, 1.0)]

    out = m.run_ab_evaluation(
        {"eval_samples": eval_samples, "include_trade_log": True, "exit_delay_seconds": 3},
        {"model": _FakeBuyModel(), "threshold": 0.5},
        {"model": _SellAllPolicy()},
        {"bc_samples": 10},
    )

    self.assertEqual(out["trade_log"][0]["exit_time"], 115)
    self.assertAlmostEqual(out["trade_log"][0]["exit_price"], 1.0)
    self.assertAlmostEqual(out["trade_log"][0]["return_pct"], 0.0)
    self.assertEqual(out["runtime_replay"]["exit_delay_seconds"], 3)
```

```python
def test_run_ab_evaluation_max_open_positions_limits_concurrent_entries(self):
    m = _load_module()

    class _FakeBuyModel:
        def predict_proba(self, X):
            return [[0.1, 0.9] for _ in range(len(X))]

    class _SellAllPolicy:
        def predict(self, obs, deterministic=True):
            return 3, None

    def sample(token, sample_time, price):
        return {
            "features": {
                "current_price": price,
                "launch_fee": 0.5,
                "holder_count": 10,
                "total_buy_volume": 10.0,
                "total_sell_volume": 1.0,
            },
            "meta": {"token_address": token, "sample_time": sample_time},
        }

    eval_samples = [
        sample("0xcapone", 100, 1.0),
        sample("0xcaptwo", 100, 1.0),
        sample("0xcapone", 110, 2.0),
        sample("0xcaptwo", 110, 2.0),
    ]

    out = m.run_ab_evaluation(
        {"eval_samples": eval_samples, "include_trade_log": True, "max_open_positions": 1},
        {"model": _FakeBuyModel(), "threshold": 0.5},
        {"model": _SellAllPolicy()},
        {"bc_samples": 10},
    )

    self.assertEqual(out["entry_count"], 1)
    self.assertEqual(out["total_trades"], 1)
    self.assertEqual(out["runtime_replay"]["max_open_positions"], 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_ab_evaluation_entry_delay_uses_later_fill_price tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_ab_evaluation_exit_delay_uses_later_fill_price tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_ab_evaluation_max_open_positions_limits_concurrent_entries`

Expected: FAIL because the replay does not yet accept or report these live-stress parameters.

## Task 2: Implement Replay Delay And Capacity

**Files:**
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Add parameters**

Update `_run_eval_replay` signature to accept:

```python
entry_delay_seconds=0,
exit_delay_seconds=0,
max_open_positions=None,
```

Normalize them near the other replay knobs:

```python
entry_delay = max(0, int(entry_delay_seconds or 0))
exit_delay = max(0, int(exit_delay_seconds or 0))
open_position_cap = None if max_open_positions is None else max(0, int(max_open_positions))
pending_entries = {}
```

- [ ] **Step 2: Schedule delayed entries and exits**

Inside the chronological replay loop, before new signal handling:

```python
pending_entry = pending_entries.get(token)
if position is None and pending_entry and sample_time >= pending_entry["due_time"]:
    # Execute at current sample price and clear the delayed signal.
```

When a new buy signal is valid and `entry_delay > 0`, store:

```python
pending_entries[token] = {"due_time": sample_time + entry_delay, "buy_prob": float(buy_prob), "signal_index": idx}
```

When an exit signal is valid and `exit_delay > 0`, store it in `position["pending_exit"]` with `due_time`, `fraction`, `requested_fraction`, and `reason`; execute once a later sample reaches the due time.

- [ ] **Step 3: Enforce max open positions**

Create an entry helper that also checks:

```python
if open_position_cap is not None and len(positions) >= open_position_cap:
    return False
```

- [ ] **Step 4: Report new replay knobs**

Add to `base_result`:

```python
"entry_delay_seconds": entry_delay,
"exit_delay_seconds": exit_delay,
"max_open_positions": open_position_cap,
```

- [ ] **Step 5: Run tests to verify pass**

Run the same command from Task 1. Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Add live stress replay execution controls"
```

## Task 3: Stress Scenario Evaluation And CLI

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `scripts/run_hybrid_training.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `tests/model/test_run_hybrid_training_cli.py`

- [ ] **Step 1: Write failing tests**

Add a pipeline test that passes `stress_replay_scenarios` and asserts `out["stress_replay"]` includes a named scenario with its replay metrics.

Add CLI assertions for `--stress-replay` in help output, default `False`, and config key `stress_replay`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_ab_evaluation_reports_stress_replay_scenarios tests.model.test_run_hybrid_training_cli.TestRunHybridTrainingCli`

Expected: FAIL because stress scenario normalization and CLI flags do not exist yet.

- [ ] **Step 3: Implement default scenarios**

Add helper:

```python
def _stress_replay_scenarios(config):
    configured = config.get("stress_replay_scenarios")
    if configured:
        return [dict(item) for item in configured]
    if not bool(config.get("stress_replay", False)):
        return []
    return [
        {"name": "mild", "entry_delay_seconds": 2, "exit_delay_seconds": 2, "slippage_bps": 300.0, "max_open_positions": 8},
        {"name": "harsh", "entry_delay_seconds": 5, "exit_delay_seconds": 5, "slippage_bps": 600.0, "max_open_positions": 4},
    ]
```

In `run_ab_evaluation`, run `_run_eval_replay` for each scenario and set `result["stress_replay"]`.

- [ ] **Step 4: Implement CLI flag**

Add parser flag:

```python
parser.add_argument("--stress-replay", action="store_true", help="Report default live-like stress replay scenarios in the manifest")
```

Pass `"stress_replay": args.stress_replay` into config.

- [ ] **Step 5: Run tests to verify pass**

Run the Task 3 command. Expected: PASS.

- [ ] **Step 6: Full validation and commit**

Run: `venv/bin/python -m unittest discover`

Expected: all tests pass. Then:

```bash
git add src/pipeline/train_hybrid.py scripts/run_hybrid_training.py tests/model/test_train_hybrid_pipeline.py tests/model/test_run_hybrid_training_cli.py
git commit -m "Report live stress replay scenarios"
```

## Task 4: Run Current Model Through Stress Replay

**Files:**
- No tracked source files required.

- [ ] **Step 1: Run or script a v20 stress evaluation**

Use existing `data/models/20260509_return_first_v20` artifacts and current evaluation samples to produce Base/Mild/Harsh metrics. If direct artifact loading is too slow, run a training command with `--stress-replay` and a new output dir.

- [ ] **Step 2: Summarize realism gap**

Report Base, Mild, Harsh `net_return_pct`, multiple, `max_drawdown_pct`, `entry_rate`, and `total_trades`. Treat stress replay as a live-readiness diagnostic, not a live guarantee.

- [ ] **Step 3: Code review before final response**

Review changed source and tests manually for timing leakage, double exits, stale pending orders, and CLI config mismatch. Run `git diff --check` and targeted tests again.
