#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import candidate_meta_label_probe as probe


PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/candidate_meta_label_probe_{stamp}.json"


FILTER_OPERATORS = (">=", "<=", "!=", "==", ">", "<")


def _parse_candidate_filter(text: str) -> dict[str, float | str]:
    for op in FILTER_OPERATORS:
        if op not in text:
            continue
        field, value_text = text.split(op, 1)
        field = field.strip()
        value_text = value_text.strip()
        if not field or not value_text:
            break
        if field not in probe.DECISION_TIME_FIELDS:
            raise ValueError(f"{field} is not decision-time")
        try:
            value = float(value_text)
        except ValueError as exc:
            raise ValueError(f"candidate filter value for {field} must be numeric") from exc
        if not math.isfinite(value):
            raise ValueError(f"candidate filter value for {field} must be finite numeric")
        return {"field": field, "op": op, "value": value}
    raise ValueError(f"invalid candidate filter: {text}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Train a read-only candidate-level meta-label probe over time-to-barrier reports",
    )
    parser.add_argument(
        "--time-to-barrier-report",
        action="append",
        required=True,
        help="Input time-to-barrier report JSON; repeat in chronological order",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument(
        "--validation-report-count",
        type=int,
        default=1,
        help="Number of latest reports to reserve for validation",
    )
    parser.add_argument(
        "--probability-threshold",
        type=float,
        default=0.5,
        help="Meta-label probability threshold for selected validation candidates",
    )
    parser.add_argument(
        "--min-validation-selected",
        type=int,
        default=3,
        help="Minimum validation candidates required before the probe is eligible",
    )
    parser.add_argument("--max-depth", type=int, default=3, help="Decision-tree max depth")
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=3,
        help="Decision-tree min samples per leaf",
    )
    parser.add_argument(
        "--candidate-filter",
        action="append",
        default=[],
        help="Decision-time numeric filter such as prob>=0.94; repeatable",
    )
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


def _validate_output_path(output_text: str, *, input_paths: list[Path]) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in PROTECTED_OUTPUTS:
        raise ValueError(f"refusing output path: {output_text}")

    repo_root = PROJECT_ROOT.resolve()
    replay_root = repo_root / REPLAY_REPORTS_DIR
    _refuse_symlinked_replay_root(repo_root, replay_root)
    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else repo_root / output_path
    resolved_output = logical_output.resolve()
    resolved_replay_root = replay_root.resolve()
    if not _is_relative_to(resolved_output, resolved_replay_root):
        raise ValueError(f"refusing output path outside {REPLAY_REPORTS_DIR}: {output_text}")

    resolved_inputs = {
        (path if path.is_absolute() else repo_root / path).resolve()
        for path in input_paths
    }
    if resolved_output in resolved_inputs:
        raise ValueError("refusing to overwrite input report")
    return resolved_output


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        input_paths = [Path(path) for path in args.time_to_barrier_report]
        output_path = _validate_output_path(args.output, input_paths=input_paths)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        time_reports = [json.loads(path.read_text(encoding="utf-8")) for path in input_paths]
        candidate_filters = [
            _parse_candidate_filter(candidate_filter)
            for candidate_filter in args.candidate_filter
        ]
        report = probe.build_candidate_meta_label_report(
            time_to_barrier_reports=time_reports,
            source_names=[str(path) for path in input_paths],
            validation_report_count=args.validation_report_count,
            probability_threshold=args.probability_threshold,
            min_validation_selected=args.min_validation_selected,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            candidate_filters=candidate_filters,
        )
        report["inputs"] = {"time_to_barrier_reports": [str(path) for path in input_paths]}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"selected_count={report.get('validation', {}).get('selected_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
