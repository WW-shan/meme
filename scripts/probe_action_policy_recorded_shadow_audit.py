#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import action_policy_live_shadow as shadow  # noqa: E402


DEFAULT_SIGNAL_AUDIT = "data/signal_audit.jsonl"
DEFAULT_PAPER_TRADES = "data/paper_trades.jsonl"
DEFAULT_OUTPUT_JSON = "data/replay_reports/action_policy_recorded_shadow_audit.json"
DEFAULT_OUTPUT_MD = "data/replay_reports/action_policy_recorded_shadow_audit.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Summarize recorded in-process action-policy shadow audit fields",
    )
    parser.add_argument("--signal-audit", default=DEFAULT_SIGNAL_AUDIT)
    parser.add_argument("--paper-trades", default=DEFAULT_PAPER_TRADES)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--since", default=None)
    parser.add_argument("--until", default=None)
    parser.add_argument("--active-model", default=None)
    parser.add_argument("--decision", action="append", default=None, help="Signal decision to include; repeatable")
    parser.add_argument("--max-match-seconds", type=float, default=20.0)
    parser.add_argument("--max-sample-rows", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.max_match_seconds < 0.0:
        parser.error("--max-match-seconds must be non-negative")
    if args.max_sample_rows < 0:
        parser.error("--max-sample-rows must be non-negative")
    return args


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _assert_output(path_text: str, *, force: bool) -> Path:
    path = Path(path_text)
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    allowed_roots = [
        (PROJECT_ROOT / "data" / "replay_reports").resolve(),
        (PROJECT_ROOT / "docs" / "research").resolve(),
    ]
    resolved = resolved.resolve()
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise SystemExit(f"refusing output outside replay/research roots: {path_text}")
    if resolved.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing output without --force: {resolved}")
    return resolved


def main(argv=None):
    args = parse_args(argv)
    output_json = _assert_output(args.output_json, force=bool(args.force))
    output_md = _assert_output(args.output_md, force=bool(args.force))

    report = shadow.build_recorded_shadow_audit_report(
        signal_rows=shadow.load_jsonl(args.signal_audit),
        trade_rows=shadow.load_jsonl(args.paper_trades),
        since=args.since,
        until=args.until,
        active_model=args.active_model,
        decisions=tuple(args.decision or ("queued", "rejected")),
        max_match_seconds=float(args.max_match_seconds),
        max_sample_rows=int(args.max_sample_rows),
    )
    report["input_paths"] = {
        "signal_audit": args.signal_audit,
        "paper_trades": args.paper_trades,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(shadow.to_json_text(report), encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(shadow.recorded_shadow_to_markdown_text(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(
        "status={status} signals={signals} recorded={recorded} queued_recorded_used={used} matched={matched}".format(
            status=report["go_no_go"]["status"],
            signals=report["summary"]["signal_count"],
            recorded=report["summary"]["recorded_shadow_count"],
            used=report["summary"]["queued_recorded_shadow_used_count"],
            matched=report["summary"]["queued_recorded_shadow_used_matched_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
