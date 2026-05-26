#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import accepted_entry_feature_contrast as probe


PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
REPLAY_REPORTS_DIR = Path("data/replay_reports")


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/accepted_entry_feature_contrast_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare decision-time features for accepted replay entries by realized trade outcome",
    )
    parser.add_argument("--trade-log", action="append", required=True, help="Replay trade-log JSONL file")
    parser.add_argument("--sample-cache", action="append", required=True, help="Replay sample cache pickle")
    parser.add_argument("--output", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--top-n", type=int, default=25)
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

    for input_path in input_paths:
        resolved_input = (input_path if input_path.is_absolute() else repo_root / input_path).resolve()
        if resolved_output == resolved_input:
            raise ValueError("refusing to overwrite input report")
    return resolved_output


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        trade_log_paths = [Path(path) for path in args.trade_log]
        sample_cache_paths = [Path(path) for path in args.sample_cache]
        output_path = _validate_output_path(
            args.output,
            input_paths=trade_log_paths + sample_cache_paths,
        )
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")
        if args.top_n <= 0:
            raise ValueError("--top-n must be positive")

        trade_rows = probe.load_trade_logs(trade_log_paths)
        sample_rows = probe.load_sample_caches(sample_cache_paths)
        report = probe.build_contrast_report(
            trade_rows=trade_rows,
            sample_rows=sample_rows,
            trade_log_sources=[str(path) for path in trade_log_paths],
            sample_sources=[str(path) for path in sample_cache_paths],
            top_n=args.top_n,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(
        "decision={decision} matched={matched} unmatched={unmatched}".format(
            decision=report.get("decision"),
            matched=report.get("match_summary", {}).get("matched_trade_count"),
            unmatched=report.get("match_summary", {}).get("unmatched_trade_count"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
