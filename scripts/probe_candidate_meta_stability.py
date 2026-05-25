#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import probe_candidate_meta_label as label_cli
from src.pipeline import candidate_meta_stability_probe as stability_probe


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/candidate_meta_stability_probe_{stamp}.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run rolling source-window stability checks for candidate meta-label probes",
    )
    parser.add_argument(
        "--time-to-barrier-report",
        action="append",
        required=True,
        help="Input time-to-barrier report JSON; repeat in chronological order",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--validation-report-count", action="append", type=int, default=[])
    parser.add_argument("--probability-threshold", action="append", type=float, default=[])
    parser.add_argument("--max-depth", action="append", type=int, default=[])
    parser.add_argument("--min-samples-leaf", action="append", type=int, default=[])
    parser.add_argument("--min-validation-selected", type=int, default=3)
    parser.add_argument("--min-train-selected", type=int, default=3)
    parser.add_argument("--min-stable-precision", type=float, default=0.5)
    parser.add_argument(
        "--candidate-filter",
        action="append",
        default=[],
        help="Decision-time numeric filter such as prob>=0.94; repeatable",
    )
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = _default_output()
    if not args.validation_report_count:
        args.validation_report_count = [1]
    if not args.probability_threshold:
        args.probability_threshold = [0.5]
    if not args.max_depth:
        args.max_depth = [3]
    if not args.min_samples_leaf:
        args.min_samples_leaf = [3]
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        input_paths = [Path(path) for path in args.time_to_barrier_report]
        output_path = label_cli._validate_output_path(args.output, input_paths=input_paths)
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        reports = [json.loads(path.read_text(encoding="utf-8")) for path in input_paths]
        candidate_filters = [
            label_cli._parse_candidate_filter(candidate_filter)
            for candidate_filter in args.candidate_filter
        ]
        report = stability_probe.build_candidate_meta_stability_report(
            time_to_barrier_reports=reports,
            source_names=[str(path) for path in input_paths],
            validation_report_counts=args.validation_report_count,
            probability_thresholds=args.probability_threshold,
            max_depths=args.max_depth,
            min_samples_leaf_values=args.min_samples_leaf,
            min_validation_selected=args.min_validation_selected,
            min_train_selected=args.min_train_selected,
            min_stable_precision=args.min_stable_precision,
            candidate_filters=candidate_filters,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(stability_probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_path}")
    print(f"stable_results={len(report.get('top_stable_results', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
