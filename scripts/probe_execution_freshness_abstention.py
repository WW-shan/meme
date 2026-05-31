#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import execution_freshness_abstention_probe as probe  # noqa: E402


DEFAULT_PAPER_TRADES = "data/paper_trades.jsonl"
DEFAULT_SIGNAL_AUDIT = "data/signal_audit.jsonl"
REPLAY_REPORTS_DIR = Path("data/replay_reports")
PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Scan live real-trade freshness fields for read-only abstention candidates",
    )
    parser.add_argument("--paper-trades", default=DEFAULT_PAPER_TRADES)
    parser.add_argument("--signal-audit", default=DEFAULT_SIGNAL_AUDIT)
    parser.add_argument("--signal-match-tolerance-seconds", type=float, default=3.0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--since", default=None)
    parser.add_argument("--until", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output")
    parser.add_argument("--train-fraction", type=float, default=0.60)
    parser.add_argument("--validation-fraction", type=float, default=0.20)
    parser.add_argument("--min-train-selected", type=int, default=3)
    parser.add_argument("--min-train-loss-precision", type=float, default=0.60)
    parser.add_argument("--max-train-winner-count", type=int, default=4)
    parser.add_argument("--min-validation-selected", type=int, default=1)
    parser.add_argument("--max-validation-winner-count", type=int, default=0)
    parser.add_argument("--min-final-selected", type=int, default=1)
    parser.add_argument("--max-final-winner-count", type=int, default=1)
    parser.add_argument("--max-sample-rows", type=int, default=25)
    parser.add_argument(
        "--write-selected-trade-delta",
        action="store_true",
        help="Include validation/final trade-delta attribution for the selected proxy rule",
    )
    args = parser.parse_args(argv)
    if args.signal_match_tolerance_seconds < 0.0:
        parser.error("--signal-match-tolerance-seconds must be non-negative")
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


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output_path = _validate_output_path(args.output)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")
        report = probe.build_execution_freshness_abstention_report(
            trade_rows=probe.load_jsonl(args.paper_trades),
            signal_rows=probe.load_jsonl(args.signal_audit),
            signal_match_tolerance_seconds=args.signal_match_tolerance_seconds,
            since=args.since,
            until=args.until,
            train_fraction=args.train_fraction,
            validation_fraction=args.validation_fraction,
            min_train_selected=args.min_train_selected,
            min_train_loss_precision=args.min_train_loss_precision,
            max_train_winner_count=args.max_train_winner_count,
            min_validation_selected=args.min_validation_selected,
            max_validation_winner_count=args.max_validation_winner_count,
            min_final_selected=args.min_final_selected,
            max_final_winner_count=args.max_final_winner_count,
            max_sample_rows=args.max_sample_rows,
            include_trade_delta_attribution=bool(args.write_selected_trade_delta),
        )
        report["inputs"] = {
            "paper_trades": args.paper_trades,
            "signal_audit": args.signal_audit,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"outcome_tier={report.get('outcome_tier')}")
    print(f"decision={report.get('decision')}")
    selected = report.get("selected_candidate") or {}
    rule = selected.get("rule") if isinstance(selected, dict) else {}
    if isinstance(rule, dict):
        print(f"selected_rule={rule.get('label')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
