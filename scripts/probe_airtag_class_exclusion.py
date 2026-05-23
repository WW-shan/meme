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

from scripts import probe_support_action_policy as support_cli
from src.pipeline import airtag_class_exclusion_probe as probe


def _default_output() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"data/replay_reports/airtag_class_exclusion_probe_{stamp}.json"


def _parse_volume_cuts(text: str) -> tuple[float, ...]:
    parts = [part.strip() for part in str(text).split(",") if part.strip()]
    if not parts:
        raise ValueError("--volume-cuts must contain at least one numeric cut")
    cuts: list[float] = []
    for part in parts:
        try:
            cuts.append(float(part))
        except ValueError as exc:
            raise ValueError(f"invalid --volume-cuts value: {part}") from exc
    return tuple(cuts)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a read-only AirTag-class high-prob/high-volume exclusion probe",
    )
    parser.add_argument(
        "--time-to-barrier-report",
        action="append",
        required=True,
        help="Input time-to-barrier report JSON. Repeat for pooled frozen evidence.",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--min-prob", type=float, default=0.985, help="High-probability floor")
    parser.add_argument(
        "--min-pred-return",
        type=float,
        default=5.0,
        help="Positive PredReturn floor for the AirTag-class stratum",
    )
    parser.add_argument(
        "--min-volume-floor",
        type=float,
        default=0.75,
        help="Lower volume bound for the medium-volume comparison stratum",
    )
    parser.add_argument(
        "--high-volume-cut",
        type=float,
        default=1.5,
        help="High volume cut used for the AirTag-class watchpoint",
    )
    parser.add_argument(
        "--volume-cuts",
        default="1.25,1.5,1.75,2.0",
        help="Comma-separated volume cut sweep values",
    )
    parser.add_argument(
        "--max-candidate-sample",
        type=int,
        default=50,
        help="Max candidates to emit per stratum sample",
    )
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = _default_output()
    return args


def _resolved_input_paths(path_texts: list[str]) -> list[Path]:
    return [
        (Path(path_text) if Path(path_text).is_absolute() else PROJECT_ROOT / path_text).resolve()
        for path_text in path_texts
    ]


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        input_paths = [Path(path) for path in args.time_to_barrier_report]
        resolved_inputs = _resolved_input_paths(args.time_to_barrier_report)
        if len(set(resolved_inputs)) != len(resolved_inputs):
            raise ValueError("refusing duplicate time-to-barrier input reports")

        output_path = support_cli._validate_output_path(args.output, input_path=input_paths[0])
        if output_path in resolved_inputs:
            raise ValueError("refusing to overwrite input report")
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        volume_cuts = _parse_volume_cuts(args.volume_cuts)
        time_reports = [json.loads(path.read_text(encoding="utf-8")) for path in input_paths]
        report = probe.build_exclusion_probe_report(
            time_to_barrier_reports=time_reports,
            source_names=[str(path) for path in input_paths],
            min_prob=args.min_prob,
            min_pred_return=args.min_pred_return,
            min_volume_floor=args.min_volume_floor,
            high_volume_cut=args.high_volume_cut,
            volume_cuts=volume_cuts,
            max_candidate_sample=args.max_candidate_sample,
        )
        report["inputs"] = {"time_to_barrier_reports": [str(path) for path in input_paths]}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    watchpoint = report.get("airtag_class_watchpoint", {})
    print(f"wrote {output_path}")
    print(
        "decision={decision} false_positives={false_positives} symbols={symbols}".format(
            decision=report.get("decision"),
            false_positives=int(watchpoint.get("false_positive_count") or 0),
            symbols=",".join(str(symbol) for symbol in watchpoint.get("false_positive_symbols", [])),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
