#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _parse_float_list(raw):
    return [float(part.strip()) for part in str(raw).split(",") if part.strip()]


def _parse_trailing_pairs(raw):
    pairs = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        start, stop = part.split(":", 1)
        pairs.append((float(start), float(stop)))
    return pairs


def _candidate_grid(thresholds, stop_losses, trailing_pairs, max_open_positions):
    candidates = []
    for threshold in thresholds:
        for stop_loss in stop_losses:
            for trailing_start, trailing_stop in trailing_pairs:
                candidates.append({
                    "buy_threshold": float(threshold),
                    "stop_loss": float(stop_loss),
                    "trailing_start_pct": float(trailing_start),
                    "trailing_stop_pct": float(trailing_stop),
                    "max_open_positions": int(max_open_positions),
                })
    return candidates


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Search replay parameters on validation split and report sealed final replay")
    parser.add_argument("--model-dir", required=True, help="Directory containing trained hybrid model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=None, help="Search report JSON path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for generated eval sample cache")
    parser.add_argument("--max-open-positions", type=int, default=8, help="Live capacity for replay search")
    parser.add_argument("--thresholds", default="0.75,0.8,0.825,0.85,0.875,0.9", help="Comma-separated buy thresholds")
    parser.add_argument("--stop-losses", default="-0.2,-0.25,-0.3", help="Comma-separated stop-loss values")
    parser.add_argument("--trailing-pairs", default="0.2:0.1,0.2:0.15,0.25:0.15", help="Comma-separated trailing_start:trailing_stop pairs")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild eval samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    from src.pipeline.model_replay import run_parameter_search

    candidates = _candidate_grid(
        _parse_float_list(args.thresholds),
        _parse_float_list(args.stop_losses),
        _parse_trailing_pairs(args.trailing_pairs),
        args.max_open_positions,
    )
    result = run_parameter_search(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        cache_dir=args.cache_dir,
        candidates=candidates,
        max_open_positions=args.max_open_positions,
        use_cache=args.use_cache,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    main()
