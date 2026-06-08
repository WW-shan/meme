#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import action_policy_live_shadow as shadow  # noqa: E402
from src.pipeline import reentry_probe  # noqa: E402


DEFAULT_SIGNAL_AUDIT = "data/signal_audit.jsonl"
DEFAULT_COLLECTOR_STATE = "data/training/collector_runtime_state.json"
DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT_JSON = "data/replay_reports/action_policy_recorded_shadow_path_attribution.json"
DEFAULT_OUTPUT_MD = "data/replay_reports/action_policy_recorded_shadow_path_attribution.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Attribute recorded action-policy shadow routes to post-signal price paths",
    )
    parser.add_argument("--signal-audit", default=DEFAULT_SIGNAL_AUDIT)
    parser.add_argument("--collector-state", default=DEFAULT_COLLECTOR_STATE)
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR)
    parser.add_argument("--recent-lifecycle-files", type=int, default=24)
    parser.add_argument("--lifecycle-file", action="append", default=[])
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--since", default=None)
    parser.add_argument("--until", default=None)
    parser.add_argument("--active-model", default=None)
    parser.add_argument("--decision", action="append", default=None, help="Signal decision to include; repeatable")
    parser.add_argument("--horizon-seconds", type=float, default=600.0)
    parser.add_argument("--quick-profit-seconds", type=float, default=120.0)
    parser.add_argument("--min-route-path-support", type=int, default=7)
    parser.add_argument("--min-quick-profit-precision", type=float, default=0.6)
    parser.add_argument("--max-sample-rows", type=int, default=100)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.recent_lifecycle_files < 0:
        parser.error("--recent-lifecycle-files must be non-negative")
    if args.horizon_seconds <= 0.0 or not math.isfinite(args.horizon_seconds):
        parser.error("--horizon-seconds must be positive and finite")
    if args.quick_profit_seconds <= 0.0 or not math.isfinite(args.quick_profit_seconds):
        parser.error("--quick-profit-seconds must be positive and finite")
    if args.quick_profit_seconds > args.horizon_seconds:
        parser.error("--quick-profit-seconds must be less than or equal to --horizon-seconds")
    if args.min_route_path_support < 1:
        parser.error("--min-route-path-support must be at least 1")
    if not math.isfinite(args.min_quick_profit_precision) or not 0.0 <= args.min_quick_profit_precision <= 1.0:
        parser.error("--min-quick-profit-precision must be in [0, 1]")
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
    resolved = resolved.resolve()
    allowed_roots = [
        (PROJECT_ROOT / "data" / "replay_reports").resolve(),
        (PROJECT_ROOT / "docs" / "research").resolve(),
    ]
    if not any(_is_relative_to(resolved, root) for root in allowed_roots):
        raise SystemExit(f"refusing output outside replay/research roots: {path_text}")
    if resolved.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing output without --force: {resolved}")
    return resolved


def _load_lifecycles(args):
    lifecycle_paths = list(args.lifecycle_file or [])
    lifecycle_paths.extend(
        str(path)
        for path in reentry_probe.latest_lifecycle_files(
            args.lifecycle_dir,
            limit=args.recent_lifecycle_files,
        )
    )
    lifecycle_paths = list(dict.fromkeys(lifecycle_paths))
    lifecycles = reentry_probe.load_lifecycles(
        collector_state_path=args.collector_state,
        lifecycle_paths=lifecycle_paths,
    )
    return lifecycles, lifecycle_paths


def main(argv=None):
    args = parse_args(argv)
    output_json = _assert_output(args.output_json, force=bool(args.force))
    output_md = _assert_output(args.output_md, force=bool(args.force))
    lifecycles, lifecycle_paths = _load_lifecycles(args)

    report = shadow.build_recorded_shadow_path_attribution_report(
        signal_rows=shadow.load_jsonl(args.signal_audit),
        lifecycles=lifecycles,
        since=args.since,
        until=args.until,
        active_model=args.active_model,
        decisions=tuple(args.decision or ("queued", "rejected")),
        horizon_seconds=float(args.horizon_seconds),
        quick_profit_seconds=float(args.quick_profit_seconds),
        min_route_path_support=int(args.min_route_path_support),
        min_quick_profit_precision=float(args.min_quick_profit_precision),
        max_sample_rows=int(args.max_sample_rows),
    )
    report["input_paths"] = {
        "signal_audit": args.signal_audit,
        "collector_state": args.collector_state,
        "lifecycle_dir": args.lifecycle_dir,
        "lifecycle_files": lifecycle_paths,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(shadow.to_json_text(report), encoding="utf-8")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(shadow.recorded_shadow_path_to_markdown_text(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(
        "status={status} signals={signals} recorded={recorded} path_evaluable={path_evaluable} qtp_path={qtp_path} qtp_precision={qtp_precision}".format(
            status=report["go_no_go"]["status"],
            signals=report["summary"]["signal_count"],
            recorded=report["summary"]["recorded_shadow_count"],
            path_evaluable=report["summary"]["path_evaluable_count"],
            qtp_path=report["go_no_go"]["quick_take_profit_path_count"],
            qtp_precision=report["go_no_go"]["quick_take_profit_precision"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
