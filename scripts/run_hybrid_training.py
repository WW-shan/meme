#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.train_hybrid import run_hybrid_training


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run hybrid CatBoost+PPO training")
    parser.add_argument("--output-dir", default="data/models", help="Output directory for artifacts")
    parser.add_argument("--total-timesteps", type=int, default=20000, help="PPO total timesteps")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = {
        "output_dir": args.output_dir,
        "total_timesteps": args.total_timesteps,
    }
    result = run_hybrid_training(config)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
