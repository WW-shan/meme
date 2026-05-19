# Time-To-Barrier Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only probe that labels rejected live signals by first profit/stop/time barrier and simulates whether a quick take-profit or slow-runner policy is worth training next.

**Architecture:** Keep the live bot untouched. Add a small `src.pipeline` module that reuses `reentry_probe` parsing, lifecycle loading, and path-metric helpers, plus a thin CLI that writes a JSON report with run-time input SHA-256 fingerprints under `data/replay_reports/`. The probe is evidence only: it cannot switch live, cannot change sizing, and must compare candidates against the v95 live evidence before any later model work. The live input paths are mutable, so each input is read once into a bytes snapshot and fingerprints/parsing use those same bytes; they are not expected to keep matching current collector/bot files after collection continues.

**Tech Stack:** Python stdlib, existing `src.pipeline.reentry_probe` helpers, `unittest`, JSONL live artifacts.

---

## Files

- Create: `src/pipeline/time_to_barrier_probe.py`
- Create: `scripts/probe_time_to_barrier.py`
- Create: `tests/model/test_time_to_barrier_probe.py`
- Create: `tests/model/test_time_to_barrier_probe_cli.py`
- Read-only inputs for the first run: `data/signal_audit.jsonl`, `data/training/lifecycle_20260519_104017.jsonl`, `data/training/lifecycle_incremental_20260516_212852.jsonl`
- Output for the first run: `data/replay_reports/time_to_barrier_probe_20260519_v95.json`

## Live Trigger And Hypothesis

Live trigger:

- v95 initially had `0` accepted buys after restart and `1293` rejected signal decisions; the final read-only probe snapshot covered `2042` rejected signal decisions.
- Rejected paths split into fast-profit-then-collapse (`SZN`, `1Binance`, `520`), slow clean runners (`Neymar404`, `布剪刀石头`, `A9自由`), and correct skips (`Vera`).

Hypothesis:

Because v95 rejects contain both first-`+25` opportunities and first-stop collapses, a first-barrier/time-to-barrier probe can identify whether the next model should learn conditional quick take-profit, slow-runner hold, or stricter skip behavior without lowering the global entry threshold or increasing position size.

Falsification:

- Reject the direction if the probe mostly classifies candidates as collapse/flat, if quick/slow candidates are too rare to matter, or if accepted-looking candidates are only explained by hindsight rules that cannot be represented from signal-time features.
- The probe itself is not live-switch evidence.

## Subagent Ownership

- Worker subagent owns implementation and tests in `src/pipeline/time_to_barrier_probe.py`, `scripts/probe_time_to_barrier.py`, and the two new test files.
- Parent agent owns live-state monitoring, plan integration, report command execution, scoreboard/research interpretation, two final review passes, commit, push, and any live-switch decision.
- Do not delegate bot restart, collector restart, `.env` live switch, wallet/risk changes, or destructive cleanup.

## Task 1: Core Probe Module

**Files:**
- Create: `src/pipeline/time_to_barrier_probe.py`
- Test: `tests/model/test_time_to_barrier_probe.py`

- [x] **Step 1: Write failing tests for first-barrier classification**

Create `tests/model/test_time_to_barrier_probe.py` with these behaviors:

```python
import datetime as dt
import json
import unittest

from src.pipeline import reentry_probe
from src.pipeline import time_to_barrier_probe as p


class TestTimeToBarrierProbe(unittest.TestCase):
    def test_score_signal_marks_fast_profit_before_later_collapse(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xA",
            "symbol": "FAST",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.99,
            "pred_return": 25.0,
            "reason": "pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.26, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 0.80, "sell"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "fast_profit_then_collapse")
        self.assertEqual(scored["recommended_policy"], "quick_take_profit")
        self.assertEqual(scored["first_barrier"], "+25")
        self.assertEqual(scored["time_to_plus_25_seconds"], 20.0)
        self.assertEqual(scored["time_to_minus_18_seconds"], 90.0)
        self.assertTrue(scored["quick_take_profit_candidate"])
        self.assertFalse(scored["slow_runner_candidate"])

    def test_score_signal_marks_stop_first_as_collapse_skip(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xB",
            "symbol": "BAD",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.97,
            "pred_return": 8.0,
            "reason": "near_threshold_pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=12), 0.81, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=50), 1.30, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "stop_first")
        self.assertEqual(scored["recommended_policy"], "skip")
        self.assertEqual(scored["first_barrier"], "-18")
        self.assertFalse(scored["quick_take_profit_candidate"])

    def test_score_signal_marks_slow_runner_without_stop(self):
        anchor = dt.datetime(2026, 5, 19, 9, 32, 52)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xC",
            "symbol": "SLOW",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.978,
            "pred_return": 11.0,
            "reason": "near_threshold_pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=300), 1.30, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=540), 1.65, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "slow_runner")
        self.assertEqual(scored["recommended_policy"], "conditional_slow_hold")
        self.assertTrue(scored["slow_runner_candidate"])
        self.assertEqual(scored["time_to_plus_25_seconds"], 300.0)
        self.assertEqual(scored["time_to_plus_60_seconds"], 540.0)

    def test_score_signal_marks_missing_path(self):
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xD",
            "symbol": "MISS",
            "time": "2026-05-19 04:11:18",
            "prob": 0.99,
            "pred_return": 30.0,
            "reason": "pred_return_below_min",
        }

        scored = p.score_signal_time_to_barrier(signal, [])

        self.assertEqual(scored["barrier_class"], "missing_path")
        self.assertEqual(scored["recommended_policy"], "skip")

    def test_build_probe_report_deduplicates_by_token_and_counts_classes(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xA",
                "symbol": "A",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.95,
                "pred_return": 5.0,
                "reason": "near_threshold_pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xA",
                "symbol": "A",
                "time": (anchor + dt.timedelta(seconds=2)).isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 25.0,
                "reason": "pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xB",
                "symbol": "B",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.96,
                "pred_return": 7.0,
                "reason": "near_threshold_pred_return_below_min",
            },
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": (anchor + dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 1.3, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=100)).timestamp(), "price": 0.8, "type": "sell"},
                ],
            },
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": (anchor - dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=10)).timestamp(), "price": 0.8, "type": "sell"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["candidate_counts"]["signal_decisions"], 3)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 2)
        self.assertEqual(report["candidate_counts"]["dropped_duplicate_signal_decisions"], 1)
        self.assertEqual(report["class_counts"]["fast_profit_then_collapse"], 1)
        self.assertEqual(report["class_counts"]["stop_first"], 1)
        json.loads(p.to_json_text(report))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run the test and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_time_to_barrier_probe
```

Expected: FAIL because `src.pipeline.time_to_barrier_probe` does not exist.

- [x] **Step 3: Implement minimal probe module**

Create `src/pipeline/time_to_barrier_probe.py` with:

- `score_signal_time_to_barrier(signal, path, horizon_seconds=600, quick_profit_seconds=120)`
- `build_probe_report(signal_rows, lifecycles, generated_at=None, horizon_seconds=600, quick_profit_seconds=120, since=None)`
- `to_json_text(report)`

Implementation requirements:

- Reuse `reentry_probe.iter_signal_decisions`, `price_path_for_token`, `path_metrics`, `_anchor_price_at_or_before`, `safe_float`, `normalize_token`, and `parse_time`.
- Use only rejected `SIGNAL_DECISION` rows.
- Filter out signals before `since` when `since` is provided, so the report can stay scoped to the current live-model window.
- Keep one candidate per token: choose the row with highest `(pred_return, prob, time)`.
- Require no model loading and no live trading side effects.
- Use `reentry_probe.ANALYSIS_TZ` for default `generated_at`, matching live attribution timestamps.
- Return `probe_contract = {"read_only": True, "live_switch_evidence": False, "requires_replay_before_live_change": True}`.
- Classify:
  - `missing_path`: no path or no anchor price.
  - `stop_first`: first barrier is `-18` or `-25`.
  - `fast_profit_then_collapse`: `+25` occurs at or before `quick_profit_seconds`, before any `-18`, and an `-18` or `-25` later appears within horizon.
  - `fast_profit`: `+25` occurs at or before `quick_profit_seconds`, before any `-18`, with no later stop barrier in horizon.
  - `slow_runner`: `+25` occurs after `quick_profit_seconds`, before any `-18`, or `+60` occurs before any stop barrier.
  - `flat_timeout`: no profit or stop barrier appears in horizon.
- Set `recommended_policy`:
  - `quick_take_profit` for `fast_profit_then_collapse` and `fast_profit`.
  - `conditional_slow_hold` for `slow_runner`.
  - `skip` otherwise.

- [x] **Step 4: Run the module test and verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_time_to_barrier_probe
```

Expected: OK.

## Task 2: CLI Wrapper

**Files:**
- Create: `scripts/probe_time_to_barrier.py`
- Test: `tests/model/test_time_to_barrier_probe_cli.py`

- [x] **Step 1: Write failing CLI tests**

Create `tests/model/test_time_to_barrier_probe_cli.py` with these behaviors:

```python
import contextlib
import importlib.util
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_time_to_barrier.py"
    spec = importlib.util.spec_from_file_location("probe_time_to_barrier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTimeToBarrierProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 1)
        self.assertIsNone(args.lifecycle_file)
        self.assertEqual(args.horizon_seconds, 600)
        self.assertEqual(args.quick_profit_seconds, 120)

    def test_main_calls_probe_and_writes_report(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.time_to_barrier_probe")
        fake_reentry = types.SimpleNamespace(
            iter_jsonl=lambda path: [],
            latest_lifecycle_files=lambda lifecycle_dir, limit: [Path("data/training/a.jsonl")],
            load_lifecycles=lambda collector_state_path=None, lifecycle_paths=None: {"0xa": {}},
            build_input_status=lambda **kwargs: {"existing_lifecycle_path_count": 1},
            to_json_text=lambda report: "{\\"ok\\": true}\\n",
        )
        fake_module.build_probe_report = lambda **kwargs: {"candidate_counts": {"per_token_candidates": 2}}
        fake_module.reentry_probe = fake_reentry

        with patch.dict(sys.modules, {"src.pipeline.time_to_barrier_probe": fake_module}):
            with patch.object(fake_module, "build_probe_report", return_value={"candidate_counts": {"per_token_candidates": 2}}) as mock_run:
                stdout = io.StringIO()
                with patch("pathlib.Path.write_text") as mock_write, contextlib.redirect_stdout(stdout):
                    result = cli.main(["--output", "data/replay_reports/out.json", "--lifecycle-file", "data/training/custom.jsonl"])

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["horizon_seconds"], 600)
        self.assertEqual(kwargs["quick_profit_seconds"], 120)
        self.assertEqual(result, 0)
        mock_write.assert_called_once_with('{\\"ok\\": true}\\n', encoding="utf-8")
        self.assertIn("per_token_candidates=2", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run CLI test and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_time_to_barrier_probe_cli
```

Expected: FAIL because `scripts/probe_time_to_barrier.py` does not exist.

- [x] **Step 3: Implement CLI**

Create `scripts/probe_time_to_barrier.py` with:

- repo-root `sys.path` insertion, matching existing scripts.
- `parse_args(argv=None)` args:
  - `--signal-audit`, default `data/signal_audit.jsonl`
  - `--collector-state`, default `data/training/collector_runtime_state.json`
  - `--lifecycle-dir`, default `data/training`
  - `--recent-lifecycle-files`, default `1`
  - repeated `--lifecycle-file`
  - `--output`, default timestamped `data/replay_reports/time_to_barrier_probe_<YYYYMMDD_HHMMSS>.json`
  - `--since`, default `None`
  - `--horizon-seconds`, default `600`
  - `--quick-profit-seconds`, default `120`
- `main(argv=None)` loads signal audit rows if present, loads collector state plus lifecycle paths, builds the report, adds `inputs` and `input_status`, writes JSON, and prints:
  - `wrote <path>`
  - `per_token_candidates=<n>`

- [x] **Step 4: Run CLI tests and module tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli
```

Expected: OK.

## Task 3: Run Probe And Record Decision

**Files:**
- Output: `data/replay_reports/time_to_barrier_probe_20260519_v95.json`
- Modify: `docs/research/20260519-time-to-barrier-entry-exit/summary.md`
- Modify: `docs/model_scoreboard.md`

- [x] **Step 1: Run the live read-only probe**

Run:

```bash
venv/bin/python scripts/probe_time_to_barrier.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 0 \
  --lifecycle-file data/training/lifecycle_20260519_104017.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212852.jsonl \
  --output data/replay_reports/time_to_barrier_probe_20260519_v95.json \
  --horizon-seconds 600 \
  --quick-profit-seconds 120 \
  --since '2026-05-19 04:02:23'
```

Expected: writes the output report and prints `per_token_candidates=<n>`.

- [x] **Step 2: Extract key metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path('data/replay_reports/time_to_barrier_probe_20260519_v95.json')
r = json.loads(p.read_text())
print(json.dumps({
    'candidate_counts': r.get('candidate_counts'),
    'class_counts': r.get('class_counts'),
    'policy_counts': r.get('policy_counts'),
}, ensure_ascii=False, indent=2, sort_keys=True))
for row in r.get('candidate_sample', [])[:20]:
    print(json.dumps({
        'symbol': row.get('symbol'),
        'token': row.get('token'),
        'pred_return': row.get('pred_return'),
        'prob': row.get('prob'),
        'barrier_class': row.get('barrier_class'),
        'recommended_policy': row.get('recommended_policy'),
        'mfe_pct': row.get('mfe_pct'),
        'mae_pct': row.get('mae_pct'),
        'time_to_plus_25_seconds': row.get('time_to_plus_25_seconds'),
        'time_to_minus_18_seconds': row.get('time_to_minus_18_seconds'),
    }, ensure_ascii=False, sort_keys=True))
PY
```

- [x] **Step 3: Update research summary and scoreboard**

Append a concise "Local Probe Result" section to `docs/research/20260519-time-to-barrier-entry-exit/summary.md` and a note to `docs/model_scoreboard.md`.

The decision must be one of:

- `reject_probe`: if quick/slow candidates are too rare, mostly hindsight-only, or collapse-heavy.
- `evidence_only`: if the probe supports a follow-up replay/model experiment but does not itself beat baseline.
- `promote_to_replay_experiment`: only if the probe shows enough clean, signal-time-plausible candidates to justify a replay-integrated policy. This still must not switch live.

## Required Verification

Run after implementation:

```bash
venv/bin/python -m unittest tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli
git diff --check
```

If code changes occurred, run two strict review passes after the final edit:

- Review pass 1: parent-agent review of full diff, focused on correctness, read-only contract, live safety, tests, artifact paths, and replay/live alignment.
- Review pass 2: independent subagent or fresh-pass review, focused on bugs, data leakage, missing tests, missing artifacts, and pull-and-run readiness.

If either review finds a material issue and code changes, reset the review count and rerun both passes.

## Commit And Push

Commit and push when the probe, report, research summary, and scoreboard decision are complete:

```bash
git add src/pipeline/time_to_barrier_probe.py scripts/probe_time_to_barrier.py tests/model/test_time_to_barrier_probe.py tests/model/test_time_to_barrier_probe_cli.py docs/research/20260519-time-to-barrier-entry-exit data/replay_reports/time_to_barrier_probe_20260519_v95.json docs/model_scoreboard.md docs/superpowers/plans/2026-05-19-time-to-barrier-probe.md
git commit -m "Add time-to-barrier probe"
git push
```

Do not include unrelated artifacts.
