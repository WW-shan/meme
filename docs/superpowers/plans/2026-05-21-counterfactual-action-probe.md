# Counterfactual Action Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only action-level probe that combines rejected-signal time-to-barrier evidence and accepted-trade post-target evidence into one counterfactual action report, so the next replay experiment can be selected without repeating static rescue or blanket exit failures.

**Architecture:** Add a small pure module under `src/pipeline/` that classifies already-scored probe candidates into actions: `skip`, `rescue_quick_tp`, `conditional_slow_hold`, `post_target_lock`, `continue_hold`, and `monitor_after_target`. Add a thin CLI that reads existing JSON reports, writes a protected report under `data/replay_reports`, and never modifies live bot state, `.env`, model artifacts, or goal docs.

**Tech Stack:** Python stdlib, existing `src.pipeline.time_to_barrier_probe`, existing `src.pipeline.post_target_exit_state_probe`, `unittest`.

---

### Task 1: Pure Action Probe Module

**Files:**
- Create: `src/pipeline/counterfactual_action_probe.py`
- Test: `tests/model/test_counterfactual_action_probe.py`

- [ ] **Step 1: Write failing tests**

Create `tests/model/test_counterfactual_action_probe.py` with these tests:

```python
import datetime as dt
import json
import unittest

from src.pipeline import counterfactual_action_probe as p


class TestCounterfactualActionProbe(unittest.TestCase):
    def test_classifies_rejected_fast_profit_as_rescue_quick_tp_only_when_quality_gate_passes(self):
        candidate = {
            "token": "0xA",
            "symbol": "Arnold",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "fast_profit",
            "recommended_policy": "quick_take_profit",
            "reason": "pred_return_below_min",
            "prob": 0.9879,
            "pred_return": 32.17,
            "mfe_pct": 334.6,
            "mae_pct": -9.7,
            "time_to_plus_25_seconds": 56.9,
            "time_to_minus_18_seconds": None,
        }

        result = p.classify_time_to_barrier_action(candidate)

        self.assertEqual(result["action"], "rescue_quick_tp")
        self.assertEqual(result["evidence_class"], "fast_profit")
        self.assertTrue(result["eligible"])
        self.assertEqual(result["risk_policy"], "quick_take_profit_only")

    def test_keeps_high_mfe_stop_first_or_negative_score_as_skip(self):
        stop_first = {
            "token": "0xB",
            "symbol": "MEMES",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "stop_first",
            "recommended_policy": "skip",
            "prob": 0.987,
            "pred_return": -34.0,
            "mfe_pct": 89.0,
            "mae_pct": -23.0,
            "time_to_plus_25_seconds": 10.8,
            "time_to_minus_18_seconds": 1.8,
        }

        result = p.classify_time_to_barrier_action(stop_first)

        self.assertEqual(result["action"], "skip")
        self.assertFalse(result["eligible"])
        self.assertIn("stop_first", result["reject_reasons"])

    def test_classifies_post_target_collapse_as_lock_and_continuation_as_hold(self):
        collapse = {
            "token": "0xC",
            "symbol": "CMC",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "post_target_collapse",
            "recommended_policy": "lock_profit",
            "target_hit": True,
            "time_to_target_seconds": 225.0,
            "time_to_post_target_collapse_seconds": 260.0,
        }
        continuation = {
            "token": "0xD",
            "symbol": "RUN",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "post_target_continuation",
            "recommended_policy": "continue_hold",
            "target_hit": True,
            "time_to_target_seconds": 30.0,
            "time_to_continuation_seconds": 55.0,
        }

        self.assertEqual(p.classify_post_target_action(collapse)["action"], "post_target_lock")
        self.assertEqual(p.classify_post_target_action(continuation)["action"], "continue_hold")

    def test_build_action_report_counts_sources_actions_and_keeps_read_only_contract(self):
        report = p.build_action_report(
            time_to_barrier_report={
                "probe_contract": {"read_only": True, "live_switch_evidence": False},
                "candidate_sample": [
                    {
                        "token": "0xA",
                        "symbol": "Arnold",
                        "candidate_type": "rejected_signal_time_to_barrier",
                        "barrier_class": "fast_profit",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.9879,
                        "pred_return": 32.17,
                        "mfe_pct": 334.6,
                        "mae_pct": -9.7,
                        "time_to_plus_25_seconds": 56.9,
                    },
                    {
                        "token": "0xB",
                        "symbol": "MEMES",
                        "candidate_type": "rejected_signal_time_to_barrier",
                        "barrier_class": "stop_first",
                        "recommended_policy": "skip",
                        "prob": 0.987,
                        "pred_return": -34.0,
                        "mfe_pct": 89.0,
                        "mae_pct": -23.0,
                    },
                ],
            },
            post_target_report={
                "probe_contract": {"read_only": True, "live_switch_evidence": False},
                "candidate_sample": [
                    {
                        "token": "0xC",
                        "symbol": "CMC",
                        "candidate_type": "accepted_trade_post_target_exit_state",
                        "classification": "post_target_collapse",
                        "recommended_policy": "lock_profit",
                        "target_hit": True,
                    }
                ],
            },
            generated_at=dt.datetime(2026, 5, 21, 7, 0, 0),
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertEqual(report["source_counts"]["time_to_barrier_candidates"], 2)
        self.assertEqual(report["source_counts"]["post_target_candidates"], 1)
        self.assertEqual(report["action_counts"]["rescue_quick_tp"], 1)
        self.assertEqual(report["action_counts"]["skip"], 1)
        self.assertEqual(report["action_counts"]["post_target_lock"], 1)
        self.assertEqual(report["decision"], "probe_only_replay_required")
        json.loads(p.to_json_text(report))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_counterfactual_action_probe
```

Expected: import failure for missing `counterfactual_action_probe`.

- [ ] **Step 3: Implement minimal module**

Create `src/pipeline/counterfactual_action_probe.py`:

```python
from __future__ import annotations

import datetime as dt
import json
from collections import Counter
from typing import Any, Mapping

MIN_RESCUE_PROB = 0.985
MIN_RESCUE_PRED_RETURN = 30.0
MAX_RESCUE_MAE_PCT = -18.0


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: dict[str, Any]) -> str:
    return json.dumps(report, default=_json_default, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else default


def classify_time_to_barrier_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    barrier_class = str(candidate.get("barrier_class") or "")
    prob = _safe_float(candidate.get("prob"))
    pred_return = _safe_float(candidate.get("pred_return"))
    mae_pct = _safe_float(candidate.get("mae_pct"), default=0.0)
    reject_reasons: list[str] = []
    if barrier_class == "stop_first":
        reject_reasons.append("stop_first")
    if barrier_class not in {"fast_profit", "fast_profit_then_collapse"}:
        reject_reasons.append("not_fast_profit")
    if prob < MIN_RESCUE_PROB:
        reject_reasons.append("prob_below_rescue_min")
    if pred_return < MIN_RESCUE_PRED_RETURN:
        reject_reasons.append("pred_return_below_rescue_min")
    if mae_pct <= MAX_RESCUE_MAE_PCT:
        reject_reasons.append("mae_breached_stop")
    eligible = not reject_reasons
    return {
        "token": candidate.get("token"),
        "symbol": candidate.get("symbol"),
        "source": "time_to_barrier",
        "evidence_class": barrier_class,
        "action": "conditional_slow_hold" if eligible and barrier_class == "slow_runner" else ("rescue_quick_tp" if eligible else "skip"),
        "eligible": eligible,
        "risk_policy": "conditional_hold_probe_only" if eligible and barrier_class == "slow_runner" else ("quick_take_profit_only" if eligible else "no_trade"),
        "reject_reasons": reject_reasons,
        "prob": candidate.get("prob"),
        "pred_return": candidate.get("pred_return"),
        "mfe_pct": candidate.get("mfe_pct"),
        "mae_pct": candidate.get("mae_pct"),
        "time_to_plus_25_seconds": candidate.get("time_to_plus_25_seconds"),
    }


def classify_post_target_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    classification = str(candidate.get("classification") or "")
    action = "monitor_after_target"
    if classification == "post_target_collapse":
        action = "post_target_lock"
    elif classification == "post_target_continuation":
        action = "continue_hold"
    elif classification == "target_not_hit":
        action = "monitor_after_target"
    return {
        "token": candidate.get("token"),
        "symbol": candidate.get("symbol"),
        "source": "post_target",
        "evidence_class": classification,
        "action": action,
        "eligible": action in {"post_target_lock", "continue_hold"},
        "risk_policy": "post_target_decision_only",
        "target_hit": candidate.get("target_hit"),
        "time_to_target_seconds": candidate.get("time_to_target_seconds"),
        "time_to_post_target_collapse_seconds": candidate.get("time_to_post_target_collapse_seconds"),
        "time_to_continuation_seconds": candidate.get("time_to_continuation_seconds"),
    }


def _candidate_list(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = report.get("candidate_sample") or report.get("candidates") or []
    return [row for row in rows if isinstance(row, Mapping)]


def build_action_report(
    *,
    time_to_barrier_report: Mapping[str, Any],
    post_target_report: Mapping[str, Any],
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    time_rows = _candidate_list(time_to_barrier_report)
    post_rows = _candidate_list(post_target_report)
    actions = [classify_time_to_barrier_action(row) for row in time_rows]
    actions.extend(classify_post_target_action(row) for row in post_rows)
    action_counts = Counter(row["action"] for row in actions)
    source_counts = Counter(row["source"] for row in actions)
    return {
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
        },
        "parameters": {
            "min_rescue_prob": MIN_RESCUE_PROB,
            "min_rescue_pred_return": MIN_RESCUE_PRED_RETURN,
            "max_rescue_mae_pct": MAX_RESCUE_MAE_PCT,
            "position_fraction": 0.10,
            "max_open_positions": 8,
        },
        "source_counts": {
            "time_to_barrier_candidates": len(time_rows),
            "post_target_candidates": len(post_rows),
            **dict(sorted(source_counts.items())),
        },
        "action_counts": dict(sorted(action_counts.items())),
        "decision": "probe_only_replay_required",
        "actions": actions[:200],
    }
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_counterfactual_action_probe
```

Expected: `OK`.

### Task 2: CLI For Combining Probe Reports

**Files:**
- Create: `scripts/probe_counterfactual_action_policy.py`
- Test: `tests/model/test_counterfactual_action_probe_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/model/test_counterfactual_action_probe_cli.py` with subprocess tests that create two small JSON reports in a temporary directory, run the CLI, assert `action_candidates=3`, and assert output path is under `data/replay_reports`. Also test refusing protected outputs such as `.env` and `docs/goals/live-model-optimization-goal.md`.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_counterfactual_action_probe_cli
```

Expected: script missing failure.

- [ ] **Step 3: Implement CLI**

Create `scripts/probe_counterfactual_action_policy.py` that:

- Accepts `--time-to-barrier-report`, `--post-target-report`, `--output`, and `--force`.
- Defaults output to `data/replay_reports/counterfactual_action_probe_<timestamp>.json`.
- Refuses outputs outside `data/replay_reports` and protected paths including `.env`, `.env.example`, and `docs/goals/live-model-optimization-goal.md`.
- Reads both JSON files, calls `src.pipeline.counterfactual_action_probe.build_action_report`, writes JSON via `to_json_text`.
- Prints `wrote <path>` and `action_candidates=<n>`.

- [ ] **Step 4: Run CLI tests to verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_counterfactual_action_probe_cli
```

Expected: `OK`.

### Task 3: Run Live-Evidence Probe And Record Decision

**Files:**
- Create/overwrite with `--force`: `data/replay_reports/counterfactual_action_probe_20260521_post_cmc_live.json`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run the probe using latest reports**

Run:

```bash
venv/bin/python scripts/probe_counterfactual_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260521_post_cmc_live_latest.json \
  --post-target-report data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json \
  --output data/replay_reports/counterfactual_action_probe_20260521_post_cmc_live.json \
  --force
```

Expected: output file written, no bot/process changes.

- [ ] **Step 2: Summarize the report into scoreboard**

Append a dated bullet to `docs/model_scoreboard.md` stating that this is `probe_only`, `live_switch_evidence=false`, and whether the action buckets are sufficient for a replay-integrated follow-up. Do not recommend live switch from this report.

### Task 4: Verification, Reviews, Commit, Push

**Files:** all changed files from Tasks 1-3.

- [ ] **Step 1: Run focused verification**

Run:

```bash
venv/bin/python -m unittest tests.model.test_counterfactual_action_probe tests.model.test_counterfactual_action_probe_cli tests.model.test_time_to_barrier_probe tests.model.test_post_target_exit_state_probe
venv/bin/python -m py_compile src/pipeline/counterfactual_action_probe.py scripts/probe_counterfactual_action_policy.py
```

Expected: all pass.

- [ ] **Step 2: Run safety diffs**

Run:

```bash
git diff -- docs/goals/live-model-optimization-goal.md .env .env.example config src/trader
git diff --check
```

Expected: no output from the protected diff and no whitespace errors.

- [ ] **Step 3: Request two strict code reviews**

Dispatch two independent reviewer subagents after the final code edit. They must verify:

- No live bot, `.env`, or goal-doc changes.
- Output path protection works.
- Probe is read-only and not live-switch evidence.
- Action classification does not repeat rejected static global lowering.
- Tests cover core behavior and CLI protection.

- [ ] **Step 4: Commit and push important node**

If verification and both reviews pass, commit and push:

```bash
git add src/pipeline/counterfactual_action_probe.py scripts/probe_counterfactual_action_policy.py tests/model/test_counterfactual_action_probe.py tests/model/test_counterfactual_action_probe_cli.py docs/research/20260521-live-counterfactual-policy-selection docs/superpowers/plans/2026-05-21-counterfactual-action-probe.md docs/model_scoreboard.md
git add -f data/replay_reports/time_to_barrier_probe_20260521_post_cmc_live_latest.json data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json data/replay_reports/counterfactual_action_probe_20260521_post_cmc_live.json
git commit -m "test: add counterfactual action probe"
git push
```

---

## Self-Review

- Spec coverage: The plan starts from live evidence, uses historical failed directions, records SmartSearch research, creates a probe-only experiment, keeps 10% sizing/max 8, and forbids live switch without strict replay.
- Placeholder scan: No TBD/TODO placeholders remain; Task 2 gives behavioral details instead of full code because it is a thin CLI matching existing script patterns.
- Type consistency: Public functions are `classify_time_to_barrier_action`, `classify_post_target_action`, `build_action_report`, and `to_json_text`; CLI uses those names.
