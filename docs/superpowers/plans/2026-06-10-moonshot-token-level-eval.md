# Moonshot Token-Level Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully offline token-level evaluation probe for the local Four.meme `>=10x` moonshot proxy.

**Architecture:** Reuse the existing Phase 0/1 label and snapshot builders, add a small token-level evaluation module that reconciles duplicate local lifecycle labels, collapses fixed checkpoint snapshots to one candidate per token, and evaluates a group-disjoint time split. Add a read-only CLI and tests; do not touch live runtime or model promotion paths.

**Tech Stack:** Python standard library, `unittest`, existing `src.pipeline.moonshot_label_truth`, `src.pipeline.moonshot_feature_snapshot`, and `src.pipeline.moonshot_local_runner_baseline`.

---

## File Structure

- Create `src/pipeline/moonshot_token_level_eval.py`: pure functions for local label candidate grouping, dedupe policy selection, token-level snapshot collapse, group-disjoint time split, and metrics.
- Create `scripts/probe_moonshot_token_level_eval.py`: CLI wrapper with output-root guard and deterministic JSON report writer.
- Create `tests/model/test_moonshot_token_level_eval.py`: unit tests for dedupe, collapse, split, metrics, and leakage checks.
- Create `tests/model/test_moonshot_token_level_eval_cli.py`: CLI contract tests for output guard and deterministic smoke report.
- Create `docs/research/20260610-moonshot-token-level-eval/summary.md`: implementation closeout after the probe is run.
- Create `data/replay_reports/moonshot_token_level_eval_20260610.json`: generated offline report.

## Task 1: Token-Level Eval Unit Tests

**Files:**
- Create: `tests/model/test_moonshot_token_level_eval.py`
- Create later: `src/pipeline/moonshot_token_level_eval.py`

- [ ] **Step 1: Write failing tests for dedupe policies**

```python
import unittest

from src.pipeline import moonshot_token_level_eval as token_eval


class TestMoonshotTokenLevelEval(unittest.TestCase):
    def _label(self, token, multiple, event_count, launch_time=1000):
        return {
            "chain": "bsc",
            "token_address": token.lower(),
            "launch_time": launch_time,
            "first_observed_price": 1.0,
            "max_observed_price": float(multiple),
            "max_multiple": float(multiple),
            "hit_10x": float(multiple) >= 10.0,
            "source": "local_lifecycle",
            "_event_count": int(event_count),
        }

    def test_dedupe_policy_max_events_chooses_most_complete_lifecycle(self):
        rows = [self._label("0xA", 8.0, 2), self._label("0xA", 12.0, 5)]
        selected, summary = token_eval.dedupe_label_rows(rows, policy="max_events")
        self.assertEqual(selected[0]["token_address"], "0xa")
        self.assertEqual(selected[0]["max_multiple"], 12.0)
        self.assertEqual(summary["duplicate_token_count"], 1)
        self.assertEqual(summary["policy"], "max_events")

    def test_dedupe_sensitivity_reports_optimistic_and_conservative_counts(self):
        rows = [self._label("0xA", 8.0, 2), self._label("0xA", 12.0, 5), self._label("0xB", 11.0, 1)]
        summary = token_eval.dedupe_sensitivity(rows)
        self.assertEqual(summary["max_multiple"][">=10x"], 2)
        self.assertEqual(summary["min_multiple"][">=10x"], 1)
        self.assertEqual(summary["max_events"][">=10x"], 2)
```

- [ ] **Step 2: Run tests to verify import failure**

Run: `python -m unittest tests.model.test_moonshot_token_level_eval`

Expected: FAIL with `ImportError` for `moonshot_token_level_eval`.

## Task 2: Implement Core Token-Level Module

**Files:**
- Create: `src/pipeline/moonshot_token_level_eval.py`
- Test: `tests/model/test_moonshot_token_level_eval.py`

- [ ] **Step 1: Add initial module with dedupe logic**

```python
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

from src.pipeline import moonshot_local_runner_baseline as baseline

TOP_K_DEFAULTS = (10, 25, 50, 100)
VALID_DEDUPE_POLICIES = {"max_events", "max_multiple", "min_multiple"}


def _normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def _event_count(row: Dict) -> int:
    try:
        return int(row.get("_event_count", row.get("event_count", 0)) or 0)
    except (TypeError, ValueError):
        return 0


def _launch_time(row: Dict) -> int:
    try:
        return int(float(row.get("launch_time", 0) or 0))
    except (TypeError, ValueError):
        return 0


def _row_sort_key(row: Dict) -> Tuple[str, str, int, float, int]:
    return (
        str(row.get("chain") or "bsc").lower(),
        _normalize_address(row.get("token_address")),
        _launch_time(row),
        _float_value(row.get("max_multiple")),
        _event_count(row),
    )


def _dedupe_key(row: Dict) -> Tuple[str, str]:
    return (str(row.get("chain") or "bsc").lower(), _normalize_address(row.get("token_address")))


def _choose(rows: Sequence[Dict], policy: str) -> Dict:
    if policy == "max_events":
        return sorted(rows, key=lambda row: (_event_count(row), _float_value(row.get("max_multiple")), _launch_time(row)))[-1]
    if policy == "max_multiple":
        return sorted(rows, key=lambda row: (_float_value(row.get("max_multiple")), _event_count(row), _launch_time(row)))[-1]
    if policy == "min_multiple":
        return sorted(rows, key=lambda row: (_float_value(row.get("max_multiple")), -_event_count(row), _launch_time(row)))[0]
    raise ValueError(f"unknown dedupe policy: {policy}")


def dedupe_label_rows(rows: Iterable[Dict], policy: str = "max_events") -> Tuple[List[Dict], Dict]:
    if policy not in VALID_DEDUPE_POLICIES:
        raise ValueError(f"unknown dedupe policy: {policy}")
    groups: Dict[Tuple[str, str], List[Dict]] = {}
    for row in rows or []:
        key = _dedupe_key(row)
        if not key[1]:
            continue
        groups.setdefault(key, []).append(dict(row))
    selected = [_choose(group, policy) for group in groups.values()]
    duplicate_groups = [group for group in groups.values() if len(group) > 1]
    conflicts = [
        group for group in duplicate_groups
        if min(_float_value(row.get("max_multiple")) for row in group) > 0
        and (max(_float_value(row.get("max_multiple")) for row in group) - min(_float_value(row.get("max_multiple")) for row in group))
        / min(_float_value(row.get("max_multiple")) for row in group) > 0.20
    ]
    summary = {
        "policy": policy,
        "input_row_count": sum(len(group) for group in groups.values()),
        "output_token_count": len(selected),
        "duplicate_token_count": len(duplicate_groups),
        "conflict_token_count": len(conflicts),
    }
    return sorted([dict(row) for row in selected], key=_row_sort_key), summary


def dedupe_sensitivity(rows: Iterable[Dict]) -> Dict[str, Dict[str, int]]:
    row_list = [dict(row) for row in rows or []]
    result = {}
    for policy in sorted(VALID_DEDUPE_POLICIES):
        selected, _ = dedupe_label_rows(row_list, policy=policy)
        result[policy] = {
            ">=10x": sum(1 for row in selected if _float_value(row.get("max_multiple")) >= 10.0),
            "token_count": len(selected),
        }
    return result
```

- [ ] **Step 2: Run focused tests**

Run: `python -m unittest tests.model.test_moonshot_token_level_eval`

Expected: PASS for the dedupe tests added in Task 1.

- [ ] **Step 3: Extend tests for token collapse and group-disjoint split**

```python
    def _snapshot(self, token, score, hit, launch_time, snapshot_time):
        return {
            "chain": "bsc",
            "token_address": token.lower(),
            "snapshot_time": snapshot_time,
            "features": {"buy_volume_300s": score, "unique_buyers_300s": score},
            "label": {"hit_10x": bool(hit), "launch_time": launch_time},
            "_score": float(score),
        }

    def test_collapse_snapshots_keeps_one_candidate_per_token(self):
        rows = [self._snapshot("0xA", 1, False, 1000, 1030), self._snapshot("0xA", 5, False, 1000, 1300)]
        collapsed = token_eval.collapse_snapshots_to_tokens(rows, score_key="_score")
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(collapsed[0]["token_address"], "0xa")
        self.assertEqual(collapsed[0]["chosen_snapshot_time"], 1300)

    def test_group_time_split_has_zero_token_overlap(self):
        rows = [self._snapshot(f"0x{i}", i, i == 4, 1000 + i, 1100 + i) for i in range(5)]
        train, validation, split = token_eval.group_time_split(rows, validation_ratio=0.4)
        self.assertEqual(split["token_overlap"], 0)
        self.assertEqual(len(train), 3)
        self.assertEqual(len(validation), 2)
```

- [ ] **Step 4: Implement collapse, split, and metrics in the module**

```python
def _score_row(row: Dict, score_key: str | None = None) -> float:
    if score_key and score_key in row:
        return _float_value(row.get(score_key))
    return _float_value(baseline.score_snapshot(row).get("score"))


def _row_hit_10x(row: Dict) -> bool:
    return bool((row.get("label") or {}).get("hit_10x"))


def collapse_snapshots_to_tokens(rows: Iterable[Dict], *, score_key: str | None = None) -> List[Dict]:
    best: Dict[Tuple[str, str], Dict] = {}
    for row in rows or []:
        key = _dedupe_key(row)
        if not key[1]:
            continue
        score = _score_row(row, score_key=score_key)
        candidate = dict(row)
        candidate["token_score"] = score
        candidate["chosen_snapshot_time"] = candidate.get("snapshot_time")
        existing = best.get(key)
        if existing is None or (score, -int(candidate.get("snapshot_time", 0) or 0)) > (
            _float_value(existing.get("token_score")), -int(existing.get("chosen_snapshot_time", 0) or 0)
        ):
            best[key] = candidate
    return sorted(best.values(), key=lambda row: (_launch_time(row.get("label") or {}), str(row.get("token_address"))))


def group_time_split(rows: Iterable[Dict], validation_ratio: float = 0.2) -> Tuple[List[Dict], List[Dict], Dict]:
    row_list = sorted(list(rows or []), key=lambda row: (_launch_time(row.get("label") or row), str(row.get("token_address"))))
    if not row_list:
        return [], [], {"token_overlap": 0, "train_tokens": 0, "validation_tokens": 0}
    ratio = max(0.0, min(1.0, float(validation_ratio)))
    validation_count = max(1, int(math.ceil(len(row_list) * ratio))) if ratio > 0 else 0
    split_at = max(0, len(row_list) - validation_count)
    train = row_list[:split_at]
    validation = row_list[split_at:]
    train_tokens = {str(row.get("token_address")) for row in train}
    validation_tokens = {str(row.get("token_address")) for row in validation}
    split = {
        "token_overlap": len(train_tokens & validation_tokens),
        "train_tokens": len(train_tokens),
        "validation_tokens": len(validation_tokens),
    }
    return train, validation, split


def evaluate_token_level(rows: Iterable[Dict], top_k_values: Sequence[int] = TOP_K_DEFAULTS) -> Dict:
    token_rows = list(rows or [])
    if not token_rows:
        return {"decision": "invalid_input", "token_count": 0, "positive_count": 0, "metrics": {}}
    positives = sum(1 for row in token_rows if _row_hit_10x(row))
    base_rate = positives / float(len(token_rows)) if token_rows else 0.0
    train, validation, split = group_time_split(token_rows)
    eval_rows = validation or token_rows
    scores = [row.get("token_score", 0.0) for row in eval_rows]
    metrics = {}
    for k in top_k_values:
        metrics[f"precision_at_{int(k)}"] = baseline.precision_at_k(eval_rows, scores, int(k))
        metrics[f"lift_at_{int(k)}"] = baseline.lift_at_k(eval_rows, scores, int(k))
    return {
        "decision": "research_baseline_only" if positives else "insufficient_positive_support",
        "token_count": len(token_rows),
        "positive_count": positives,
        "base_positive_rate": base_rate,
        "split": split,
        "validation_token_count": len(eval_rows),
        "validation_positive_count": sum(1 for row in eval_rows if _row_hit_10x(row)),
        "metrics": metrics,
    }
```

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.model.test_moonshot_token_level_eval`

Expected: PASS.

## Task 3: Read-Only CLI and CLI Tests

**Files:**
- Create: `scripts/probe_moonshot_token_level_eval.py`
- Create: `tests/model/test_moonshot_token_level_eval_cli.py`

- [ ] **Step 1: Write CLI smoke tests**

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts import probe_moonshot_token_level_eval as cli


class TestMoonshotTokenLevelEvalCli(unittest.TestCase):
    def test_output_guard_rejects_tmp_path(self):
        with self.assertRaises(SystemExit):
            cli._assert_output("/tmp/moonshot_token_eval.json", force=True)

    def test_report_shape_for_empty_inputs(self):
        report = cli.build_report([], [], snapshot_seconds=(30, 60, 300), dedupe_policy="max_events")
        self.assertFalse(report["external_api_calls"])
        self.assertEqual(report["decision"], "invalid_input")
        self.assertIn("dedupe", report)
        self.assertIn("token_level_evaluation", report)
```

- [ ] **Step 2: Implement the CLI wrapper**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import probe_moonshot_local_runner_baseline as baseline_cli  # noqa: E402
from src.pipeline import moonshot_label_truth as labels  # noqa: E402
from src.pipeline import moonshot_token_level_eval as token_eval  # noqa: E402

DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT = "data/replay_reports/moonshot_token_level_eval_20260610.json"
DEFAULT_SNAPSHOT_SECONDS = "30,60,300"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate token-level moonshot runner proxy precision")
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR)
    parser.add_argument("--snapshot-seconds", default=DEFAULT_SNAPSHOT_SECONDS)
    parser.add_argument("--dedupe-policy", default="max_events", choices=sorted(token_eval.VALID_DEDUPE_POLICIES))
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _assert_output(path_text: str, *, force: bool) -> Path:
    path = Path(path_text)
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    resolved = resolved.resolve()
    allowed_roots = [(PROJECT_ROOT / "data" / "replay_reports").resolve(), (PROJECT_ROOT / "docs" / "research").resolve()]
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise SystemExit(f"refusing output outside replay/research roots: {path_text}")
    if resolved.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing output without --force: {resolved}")
    return resolved


def _parse_snapshot_seconds(text: object):
    return baseline_cli._parse_snapshot_seconds(text)


def _local_label_candidates(lifecycles: Iterable[dict], generated_at: str):
    rows = []
    rejects = []
    for lifecycle in lifecycles or []:
        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at=generated_at)
        if row is not None:
            data = row.to_dict()
            data["_event_count"] = len(lifecycle.get("buys", []) or []) + len(lifecycle.get("sells", []) or [])
            rows.append(data)
        if reject is not None:
            rejects.append(reject.to_dict())
    return rows, rejects


def build_report(lifecycles: Iterable[dict], label_candidates: Iterable[dict], *, snapshot_seconds: Sequence[int], dedupe_policy: str):
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    deduped, dedupe_summary = token_eval.dedupe_label_rows(label_candidates, policy=dedupe_policy)
    token_rows = []
    future_field_violations = []
    lifecycle_by_token = {str(row.get("token_address", "")).lower(): row for row in lifecycles or []}
    for label_row in deduped:
        lifecycle = lifecycle_by_token.get(str(label_row.get("token_address", "")).lower())
        if lifecycle is None:
            continue
        rows, _skipped, violations = baseline_cli._build_rows_for_label(lifecycle, label_row, snapshot_seconds)
        future_field_violations.extend(violations)
        token_rows.extend(token_eval.collapse_snapshots_to_tokens(rows))
    evaluation = token_eval.evaluate_token_level(token_rows)
    return {
        "generated_at": generated_at,
        "decision": evaluation.get("decision", "invalid_input"),
        "external_api_calls": False,
        "dedupe": dedupe_summary,
        "dedupe_sensitivity": token_eval.dedupe_sensitivity(label_candidates),
        "snapshot_seconds": list(snapshot_seconds),
        "future_field_violations": future_field_violations,
        "token_level_evaluation": evaluation,
    }
```

- [ ] **Step 3: Complete CLI main by loading lifecycles through existing helpers**

```python
def main(argv=None):
    args = parse_args(argv)
    output = _assert_output(args.output, force=bool(args.force))
    snapshot_seconds = _parse_snapshot_seconds(args.snapshot_seconds)
    lifecycles = list(baseline_cli._iter_lifecycles(args.lifecycle_dir))
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    label_candidates, rejects = _local_label_candidates(lifecycles, generated_at)
    report = build_report(lifecycles, label_candidates, snapshot_seconds=snapshot_seconds, dedupe_policy=args.dedupe_policy)
    report["rejects"] = rejects
    report["input_paths"] = {"lifecycle_dir": str(args.lifecycle_dir)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    print(f"decision={report['decision']} tokens={report['token_level_evaluation'].get('token_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests**

Run: `python -m unittest tests.model.test_moonshot_token_level_eval_cli`

Expected: PASS.

## Task 4: Generate Report and Closeout Docs

**Files:**
- Create: `data/replay_reports/moonshot_token_level_eval_20260610.json`
- Create: `docs/research/20260610-moonshot-token-level-eval/summary.md`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run the focused moonshot tests**

Run: `python -m unittest tests.model.test_moonshot_token_level_eval tests.model.test_moonshot_token_level_eval_cli tests.model.test_moonshot_local_runner_baseline tests.model.test_moonshot_feature_snapshot tests.model.test_moonshot_label_truth tests.model.test_moonshot_phase0_clis`

Expected: all tests PASS.

- [ ] **Step 2: Run the token-level report**

Run: `python scripts/probe_moonshot_token_level_eval.py --lifecycle-dir data/training --output data/replay_reports/moonshot_token_level_eval_20260610.json --force`

Expected: writes a report with `external_api_calls=false`, `decision=research_baseline_only` or a conservative non-promotion decision, `split.token_overlap=0`, and no future-field violations.

- [ ] **Step 3: Write closeout summary**

Create `docs/research/20260610-moonshot-token-level-eval/summary.md` with these sections:

```markdown
# Moonshot Token-Level Evaluation

Created: 2026-06-10

Purpose: replace snapshot-level moonshot baseline diagnostics with an honest token-level evaluation for the local `>=10x` proxy.

## Inputs

- Lifecycle dir: `data/training`
- Snapshot seconds: `30,60,300`
- Dedupe policy: `max_events`

## Results

- Token count: value from `token_level_evaluation.token_count`
- Positive count: value from `token_level_evaluation.positive_count`
- Base positive rate: value from `token_level_evaluation.base_positive_rate`
- Token overlap: value from `token_level_evaluation.split.token_overlap`
- Future field violations: count from `future_field_violations`

## Interpretation

- This is still local `>=10x` proxy evidence only.
- It is not evidence for `20x/50x/100x` exits.
- It does not change live runtime behavior.

## Scoreboard Closeout

`docs/model_scoreboard.md` was updated because this round changes the next model direction.
```

- [ ] **Step 4: Append scoreboard note**

Append one concise bullet to `docs/model_scoreboard.md` stating the token-level evaluation result, whether it supports continuing to external label backfill, and that there is no live switch.

- [ ] **Step 5: Run full verification**

Run: `python -m unittest discover`

Expected: all tests PASS.

- [ ] **Step 6: Guardrail checks before reporting completion**

Run:

```bash
git diff -- docs/goals/
git diff --cached -- docs/goals/
git ls-files .ccg
python - <<'PY'
from pathlib import Path
needles = ["TB" + "D", "TO" + "DO", "PLACE" + "HOLDER"]
paths = [Path("docs/research/20260610-moonshot-token-level-eval"), Path("docs/superpowers/plans/2026-06-10-moonshot-token-level-eval.md")]
for path in paths:
    files = path.rglob("*.md") if path.is_dir() else [path]
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in text:
                raise SystemExit(f"{needle} found in {file_path}")
PY
```

Expected: no `docs/goals` changes, no tracked `.ccg` files, and no placeholders in new docs.
