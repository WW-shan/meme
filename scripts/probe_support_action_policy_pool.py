#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import probe_support_action_policy as single_probe_cli
from src.pipeline import support_action_policy_probe as probe


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a pooled read-only support report for rejected-signal action rules",
    )
    parser.add_argument(
        "--time-to-barrier-report",
        action="append",
        required=True,
        help="Input time-to-barrier report JSON. Repeat for pooled evidence.",
    )
    parser.add_argument("--output", default=None, help="Output JSON report path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument(
        "--min-selected",
        type=int,
        default=3,
        help="Minimum selected candidates for an eligible rule",
    )
    parser.add_argument(
        "--min-pooled-selected",
        type=int,
        default=30,
        help="Minimum target-rule selected candidates across pooled evidence",
    )
    parser.add_argument(
        "--min-pooled-positive",
        type=int,
        default=12,
        help="Minimum target-rule positive candidates across pooled evidence",
    )
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = single_probe_cli._default_output().replace(
            "support_action_policy_probe_",
            "support_action_policy_pool_",
        )
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

        output_path = single_probe_cli._validate_output_path(args.output, input_path=input_paths[0])
        if output_path in resolved_inputs:
            raise ValueError("refusing to overwrite input report")
        if output_path.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_path}")

        time_reports = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in input_paths
        ]
        report = probe.build_pooled_support_report(
            time_to_barrier_reports=time_reports,
            source_names=[str(path) for path in input_paths],
            min_selected=args.min_selected,
            min_pooled_selected=args.min_pooled_selected,
            min_pooled_positive=args.min_pooled_positive,
        )
        report["inputs"] = {"time_to_barrier_reports": [str(path) for path in input_paths]}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    gate = report.get("evidence_gate", {})
    print(f"wrote {output_path}")
    print(
        "decision={decision} selected={selected} positives={positives}".format(
            decision=report.get("decision"),
            selected=int(gate.get("selected_count") or 0),
            positives=int(gate.get("positive_count") or 0),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
