# Stop-Loss Re-Entry Runner-Retention Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only offline probe that uses live trades, rejected signals, and lifecycle price paths to falsify or support a conditional stop-loss re-entry / runner-retention direction before changing training or live bot behavior.

**Architecture:** Add a small `src/pipeline/reentry_probe.py` module with pure parsing and path-metric helpers, plus a thin `scripts/probe_reentry_retention.py` CLI that writes JSON reports under `data/replay_reports/`. Keep the probe read-only: it must not edit `.env`, model manifests, bot state, or lifecycle files. Use the output to decide whether a later model or replay change is justified.

**Tech Stack:** Python 3.12, `unittest`, JSONL live artifacts, existing lifecycle JSON structures, existing `tools/memectl` runtime contract.

---

## File Map

- Create `src/pipeline/reentry_probe.py`: reusable probe helpers for token normalization, timestamp parsing, lifecycle extraction, price path metrics, trade pairing, and candidate scoring.
- Create `scripts/probe_reentry_retention.py`: CLI wrapper that reads current default artifacts and writes a report.
- Create `tests/model/test_reentry_probe.py`: unit tests for parsers, barrier ordering, trade pairing, and candidate scoring.
- Output generated reports to `data/replay_reports/`; these are local analysis artifacts unless an experiment is accepted.
- Do not modify `src/trader/bot.py`, `.env`, `.env.example`, model manifests, or live runtime control in this plan.

## Task 1: Add Path Metric Helpers With TDD

**Files:**
- Create: `tests/model/test_reentry_probe.py`
- Create: `src/pipeline/reentry_probe.py`

- [ ] **Step 1: Write failing path-metric tests**

Add `tests/model/test_reentry_probe.py`:

```python
import datetime as dt
import unittest

from src.pipeline import reentry_probe as p


class TestReentryProbe(unittest.TestCase):
    def test_parse_time_accepts_live_local_datetime_and_epoch(self):
        parsed = p.parse_time("2026-05-19 04:11:18.755211")
        self.assertEqual(parsed, dt.datetime(2026, 5, 19, 4, 11, 18, 755211))
        self.assertEqual(p.parse_time(1779135078), dt.datetime.fromtimestamp(1779135078))

    def test_path_metrics_reports_barrier_order_from_anchor_price(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        path = [
            p.PricePoint(anchor, 1.00, "anchor"),
            p.PricePoint(anchor + dt.timedelta(seconds=10), 1.26, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=20), 1.70, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=30), 0.78, "sell"),
        ]

        metrics = p.path_metrics(path, anchor_time=anchor, anchor_price=1.0, horizon_seconds=90)

        self.assertAlmostEqual(metrics["mfe_pct"], 70.0)
        self.assertAlmostEqual(metrics["mae_pct"], -22.0)
        self.assertEqual(metrics["time_to_plus_25_seconds"], 10.0)
        self.assertEqual(metrics["time_to_plus_60_seconds"], 20.0)
        self.assertEqual(metrics["time_to_minus_18_seconds"], 30.0)
        self.assertEqual(metrics["first_barrier"], "+25")

    def test_path_metrics_marks_collapse_before_reclaim(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        path = [
            p.PricePoint(anchor, 1.00, "anchor"),
            p.PricePoint(anchor + dt.timedelta(seconds=4), 0.80, "sell"),
            p.PricePoint(anchor + dt.timedelta(seconds=12), 1.30, "buy"),
        ]

        metrics = p.path_metrics(path, anchor_time=anchor, anchor_price=1.0, horizon_seconds=90)

        self.assertEqual(metrics["time_to_minus_18_seconds"], 4.0)
        self.assertEqual(metrics["time_to_plus_25_seconds"], 12.0)
        self.assertEqual(metrics["first_barrier"], "-18")
```

- [ ] **Step 2: Run test and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe.TestReentryProbe.test_parse_time_accepts_live_local_datetime_and_epoch tests.model.test_reentry_probe.TestReentryProbe.test_path_metrics_reports_barrier_order_from_anchor_price tests.model.test_reentry_probe.TestReentryProbe.test_path_metrics_marks_collapse_before_reclaim
```

Expected: FAIL because `src.pipeline.reentry_probe` does not exist.

- [ ] **Step 3: Implement minimal helpers**

Create `src/pipeline/reentry_probe.py` with:

- `PricePoint` dataclass.
- `parse_time(value) -> datetime`.
- `normalize_token(value) -> str`.
- `path_metrics(path, anchor_time, anchor_price, horizon_seconds=900) -> dict`.

The metric helper must report MFE/MAE percent, first-hit seconds for `+25`, `+60`, `-18`, and `-25`, and `first_barrier` from chronological barrier hits.

- [ ] **Step 4: Run tests and verify GREEN**

Run the same targeted unittest command. Expected: OK.

## Task 2: Add Live Artifact Parsers And Candidate Construction

**Files:**
- Modify: `tests/model/test_reentry_probe.py`
- Modify: `src/pipeline/reentry_probe.py`

- [ ] **Step 1: Write failing parser tests**

Add tests that cover the current live formats:

```python
    def test_signal_decision_parser_uses_action_and_time_fields(self):
        row = {
            "action": "SIGNAL_DECISION",
            "time": "2026-05-19 04:11:18.755211",
            "token": "0xABC",
            "symbol": "SZN",
            "decision": "rejected",
            "reason": "pred_return_below_min",
            "prob": 0.989,
            "pred_return": 25.04,
            "volume_30s": 3.5,
            "price_volatility": 0.32,
        }

        parsed = list(p.iter_signal_decisions([row]))

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["token"], "0xabc")
        self.assertEqual(parsed[0]["time"], dt.datetime(2026, 5, 19, 4, 11, 18, 755211))
        self.assertEqual(parsed[0]["reason"], "pred_return_below_min")

    def test_pair_live_trades_matches_open_and_close_by_token_order(self):
        rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-18 20:21:15", "entry_price": 1.0, "symbol": "A"},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-18 20:21:40", "exit_price": 0.75, "reason": "STOP_LOSS", "symbol": "A"},
        ]

        pairs = list(p.pair_live_trades(rows))

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["token"], "0xa")
        self.assertEqual(pairs[0]["open"]["entry_price"], 1.0)
        self.assertEqual(pairs[0]["close"]["reason"], "STOP_LOSS")
```

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe.TestReentryProbe.test_signal_decision_parser_uses_action_and_time_fields tests.model.test_reentry_probe.TestReentryProbe.test_pair_live_trades_matches_open_and_close_by_token_order
```

Expected: FAIL because parser functions do not exist.

- [ ] **Step 3: Implement minimal parsers**

Implement:

- `iter_jsonl(path) -> iterator[dict]`.
- `iter_signal_decisions(rows) -> iterator[dict]`, using `action == "SIGNAL_DECISION"` and local `time`.
- `pair_live_trades(rows) -> iterator[dict]`, matching OPEN/CLOSE in chronological order by normalized token. Ignore unmatched rows but count them in report-level diagnostics later.

- [ ] **Step 4: Run tests and verify GREEN**

Run the targeted tests. Expected: OK.

## Task 3: Add Lifecycle Price Path Loading And Scoring

**Files:**
- Modify: `tests/model/test_reentry_probe.py`
- Modify: `src/pipeline/reentry_probe.py`

- [ ] **Step 1: Write failing lifecycle/scoring tests**

Add tests:

```python
    def test_lifecycle_price_path_reads_active_runtime_state(self):
        state = {
            "active_lifecycles": [
                {
                    "token_address": "0xABC",
                    "symbol": "SZN",
                    "price_history": [
                        {"timestamp": 1779135078, "price": 1.0, "type": "buy"},
                        {"timestamp": 1779135088, "price": 1.3, "type": "buy"},
                    ],
                }
            ]
        }

        lifecycles = p.extract_lifecycles_from_runtime_state(state)
        path = p.price_path_for_token(lifecycles, "0xabc")

        self.assertEqual(len(path), 2)
        self.assertEqual(path[0].price, 1.0)

    def test_score_stoploss_reentry_requires_reclaim_before_collapse(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        close_pair = {
            "token": "0xabc",
            "symbol": "A",
            "close": {"time": anchor, "exit_price": 1.0, "reason": "STOP_LOSS"},
        }
        path = [
            p.PricePoint(anchor, 1.0, "exit"),
            p.PricePoint(anchor + dt.timedelta(seconds=20), 1.28, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=80), 1.70, "buy"),
        ]

        scored = p.score_stoploss_reentry_candidate(close_pair, path)

        self.assertTrue(scored["accepted_by_probe"])
        self.assertEqual(scored["time_to_plus_25_seconds"], 20.0)
        self.assertEqual(scored["first_barrier"], "+25")
```

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe.TestReentryProbe.test_lifecycle_price_path_reads_active_runtime_state tests.model.test_reentry_probe.TestReentryProbe.test_score_stoploss_reentry_requires_reclaim_before_collapse
```

Expected: FAIL because lifecycle/scoring functions do not exist.

- [ ] **Step 3: Implement minimal scoring**

Implement:

- `extract_lifecycles_from_runtime_state(state) -> dict[str, dict]`.
- `price_path_from_lifecycle(lifecycle) -> list[PricePoint]`.
- `price_path_for_token(lifecycles, token) -> list[PricePoint]`.
- `score_stoploss_reentry_candidate(pair, path, reclaim_pct=25.0, collapse_pct=-18.0, horizon_seconds=300) -> dict`.

The first version should only accept STOP_LOSS candidates when `+25` is reached before `-18` within the horizon.

- [ ] **Step 4: Run tests and verify GREEN**

Run the targeted tests. Expected: OK.

## Task 4: Add CLI Report

**Files:**
- Create: `scripts/probe_reentry_retention.py`
- Modify: `tests/model/test_reentry_probe.py`

- [ ] **Step 1: Write failing CLI smoke test**

Add a smoke test that calls a `build_probe_report(...)` helper directly with synthetic rows and asserts a stable JSON-serializable report:

```python
    def test_build_probe_report_is_json_serializable(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        trade_rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-18 20:21:15", "entry_price": 1.2, "symbol": "A"},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-18 20:21:40", "exit_price": 1.0, "reason": "STOP_LOSS", "symbol": "A"},
        ]
        signal_rows = []
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "symbol": "A",
                "price_history": [
                    {"timestamp": anchor.timestamp(), "price": 1.0, "type": "exit"},
                    {"timestamp": (anchor + dt.timedelta(seconds=20)).timestamp(), "price": 1.3, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(trade_rows=trade_rows, signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertEqual(report["candidate_counts"]["stoploss_reentry"], 1)
        self.assertEqual(report["candidate_counts"]["accepted_stoploss_reentry"], 1)
        p.to_json_text(report)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe.TestReentryProbe.test_build_probe_report_is_json_serializable
```

Expected: FAIL because `build_probe_report` and `to_json_text` do not exist.

- [ ] **Step 3: Implement report helper and CLI**

Implement in `src/pipeline/reentry_probe.py`:

- `build_probe_report(trade_rows, signal_rows, lifecycles, generated_at=None) -> dict`.
- `to_json_text(report) -> str`.

Create `scripts/probe_reentry_retention.py` with options:

- `--paper-trades data/paper_trades.jsonl`
- `--signal-audit data/signal_audit.jsonl`
- `--collector-state data/training/collector_runtime_state.json`
- `--output data/replay_reports/reentry_retention_probe_<timestamp>.json`

The CLI should load files, build the report, write JSON, and print the output path plus accepted candidate counts.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe
```

Expected: OK.

## Task 5: Run The Probe On Current Live Data

**Files:**
- Output only: `data/replay_reports/reentry_retention_probe_*.json`

- [ ] **Step 1: Run current live probe**

Run:

```bash
venv/bin/python scripts/probe_reentry_retention.py
```

Expected: Writes a JSON report and prints candidate counts.

- [ ] **Step 2: Inspect results**

Review:

- Accepted STOP_LOSS re-entry count.
- Rejected collapse controls.
- Whether `币安小子`, `何赵`, `WAGMI`, `BISMILLAH`, and `SZN` are classified consistently with live attribution.
- Whether accepted candidates depend on one or two outliers.

- [ ] **Step 3: Update research or scoreboard**

If the probe supports the direction, update `docs/model_scoreboard.md` or the current research summary with the evidence. If it rejects the direction, record the rejection so it is not retried blindly.

## Task 6: Verification, Strict Reviews, Commit, Push

**Files:**
- Review all changed source, tests, scripts, and docs.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_reentry_probe
```

- [ ] **Step 2: Run related regression tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_run_hybrid_training_cli tests.model.test_dataset_builder_is_moon_target
```

- [ ] **Step 3: Run syntax and diff checks**

Run:

```bash
venv/bin/python -m compileall src/pipeline/reentry_probe.py scripts/probe_reentry_retention.py
git diff --check
```

- [ ] **Step 4: Strict code review pass 1**

Parent-agent review of the full diff:

- Correctness of timestamp parsing and token normalization.
- No writes to live config, state, model manifests, or lifecycle data.
- No replay/live mismatch claim beyond the probe's evidence.
- No data leakage if the output is later used for training.
- Pull-and-run defaults are safe.

- [ ] **Step 5: Strict code review pass 2**

Independent subagent or fresh-pass review:

- Parser edge cases.
- Missing tests.
- JSON report stability.
- Failure behavior for missing files or missing lifecycle paths.
- Whether the report could accidentally be mistaken for accepted live-switch evidence.

- [ ] **Step 6: Commit and push**

Only after tests and two clean reviews:

```bash
git status --short
git add docs/research/20260519-stoploss-reentry-runner-retention docs/superpowers/plans/2026-05-19-stoploss-reentry-runner-retention-probe.md src/pipeline/reentry_probe.py scripts/probe_reentry_retention.py tests/model/test_reentry_probe.py
git commit -m "feat: add reentry retention probe"
git push
```

No live switch is allowed from this plan alone.

