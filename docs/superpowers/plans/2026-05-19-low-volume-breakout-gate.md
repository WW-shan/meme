# Low Volume Breakout Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only probe that tests whether live v95 `entry_volume_30s_below_min` rejects contain a separable low-volume runner/fakeout pocket before any replay or live config change.

**Architecture:** Keep live trading untouched. Add a pure `src.pipeline` module for scoring low-volume rejected signals against lifecycle price paths, then add a thin CLI that snapshots mutable live inputs once and writes a reproducible JSON report. Update docs only after the report exists.

**Tech Stack:** Python `unittest`, existing `src.pipeline.reentry_probe` lifecycle/path helpers, JSONL inputs, `scripts/` CLI pattern.

---

## File Structure

- Create `src/pipeline/low_volume_breakout_probe.py`
  - Pure scoring/report code.
  - Imports `src.pipeline.reentry_probe`.
  - No file I/O except JSON serialization helper.
- Create `scripts/probe_low_volume_breakout.py`
  - CLI and snapshot fingerprint logic.
  - Reads each mutable input once into bytes before parsing.
  - Writes `data/replay_reports/low_volume_breakout_probe_<timestamp>.json` unless `--output` is supplied.
- Create `tests/model/test_low_volume_breakout_probe.py`
  - Unit tests for scoring, filtering, dedupe, class counts, and JSON serialization.
- Create `tests/model/test_low_volume_breakout_probe_cli.py`
  - CLI tests for defaults, single-read fingerprints, and fake-module wiring.
- Modify `docs/model_scoreboard.md`
  - Add a note only after running the real probe report.
- Add `data/replay_reports/low_volume_breakout_probe_20260519_v95.json`
  - Commit the report as evidence if the run succeeds and contains no secrets.

## Task 1: Pure Probe Module

**Files:**
- Create: `src/pipeline/low_volume_breakout_probe.py`
- Test: `tests/model/test_low_volume_breakout_probe.py`

- [x] **Step 1: Write failing tests**

Add `tests/model/test_low_volume_breakout_probe.py`:

```python
import datetime as dt
import json
import unittest

from src.pipeline import low_volume_breakout_probe as p
from src.pipeline import reentry_probe


class TestLowVolumeBreakoutProbe(unittest.TestCase):
    def _signal(self, token, symbol, anchor, **overrides):
        row = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": token,
            "symbol": symbol,
            "time": anchor.isoformat(sep=" "),
            "prob": 0.985,
            "pred_return": 4.0,
            "reason": "entry_volume_30s_below_min",
            "volume_30s": 1.1,
            "price_volatility": 0.09,
            "token_age_seconds": 10.0,
        }
        row.update(overrides)
        return row

    def test_score_marks_clean_low_volume_runner(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xA", "RUN", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.30, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=50), 1.65, "buy"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_runner")
        self.assertEqual(scored["recommended_policy"], "conditional_rescue_probe")
        self.assertEqual(scored["first_barrier"], "+25")
        self.assertEqual(scored["time_to_plus_60_seconds"], 50.0)

    def test_score_marks_low_volume_fakeout_when_stop_hits_first(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xB", "FAKE", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 0.80, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 1.28, "buy"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_fakeout")
        self.assertEqual(scored["recommended_policy"], "skip")
        self.assertEqual(scored["first_barrier"], "-18")

    def test_score_marks_fast_profit_then_stop(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xC", "SPIKE", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=40), 1.27, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=110), 0.78, "sell"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_fast_profit_then_stop")
        self.assertEqual(scored["recommended_policy"], "quick_take_profit_probe")

    def test_build_probe_report_filters_low_volume_rejects_and_deduplicates_by_token(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal_rows = [
            self._signal("0xA", "RUN", anchor, prob=0.981, pred_return=1.0),
            self._signal("0xA", "RUN", anchor + dt.timedelta(seconds=2), prob=0.990, pred_return=2.0),
            self._signal("0xB", "BAD_REASON", anchor, reason="pred_return_below_min"),
            self._signal("0xC", "LOW_PROB", anchor, prob=0.970),
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": (anchor - dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=20)).timestamp(), "price": 1.4, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, since=anchor)

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["candidate_counts"]["raw_rejected_signal_decisions"], 4)
        self.assertEqual(report["candidate_counts"]["filtered_low_volume_signal_decisions"], 2)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 1)
        self.assertEqual(report["candidate_counts"]["dropped_duplicate_low_volume_signals"], 1)
        self.assertEqual(report["class_counts"]["low_volume_runner"], 1)
        self.assertEqual(report["candidate_sample"][0]["prob"], 0.99)
        json.loads(p.to_json_text(report))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe
```

Expected: import failure because `src.pipeline.low_volume_breakout_probe` does not exist.

- [x] **Step 3: Implement minimal module**

Implement these public functions:

```python
score_low_volume_signal(signal, path, *, horizon_seconds=600, quick_profit_seconds=120)
build_probe_report(signal_rows, lifecycles, generated_at=None, since=None, min_prob=0.98, min_volume_30s=0.75, max_volume_30s=1.5, min_price_volatility=0.05, max_token_age_seconds=60, horizon_seconds=600, quick_profit_seconds=120)
to_json_text(report)
```

Required behavior:
- Only candidate rows with `action=SIGNAL_DECISION`, `decision=rejected`, `reason=entry_volume_30s_below_min`.
- Filter by `prob`, `volume_30s`, `price_volatility`, and `token_age_seconds`.
- Deduplicate by token using highest `(prob, pred_return, time)`.
- Label classes:
  - `missing_path`
  - `low_volume_fakeout` when first barrier is `-18` or `-25`
  - `low_volume_runner` when `+60` or `+25` hits before stop and no stop follows inside the horizon
  - `low_volume_fast_profit_then_stop` when `+25` hits before a later stop
  - `low_volume_flat` otherwise
- Add `probe_contract.live_switch_evidence=false`.

- [x] **Step 4: Run tests and verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe
```

Expected: `OK`.

## Task 2: CLI Snapshot Runner

**Files:**
- Create: `scripts/probe_low_volume_breakout.py`
- Test: `tests/model/test_low_volume_breakout_probe_cli.py`

- [x] **Step 1: Write failing CLI tests**

Use the `tests/model/test_time_to_barrier_probe_cli.py` pattern. Required assertions:
- default `--signal-audit`, `--collector-state`, `--lifecycle-dir`, `--recent-lifecycle-files`, `--since`, `--min-prob`, `--min-volume-30s`, `--max-volume-30s`, `--min-price-volatility`, `--max-token-age-seconds`.
- `_read_path_snapshot()` returns the exact bytes that are hashed.
- `_input_fingerprint_policy()` records `snapshot_read_mode=single_read_bytes`.
- `main()` passes parsed rows, merged lifecycles, and filter parameters to `src.pipeline.low_volume_breakout_probe.build_probe_report()`.

- [x] **Step 2: Run tests and verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe_cli
```

Expected: import/path failure because the CLI does not exist.

- [x] **Step 3: Implement CLI**

Use `scripts/probe_time_to_barrier.py` as the local pattern. The CLI must:
- prepend repo root to `sys.path`;
- read mutable inputs once into bytes;
- include SHA-256 fingerprints;
- include `changed_during_read`;
- parse JSONL from the same bytes used for fingerprints;
- write output JSON with `probe.to_json_text(report)`;
- print `wrote <path>` and `per_token_candidates=<n>`.

- [x] **Step 4: Run tests and verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe_cli
```

Expected: `OK`.

## Task 3: Real Report and Docs

**Files:**
- Add: `data/replay_reports/low_volume_breakout_probe_20260519_v95.json`
- Modify: `docs/model_scoreboard.md`

- [x] **Step 1: Run focused test suite**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe tests.model.test_low_volume_breakout_probe_cli tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli tests.model.test_reentry_probe
```

Expected: `OK`.

- [x] **Step 2: Run real probe**

Run:

```bash
venv/bin/python scripts/probe_low_volume_breakout.py \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --lifecycle-file data/training/lifecycle_20260519_114017.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212852.jsonl \
  --recent-lifecycle-files 0 \
  --since "2026-05-19 04:02:23" \
  --min-prob 0.98 \
  --min-volume-30s 0.75 \
  --max-volume-30s 1.5 \
  --min-price-volatility 0.05 \
  --max-token-age-seconds 60 \
  --output data/replay_reports/low_volume_breakout_probe_20260519_v95.json
```

Expected: writes a read-only report and prints nonzero `per_token_candidates`.

- [x] **Step 3: Update scoreboard note**

Append a `2026-05-19 low-volume breakout/fakeout probe` note under `docs/model_scoreboard.md` Notes with:
- report path;
- candidate counts and class counts;
- accept/reject decision;
- statement that this is not live-switch evidence;
- next step if promising.

- [x] **Step 4: Run syntax and focused verification**

Run:

```bash
venv/bin/python -m py_compile src/pipeline/low_volume_breakout_probe.py scripts/probe_low_volume_breakout.py
venv/bin/python -m unittest tests.model.test_low_volume_breakout_probe tests.model.test_low_volume_breakout_probe_cli
```

Expected: `OK`.

## Task 4: Reviews, Commit, Push

**Files:**
- All files touched by Tasks 1-3.

- [x] **Step 1: Secret scan**

Run:

```bash
rg -n "sk-[A-Za-z0-9]|tvly|ctx7|api[_-]?key|secret|PRIVATE|BEGIN .*KEY" docs/research/20260519-low-volume-breakout-gate data/replay_reports/low_volume_breakout_probe_20260519_v95.json
```

Expected: no actual secrets. If only field names appear, inspect and confirm values are redacted/unconfigured.

- [ ] **Step 2: Strict review pass 1**

Request a reviewer to inspect the full final diff for:
- live safety;
- no bot/collector control changes;
- 10% risk policy preserved;
- mutable input fingerprint correctness;
- report/doc consistency;
- no unsupported research claims.

- [ ] **Step 3: Strict review pass 2**

Request a separate reviewer to inspect the final diff for:
- TDD coverage;
- edge cases in filtering and barrier classification;
- CLI input snapshot correctness;
- scoreboard and research artifacts matching report values.

- [ ] **Step 4: Commit and push after both reviews are clean**

Run:

```bash
git status -sb
git add src/pipeline/low_volume_breakout_probe.py scripts/probe_low_volume_breakout.py tests/model/test_low_volume_breakout_probe.py tests/model/test_low_volume_breakout_probe_cli.py docs/research/20260519-low-volume-breakout-gate docs/superpowers/plans/2026-05-19-low-volume-breakout-gate.md docs/model_scoreboard.md
git add -f data/replay_reports/low_volume_breakout_probe_20260519_v95.json
git commit -m "Add low-volume breakout probe"
git push origin main
```

Expected: commit and push succeed. If any material edit happens after review, rerun two strict reviews before committing.
