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
    parser = argparse.ArgumentParser(description="Run offline candidate-level rare-runner ranking probe")
    parser.add_argument("--model-dir", required=True, help="Directory containing incumbent model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument(
        "--output",
        default="data/replay_reports/v96_candidate_ranker_probe_20260519.json",
        help="Probe report JSON output path",
    )
    parser.add_argument("--train-split-ratio", type=float, default=0.60, help="Chronological train file ratio")
    parser.add_argument("--validation-split-ratio", type=float, default=0.20, help="Chronological validation file ratio")
    parser.add_argument("--min-validation-files", type=int, default=1, help="Minimum validation lifecycle files")
    parser.add_argument("--min-eval-files", type=int, default=1, help="Minimum final evaluation lifecycle files")
    parser.add_argument("--max-samples-per-token", type=int, default=120, help="Sample cap per token")
    parser.add_argument("--sample-cache-dir", default=".cache/model_replay", help="Probe sample cache directory")
    parser.add_argument("--no-cache", action="store_true", help="Disable probe sample cache")
    parser.add_argument("--max-lifecycle-files", type=int, default=None, help="Use only the latest N lifecycle files")
    parser.add_argument(
        "--lifecycle-file",
        action="append",
        default=None,
        help="Explicit lifecycle file path to include; repeat to make the probe input stable",
    )
    parser.add_argument("--top-k-per-group", type=int, default=1, help="Top ranked candidates per time bucket")
    parser.add_argument("--group-bucket-seconds", type=int, default=30, help="Candidate competition bucket size")
    parser.add_argument(
        "--relevance-mode",
        choices=("tiered_runner", "risk_adjusted_return"),
        default="tiered_runner",
        help="Training relevance target for the candidate ranker",
    )
    parser.add_argument(
        "--include-shadow-score-rejects",
        action="store_true",
        help="Include high-probability primary score rejects as a separate probe-only candidate source",
    )
    parser.add_argument("--shadow-min-prob", type=float, default=None, help="Minimum buy probability for shadow rejects")
    parser.add_argument(
        "--shadow-max-entry-score",
        type=float,
        default=None,
        help="Maximum entry score for shadow rejects; defaults to min_entry_score",
    )
    parser.add_argument(
        "--shadow-min-entry-volume-30s",
        type=float,
        default=None,
        help="Minimum 30s entry volume for shadow rejects; defaults to min_entry_volume_30s",
    )
    parser.add_argument(
        "--shadow-min-entry-price-volatility",
        type=float,
        default=None,
        help="Minimum entry price volatility for shadow rejects; defaults to min_entry_price_volatility",
    )
    parser.add_argument(
        "--shadow-max-age-seconds",
        type=float,
        default=None,
        help="Maximum token age for shadow rejects; defaults to max_entry_age_seconds",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    from src.pipeline.candidate_ranker_probe import run_candidate_ranker_probe

    report = run_candidate_ranker_probe(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        train_split_ratio=args.train_split_ratio,
        validation_split_ratio=args.validation_split_ratio,
        min_validation_files=args.min_validation_files,
        min_eval_files=args.min_eval_files,
        max_samples_per_token=args.max_samples_per_token,
        sample_cache_dir=None if args.no_cache else args.sample_cache_dir,
        top_k_per_group=args.top_k_per_group,
        group_bucket_seconds=args.group_bucket_seconds,
        max_lifecycle_files=args.max_lifecycle_files,
        lifecycle_files=args.lifecycle_file,
        include_shadow_score_rejects=args.include_shadow_score_rejects,
        shadow_min_prob=args.shadow_min_prob,
        shadow_max_entry_score=args.shadow_max_entry_score,
        shadow_min_entry_volume_30s=args.shadow_min_entry_volume_30s,
        shadow_min_entry_price_volatility=args.shadow_min_entry_price_volatility,
        shadow_max_age_seconds=args.shadow_max_age_seconds,
        relevance_mode=args.relevance_mode,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, default=str))
    return report


if __name__ == "__main__":
    main()
