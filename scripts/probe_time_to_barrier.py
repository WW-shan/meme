#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/time_to_barrier_probe_{stamp}.json"


def _read_path_snapshot(path: str | Path) -> tuple[dict, bytes]:
    resolved = Path(path)
    stat_before = resolved.stat() if resolved.exists() and resolved.is_file() else None
    data = resolved.read_bytes() if stat_before is not None else b""
    stat_after = resolved.stat() if resolved.exists() and resolved.is_file() else None
    fingerprint = {
        "path": str(resolved),
        "exists": stat_before is not None,
        "size_bytes": len(data),
        "path_size_bytes_before_read": int(stat_before.st_size) if stat_before is not None else 0,
        "path_size_bytes_after_read": int(stat_after.st_size) if stat_after is not None else 0,
        "mtime_ns": int(stat_before.st_mtime_ns) if stat_before is not None else None,
        "mtime_ns_after_read": int(stat_after.st_mtime_ns) if stat_after is not None else None,
        "changed_during_read": (
            stat_before is not None
            and stat_after is not None
            and (
                int(stat_before.st_size) != int(stat_after.st_size)
                or int(stat_before.st_mtime_ns) != int(stat_after.st_mtime_ns)
            )
        ),
        "snapshot_read_mode": "single_read_bytes",
        "sha256": None,
    }
    if not fingerprint["exists"] or not resolved.is_file():
        return fingerprint, data

    fingerprint["sha256"] = hashlib.sha256(data).hexdigest()
    return fingerprint, data


def _fingerprint_path(path: str | Path) -> dict:
    fingerprint, _data = _read_path_snapshot(path)
    return fingerprint


def _iter_jsonl_bytes(data: bytes):
    for line in data.decode("utf-8").splitlines():
        text = line.strip()
        if text:
            yield json.loads(text)


def _input_fingerprint_policy() -> dict:
    return {
        "mutable_live_inputs": True,
        "fingerprints_are_run_snapshot": True,
        "snapshot_read_mode": "single_read_bytes",
        "current_paths_may_change_after_run": True,
        "note": "Each input is read once into bytes; hashes and parsing use those same bytes. Live collector/bot paths may change after the report is written.",
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a read-only time-to-barrier probe for rejected signals")
    parser.add_argument("--signal-audit", default="data/signal_audit.jsonl", help="Signal audit JSONL input")
    parser.add_argument(
        "--collector-state",
        default="data/training/collector_runtime_state.json",
        help="Collector runtime state JSON input",
    )
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle JSONL files")
    parser.add_argument(
        "--recent-lifecycle-files",
        type=int,
        default=1,
        help="Number of latest lifecycle files to include from lifecycle-dir",
    )
    parser.add_argument(
        "--lifecycle-file",
        action="append",
        default=None,
        help="Explicit lifecycle JSONL file to include; may be repeated",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--since", default=None, help="Only include rejected signal decisions at or after this timestamp")
    parser.add_argument("--until", default=None, help="Only include rejected signal decisions at or before this timestamp")
    parser.add_argument("--horizon-seconds", type=int, default=600, help="Barrier scoring horizon in seconds")
    parser.add_argument(
        "--quick-profit-seconds",
        type=int,
        default=120,
        help="Max seconds for a +25 barrier to count as quick profit",
    )
    parser.add_argument(
        "--max-candidate-sample",
        type=int,
        default=100,
        help="Max candidates to emit in candidate_sample; 0 emits all scored candidates",
    )
    args = parser.parse_args(argv)
    if args.max_candidate_sample < 0:
        parser.error("--max-candidate-sample must be non-negative")
    if args.output is None:
        args.output = _default_output()
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    probe = importlib.import_module("src.pipeline.time_to_barrier_probe")
    reentry_probe = probe.reentry_probe

    lifecycle_paths = list(args.lifecycle_file or [])
    lifecycle_paths.extend(reentry_probe.latest_lifecycle_files(args.lifecycle_dir, limit=args.recent_lifecycle_files))

    signal_fingerprint, signal_bytes = _read_path_snapshot(args.signal_audit)
    signal_rows = list(_iter_jsonl_bytes(signal_bytes)) if signal_fingerprint["exists"] else []

    lifecycle_maps = []
    collector_fingerprint, collector_bytes = _read_path_snapshot(args.collector_state)
    if collector_fingerprint["exists"] and collector_bytes.strip():
        lifecycle_maps.append(
            reentry_probe.extract_lifecycles_from_runtime_state(json.loads(collector_bytes.decode("utf-8")))
        )
    lifecycle_fingerprints = []
    for lifecycle_path in lifecycle_paths:
        lifecycle_fingerprint, lifecycle_bytes = _read_path_snapshot(lifecycle_path)
        lifecycle_fingerprints.append(lifecycle_fingerprint)
        if lifecycle_fingerprint["exists"]:
            lifecycle_maps.append(reentry_probe.extract_lifecycles_from_rows(_iter_jsonl_bytes(lifecycle_bytes)))
    lifecycles = reentry_probe.merge_lifecycle_maps(*lifecycle_maps)

    report = probe.build_probe_report(
        signal_rows=signal_rows,
        lifecycles=lifecycles,
        horizon_seconds=args.horizon_seconds,
        quick_profit_seconds=args.quick_profit_seconds,
        since=args.since,
        until=args.until,
        max_candidate_sample=args.max_candidate_sample,
    )
    report["inputs"] = {
        "signal_audit": args.signal_audit,
        "collector_state": args.collector_state,
        "lifecycle_dir": args.lifecycle_dir,
        "recent_lifecycle_files": args.recent_lifecycle_files,
        "lifecycle_files": [str(path) for path in lifecycle_paths],
        "since": args.since,
        "until": args.until,
    }
    report["input_status"] = reentry_probe.build_input_status(
        paper_trades="data/paper_trades.jsonl",
        signal_audit=args.signal_audit,
        collector_state=args.collector_state,
        lifecycle_dir=args.lifecycle_dir,
        lifecycle_paths=lifecycle_paths,
    )
    report["input_fingerprints"] = {
        "signal_audit": signal_fingerprint,
        "collector_state": collector_fingerprint,
        "lifecycle_files": lifecycle_fingerprints,
    }
    report["input_fingerprint_policy"] = _input_fingerprint_policy()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    to_json_text = getattr(probe, "to_json_text", reentry_probe.to_json_text)
    output_path.write_text(to_json_text(report), encoding="utf-8")
    print(f"wrote {output_path}")
    print(f"per_token_candidates={report.get('candidate_counts', {}).get('per_token_candidates', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
