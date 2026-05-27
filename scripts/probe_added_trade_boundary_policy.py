#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import added_trade_boundary_policy_probe as probe


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Probe a support-constrained cost-sensitive keep rule for added candidate trades"
    )
    parser.add_argument("--input", required=True, help="Runner-retention replay report with trade-delta attribution")
    parser.add_argument("--output", required=True, help="JSON report output path")
    parser.add_argument("--loss-cost", type=float, default=3.0, help="Penalty multiplier for kept losing added trades")
    parser.add_argument("--min-keep-count", type=int, default=4, help="Minimum validation added trades kept by a rule")
    parser.add_argument("--min-reject-count", type=int, default=2, help="Minimum validation added trades rejected by a rule")
    parser.add_argument("--max-conditions", type=int, default=1, help="Maximum AND conditions in the selected keep rule")
    parser.add_argument("--beam-width", type=int, default=50, help="Maximum prefix rules expanded per conjunction depth")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing report without --force: {output_path}")
    payload = probe.load_trade_delta_payload(Path(args.input))
    report = probe.build_report_from_trade_delta_payload(
        payload,
        loss_cost=float(args.loss_cost),
        min_keep_count=int(args.min_keep_count),
        min_reject_count=int(args.min_reject_count),
        max_conditions=int(args.max_conditions),
        beam_width=int(args.beam_width),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    print(
        "decision={decision} selected_rule={rule} validation_delta={validation_delta:.6f} "
        "final_delta={final_delta:.6f} output={output}".format(
            decision=report["decision"],
            rule=report["selected_rule"],
            validation_delta=report["validation"]["cost_adjusted_utility_delta"],
            final_delta=report["final"]["cost_adjusted_utility_delta"],
            output=output_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
