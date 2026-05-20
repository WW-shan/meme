#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pipeline.counterfactual_action_probe import build_action_report, to_json_text

PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine counterfactual action probe reports.")
    parser.add_argument("--time-to-barrier-report", required=True, help="Path to the time-to-barrier JSON report.")
    parser.add_argument("--post-target-report", required=True, help="Path to the post-target JSON report.")
    parser.add_argument("--output", default=None, help="Output JSON path under data/replay_reports.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report.")
    return parser.parse_args(argv)


def _default_output() -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    return REPLAY_REPORTS_DIR / f"counterfactual_action_probe_{stamp}.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _validate_output_path(output_text: str | None) -> Path:
    raw_text = output_text or str(_default_output())
    normalized = _normalized_relative_text(raw_text)
    if normalized in PROTECTED_OUTPUTS:
        raise ValueError(f"refusing output path: {raw_text}")

    output_path = Path(raw_text)
    repo_root = Path(ROOT).resolve()
    replay_root = repo_root / REPLAY_REPORTS_DIR
    _refuse_symlinked_replay_root(repo_root, replay_root)
    logical_output = output_path if output_path.is_absolute() else repo_root / output_path
    resolved_output = logical_output.resolve()
    resolved_replay_root = replay_root.resolve()
    if not _is_relative_to(resolved_output, resolved_replay_root):
        raise ValueError(f"refusing output path outside {REPLAY_REPORTS_DIR}: {raw_text}")
    return resolved_output


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        output_path = _validate_output_path(args.output)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        time_to_barrier_report = _load_json(Path(args.time_to_barrier_report))
        post_target_report = _load_json(Path(args.post_target_report))
        report = build_action_report(
            time_to_barrier_report=time_to_barrier_report,
            post_target_report=post_target_report,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"action_candidates={report.get('actions_total', len(report.get('actions', [])))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
