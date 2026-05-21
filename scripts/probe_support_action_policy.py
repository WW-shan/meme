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
    parser = argparse.ArgumentParser(
        description="Build a read-only support report for rejected-signal action rules",
    )
    parser.add_argument(
        "--time-to-barrier-report",
        default=DEFAULT_INPUT,
        help="Input time-to-barrier report JSON",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument(
        "--min-selected",
        type=int,
        default=3,
        help="Minimum selected candidates for an eligible rule",
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
    resolved_replay_root = replay_root.resolve()
    if not _is_relative_to(resolved_output, resolved_replay_root):
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
        report = probe.build_support_report(
            time_to_barrier_report=time_report,
            min_selected=args.min_selected,
        )
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
