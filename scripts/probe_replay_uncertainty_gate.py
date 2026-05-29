#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import replay_uncertainty_gate_probe as probe


REPLAY_REPORTS_DIR = Path("data/replay_reports")
PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a read-only uncertainty-aware replay gate from paired trade-delta attribution",
    )
    parser.add_argument("--report", default=None, help="Replay report containing selected trade-delta attribution")
    parser.add_argument("--validation-trade-delta", default=None, help="Standalone validation trade-delta JSON")
    parser.add_argument("--final-trade-delta", default=None, help="Standalone final trade-delta JSON")
    parser.add_argument("--candidate-id", default="unnamed_candidate")
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=4000)
    parser.add_argument("--confidence-level", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--min-research-positive-probability", type=float, default=0.55)
    parser.add_argument("--min-shadow-positive-probability", type=float, default=0.80)
    parser.add_argument("--min-split-contributions", type=int, default=10)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output")
    args = parser.parse_args(argv)
    if not args.report and not (args.validation_trade_delta and args.final_trade_delta):
        parser.error("provide --report or both --validation-trade-delta and --final-trade-delta")
    if args.bootstrap_samples <= 0:
        parser.error("--bootstrap-samples must be positive")
    if not 0.0 < args.confidence_level < 1.0:
        parser.error("--confidence-level must be between 0 and 1")
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


def _load_json(path_text: str | None) -> dict | None:
    if path_text is None:
        return None
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
        report = _load_json(args.report)
        gate = probe.build_replay_uncertainty_gate_report(
            replay_report=report,
            validation_trade_delta=_load_json(args.validation_trade_delta),
            final_trade_delta=_load_json(args.final_trade_delta),
            source_report_name=args.report,
            candidate_id=args.candidate_id,
            bootstrap_samples=int(args.bootstrap_samples),
            confidence_level=float(args.confidence_level),
            seed=int(args.seed),
            min_research_positive_probability=float(args.min_research_positive_probability),
            min_shadow_positive_probability=float(args.min_shadow_positive_probability),
            min_split_contributions=int(args.min_split_contributions),
        )
        gate["inputs"] = {
            "report": args.report,
            "validation_trade_delta": args.validation_trade_delta,
            "final_trade_delta": args.final_trade_delta,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(gate), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"outcome_tier={gate.get('outcome_tier')}")
    print(f"decision={gate.get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
