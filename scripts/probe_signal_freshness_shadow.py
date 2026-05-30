#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import reentry_probe, signal_freshness_shadow_probe as probe  # noqa: E402


DEFAULT_SIGNAL_AUDIT = "data/signal_audit.jsonl"
DEFAULT_COLLECTOR_STATE = "data/training/collector_runtime_state.json"
DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT_JSON = "data/replay_reports/signal_freshness_shadow_probe.json"
DEFAULT_OUTPUT_MD = "data/replay_reports/signal_freshness_shadow_probe.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate signal-level lifecycle freshness fields in read-only shadow mode")
    parser.add_argument("--signal-audit", default=DEFAULT_SIGNAL_AUDIT)
    parser.add_argument("--collector-state", default=DEFAULT_COLLECTOR_STATE)
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR)
    parser.add_argument("--recent-lifecycle-files", type=int, default=24)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--since", default=None)
    parser.add_argument("--until", default=None)
    parser.add_argument("--decision", action="append", default=None)
    parser.add_argument("--horizon-seconds", type=float, default=600.0)
    parser.add_argument("--quick-profit-seconds", type=float, default=120.0)
    parser.add_argument("--min-candidates", type=int, default=20)
    parser.add_argument("--min-selected", type=int, default=5)
    parser.add_argument("--min-correct-skip-precision", type=float, default=0.75)
    parser.add_argument("--max-opportunity-misses", type=int, default=0)
    parser.add_argument("--opportunity-penalty", type=float, default=2.0)
    parser.add_argument("--max-candidate-sample", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.recent_lifecycle_files < 0:
        parser.error("--recent-lifecycle-files must be non-negative")
    if args.horizon_seconds <= 0:
        parser.error("--horizon-seconds must be positive")
    if args.quick_profit_seconds <= 0:
        parser.error("--quick-profit-seconds must be positive")
    if args.min_candidates < 0 or args.min_selected < 0:
        parser.error("--min-candidates and --min-selected must be non-negative")
    if not 0.0 <= args.min_correct_skip_precision <= 1.0:
        parser.error("--min-correct-skip-precision must be in [0, 1]")
    if args.max_opportunity_misses < 0:
        parser.error("--max-opportunity-misses must be non-negative")
    if args.opportunity_penalty < 0.0:
        parser.error("--opportunity-penalty must be non-negative")
    if args.max_candidate_sample < 0:
        parser.error("--max-candidate-sample must be non-negative")
    return args


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _assert_output(path_text: str, *, force: bool) -> Path:
    path = Path(path_text)
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    resolved = resolved.resolve()
    allowed_root = (PROJECT_ROOT / "data" / "replay_reports").resolve()
    if not _is_relative_to(resolved, allowed_root):
        raise SystemExit(f"refusing output outside data/replay_reports: {path_text}")
    if resolved.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing output without --force: {resolved}")
    return resolved


def main(argv=None):
    args = parse_args(argv)
    output_json = _assert_output(args.output_json, force=bool(args.force))
    output_md = _assert_output(args.output_md, force=bool(args.force))
    lifecycle_paths = reentry_probe.latest_lifecycle_files(
        args.lifecycle_dir,
        limit=int(args.recent_lifecycle_files),
    )
    report = probe.build_signal_freshness_shadow_report(
        signal_rows=probe.load_jsonl(args.signal_audit),
        lifecycles=reentry_probe.load_lifecycles(
            collector_state_path=args.collector_state,
            lifecycle_paths=lifecycle_paths,
        ),
        since=args.since,
        until=args.until,
        decisions=tuple(args.decision or ("queued", "rejected")),
        horizon_seconds=float(args.horizon_seconds),
        quick_profit_seconds=float(args.quick_profit_seconds),
        min_candidates=int(args.min_candidates),
        min_selected=int(args.min_selected),
        min_correct_skip_precision=float(args.min_correct_skip_precision),
        max_opportunity_misses=int(args.max_opportunity_misses),
        opportunity_penalty=float(args.opportunity_penalty),
        max_candidate_sample=int(args.max_candidate_sample),
    )
    report["input_paths"] = {
        "signal_audit": args.signal_audit,
        "collector_state": args.collector_state,
        "lifecycle_dir": args.lifecycle_dir,
        "lifecycle_paths": [str(path) for path in lifecycle_paths],
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(probe.to_json_text(report), encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(probe.to_markdown_text(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(
        "outcome_tier={tier} decision={decision} freshness_candidates={count}".format(
            tier=report.get("outcome_tier"),
            decision=report.get("decision"),
            count=(report.get("candidate_counts") or {}).get("freshness_candidate_count"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
