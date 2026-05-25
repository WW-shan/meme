#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_PAPER_TRADES = "data/paper_trades.jsonl"
DEFAULT_SIGNAL_AUDIT = "data/signal_audit.jsonl"
DEFAULT_COLLECTOR_STATE = "data/training/collector_runtime_state.json"
DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT_JSON = "data/replay_reports/live_trade_attribution.json"
DEFAULT_OUTPUT_MD = "data/replay_reports/live_trade_attribution.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a read-only live trade attribution refresh")
    parser.add_argument("--paper-trades", default=DEFAULT_PAPER_TRADES, help="paper_trades.jsonl path")
    parser.add_argument("--signal-audit", default=DEFAULT_SIGNAL_AUDIT, help="signal_audit.jsonl path")
    parser.add_argument("--collector-state", default=DEFAULT_COLLECTOR_STATE, help="collector runtime state JSON")
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR, help="directory containing lifecycle jsonl files")
    parser.add_argument(
        "--recent-lifecycle-files",
        type=int,
        default=1,
        help="number of recent lifecycle_incremental files to include",
    )
    parser.add_argument(
        "--lifecycle-file",
        action="append",
        default=[],
        help="additional lifecycle jsonl file; may be repeated",
    )
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON, help="output JSON report path")
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD, help="output markdown report path")
    parser.add_argument("--since", default=None, help="inclusive lower time bound for trade opens and signal decisions")
    parser.add_argument("--until", default=None, help="inclusive upper time bound for trade opens and signal decisions")
    parser.add_argument("--active-model", default=None, help="active model path or label to record in the report")
    parser.add_argument("--restart-anchor", default=None, help="optional inclusive restart-anchor trade filter")
    parser.add_argument("--near-min-prob", type=float, default=0.94, help="near-threshold lower probability")
    parser.add_argument("--primary-min-prob", type=float, default=0.98, help="primary threshold probability")
    parser.add_argument("--barrier-horizon-seconds", type=float, default=600.0, help="rejected signal path horizon")
    parser.add_argument("--quick-profit-seconds", type=float, default=120.0, help="quick-profit horizon for rejected paths")
    parser.add_argument("--minimum-same-shape-trades", type=int, default=7, help="minimum same-shape support before replay")
    parser.add_argument("--max-trade-sample", type=int, default=0, help="0 emits all trades")
    parser.add_argument("--max-candidate-sample", type=int, default=100, help="0 emits all rejected signal candidates")
    parser.add_argument("--force", action="store_true", help="overwrite existing outputs")
    args = parser.parse_args(argv)
    if args.max_trade_sample < 0:
        parser.error("--max-trade-sample must be non-negative")
    if args.max_candidate_sample < 0:
        parser.error("--max-candidate-sample must be non-negative")
    if args.recent_lifecycle_files < 0:
        parser.error("--recent-lifecycle-files must be non-negative")
    if args.minimum_same_shape_trades < 1:
        parser.error("--minimum-same-shape-trades must be at least 1")
    if args.barrier_horizon_seconds <= 0.0:
        parser.error("--barrier-horizon-seconds must be positive")
    if args.quick_profit_seconds <= 0.0:
        parser.error("--quick-profit-seconds must be positive")
    return args


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _protected_exact_paths() -> set[str]:
    return {
        ".env",
        ".env.example",
        "docs/goals/live-model-optimization-goal.md",
    }


def _allowed_output_roots() -> list[Path]:
    return [
        PROJECT_ROOT / "data" / "replay_reports",
        PROJECT_ROOT / "docs" / "research",
    ]


def _validate_output_path(output_text: str) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in _protected_exact_paths() or normalized.startswith("docs/goals/"):
        raise ValueError(f"refusing output path: {output_text}")

    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else PROJECT_ROOT / output_path
    resolved_output = logical_output.resolve()
    allowed_roots = [root.resolve() for root in _allowed_output_roots()]
    for allowed_root in allowed_roots:
        try:
            resolved_output.relative_to(allowed_root)
            return resolved_output
        except ValueError:
            continue
    allowed_text = ", ".join(str(root) for root in allowed_roots)
    raise ValueError(f"refusing output path outside allowed roots ({allowed_text}): {output_text}")


def _load_json(path: str | Path) -> dict:
    resolved = Path(path)
    if not resolved.exists():
        return {}
    return json.loads(resolved.read_text(encoding="utf-8"))


def _load_jsonl(path: str | Path) -> list[dict]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    rows = []
    with resolved.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _path_status(path: str | Path) -> dict:
    resolved = Path(path)
    exists = resolved.exists()
    sha256 = None
    if exists and resolved.is_file():
        digest = hashlib.sha256()
        with resolved.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        sha256 = digest.hexdigest()
    return {
        "path": str(resolved),
        "exists": exists,
        "size_bytes": int(resolved.stat().st_size) if exists and resolved.is_file() else 0,
        "mtime_ns": int(resolved.stat().st_mtime_ns) if exists else None,
        "sha256": sha256,
    }


def main(argv=None) -> int:
    probe = importlib.import_module("src.pipeline.live_trade_attribution_probe")

    args = parse_args(argv)
    try:
        output_json = _validate_output_path(args.output_json)
        output_md = _validate_output_path(args.output_md)
        if output_json.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_json}")
        if output_md.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_md}")

        trade_rows = _load_jsonl(args.paper_trades)
        signal_rows = _load_jsonl(args.signal_audit)
        collector_state = _load_json(args.collector_state)
        lifecycle_paths = list(args.lifecycle_file or [])
        lifecycle_paths.extend(
            str(path)
            for path in probe.reentry_probe.latest_lifecycle_files(
                args.lifecycle_dir,
                limit=args.recent_lifecycle_files,
            )
        )
        lifecycle_paths = list(dict.fromkeys(lifecycle_paths))
        lifecycle_maps = []
        if collector_state:
            lifecycle_maps.append(probe.reentry_probe.extract_lifecycles_from_runtime_state(collector_state))
        for lifecycle_path in lifecycle_paths:
            lifecycle_maps.append(probe.reentry_probe.extract_lifecycles_from_rows(_load_jsonl(lifecycle_path)))
        lifecycles = probe.reentry_probe.merge_lifecycle_maps(*lifecycle_maps)

        report = probe.build_attribution_report(
            trade_rows=trade_rows,
            signal_rows=signal_rows,
            lifecycles=lifecycles,
            since=args.since,
            until=args.until,
            active_model=args.active_model,
            restart_anchor=args.restart_anchor,
            near_min_prob=args.near_min_prob,
            primary_min_prob=args.primary_min_prob,
            barrier_horizon_seconds=args.barrier_horizon_seconds,
            quick_profit_seconds=args.quick_profit_seconds,
            minimum_same_shape_trades=args.minimum_same_shape_trades,
            max_trade_sample=args.max_trade_sample,
            max_candidate_sample=args.max_candidate_sample,
        )
        report["input_paths"] = {
            "paper_trades": args.paper_trades,
            "signal_audit": args.signal_audit,
            "collector_state": args.collector_state,
            "lifecycle_dir": args.lifecycle_dir,
            "lifecycle_files": lifecycle_paths,
        }
        report["input_status"] = {
            "fingerprints_are_run_snapshot": True,
            "mutable_live_inputs": True,
            "paper_trades": _path_status(args.paper_trades),
            "signal_audit": _path_status(args.signal_audit),
            "collector_state": _path_status(args.collector_state),
            "lifecycle_files": [_path_status(path) for path in lifecycle_paths],
        }

        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(probe.to_json_text(report), encoding="utf-8")
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(probe.to_markdown_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(f"decision={report.get('go_no_go', {}).get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
