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

from src.pipeline import action_policy_meta_label_probe as probe


PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/action_policy_meta_label_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a read-only accepted/rejected action-policy meta-label support probe",
    )
    parser.add_argument("--rejected-report", action="append", required=True, help="Rejected TTB or live-attribution JSON report")
    parser.add_argument("--accepted-report", action="append", required=True, help="Accepted post-target JSON report")
    parser.add_argument("--rejected-source-name", action="append", default=None, help="Optional source group for each rejected report")
    parser.add_argument("--accepted-source-name", action="append", default=None, help="Optional source group for each accepted report")
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--validation-source-count", type=int, default=1, help="Latest source groups reserved for validation")
    parser.add_argument("--probability-threshold", type=float, default=0.5, help="Meta-label selection probability threshold")
    parser.add_argument("--min-validation-selected", type=int, default=3, help="Minimum validation rows required")
    parser.add_argument("--max-depth", type=int, default=3, help="Decision-tree max depth")
    parser.add_argument("--min-samples-leaf", type=int, default=3, help="Decision-tree min samples per leaf")
    parser.add_argument("--min-family-candidates", type=int, default=3, help="Minimum accepted and rejected rows")
    parser.add_argument("--min-common-features", type=int, default=1, help="Minimum shared decision-time features")
    parser.add_argument(
        "--min-validation-selected-per-family",
        type=int,
        default=1,
        help="Minimum selected validation rows required for accepted and rejected families",
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


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        rejected_paths = [Path(path) for path in args.rejected_report]
        accepted_paths = [Path(path) for path in args.accepted_report]
        input_paths = rejected_paths + accepted_paths
        output_path = _validate_output_path(args.output, input_paths=input_paths)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        report = probe.build_action_policy_meta_label_report(
            rejected_reports=[_load_json(path) for path in rejected_paths],
            accepted_reports=[_load_json(path) for path in accepted_paths],
            rejected_source_names=args.rejected_source_name,
            accepted_source_names=args.accepted_source_name,
            validation_source_count=args.validation_source_count,
            probability_threshold=args.probability_threshold,
            min_validation_selected=args.min_validation_selected,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            min_family_candidates=args.min_family_candidates,
            min_common_features=args.min_common_features,
            min_validation_selected_per_family=args.min_validation_selected_per_family,
        )
        report["inputs"] = {
            "rejected_reports": [str(path) for path in rejected_paths],
            "accepted_reports": [str(path) for path in accepted_paths],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(
        "decision={decision} selected_count={selected}".format(
            decision=report.get("decision"),
            selected=report.get("validation", {}).get("selected_count", 0),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
