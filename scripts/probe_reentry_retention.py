#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import reentry_probe


def _default_output_path() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).astimezone(reentry_probe.ANALYSIS_TZ).strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/reentry_retention_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Probe stop-loss re-entry retention from read-only live artifacts")
    parser.add_argument("--paper-trades", default="data/paper_trades.jsonl")
    parser.add_argument("--signal-audit", default="data/signal_audit.jsonl")
    parser.add_argument("--collector-state", default="data/training/collector_runtime_state.json")
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument(
        "--recent-lifecycle-files",
        type=int,
        default=1,
        help="Number of latest lifecycle JSONL files to include with collector state; use 0 for active state only",
    )
    parser.add_argument("--output", default=None)
    return parser.parse_args(argv)


def _load_jsonl_if_exists(path: str | Path) -> list[dict]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    return list(reentry_probe.iter_jsonl(resolved))


def main(argv=None) -> int:
    args = parse_args(argv)
    output_path = Path(args.output or _default_output_path())
    lifecycle_paths = reentry_probe.latest_lifecycle_files(
        args.lifecycle_dir,
        limit=max(0, int(args.recent_lifecycle_files or 0)),
    )

    report = reentry_probe.build_probe_report(
        trade_rows=_load_jsonl_if_exists(args.paper_trades),
        signal_rows=_load_jsonl_if_exists(args.signal_audit),
        lifecycles=reentry_probe.load_lifecycles(
            collector_state_path=args.collector_state,
            lifecycle_paths=lifecycle_paths,
        ),
    )
    report["inputs"] = {
        "paper_trades": str(args.paper_trades),
        "signal_audit": str(args.signal_audit),
        "collector_state": str(args.collector_state),
        "lifecycle_paths": [str(path) for path in lifecycle_paths],
    }
    report["input_status"] = reentry_probe.build_input_status(
        paper_trades=args.paper_trades,
        signal_audit=args.signal_audit,
        collector_state=args.collector_state,
        lifecycle_dir=args.lifecycle_dir,
        lifecycle_paths=lifecycle_paths,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(reentry_probe.to_json_text(report), encoding="utf-8")

    counts = report["candidate_counts"]
    print(f"wrote {output_path}")
    print(
        "stoploss_reentry="
        f"{counts['stoploss_reentry']} accepted_stoploss_reentry={counts['accepted_stoploss_reentry']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
