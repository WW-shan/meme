#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.dataset_builder import stable_lifecycle_order  # noqa: E402
from src.pipeline import moonshot_label_truth as labels  # noqa: E402


DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT = "data/replay_reports/moonshot_label_truth_probe_20260609.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build point-in-time moonshot label truth diagnostics")
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR)
    parser.add_argument("--external-labels", action="append", default=[], help="External JSON/JSONL/CSV export; repeatable or comma-separated")
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


def _json_default(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return str(value)


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


def _split_external_paths(values: Iterable[str]) -> List[str]:
    paths = []
    for value in values or []:
        for item in str(value).split(","):
            item = item.strip()
            if item:
                paths.append(item)
    return paths


def build_report(lifecycle_dir: object, external_label_paths: Iterable[str] = ()) -> dict:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lifecycle_paths = _lifecycle_paths(lifecycle_dir)
    local_rows = []
    rejects = []
    lifecycle_count = 0
    for path in lifecycle_paths:
        for lifecycle in _read_jsonl(path):
            lifecycle_count += 1
            row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at=generated_at)
            if row is not None:
                local_rows.append(row)
            if reject is not None:
                rejects.append(reject)

    external_rows, external_rejects = labels.load_external_label_exports(_split_external_paths(external_label_paths))
    merged_rows, warnings = labels.merge_label_rows(local_rows, external_rows)
    report = labels.label_report(merged_rows, rejects + external_rejects, warnings)
    report["generated_at"] = generated_at
    report["input_paths"] = {
        "lifecycle_dir": str(lifecycle_dir),
        "lifecycle_files": [str(path) for path in lifecycle_paths],
        "external_labels": _split_external_paths(external_label_paths),
    }
    report["summary"]["local_lifecycle_count"] = lifecycle_count
    report["summary"]["local_label_count"] = len(local_rows)
    report["summary"]["external_label_count"] = len(external_rows)
    return report


def main(argv=None):
    args = parse_args(argv)
    output = _assert_output(args.output, force=bool(args.force))
    report = build_report(args.lifecycle_dir, args.external_labels)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    print(
        "labels={labels} rejects={rejects} hit_10x={hit_10x}".format(
            labels=report["summary"]["accepted_count"],
            rejects=report["summary"]["reject_count"],
            hit_10x=report["threshold_counts"].get(">=10x", 0),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
