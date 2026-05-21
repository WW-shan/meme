# Support Constrained Action Policy Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only probe that evaluates decision-time feature buckets for rejected-signal rescue actions, so the next model/replay iteration can avoid unsupported live overfit while searching for higher profit.

**Architecture:** Add a small pipeline module that reads `time_to_barrier_probe` candidate rows, evaluates a bounded set of decision-time-only rules, and reports support, purity, selected symbols, and negative counterexamples. Add a thin CLI that reads an existing report and writes a JSON artifact. This is not a live strategy and must explicitly set `live_switch_evidence=false` and `safe_for_live_switch=false`.

**Tech Stack:** Python stdlib, `unittest`, existing JSON report style in `src/pipeline/time_to_barrier_probe.py` and `src/pipeline/counterfactual_action_probe.py`.

---

### Task 1: Add Support Policy Probe Core

**Files:**
- Create: `src/pipeline/support_action_policy_probe.py`
- Test: `tests/model/test_support_action_policy_probe.py`

- [x] **Step 1: Write failing tests for rule evaluation**

Create `tests/model/test_support_action_policy_probe.py`:

```python
import json
import math
import unittest

from src.pipeline import support_action_policy_probe as p


class TestSupportActionPolicyProbe(unittest.TestCase):
    def test_evaluates_decision_time_rule_without_future_fields(self):
        candidates = [
            {
                "symbol": "Arnold",
                "recommended_policy": "quick_take_profit",
                "barrier_class": "fast_profit",
                "prob": 0.987,
                "pred_return": 32.0,
                "entry_volume_30s": 2.1,
                "entry_price_volatility": 0.29,
                "age_seconds": 289.0,
                "mfe_pct": 334.0,
            },
            {
                "symbol": "MEMES",
                "recommended_policy": "skip",
                "barrier_class": "stop_first",
                "prob": 0.987,
                "pred_return": -34.0,
                "entry_volume_30s": 7.2,
                "entry_price_volatility": 0.33,
                "age_seconds": 2.0,
                "mfe_pct": 89.0,
            },
        ]

        result = p.evaluate_rule(
            p.Rule(
                name="high_prob_positive_pred",
                conditions=(
                    p.Condition("prob", ">=", 0.985),
                    p.Condition("pred_return", ">=", 5.0),
                ),
            ),
            candidates,
        )

        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["positive_count"], 1)
        self.assertEqual(result["negative_count"], 0)
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["selected_symbols"], ["Arnold"])
        self.assertNotIn("mfe_pct", result["conditions"][0])

    def test_rejects_rules_that_use_ex_post_fields(self):
        with self.assertRaisesRegex(ValueError, "not decision-time"):
            p.Rule(name="leaky", conditions=(p.Condition("mfe_pct", ">=", 25.0),))

    def test_build_report_keeps_read_only_contract_and_ranks_rules(self):
        candidates = [
            {"symbol": "A", "recommended_policy": "quick_take_profit", "prob": 0.99, "pred_return": 10.0},
            {"symbol": "B", "recommended_policy": "skip", "prob": 0.99, "pred_return": -2.0},
            {"symbol": "C", "recommended_policy": "quick_take_profit", "prob": 0.97, "pred_return": 8.0},
        ]

        report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates, "candidate_counts": {"per_token_candidates": 3}},
            rules=[
                p.Rule("prob_pred", (p.Condition("prob", ">=", 0.985), p.Condition("pred_return", ">=", 5.0))),
                p.Rule("prob_only", (p.Condition("prob", ">=", 0.985),)),
            ],
            min_selected=1,
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertEqual(report["rule_results"][0]["rule"], "prob_pred")
        self.assertEqual(report["rule_results"][0]["positive_count"], 1)
        text = p.to_json_text(report)
        self.assertNotIn("NaN", text)
        json.loads(text)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe
```

Expected: import error because `src.pipeline.support_action_policy_probe` does not exist.

- [x] **Step 3: Implement minimal module**

Create `src/pipeline/support_action_policy_probe.py` with:

```python
from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

POSITIVE_POLICIES = {"quick_take_profit", "conditional_slow_hold"}
HARD_ABSTAIN_RULE = {"field": "prob", "op": "<", "value": 0.94}
HARD_ABSTAIN_THRESHOLD_EPSILON = 1e-8
DECISION_TIME_FIELDS = {
    "prob",
    "pred_return",
    "volume_30s",
    "entry_volume_30s",
    "price_volatility",
    "entry_price_volatility",
    "token_age_seconds",
    "age_seconds",
    "feature_count",
    "features_hash",
    "entry_ranking_mode",
    "near_threshold_rescue_used",
    "use_pred_return_filter",
    "min_pred_return",
    "min_entry_volume_30s",
    "min_entry_price_volatility",
    "buy_near_threshold_min_prob",
    "buy_near_min_pred_return",
    "buy_near_min_entry_volume_30s",
    "buy_near_min_entry_price_volatility",
    "buy_near_min_age_seconds",
}
OPERATORS = {">=", ">", "<=", "<", "==", "!="}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any

    def __post_init__(self):
        if self.field not in DECISION_TIME_FIELDS:
            raise ValueError(f"{self.field} is not decision-time")
        if self.op not in OPERATORS:
            raise ValueError(f"unsupported operator {self.op}")


@dataclass(frozen=True)
class Rule:
    name: str
    conditions: tuple[Condition, ...]

    def __post_init__(self):
        if not self.name:
            raise ValueError("rule name is required")
        _validate_conditions(self.conditions)


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _validate_conditions(conditions: Any) -> None:
    if type(conditions) is not tuple or not conditions:
        raise ValueError("conditions must be a non-empty tuple")
    for condition in conditions:
        _validate_condition(condition)


def _validate_condition(condition: Any) -> None:
    if type(condition) is not Condition:
        raise ValueError("conditions must be exact Condition instances")
    if condition.field not in DECISION_TIME_FIELDS:
        raise ValueError(f"{condition.field} is not decision-time")
    if condition.op not in OPERATORS:
        raise ValueError(f"unsupported operator {condition.op}")


def _validate_rule(rule: Any) -> None:
    if type(rule) is not Rule:
        raise ValueError("rules must be Rule instances")
    _validate_conditions(rule.conditions)


def _validated_rules(rules: Iterable[Rule] | None) -> list[Rule]:
    if rules is None:
        return default_rules()
    if type(rules) not in {list, tuple}:
        raise ValueError("rules must be a list or tuple")
    validated = list(rules)
    for rule in validated:
        _validate_rule(rule)
    return validated


def _condition_matches(condition: Condition, row: Mapping[str, Any]) -> bool:
    _validate_condition(condition)
    if condition.field not in row:
        return False
    left = row.get(condition.field)
    if condition.op in {">=", ">", "<=", "<"}:
        parsed_left = _finite_float(left)
        parsed_right = _finite_float(condition.value)
        if parsed_left is None or parsed_right is None:
            return False
        if condition.op == ">=":
            return parsed_left >= parsed_right
        if condition.op == ">":
            return parsed_left > parsed_right
        if condition.op == "<=":
            return parsed_left <= parsed_right
        return parsed_left < parsed_right
    return left == condition.value if condition.op == "==" else left != condition.value


def _candidate_rows(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = report.get("candidates") or report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)]


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(_json_sanitize(report), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def evaluate_rule(rule: Rule, candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    _validate_rule(rule)
    selected = [row for row in candidates if all(_condition_matches(condition, row) for condition in rule.conditions)]
    positives = [row for row in selected if row.get("recommended_policy") in POSITIVE_POLICIES]
    negatives = [row for row in selected if row.get("recommended_policy") not in POSITIVE_POLICIES]
    selected_count = len(selected)
    positive_count = len(positives)
    return {
        "rule": rule.name,
        "conditions": [{"field": condition.field, "op": condition.op, "value": condition.value} for condition in rule.conditions],
        "selected_count": selected_count,
        "positive_count": positive_count,
        "negative_count": len(negatives),
        "precision": positive_count / selected_count if selected_count else 0.0,
        "selected_symbols": [str(row.get("symbol") or row.get("token")) for row in selected[:25]],
        "positive_symbols": [str(row.get("symbol") or row.get("token")) for row in positives[:25]],
        "negative_symbols": [str(row.get("symbol") or row.get("token")) for row in negatives[:25]],
    }


def _eligible_rule_result(row: Mapping[str, Any], min_selected: int) -> bool:
    return (
        not _is_hard_abstain_result(row)
        and int(row.get("selected_count") or 0) >= min_selected
        and int(row.get("positive_count") or 0) > 0
    )


def _is_hard_abstain_result(row: Mapping[str, Any]) -> bool:
    conditions = row.get("conditions") or []
    if row.get("rule") == "low_prob_hard_abstain":
        return True
    if not isinstance(conditions, list):
        return False
    hard_threshold = _finite_float(HARD_ABSTAIN_RULE["value"])
    if hard_threshold is None:
        return False
    for condition in conditions:
        if not isinstance(condition, Mapping):
            continue
        condition_value = _finite_float(condition.get("value"))
        if (
            condition.get("field") == HARD_ABSTAIN_RULE["field"]
            and condition.get("op") in {"<", "<="}
            and condition_value is not None
            and condition_value <= hard_threshold + HARD_ABSTAIN_THRESHOLD_EPSILON
        ):
            return True
    return False


def default_rules() -> list[Rule]:
    return [
        Rule("low_prob_hard_abstain", (Condition("prob", "<", 0.94),)),
        Rule("high_prob_positive_pred", (Condition("prob", ">=", 0.985), Condition("pred_return", ">=", 5.0))),
        Rule("v95_like_pred_rescue", (Condition("prob", ">=", 0.985), Condition("pred_return", ">=", 30.0))),
        Rule("high_prob_volume_volatility", (Condition("prob", ">=", 0.985), Condition("entry_volume_30s", ">=", 1.25), Condition("entry_price_volatility", ">=", 0.08))),
        Rule("young_high_prob_positive_pred", (Condition("prob", ">=", 0.985), Condition("pred_return", ">=", 5.0), Condition("age_seconds", "<=", 60.0))),
    ]


def build_support_report(
    *,
    time_to_barrier_report: Mapping[str, Any],
    rules: Iterable[Rule] | None = None,
    min_selected: int = 3,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    candidates = _candidate_rows(time_to_barrier_report)
    evaluated = [evaluate_rule(rule, candidates) for rule in _validated_rules(rules)]
    evaluated.sort(key=lambda row: (row["precision"], row["positive_count"], -row["negative_count"], row["rule"]), reverse=True)
    candidate_counts = time_to_barrier_report.get("candidate_counts") or {}
    if not isinstance(candidate_counts, Mapping):
        candidate_counts = {}
    input_reported_candidates = candidate_counts.get("per_token_candidates", len(candidates))
    try:
        input_reported_candidates = int(input_reported_candidates)
    except (TypeError, ValueError):
        input_reported_candidates = len(candidates)
    unscored_reported_candidates = max(0, input_reported_candidates - len(candidates))
    return {
        "generated_at": (generated_at or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None)).isoformat(sep=" "),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "support_report_for_replay_experiment_design",
        },
        "parameters": {"min_selected": min_selected},
        "candidate_counts": {
            "input_candidates": len(candidates),
            "input_reported_candidates": input_reported_candidates,
            "sample_limited": unscored_reported_candidates > 0,
            "unscored_reported_candidates": unscored_reported_candidates,
            "positive_candidates": sum(1 for row in candidates if row.get("recommended_policy") in POSITIVE_POLICIES),
            "negative_candidates": sum(1 for row in candidates if row.get("recommended_policy") not in POSITIVE_POLICIES),
        },
        "rule_results": evaluated,
        "eligible_rule_results": [row for row in evaluated if _eligible_rule_result(row, min_selected)],
        "decision": "probe_only_replay_required",
    }
```

- [x] **Step 4: Run focused tests and py_compile**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe
venv/bin/python -m py_compile src/pipeline/support_action_policy_probe.py
```

Expected: tests pass and compile exits `0`.

### Task 2: Add CLI And Live Report Artifact

**Files:**
- Create: `scripts/probe_support_action_policy.py`
- Test: `tests/model/test_support_action_policy_probe_cli.py`
- Artifact: `data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json`

- [x] **Step 1: Write failing CLI tests**

Create `tests/model/test_support_action_policy_probe_cli.py`:

```python
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_support_action_policy.py"
    spec = importlib.util.spec_from_file_location("probe_support_action_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSupportActionPolicyProbeCli(unittest.TestCase):
    def test_parse_args_defaults_to_live_feature_report_input(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.time_to_barrier_report, "data/replay_reports/time_to_barrier_probe_20260521_post_commit_live_features.json")
        self.assertTrue(args.output.startswith("data/replay_reports/support_action_policy_probe_"))
        self.assertTrue(args.output.endswith(".json"))
        self.assertEqual(args.min_selected, 3)

    def test_main_writes_read_only_report_with_input_path(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            input_path = Path(tmpdir) / "time.json"
            output_path = Path(tmpdir) / "out.json"
            input_path.write_text(json.dumps({"candidate_sample": [{"symbol": "A", "recommended_policy": "quick_take_profit", "prob": 0.99, "pred_return": 10.0}]}), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = cli.main(["--time-to-barrier-report", str(input_path), "--output", str(output_path), "--min-selected", "1"])

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(report["probe_contract"]["read_only"])
            self.assertFalse(report["probe_contract"]["live_switch_evidence"])
            self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
            self.assertEqual(report["inputs"]["time_to_barrier_report"], str(input_path))
            self.assertIn("wrote", stdout.getvalue())
            self.assertIn("eligible_rules=", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe_cli
```

Expected: file-not-found/import failure because CLI does not exist.

- [x] **Step 3: Implement CLI**

Create `scripts/probe_support_action_policy.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import support_action_policy_probe as probe


DEFAULT_INPUT = "data/replay_reports/time_to_barrier_probe_20260521_post_commit_live_features.json"
PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/support_action_policy_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a read-only support report for rejected-signal action rules")
    parser.add_argument("--time-to-barrier-report", default=DEFAULT_INPUT, help="Input time-to-barrier report JSON")
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--min-selected", type=int, default=3, help="Minimum selected candidates for an eligible rule")
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = _default_output()
    return args


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _refuse_symlinked_replay_root(repo_root: Path, replay_root: Path) -> None:
    current = repo_root
    for part in replay_root.relative_to(repo_root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing output path because {current} is a symlink")


def _validate_output_path(output_text: str, *, input_path: Path) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in PROTECTED_OUTPUTS:
        raise ValueError(f"refusing output path: {output_text}")

    repo_root = PROJECT_ROOT.resolve()
    replay_root = repo_root / REPLAY_REPORTS_DIR
    _refuse_symlinked_replay_root(repo_root, replay_root)
    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else repo_root / output_path
    resolved_output = logical_output.resolve()
    if not _is_relative_to(resolved_output, replay_root.resolve()):
        raise ValueError(f"refusing output path outside {REPLAY_REPORTS_DIR}: {output_text}")

    resolved_input = (input_path if input_path.is_absolute() else repo_root / input_path).resolve()
    if resolved_output == resolved_input:
        raise ValueError("refusing to overwrite input report")
    return resolved_output


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        input_path = Path(args.time_to_barrier_report)
        output_path = _validate_output_path(args.output, input_path=input_path)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        time_report = json.loads(input_path.read_text(encoding="utf-8"))
        report = probe.build_support_report(time_to_barrier_report=time_report, min_selected=args.min_selected)
        report["inputs"] = {"time_to_barrier_report": str(input_path)}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"eligible_rules={len(report.get('eligible_rule_results', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run CLI tests and generate live report**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe_cli
venv/bin/python scripts/probe_support_action_policy.py --output data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json --min-selected 3 --force
```

Expected: tests pass, CLI prints output path and eligible rule count.

### Task 3: Document Result And Review

**Files:**
- Modify: `docs/model_scoreboard.md`
- Artifact: `data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json`

- [x] **Step 1: Append scoreboard note**

Append one rejected/support row or bullet to `docs/model_scoreboard.md` under rejected/support probes:

```markdown
| 2026-05-21 | `data/models/20260519_v95_v84_selective_nearmiss_gate` + support-constrained action policy probe | supports follow-up/read-only probe | `0.98` primary, support rules only | `74` rejected path candidates | n/a | n/a | n/a | n/a | n/a | Research `docs/research/20260521-conservative-action-policy-from-oracle-labels/summary.md`; report `data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json`; `live_switch_evidence=false`, `safe_for_live_switch=false`. This probe keeps only decision-time features in rules and uses ex-post barrier classes only as labels. It is intended to find support-constrained buckets for the next replay-integrated action-policy experiment, not to change live bot behavior. | Do not switch live. Any candidate rule must still be integrated into replay and beat current best v95 on validation, final, walk-forward, stress, drawdown, and trade discipline at 10% sizing before deployment. |
```

- [x] **Step 2: Run full focused verification**

Run:

```bash
venv/bin/python -m unittest tests.model.test_support_action_policy_probe tests.model.test_support_action_policy_probe_cli tests.model.test_time_to_barrier_probe tests.model.test_time_to_barrier_probe_cli
venv/bin/python -m py_compile src/pipeline/support_action_policy_probe.py scripts/probe_support_action_policy.py
git diff --check
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Expected: tests pass, compile exits `0`, no whitespace errors, and no goal-file changes.

- [x] **Step 3: Request two strict reviews**

Dispatch two reviewer subagents over:

- `src/pipeline/support_action_policy_probe.py`
- `scripts/probe_support_action_policy.py`
- `tests/model/test_support_action_policy_probe.py`
- `tests/model/test_support_action_policy_probe_cli.py`
- `docs/superpowers/plans/2026-05-21-support-constrained-action-policy-probe.md`
- `docs/model_scoreboard.md`
- `data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json`

Review gates:

- no live bot/config/.env/docs/goals changes;
- no ex-post fields used as rule conditions;
- report contract says read-only and not safe for live switch;
- tests cover leaky field rejection and CLI output;
- scoreboard does not claim deployment readiness.

- [ ] **Step 4: Commit and push**

If both reviews pass and verification remains green:

```bash
git add src/pipeline/support_action_policy_probe.py scripts/probe_support_action_policy.py tests/model/test_support_action_policy_probe.py tests/model/test_support_action_policy_probe_cli.py docs/superpowers/plans/2026-05-21-support-constrained-action-policy-probe.md docs/model_scoreboard.md
git add -f data/replay_reports/support_action_policy_probe_20260521_post_cmc_live.json
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
git commit -m "test: add support constrained action probe"
git push
```

Expected: new commit pushed to `main`.
