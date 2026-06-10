#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Iterable, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import probe_moonshot_local_runner_baseline as baseline_cli  # noqa: E402
from src.pipeline import moonshot_label_truth as labels  # noqa: E402
from src.pipeline import moonshot_local_runner_baseline as baseline  # noqa: E402
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
    allowed_roots = [
        (PROJECT_ROOT / "data" / "replay_reports").resolve(),
        (PROJECT_ROOT / "docs" / "research").resolve(),
    ]
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise SystemExit(f"refusing output outside replay/research roots: {path_text}")
    if resolved.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing output without --force: {resolved}")
    return resolved


def _parse_snapshot_seconds(text: object) -> List[int]:
    return baseline_cli._parse_snapshot_seconds(text)


def _generated_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _event_count(lifecycle: dict) -> int:
    return len(lifecycle.get("buys", []) or []) + len(lifecycle.get("sells", []) or [])


def _normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _local_label_candidates(lifecycles: Iterable[dict], generated_at: str):
    rows = []
    rejects = []
    for index, lifecycle in enumerate(lifecycles or []):
        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at=generated_at)
        if row is not None:
            data = row.to_dict()
            data["_event_count"] = _event_count(lifecycle)
            data["_lifecycle_index"] = index
            rows.append(data)
        if reject is not None:
            rejects.append(reject.to_dict())
    return rows, rejects


def _snapshot_level_summary(snapshot_rows: Sequence[dict]) -> dict:
    evaluation = baseline.evaluate_baseline(snapshot_rows)
    positive_count = sum(1 for row in snapshot_rows if (row.get("label") or {}).get("hit_10x"))
    return {
        "sample_count": len(snapshot_rows),
        "positive_count": positive_count,
        "base_rate": positive_count / float(len(snapshot_rows)) if snapshot_rows else 0.0,
        "top_k_metrics": dict(evaluation.get("metrics", {})),
        "validation_metrics": {
            "train_count": evaluation.get("train_count", 0),
            "validation_count": evaluation.get("validation_count", 0),
            "validation_positive_count": evaluation.get("validation_positive_count", 0),
        },
        "evaluation_decision": evaluation.get("decision"),
    }


def build_report(
    lifecycles: Iterable[dict],
    label_candidates: Iterable[dict],
    *,
    snapshot_seconds: Sequence[int],
    dedupe_policy: str,
):
    generated_at = _generated_at()
    lifecycle_list = list(lifecycles or [])
    candidate_list = [dict(row) for row in label_candidates or []]
    deduped, dedupe_summary = token_eval.dedupe_label_rows(candidate_list, policy=dedupe_policy)
    lifecycle_by_index = {index: lifecycle for index, lifecycle in enumerate(lifecycle_list)}
    lifecycle_by_token = {_normalize_address(row.get("token_address")): row for row in lifecycle_list if _normalize_address(row.get("token_address"))}

    token_rows = []
    snapshot_rows = []
    skipped_labels = []
    future_field_violations = []
    for label_row in deduped:
        lifecycle = lifecycle_by_index.get(label_row.get("_lifecycle_index"))
        if lifecycle is None:
            lifecycle = lifecycle_by_token.get(_normalize_address(label_row.get("token_address")))
        if lifecycle is None:
            skipped_labels.append({"token_address": label_row.get("token_address"), "reason": "missing_lifecycle"})
            continue
        rows, skipped, violations = baseline_cli._build_rows_for_label(lifecycle, label_row, snapshot_seconds)
        skipped_labels.extend(skipped)
        future_field_violations.extend(violations)
        snapshot_rows.extend(rows)
        token_rows.extend(token_eval.collapse_snapshots_to_tokens(rows))

    evaluation = token_eval.evaluate_token_level(token_rows)
    return {
        "generated_at": generated_at,
        "decision": evaluation.get("decision", "invalid_input"),
        "external_api_calls": False,
        "dedupe": dedupe_summary,
        "dedupe_sensitivity": token_eval.dedupe_sensitivity(candidate_list),
        "snapshot_seconds": list(snapshot_seconds),
        "snapshot_level_evaluation": _snapshot_level_summary(snapshot_rows),
        "future_field_violations": future_field_violations,
        "skipped_labels": skipped_labels,
        "token_level_evaluation": evaluation,
    }



def _candidate_event_count(row: dict) -> int:
    try:
        return int(row.get("_event_count", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _candidate_multiple(row: dict) -> float:
    try:
        return float(row.get("max_multiple", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _candidate_launch_time(row: dict) -> int:
    try:
        return int(float(row.get("launch_time", 0) or 0))
    except (TypeError, ValueError):
        return 0


def _candidate_sequence(row: dict) -> int:
    try:
        return int(row.get("_candidate_sequence", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _is_better_candidate(incoming: dict, existing: dict | None, policy: str) -> bool:
    if existing is None:
        return True
    if policy == "max_events":
        return (
            _candidate_event_count(incoming),
            _candidate_multiple(incoming),
            _candidate_launch_time(incoming),
            _candidate_sequence(incoming),
        ) > (
            _candidate_event_count(existing),
            _candidate_multiple(existing),
            _candidate_launch_time(existing),
            _candidate_sequence(existing),
        )
    if policy == "max_multiple":
        return (
            _candidate_multiple(incoming),
            _candidate_event_count(incoming),
            _candidate_launch_time(incoming),
            _candidate_sequence(incoming),
        ) > (
            _candidate_multiple(existing),
            _candidate_event_count(existing),
            _candidate_launch_time(existing),
            _candidate_sequence(existing),
        )
    if policy == "min_multiple":
        return (
            _candidate_multiple(incoming),
            -_candidate_event_count(incoming),
            _candidate_launch_time(incoming),
            _candidate_sequence(incoming),
        ) < (
            _candidate_multiple(existing),
            -_candidate_event_count(existing),
            _candidate_launch_time(existing),
            _candidate_sequence(existing),
        )
    raise ValueError(f"unknown dedupe policy: {policy}")


def _dedupe_summary_from_stats(stats: dict, policy: str) -> dict:
    duplicate_count = sum(1 for item in stats.values() if item["count"] > 1)
    conflict_count = 0
    for item in stats.values():
        low = item["min_multiple"]
        high = item["max_multiple"]
        if item["count"] > 1 and low > 0 and ((high - low) / low) > 0.20:
            conflict_count += 1
    return {
        "policy": policy,
        "input_row_count": sum(item["count"] for item in stats.values()),
        "output_token_count": len(stats),
        "duplicate_token_count": duplicate_count,
        "conflict_token_count": conflict_count,
    }


def _sensitivity_from_policy_selected(policy_selected: dict) -> dict:
    result = {}
    for policy in sorted(policy_selected):
        rows = list(policy_selected[policy].values())
        result[policy] = {
            ">=10x": sum(1 for row in rows if _candidate_multiple(row) >= 10.0),
            "token_count": len(rows),
        }
    return result


def build_report_from_lifecycles(
    lifecycles: Iterable[dict],
    *,
    snapshot_seconds: Sequence[int],
    dedupe_policy: str,
) -> dict:
    generated_at = _generated_at()
    selected_candidates = {}
    policy_selected = {policy: {} for policy in sorted(token_eval.VALID_DEDUPE_POLICIES)}
    stats = {}
    rejects = []

    for sequence, lifecycle in enumerate(lifecycles or []):
        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at=generated_at)
        if reject is not None:
            rejects.append(reject.to_dict())
        if row is None:
            continue

        label_row = row.to_dict()
        label_row["_event_count"] = _event_count(lifecycle)
        label_row["_candidate_sequence"] = sequence
        key = (str(label_row.get("chain") or "bsc").lower(), _normalize_address(label_row.get("token_address")))
        if not key[1]:
            continue

        item = stats.setdefault(key, {"count": 0, "min_multiple": None, "max_multiple": None})
        multiple = _candidate_multiple(label_row)
        item["count"] += 1
        item["min_multiple"] = multiple if item["min_multiple"] is None else min(item["min_multiple"], multiple)
        item["max_multiple"] = multiple if item["max_multiple"] is None else max(item["max_multiple"], multiple)

        for policy, selected in policy_selected.items():
            if _is_better_candidate(label_row, selected.get(key), policy):
                selected[key] = dict(label_row)

        snapshot_rows, skipped, violations = baseline_cli._build_rows_for_label(lifecycle, label_row, snapshot_seconds)
        token_rows = token_eval.collapse_snapshots_to_tokens(snapshot_rows)
        candidate = {
            "label": label_row,
            "snapshot_rows": snapshot_rows,
            "token_rows": token_rows,
            "skipped_labels": skipped,
            "future_field_violations": violations,
        }
        existing = selected_candidates.get(key)
        existing_label = existing["label"] if existing is not None else None
        if _is_better_candidate(label_row, existing_label, dedupe_policy):
            selected_candidates[key] = candidate

    snapshot_rows = []
    token_rows = []
    skipped_labels = []
    future_field_violations = []
    for key in sorted(selected_candidates):
        candidate = selected_candidates[key]
        snapshot_rows.extend(candidate["snapshot_rows"])
        token_rows.extend(candidate["token_rows"])
        skipped_labels.extend(candidate["skipped_labels"])
        future_field_violations.extend(candidate["future_field_violations"])

    evaluation = token_eval.evaluate_token_level(token_rows)
    return {
        "generated_at": generated_at,
        "decision": evaluation.get("decision", "invalid_input"),
        "external_api_calls": False,
        "dedupe": _dedupe_summary_from_stats(stats, dedupe_policy),
        "dedupe_sensitivity": _sensitivity_from_policy_selected(policy_selected),
        "snapshot_seconds": list(snapshot_seconds),
        "snapshot_level_evaluation": _snapshot_level_summary(snapshot_rows),
        "future_field_violations": future_field_violations,
        "skipped_labels": skipped_labels,
        "token_level_evaluation": evaluation,
        "rejects": rejects,
    }

def main(argv=None):
    args = parse_args(argv)
    output = _assert_output(args.output, force=bool(args.force))
    snapshot_seconds = _parse_snapshot_seconds(args.snapshot_seconds)
    report = build_report_from_lifecycles(
        baseline_cli._iter_lifecycles(args.lifecycle_dir),
        snapshot_seconds=snapshot_seconds,
        dedupe_policy=args.dedupe_policy,
    )
    report["input_paths"] = {"lifecycle_dir": str(args.lifecycle_dir)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    print(f"decision={report['decision']} tokens={report['token_level_evaluation'].get('token_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
