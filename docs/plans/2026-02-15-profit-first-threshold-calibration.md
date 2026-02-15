# Profit-First Threshold Calibration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a profit-first calibration workflow that tunes classifier/regressor entry thresholds on the latest dataset and outputs a recommended production configuration that prioritizes backtest profitability over trade frequency.

**Architecture:** Keep the current dual-model training architecture unchanged, and add a standalone calibration pipeline that reuses model artifacts + latest test split to run deterministic grid-search over strategy thresholds. Evaluation uses the same event-driven, one-trade-per-token simulation as trainer gate to avoid train/runtime mismatch. Results are persisted as machine-readable JSON and a concise operator-facing report.

**Tech Stack:** Python 3, pandas/numpy/joblib, existing `MemeModelTrainer` and `SimpleBacktester` logic, unittest, venv + requirements.txt.

---

### Task 1: Add failing tests for profit-first calibrator API and constraints

**Files:**
- Create: `tests/model/test_profit_first_calibrator.py`
- Reference: `src/model/trainer.py:415-514` (gate simulation behavior)

**Step 1: Write the failing test**

```python
import unittest
from pathlib import Path
import importlib.util


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestProfitFirstCalibrator(unittest.TestCase):
    def test_selects_highest_return_candidate_under_drawdown_guard(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )
        selector = module._select_best_candidate

        candidates = [
            {"prob_threshold": 0.20, "reg_min_return": 50.0, "return_pct": 30.0, "max_drawdown_pct": 18.0, "trades": 120},
            {"prob_threshold": 0.35, "reg_min_return": 60.0, "return_pct": 40.0, "max_drawdown_pct": 24.0, "trades": 70},
            {"prob_threshold": 0.45, "reg_min_return": 80.0, "return_pct": 55.0, "max_drawdown_pct": 42.0, "trades": 50},
        ]

        best = selector(candidates, max_drawdown_limit=35.0, min_trades=20)
        self.assertEqual(best["prob_threshold"], 0.35)
        self.assertEqual(best["reg_min_return"], 60.0)

    def test_returns_none_when_all_candidates_fail_constraints(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "profit_first_calibrator.py",
            "profit_first_calibrator",
        )
        selector = module._select_best_candidate

        candidates = [
            {"prob_threshold": 0.50, "reg_min_return": 90.0, "return_pct": 12.0, "max_drawdown_pct": 45.0, "trades": 18},
        ]

        best = selector(candidates, max_drawdown_limit=35.0, min_trades=20)
        self.assertIsNone(best)
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: FAIL with `FileNotFoundError` / missing module because calibrator file does not exist yet.

**Step 3: Write minimal implementation**

Create file `src/backtest/profit_first_calibrator.py` with stubs:

```python
def _select_best_candidate(candidates, max_drawdown_limit=35.0, min_trades=20):
    filtered = [
        c for c in candidates
        if float(c.get("max_drawdown_pct", 999.0)) <= max_drawdown_limit
        and int(c.get("trades", 0)) >= min_trades
    ]
    if not filtered:
        return None
    filtered.sort(key=lambda c: (float(c.get("return_pct", -1e9)), int(c.get("trades", 0))), reverse=True)
    return filtered[0]
```

**Step 4: Run test to verify it passes**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_profit_first_calibrator.py src/backtest/profit_first_calibrator.py
git commit -m "test+feat: add profit-first candidate selector"
```

---

### Task 2: Add failing tests for deterministic grid calibration outputs

**Files:**
- Modify: `tests/model/test_profit_first_calibrator.py`
- Modify: `src/backtest/profit_first_calibrator.py`

**Step 1: Write the failing test**

Append tests validating:
- `run_profit_first_calibration(...)` returns result dict with keys: `dataset_timestamp`, `model_timestamp`, `search_space`, `top_candidates`, `recommended`.
- candidates sorted by `return_pct` descending among valid constrained rows.
- recommendation is one of candidates and satisfies constraints.

Use an in-memory list of synthetic candidate metrics by monkeypatching an internal evaluator function.

Example test skeleton:

```python
def test_run_calibration_builds_ranked_outputs(self):
    module = _load_module(...)

    def fake_eval(*args, **kwargs):
        return [
            {"prob_threshold": 0.2, "reg_min_return": 50.0, "return_pct": 25.0, "max_drawdown_pct": 20.0, "trades": 100},
            {"prob_threshold": 0.3, "reg_min_return": 60.0, "return_pct": 35.0, "max_drawdown_pct": 30.0, "trades": 70},
            {"prob_threshold": 0.4, "reg_min_return": 70.0, "return_pct": 40.0, "max_drawdown_pct": 38.0, "trades": 50},
        ]

    with patch.object(module, "_evaluate_grid", side_effect=fake_eval):
        result = module.run_profit_first_calibration(...)

    self.assertEqual(result["recommended"]["prob_threshold"], 0.3)
    self.assertIn("top_candidates", result)
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: FAIL due to missing `run_profit_first_calibration` and output assembly logic.

**Step 3: Write minimal implementation**

In `src/backtest/profit_first_calibrator.py`, add:
- `run_profit_first_calibration(...)`
- placeholder `_evaluate_grid(...)` (real implementation in next task)
- deterministic sorting and top-k extraction

Return schema:

```python
{
  "dataset_timestamp": "...",
  "model_timestamp": "...",
  "search_space": {"prob_thresholds": [...], "reg_min_returns": [...], "max_age_seconds": [...]},
  "constraints": {"max_drawdown_limit": 35.0, "min_trades": 20},
  "top_candidates": [...],
  "recommended": {...} or None,
}
```

**Step 4: Run test to verify it passes**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_profit_first_calibrator.py src/backtest/profit_first_calibrator.py
git commit -m "test+feat: add calibration result schema and ranking"
```

---

### Task 3: Implement real grid evaluation by reusing trainer gate simulation semantics

**Files:**
- Modify: `src/backtest/profit_first_calibrator.py`
- Reference: `src/model/trainer.py:415-514`
- Optional helper reuse: `src/backtest/simple_backtest.py:67-142`

**Step 1: Write the failing test**

Add integration-style unit test using tiny synthetic dataframe and fake classifier/regressor objects to assert evaluator behavior:
- respects `prob_threshold`, `reg_min_return`, `max_age_seconds`
- enforces one trade per token
- computes `return_pct`, `max_drawdown_pct`, `trades`

**Step 2: Run test to verify it fails**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: FAIL because `_evaluate_grid` currently stubbed.

**Step 3: Write minimal implementation**

Implement in `src/backtest/profit_first_calibrator.py`:
- `_load_latest_dataset_and_model(...)`
  - find latest `data/datasets/test_*.jsonl`
  - find latest `data/models/models_*` with `classifier_xgb.pkl` (+ reg optional)
- `_evaluate_single_config(...)`
  - same event order and return accounting as trainer gate
- `_evaluate_grid(...)`
  - cartesian over `prob_thresholds × reg_min_returns × max_age_seconds`

Keep core PnL logic aligned with trainer gate formula (`size=0.1`, buy_slippage=0.20, sell_slippage=0.05, fee=0.02) to prevent metric drift.

**Step 4: Run test to verify it passes**

Run: `python3 tests/model/test_profit_first_calibrator.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_profit_first_calibrator.py src/backtest/profit_first_calibrator.py
git commit -m "feat: implement deterministic profit-first grid evaluator"
```

---

### Task 4: Add CLI entrypoint for calibration with venv-friendly execution

**Files:**
- Create: `tools/calibrate_profit_first.py`
- Modify: `README.md` (usage section only)
- Modify: `tests/model/test_run_training_cli.py` or create `tests/model/test_calibrate_profit_first_cli.py`

**Step 1: Write the failing test**

Test expectations:
- CLI parses flags:
  - `--prob-thresholds` (csv list)
  - `--reg-min-returns` (csv list)
  - `--max-age-seconds` (csv list)
  - `--min-trades`
  - `--max-drawdown`
  - `--top-k`
- CLI writes JSON output under `data/models/calibration_*.json`

**Step 2: Run test to verify it fails**

Run: `python3 tests/model/test_calibrate_profit_first_cli.py`
Expected: FAIL because CLI not implemented.

**Step 3: Write minimal implementation**

`tools/calibrate_profit_first.py`:
- parse args
- call `run_profit_first_calibration(...)`
- write output JSON
- print concise summary:
  - selected threshold tuple
  - return/drawdown/trades

Use project venv interpreter explicitly in docs:
- `./venv/bin/python tools/calibrate_profit_first.py ...`

**Step 4: Run test to verify it passes**

Run: `python3 tests/model/test_calibrate_profit_first_cli.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add tools/calibrate_profit_first.py tests/model/test_calibrate_profit_first_cli.py README.md
git commit -m "feat: add profit-first calibration CLI"
```

---

### Task 5: Add production handoff artifact and guardrail checks

**Files:**
- Modify: `src/model/trainer.py` (metadata extension only)
- Modify: `tests/model/test_trainer_metadata.py`
- Modify: `src/backtest/simple_backtest.py` (optional read recommended config)

**Step 1: Write the failing test**

Add metadata test asserting optional `strategy_recommendation` block can be embedded with fields:
- `prob_threshold`
- `reg_min_return`
- `max_age_seconds`
- `source_calibration_file`

**Step 2: Run test to verify it fails**

Run: `python3 tests/model/test_trainer_metadata.py`
Expected: FAIL due to missing metadata support.

**Step 3: Write minimal implementation**

- Extend `_build_model_metadata(...)` to accept optional `strategy_recommendation=None`.
- Include it when provided.
- Keep backward compatibility when absent.

**Step 4: Run test to verify it passes**

Run: `python3 tests/model/test_trainer_metadata.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/trainer.py tests/model/test_trainer_metadata.py
git commit -m "feat: support calibrated strategy recommendation in metadata"
```

---

### Task 6: Full verification in venv and operator-ready output

**Files:**
- No new code unless failures discovered
- Output artifacts in:
  - `data/models/calibration_*.json`
  - `data/models/calibration_latest.json` (copy/symlink)

**Step 1: Activate venv and install dependencies**

Run:

```bash
./venv/bin/python -m pip install -r requirements.txt
```

Expected: dependencies installed (`numpy`, `pandas`, `joblib`, `xgboost`, `lightgbm`).

**Step 2: Run focused test suite**

Run:

```bash
./venv/bin/python tests/model/test_profit_first_calibrator.py
./venv/bin/python tests/model/test_calibrate_profit_first_cli.py
./venv/bin/python tests/model/test_trainer_metadata.py
```

Expected: all pass.

**Step 3: Run calibration against latest real artifacts**

Run:

```bash
./venv/bin/python tools/calibrate_profit_first.py \
  --prob-thresholds 0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60 \
  --reg-min-returns 30,40,50,60,70,80,100 \
  --max-age-seconds 90,120,150,180 \
  --max-drawdown 35 \
  --min-trades 20 \
  --top-k 10
```

Expected:
- JSON report generated
- recommended config present (or explicit `recommended=null` with reason)
- printed summary includes return/drawdown/trades.

**Step 4: Sanity-check recommendation against business goal**

Acceptance criteria:
- recommendation maximizes `return_pct` under constraints
- no hidden hard dependency on `trades >= 80`
- recommendation states if frequency is low but profitability stronger (intended behavior)

**Step 5: Commit**

```bash
git add data/models/calibration_*.json data/models/calibration_latest.json
git commit -m "chore: add latest profit-first calibration report"
```

---

## Notes for the implementing engineer

- Do **not** retrain models in this plan; this is strategy calibration on existing latest artifacts.
- Keep DRY: reuse trainer gate execution semantics, avoid duplicating divergent PnL formulas.
- Keep YAGNI: no dashboard/DB/service; JSON + CLI is sufficient.
- Keep deterministic ordering when scores tie: `return_pct desc`, then `max_drawdown_pct asc`, then `trades desc`.
- If no candidate satisfies constraints, output diagnostics and relax constraints only via CLI flags (never hardcode silent fallback).
