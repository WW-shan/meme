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

from src.pipeline import action_policy_router_probe as probe


PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/action_policy_router_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a read-only multi-policy action-router shadow probe",
    )
    parser.add_argument("--train-rejected-report", action="append", required=True)
    parser.add_argument("--train-accepted-report", action="append", default=[])
    parser.add_argument("--validation-rejected-report", action="append", required=True)
    parser.add_argument("--validation-accepted-report", action="append", default=[])
    parser.add_argument("--final-rejected-report", action="append", default=[])
    parser.add_argument("--final-accepted-report", action="append", default=[])
    parser.add_argument("--train-rejected-source-name", action="append", default=None)
    parser.add_argument("--train-accepted-source-name", action="append", default=None)
    parser.add_argument("--validation-rejected-source-name", action="append", default=None)
    parser.add_argument("--validation-accepted-source-name", action="append", default=None)
    parser.add_argument("--final-rejected-source-name", action="append", default=None)
    parser.add_argument("--final-accepted-source-name", action="append", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--route-confidence-threshold", type=float, default=0.5)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-samples-leaf", type=int, default=3)
    parser.add_argument("--min-common-features", type=int, default=1)
    parser.add_argument("--min-selected-per-family", type=int, default=1)
    parser.add_argument("--quick-take-profit-pct", type=float, default=25.0)
    parser.add_argument("--stop-loss-pct", type=float, default=-18.0)
    parser.add_argument("--post-target-window-seconds", type=float, default=60.0)
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


def _paths(values: list[str]) -> list[Path]:
    return [Path(value) for value in values]


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        train_rejected_paths = _paths(args.train_rejected_report)
        train_accepted_paths = _paths(args.train_accepted_report)
        validation_rejected_paths = _paths(args.validation_rejected_report)
        validation_accepted_paths = _paths(args.validation_accepted_report)
        final_rejected_paths = _paths(args.final_rejected_report)
        final_accepted_paths = _paths(args.final_accepted_report)
        input_paths = (
            train_rejected_paths
            + train_accepted_paths
            + validation_rejected_paths
            + validation_accepted_paths
            + final_rejected_paths
            + final_accepted_paths
        )
        output_path = _validate_output_path(args.output, input_paths=input_paths)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        report = probe.build_action_policy_router_report(
            train_rejected_reports=[_load_json(path) for path in train_rejected_paths],
            train_accepted_reports=[_load_json(path) for path in train_accepted_paths],
            validation_rejected_reports=[_load_json(path) for path in validation_rejected_paths],
            validation_accepted_reports=[_load_json(path) for path in validation_accepted_paths],
            final_rejected_reports=[_load_json(path) for path in final_rejected_paths],
            final_accepted_reports=[_load_json(path) for path in final_accepted_paths],
            train_rejected_source_names=args.train_rejected_source_name,
            train_accepted_source_names=args.train_accepted_source_name,
            validation_rejected_source_names=args.validation_rejected_source_name,
            validation_accepted_source_names=args.validation_accepted_source_name,
            final_rejected_source_names=args.final_rejected_source_name,
            final_accepted_source_names=args.final_accepted_source_name,
            route_confidence_threshold=args.route_confidence_threshold,
            max_depth=args.max_depth,
            min_samples_leaf=args.min_samples_leaf,
            min_common_features=args.min_common_features,
            min_selected_per_family=args.min_selected_per_family,
            quick_take_profit_pct=args.quick_take_profit_pct,
            stop_loss_pct=args.stop_loss_pct,
            post_target_window_seconds=args.post_target_window_seconds,
        )
        report["inputs"] = {
            "train_rejected_reports": [str(path) for path in train_rejected_paths],
            "train_accepted_reports": [str(path) for path in train_accepted_paths],
            "validation_rejected_reports": [str(path) for path in validation_rejected_paths],
            "validation_accepted_reports": [str(path) for path in validation_accepted_paths],
            "final_rejected_reports": [str(path) for path in final_rejected_paths],
            "final_accepted_reports": [str(path) for path in final_accepted_paths],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(
        "decision={decision} validation_reward_pct={reward}".format(
            decision=report.get("decision"),
            reward=report.get("validation", {}).get("selected_reward_pct", 0.0),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
