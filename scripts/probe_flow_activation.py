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


def _default_output_path() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/flow_activation_probe_{stamp}.json"


def _read_path_snapshot(path: str | Path) -> tuple[dict, bytes]:
    resolved = Path(path)
    stat_before = resolved.stat() if resolved.exists() and resolved.is_file() else None
    data = resolved.read_bytes() if stat_before is not None else b""
    exists_after_read = resolved.exists() and resolved.is_file()
    stat_after = resolved.stat() if exists_after_read else None
    fingerprint = {
        "path": str(resolved),
        "exists": stat_before is not None,
        "exists_after_read": exists_after_read,
        "size_bytes": len(data),
        "path_size_bytes_before_read": int(stat_before.st_size) if stat_before is not None else 0,
        "path_size_bytes_after_read": int(stat_after.st_size) if stat_after is not None else 0,
        "mtime_ns": int(stat_before.st_mtime_ns) if stat_before is not None else None,
        "mtime_ns_after_read": int(stat_after.st_mtime_ns) if stat_after is not None else None,
        "changed_during_read": (
            stat_before is not None
            and (
                stat_after is None
                or int(stat_before.st_size) != int(stat_after.st_size)
                or int(stat_before.st_mtime_ns) != int(stat_after.st_mtime_ns)
            )
        ),
        "snapshot_read_mode": "single_read_bytes",
        "sha256": None,
    }
    if fingerprint["exists"]:
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
        "input_fingerprint_policy": (
            "Each input is read once into bytes; hashes and JSON parsing use those same bytes."
        ),
    }


def _dedupe_paths(paths) -> list:
    unique = []
    seen = set()
    for path in paths:
        resolved = Path(path).resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _build_input_status(
    *,
    signal_audit: dict,
    collector_state: dict,
    lifecycle_dir: str | Path,
    lifecycle_paths: list[dict],
) -> dict:
    lifecycle_dir_path = Path(lifecycle_dir)
    return {
        "signal_audit": signal_audit,
        "collector_state": collector_state,
        "lifecycle_dir": {
            "path": str(lifecycle_dir_path),
            "exists": lifecycle_dir_path.exists(),
        },
        "lifecycle_paths": lifecycle_paths,
        "existing_lifecycle_path_count": sum(1 for row in lifecycle_paths if row.get("exists")),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a read-only flow activation fakeout probe")
    parser.add_argument("--signal-audit", default="data/signal_audit.jsonl", help="Signal audit JSONL input")
    parser.add_argument(
        "--collector-state",
        default="data/training/collector_runtime_state.json",
        help="Collector runtime state JSON input",
    )
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle JSONL files")
    parser.add_argument(
        "--lifecycle-file",
        action="append",
        default=None,
        help="Explicit lifecycle JSONL file to include; may be repeated",
    )
    parser.add_argument(
        "--recent-lifecycle-files",
        type=int,
        default=4,
        help="Number of latest lifecycle files to include from lifecycle-dir",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--since", default=None, help="Only include signal decisions at or after this timestamp")
    parser.add_argument("--lookback-seconds", type=float, default=30, help="Signal trajectory lookback window")
    parser.add_argument("--flow-window-seconds", type=float, default=30, help="Pre-anchor buy/sell flow window")
    parser.add_argument("--horizon-seconds", type=float, default=300, help="Post-anchor path scoring horizon")
    parser.add_argument("--max-candidates", type=int, default=None, help="Maximum per-token candidates to score")
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = _default_output_path()
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    probe = importlib.import_module("src.pipeline.flow_activation_probe")
    reentry_probe = probe.reentry_probe

    lifecycle_paths = _dedupe_paths(
        list(args.lifecycle_file or [])
        + list(reentry_probe.latest_lifecycle_files(args.lifecycle_dir, limit=args.recent_lifecycle_files))
    )

    signal_fingerprint, signal_bytes = _read_path_snapshot(args.signal_audit)
    signal_rows = list(_iter_jsonl_bytes(signal_bytes)) if signal_fingerprint["exists"] else []
    signal_events = list(probe.iter_signal_events(signal_rows))

    collector_lifecycles = {}
    lifecycle_maps = []
    collector_fingerprint, collector_bytes = _read_path_snapshot(args.collector_state)
    if collector_fingerprint["exists"] and collector_bytes.strip():
        collector_lifecycles = reentry_probe.extract_lifecycles_from_runtime_state(
            json.loads(collector_bytes.decode("utf-8"))
        )

    lifecycle_fingerprints = []
    for lifecycle_path in lifecycle_paths:
        lifecycle_fingerprint, lifecycle_bytes = _read_path_snapshot(lifecycle_path)
        lifecycle_fingerprints.append(lifecycle_fingerprint)
        if lifecycle_fingerprint["exists"]:
            lifecycle_maps.append(probe.extract_lifecycles_from_rows_for_flow(_iter_jsonl_bytes(lifecycle_bytes)))
    lifecycles = probe.merge_lifecycle_maps_for_flow(*lifecycle_maps)

    report = probe.build_flow_activation_report(
        signal_events=signal_events,
        lifecycle_by_token=lifecycles,
        collector_lifecycles=collector_lifecycles,
        since=args.since,
        max_candidates=args.max_candidates,
        lookback_seconds=args.lookback_seconds,
        flow_window_seconds=args.flow_window_seconds,
        horizon_seconds=args.horizon_seconds,
    )
    report["inputs"] = {
        "signal_audit": args.signal_audit,
        "collector_state": args.collector_state,
        "lifecycle_dir": args.lifecycle_dir,
        "recent_lifecycle_files": args.recent_lifecycle_files,
        "lifecycle_files": [str(path) for path in lifecycle_paths],
        "since": args.since,
        "lookback_seconds": args.lookback_seconds,
        "flow_window_seconds": args.flow_window_seconds,
        "horizon_seconds": args.horizon_seconds,
        "max_candidates": args.max_candidates,
    }
    report["input_status"] = _build_input_status(
        signal_audit=signal_fingerprint,
        collector_state=collector_fingerprint,
        lifecycle_dir=args.lifecycle_dir,
        lifecycle_paths=lifecycle_fingerprints,
    )
    report["input_fingerprints"] = {
        "signal_audit": signal_fingerprint,
        "collector_state": collector_fingerprint,
        "lifecycle_files": lifecycle_fingerprints,
    }
    report["input_fingerprint_policy"] = _input_fingerprint_policy()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    flow_candidate_count = report.get("candidate_counts", {}).get("flow_activation_candidates", 0)
    accepted_count = report.get("candidate_counts", {}).get("accepted_by_probe", 0)
    print(f"wrote {output_path}")
    print(f"flow_activation_candidates={flow_candidate_count}")
    print(f"accepted_by_probe={accepted_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
