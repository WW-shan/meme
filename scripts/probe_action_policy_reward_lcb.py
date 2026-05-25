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

from src.pipeline import action_policy_reward_lcb_probe as probe


PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/action_policy_reward_lcb_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a read-only bootstrap lower-confidence-bound diagnostic for action-policy reward reports",
    )
    parser.add_argument("--reward-report", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--confidence-level", type=float, default=0.95)
    parser.add_argument("--min-selected-per-family", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
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


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        reward_path = Path(args.reward_report)
        output_path = _validate_output_path(args.output, input_path=reward_path)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        report = probe.build_action_policy_reward_lcb_report(
            _load_json(reward_path),
            bootstrap_samples=args.bootstrap_samples,
            confidence_level=args.confidence_level,
            min_selected_per_family=args.min_selected_per_family,
            seed=args.seed,
        )
        report["inputs"] = {"reward_report": str(reward_path)}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(
        "decision={decision} validation_lcb_pct={validation_lcb} final_lcb_pct={final_lcb}".format(
            decision=report.get("decision"),
            validation_lcb=report.get("validation", {}).get("reward_lcb_pct", 0.0),
            final_lcb=report.get("final", {}).get("reward_lcb_pct", 0.0),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
