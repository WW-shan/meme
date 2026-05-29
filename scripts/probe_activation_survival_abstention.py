#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import activation_survival_abstention_probe as probe


REPLAY_REPORTS_DIR = Path("data/replay_reports")
PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Train/validate a decision-time abstention scan for never-activated accepted candidates",
    )
    parser.add_argument("--train-report", required=True)
    parser.add_argument("--validation-report", required=True)
    parser.add_argument("--final-report", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output")
    parser.add_argument("--bad-class", action="append", default=None)
    parser.add_argument("--protected-class", action="append", default=None)
    parser.add_argument("--min-train-selected", type=int, default=3)
    parser.add_argument("--min-train-bad-precision", type=float, default=0.65)
    parser.add_argument("--max-train-protected", type=int, default=1)
    parser.add_argument("--min-validation-selected", type=int, default=1)
    parser.add_argument("--max-validation-protected", type=int, default=0)
    parser.add_argument("--min-final-selected", type=int, default=1)
    parser.add_argument("--max-final-protected", type=int, default=0)
    parser.add_argument("--post-target-window-seconds", type=float, default=60.0)
    parser.add_argument("--max-conditions", type=int, default=1)
    parser.add_argument("--max-atomic-rules", type=int, default=probe.DEFAULT_MAX_ATOMIC_RULES)
    return parser.parse_args(argv)


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


def _validate_output_path(output_text: str) -> Path:
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
    return resolved_output


def _load_json(path_text: str) -> dict:
    data = json.loads(Path(path_text).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path_text}")
    return data


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output_path = _validate_output_path(args.output)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")
        report = probe.build_activation_survival_abstention_report(
            train_report=_load_json(args.train_report),
            validation_report=_load_json(args.validation_report),
            final_report=_load_json(args.final_report),
            train_source_name=args.train_report,
            validation_source_name=args.validation_report,
            final_source_name=args.final_report,
            bad_classes=args.bad_class or probe.DEFAULT_BAD_CLASSES,
            protected_classes=args.protected_class or probe.DEFAULT_PROTECTED_CLASSES,
            min_train_selected=args.min_train_selected,
            min_train_bad_precision=args.min_train_bad_precision,
            max_train_protected=args.max_train_protected,
            min_validation_selected=args.min_validation_selected,
            max_validation_protected=args.max_validation_protected,
            min_final_selected=args.min_final_selected,
            max_final_protected=args.max_final_protected,
            post_target_window_seconds=args.post_target_window_seconds,
            max_conditions=args.max_conditions,
            max_atomic_rules=args.max_atomic_rules,
        )
        report["inputs"]["train_report"] = args.train_report
        report["inputs"]["validation_report"] = args.validation_report
        report["inputs"]["final_report"] = args.final_report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"outcome_tier={report.get('outcome_tier')}")
    print(f"decision={report.get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
