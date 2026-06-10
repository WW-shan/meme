#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Dict, Iterable, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.dataset_builder import stable_lifecycle_order  # noqa: E402
from src.pipeline import moonshot_feature_snapshot as snapshots  # noqa: E402
from src.pipeline import moonshot_label_truth as labels  # noqa: E402
from src.pipeline import moonshot_local_runner_baseline as baseline  # noqa: E402


DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_LABEL_REPORT = "data/replay_reports/moonshot_label_truth_probe_20260609.json"
DEFAULT_OUTPUT = "data/replay_reports/moonshot_local_runner_baseline_20260609.json"
DEFAULT_SNAPSHOT_SECONDS = "30,60,300"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate a pure on-chain moonshot runner baseline")
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR)
    parser.add_argument("--label-report", default=DEFAULT_LABEL_REPORT)
    parser.add_argument("--snapshot-seconds", default=DEFAULT_SNAPSHOT_SECONDS)
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


def _normalize_address(value: object) -> str:
    return str(value or "").strip().lower()


def _parse_time(value: object) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, datetime):
        timestamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return int(timestamp.timestamp())
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        pass
    iso_text = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(iso_text)
    except ValueError:
        return 0
    parsed = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def _parse_snapshot_seconds(text: object) -> List[int]:
    values = []
    for item in str(text or "").split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if value <= 0:
            raise SystemExit("--snapshot-seconds values must be positive")
        values.append(value)
    if not values:
        raise SystemExit("--snapshot-seconds must include at least one positive value")
    return values


def _read_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _lifecycle_paths(lifecycle_dir: object) -> List[Path]:
    root = Path(lifecycle_dir)
    if not root.exists():
        return []
    paths = list(root.glob("lifecycle_incremental_*.jsonl"))
    paths.extend(path for path in root.glob("lifecycle_*.jsonl") if not path.name.startswith("lifecycle_incremental_"))
    return stable_lifecycle_order(paths)


def _iter_lifecycles(lifecycle_dir: object) -> Iterable[dict]:
    for path in _lifecycle_paths(lifecycle_dir):
        for lifecycle in _read_jsonl(path):
            yield lifecycle


def _load_label_rows(label_report_path: object) -> List[dict]:
    path = Path(label_report_path)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [dict(row) for row in payload.get("rows", [])]
    return []


def _component_summary(snapshot_rows: Sequence[dict]) -> Dict[str, dict]:
    component_values: Dict[str, List[float]] = {}
    for row in snapshot_rows:
        for name, value in baseline.score_snapshot(row)["components"].items():
            component_values.setdefault(name, []).append(float(value))
    return {
        name: {
            "mean": sum(values) / float(len(values)),
            "min": min(values),
            "max": max(values),
        }
        for name, values in sorted(component_values.items())
        if values
    }


def _event_count(lifecycle: dict) -> int:
    return len(lifecycle.get("buys", []) or []) + len(lifecycle.get("sells", []) or [])


def _build_rows_for_label(lifecycle: dict, label_row: dict, snapshot_seconds: Sequence[int]) -> tuple:
    token_address = _normalize_address(label_row.get("token_address"))
    launch_time = _parse_time(label_row.get("launch_time"))
    if launch_time <= 0:
        launch_time = _parse_time(lifecycle.get("create_timestamp", lifecycle.get("created_at")))
    if launch_time <= 0:
        return [], [{"token_address": token_address, "reason": "missing_launch_time"}], []

    rows = []
    skipped = []
    violations = []
    for seconds in snapshot_seconds:
        row = snapshots.build_snapshot_row(lifecycle, label_row, snapshot_time=launch_time + int(seconds))
        row_violations = snapshots.validate_snapshot_no_future_fields(row)
        if row_violations:
            violations.append({"token_address": token_address, "violations": row_violations})
            continue
        rows.append(row)
    if not rows and not violations:
        skipped.append({"token_address": token_address, "reason": "no_valid_snapshots"})
    return rows, skipped, violations


def build_report(lifecycle_dir: object, label_report_path: object, snapshot_seconds: Sequence[int]) -> dict:
    label_rows = _load_label_rows(label_report_path)
    has_label_report = Path(label_report_path).exists()
    label_by_token = {
        _normalize_address(row.get("token_address")): row
        for row in label_rows
        if _normalize_address(row.get("token_address"))
    }
    best_event_counts: Dict[str, int] = {}
    snapshot_rows_by_token: Dict[str, List[dict]] = {}
    skipped_labels = []
    future_field_violations = []
    seen_tokens = set()

    for lifecycle in _iter_lifecycles(lifecycle_dir):
        token_address = _normalize_address(lifecycle.get("token_address"))
        if not token_address:
            continue
        if has_label_report:
            label_row = label_by_token.get(token_address)
            if label_row is None:
                continue
        else:
            extracted, _ = labels.extract_local_lifecycle_label(lifecycle)
            if extracted is None:
                continue
            label_row = extracted.to_dict()
            label_by_token[token_address] = label_row

        current_event_count = _event_count(lifecycle)
        if current_event_count < best_event_counts.get(token_address, -1):
            continue
        rows, skipped, violations = _build_rows_for_label(lifecycle, label_row, snapshot_seconds)
        best_event_counts[token_address] = current_event_count
        snapshot_rows_by_token[token_address] = rows
        seen_tokens.add(token_address)
        skipped_labels.extend(skipped)
        future_field_violations.extend(violations)

    if has_label_report:
        for token_address in sorted(set(label_by_token) - seen_tokens):
            skipped_labels.append({"token_address": token_address, "reason": "missing_lifecycle"})

    snapshot_rows = [row for token in sorted(snapshot_rows_by_token) for row in snapshot_rows_by_token[token]]
    evaluation = baseline.evaluate_baseline(snapshot_rows)
    positive_count = sum(1 for row in snapshot_rows if (row.get("label") or {}).get("hit_10x"))
    base_rate = positive_count / float(len(snapshot_rows)) if snapshot_rows else 0.0
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "decision": evaluation["decision"],
        "sample_count": len(snapshot_rows),
        "positive_count": positive_count,
        "base_rate": base_rate,
        "top_k_metrics": dict(evaluation.get("metrics", {})),
        "validation_metrics": {
            "train_count": evaluation.get("train_count", 0),
            "validation_count": evaluation.get("validation_count", 0),
            "validation_positive_count": evaluation.get("validation_positive_count", 0),
        },
        "feature_component_summary": _component_summary(snapshot_rows),
        "snapshot_seconds": list(snapshot_seconds),
        "skipped_labels": skipped_labels,
        "future_field_violations": future_field_violations,
        "evaluation": evaluation,
        "input_paths": {
            "lifecycle_dir": str(lifecycle_dir),
            "label_report": str(label_report_path),
        },
        "external_api_calls": False,
    }


def main(argv=None):
    args = parse_args(argv)
    output = _assert_output(args.output, force=bool(args.force))
    snapshot_seconds = _parse_snapshot_seconds(args.snapshot_seconds)
    report = build_report(args.lifecycle_dir, args.label_report, snapshot_seconds)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    print(
        "decision={decision} samples={samples} positives={positives} base_rate={base_rate:.6f}".format(
            decision=report["decision"],
            samples=report["sample_count"],
            positives=report["positive_count"],
            base_rate=report["base_rate"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
