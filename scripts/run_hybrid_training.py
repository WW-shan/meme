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
    parser = argparse.ArgumentParser(description="Run hybrid CatBoost+PPO training")
    parser.add_argument("--output-dir", default="data/models", help="Output directory for artifacts")
    parser.add_argument("--total-timesteps", type=int, default=20000, help="PPO total timesteps")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--sample-mode", default="trade_event", help="DatasetBuilder sample mode")
    parser.add_argument("--max-sample-age-seconds", type=int, default=180, help="Max sample age in seconds")
    parser.add_argument("--target-label-column", default="max_return_pct", help="Label column for buy target")
    parser.add_argument("--target-threshold-value", type=float, default=80.0, help="Threshold for positive buy label")
    parser.add_argument("--buy-min-precision", type=float, default=0.10, help="Min precision for buy threshold selection")
    parser.add_argument("--train-split-ratio", type=float, default=0.8, help="Train split ratio for lifecycle file partitioning")
    parser.add_argument("--min-eval-files", type=int, default=1, help="Minimum number of files reserved for evaluation")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    from src.pipeline.train_hybrid import run_hybrid_training

    config = {
        "output_dir": args.output_dir,
        "total_timesteps": args.total_timesteps,
        "lifecycle_dir": args.lifecycle_dir,
        "sample_mode": args.sample_mode,
        "max_sample_age_seconds": args.max_sample_age_seconds,
        "target_label_column": args.target_label_column,
        "target_threshold_value": args.target_threshold_value,
        "buy_min_precision": args.buy_min_precision,
        "train_split_ratio": args.train_split_ratio,
        "min_eval_files": args.min_eval_files,
    }
    result = run_hybrid_training(config)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
