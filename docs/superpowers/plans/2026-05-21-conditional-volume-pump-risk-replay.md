# Conditional Volume Pump Risk Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether v95's live loss pattern can be improved by disabling the fragile near-threshold rescue while adding only tightly bounded low-volume primary rescues protected by a pump-exhaustion/slippage-risk veto.

**Architecture:** This is a replay-only falsification experiment. It reuses existing `_run_eval_replay` controls for `buy_low_volume_rescue_*` and `buy_late_pump_veto_*`, creates one bounded grid runner, and compares every candidate against the current v95 validation baseline and sealed final baseline under 10% sizing. It does not change live bot behavior or `docs/goals/live-model-optimization-goal.md`.

**Tech Stack:** Python `unittest`, existing `src.pipeline.model_replay.run_model_replay`, existing replay counters, JSON replay reports.

---

### Task 1: Add CLI Contract Tests

**Files:**
- Create: `tests/model/test_conditional_volume_pump_risk_replay_cli.py`
- Read: `tests/model/test_low_volume_rescue_replay_cli.py`
- Read: `tests/model/test_late_pump_exhaustion_replay_cli.py`

- [ ] **Step 1: Write the failing test file**

Create `tests/model/test_conditional_volume_pump_risk_replay_cli.py` with tests that load `scripts/run_conditional_volume_pump_risk_replay.py` and assert:

```python
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_conditional_volume_pump_risk_replay.py"
    spec = importlib.util.spec_from_file_location("run_conditional_volume_pump_risk_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class patch_modules:
    def __init__(self, modules):
        self.modules = modules
        self._patch = None

    def __enter__(self):
        from unittest.mock import patch

        self._patch = patch.dict(sys.modules, self.modules)
        return self._patch.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self._patch.__exit__(exc_type, exc, tb)


class TestConditionalVolumePumpRiskReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.2"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-position-fraction", "0.2"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-open-positions", "9"])

    def test_candidate_grid_combines_near_rescue_disable_low_volume_rescue_and_pump_veto(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 72)
        for candidate in candidates:
            self.assertIn("buy_near_threshold_min_prob", candidate)
            self.assertIsNone(candidate["buy_near_threshold_min_prob"])
            self.assertIn("buy_low_volume_rescue_min_prob", candidate)
            self.assertIn("buy_low_volume_rescue_min_entry_volume_30s", candidate)
            self.assertIn("buy_low_volume_rescue_max_entry_volume_30s", candidate)
            self.assertIn("buy_late_pump_veto_min_age_seconds", candidate)
            self.assertIn("buy_late_pump_veto_min_price_extension_pct", candidate)
            self.assertLessEqual(candidate["buy_low_volume_rescue_max_entry_volume_30s"], 1.5)
            self.assertLessEqual(candidate["buy_late_pump_veto_min_entry_volume_30s"], 1.5)

    def test_main_selects_validation_candidate_and_confirms_on_final(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_near_threshold_min_prob": None,
                "buy_near_min_pred_return": None,
                "buy_near_min_entry_volume_30s": None,
                "buy_near_min_entry_price_volatility": None,
                "buy_near_min_age_seconds": None,
                "buy_low_volume_rescue_min_prob": 0.988,
                "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
                "buy_low_volume_rescue_min_entry_price_volatility": 0.08,
                "buy_low_volume_rescue_max_age_seconds": 90,
                "buy_low_volume_rescue_take_profit_pct": 0.35,
                "buy_late_pump_veto_min_age_seconds": 15,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 1.0,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 0.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.08,
            },
            {
                "buy_near_threshold_min_prob": None,
                "buy_near_min_pred_return": None,
                "buy_near_min_entry_volume_30s": None,
                "buy_near_min_entry_price_volatility": None,
                "buy_near_min_age_seconds": None,
                "buy_low_volume_rescue_min_prob": 0.99,
                "buy_low_volume_rescue_min_entry_volume_30s": 0.95,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
                "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
                "buy_low_volume_rescue_max_age_seconds": 60,
                "buy_low_volume_rescue_take_profit_pct": 0.35,
                "buy_late_pump_veto_min_age_seconds": 15,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 0.8,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 0.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.08,
            },
        ])
        calls = []

        def evaluation_for(overrides):
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            is_second = overrides.get("buy_low_volume_rescue_min_prob") == 0.99
            if not is_candidate:
                return {
                    "net_profit_bnb": 0.001,
                    "total_trades": 4,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": 5.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{"name": "harsh_execution", "net_return_pct": 2.0, "net_profit_bnb": 0.0002, "max_drawdown_pct": -15.0}],
                    "low_volume_rescue_entry_count": 0,
                    "late_pump_veto_reject_count": 0,
                    "near_threshold_entry_count": 1,
                }
            return {
                "net_profit_bnb": 0.003 if is_second else 0.002,
                "total_trades": 4,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.75 if is_second else 0.5,
                "walk_forward_worst_net_return_pct": 7.0 if is_second else 4.0,
                "walk_forward_worst_max_drawdown_pct": -11.0,
                "stress_replay": [{"name": "harsh_execution", "net_return_pct": 3.0, "net_profit_bnb": 0.0003, "max_drawdown_pct": -14.0}],
                "low_volume_rescue_entry_count": 1,
                "late_pump_veto_reject_count": 2,
                "near_threshold_entry_count": 0,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "conditional_volume_pump_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertEqual(report["decision"], "accept")
        self.assertFalse(report["live_switch_evidence"])
        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertIsNone(calls[1]["overrides"]["buy_near_threshold_min_prob"])
        self.assertEqual(calls[1]["overrides"]["position_fraction"], 0.1)
        self.assertEqual(calls[1]["overrides"]["max_position_fraction"], 0.1)
        self.assertIsNone(calls[1]["overrides"]["fixed_stake_bnb"])
        self.assertTrue(calls[1]["overrides"]["skip_all_in_replay"])

    def test_main_rejects_candidate_without_both_live_triggered_activities(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": None,
            "buy_near_min_pred_return": None,
            "buy_near_min_entry_volume_30s": None,
            "buy_near_min_entry_price_volatility": None,
            "buy_near_min_age_seconds": None,
            "buy_low_volume_rescue_min_prob": 0.99,
            "buy_low_volume_rescue_min_entry_volume_30s": 0.95,
            "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
            "buy_low_volume_rescue_max_age_seconds": 60,
            "buy_low_volume_rescue_take_profit_pct": 0.35,
            "buy_late_pump_veto_min_age_seconds": 15,
            "buy_late_pump_veto_extension_window_seconds": 30,
            "buy_late_pump_veto_min_price_extension_pct": 0.8,
            "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
            "buy_late_pump_veto_min_entry_volume_30s": 0.0,
            "buy_late_pump_veto_min_entry_price_volatility": 0.08,
        }])

        def fake_run_model_replay(**kwargs):
            is_candidate = "buy_low_volume_rescue_min_prob" in dict(kwargs.get("overrides") or {})
            return {"evaluation": {
                "net_profit_bnb": 0.003 if is_candidate else 0.001,
                "total_trades": 4,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.75,
                "walk_forward_worst_net_return_pct": 7.0,
                "walk_forward_worst_max_drawdown_pct": -11.0,
                "stress_replay": [{"name": "harsh_execution", "net_return_pct": 3.0, "net_profit_bnb": 0.0003, "max_drawdown_pct": -14.0}],
                "low_volume_rescue_entry_count": 0,
                "late_pump_veto_reject_count": 2 if is_candidate else 0,
                "near_threshold_entry_count": 0,
            }}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "conditional_volume_pump_reject.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual(report["decision"], "reject")
        self.assertFalse(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertFalse(report["live_switch_evidence"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_conditional_volume_pump_risk_replay_cli
```

Expected: import failure because `scripts/run_conditional_volume_pump_risk_replay.py` does not exist.

### Task 2: Add Replay Grid CLI

**Files:**
- Create: `scripts/run_conditional_volume_pump_risk_replay.py`
- Read: `scripts/run_low_volume_rescue_replay.py`
- Read: `scripts/run_late_pump_exhaustion_replay.py`

- [ ] **Step 1: Implement the minimal CLI**

Create `scripts/run_conditional_volume_pump_risk_replay.py` by adapting the bounded replay-runner pattern:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.004204022777736465
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
MAX_TRADE_COUNT_EXPANSION_RATIO = 0.25
MAX_TRADE_COUNT_EXPANSION_MIN_EXTRA = 1
MAX_TRADE_COUNT_REDUCTION_RATIO = 0.25
MAX_TRADE_COUNT_REDUCTION_MIN_MISSING = 1
PROTECTED_MODEL_ARTIFACT_NAMES = frozenset((
    "hybrid_manifest.json",
    "buy_model.cbm",
    "buy_threshold.json",
    "feature_schema.json",
    "entry_value_model.cbm",
    "sell_policy.zip",
    "bc.pt",
    "trade_log.jsonl",
))
```

Use strict parsers so `position_fraction`, `max_position_fraction`, and `max_open_positions` cannot increase live risk. Use `candidate_grid()` to emit candidates that:

- Disable v95 near-threshold rescue by setting all `buy_near_*` values to `None`.
- Add `buy_low_volume_rescue_*` bounded around `volume_30s < 1.5`.
- Add `buy_late_pump_veto_*` with `min_entry_volume_30s=0.0` so the veto can protect low-volume candidates too.

The acceptance gate must require all baseline-comparison checks plus:

- `low_volume_rescue_entry_count > 0`
- `late_pump_veto_reject_count > 0`
- `near_threshold_entry_count == 0`

The report must include `live_switch_evidence: False`.

- [ ] **Step 2: Run tests to verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_conditional_volume_pump_risk_replay_cli
```

Expected: OK.

### Task 3: Run Strict Replay Experiment

**Files:**
- Output: `data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json`

- [ ] **Step 1: Run the bounded replay grid**

Run:

```bash
venv/bin/python scripts/run_conditional_volume_pump_risk_replay.py --force
```

Expected: prints `decision=accept` or `decision=reject` and writes the JSON report.

- [ ] **Step 2: Inspect the result**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json')
d = json.loads(p.read_text())
print('decision', d['decision'])
print('validation baseline', d['baseline']['summary'])
print('selected validation params', d['selected_candidate']['params'])
print('selected validation summary', d['selected_candidate']['summary'])
print('final passed', d['final_confirmation']['passes_acceptance_gate'])
print('final candidate summary', d['final_confirmation']['candidate']['summary'])
PY
```

Expected: enough evidence to accept or reject the direction against v95 and current best baseline.

### Task 4: Document Decision

**Files:**
- Modify: `docs/model_scoreboard.md`
- Modify: `docs/research/20260521-conditional-volume-pump-risk/summary.md`

- [ ] **Step 1: Add a scoreboard row**

Add a rejected or accepted row that records:

- live trigger: v95 near rescue lost live money; FENGSHUI/挠头 showed pump/slippage risk; EX677/FourPass/GNGN showed low-volume missed-runner risk.
- report path: `data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json`
- selected params and strict metrics.
- decision: no live switch unless validation and final both beat baseline with robustness gates.

- [ ] **Step 2: Add a research summary result line**

Append a short "Experiment result" section to `docs/research/20260521-conditional-volume-pump-risk/summary.md` with the report path, selected params, result, and next hypothesis.

### Task 5: Verification, Two Reviews, Commit/Push

**Files:**
- All changed files in this plan.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_conditional_volume_pump_risk_replay_cli tests.model.test_low_volume_rescue_replay tests.model.test_late_pump_exhaustion_veto tests.model.test_model_replay
```

Expected: OK.

- [ ] **Step 2: Run syntax checks**

Run:

```bash
venv/bin/python -m py_compile scripts/run_conditional_volume_pump_risk_replay.py
```

Expected: no output.

- [ ] **Step 3: Review pass 1**

Strictly inspect:

```bash
git diff -- scripts/run_conditional_volume_pump_risk_replay.py tests/model/test_conditional_volume_pump_risk_replay_cli.py docs/model_scoreboard.md docs/research/20260521-conditional-volume-pump-risk/summary.md
git diff -- docs/goals/live-model-optimization-goal.md
```

Expected: no `docs/goals/live-model-optimization-goal.md` diff; no live bot behavior change; no risk expansion; report paths accurate.

- [ ] **Step 4: Review pass 2**

Repeat the same diff inspection after any final edit. If a material issue requires code/docs changes, reset review count and do two clean passes after the last edit.

- [ ] **Step 5: Commit and push**

Run:

```bash
git add scripts/run_conditional_volume_pump_risk_replay.py tests/model/test_conditional_volume_pump_risk_replay_cli.py docs/superpowers/plans/2026-05-21-conditional-volume-pump-risk-replay.md docs/model_scoreboard.md docs/research/20260521-conditional-volume-pump-risk data/replay_reports/conditional_volume_pump_risk_replay_20260521_v95.json
git commit -m "test: evaluate conditional volume pump risk replay"
git push
```

Expected: commit and push succeed.

### Self-Review

- Spec coverage: The plan starts from live v95 loss evidence, reuses SmartSearch research, avoids already rejected global threshold/volume relaxation, keeps 10% sizing, compares against v95 baseline, writes report artifacts, requires two review passes, and does not edit the goal document.
- Placeholder scan: No TODO/TBD placeholders remain.
- Type consistency: Script/test names, report path, and counter names match existing replay counters.
