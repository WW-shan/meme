#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Replay an existing trained hybrid model without retraining")
    parser.add_argument("--model-dir", required=True, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=None, help="Optional replay report JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--split", choices=("validation", "final"), default="final", help="Lifecycle split to replay")
    parser.add_argument("--max-open-positions", type=int, default=8, help="Maximum simultaneous open positions")
    parser.add_argument("--include-trade-log", action="store_true", help="Write trade logs as a sidecar and report sidecar metadata")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.set_defaults(use_cache=True)

    parser.add_argument("--threshold", type=float, default=None, help="Override buy probability threshold")
    parser.add_argument("--stop-loss", type=float, default=None, help="Override hard stop-loss")
    parser.add_argument("--trailing-start-pct", type=float, default=None, help="Override profit threshold for trailing stop activation")
    parser.add_argument("--trailing-stop-pct", type=float, default=None, help="Override drawdown from peak that triggers trailing stop")
    parser.add_argument("--entry-price-protection-pct", type=float, default=None, help="Override maximum delayed entry fill slippage fraction")
    parser.add_argument("--max-pending-entries", type=int, default=None, help="Override maximum simultaneous pending delayed buy fills")
    return parser.parse_args(argv)


def _overrides_from_args(args):
    mapping = {
        "threshold": "buy_threshold",
        "stop_loss": "stop_loss",
        "trailing_start_pct": "trailing_start_pct",
        "trailing_stop_pct": "trailing_stop_pct",
        "entry_price_protection_pct": "entry_price_protection_pct",
        "max_pending_entries": "max_pending_entries",
    }
    return {
        override_key: getattr(args, arg_name)
        for arg_name, override_key in mapping.items()
        if getattr(args, arg_name) is not None
    }


def main(argv=None):
    args = parse_args(argv)

    from src.pipeline.model_replay import run_model_replay

    report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        cache_dir=args.cache_dir,
        split=args.split,
        max_open_positions=args.max_open_positions,
        include_trade_log=args.include_trade_log,
        use_cache=args.use_cache,
        overrides=_overrides_from_args(args),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))
    return report


if __name__ == "__main__":
    main()
