#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_LIVE_ATTRIBUTION = "data/replay_reports/live_trade_attribution_20260526_runner_retention_label_probe_round.json"
DEFAULT_OUTPUT = "data/replay_reports/runner_retention_label_support_20260526.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a read-only runner-retention label support probe")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument("--live-attribution", default=DEFAULT_LIVE_ATTRIBUTION)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output report")
    parser.add_argument("--train-split-ratio", type=float, default=0.60)
    parser.add_argument("--validation-split-ratio", type=float, default=0.20)
    parser.add_argument("--min-validation-files", type=int, default=1)
    parser.add_argument("--min-eval-files", type=int, default=1)
    parser.add_argument("--max-samples-per-token", type=int, default=80)
    parser.add_argument("--sample-cache-dir", default=".cache/model_replay")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--max-lifecycle-files", type=int, default=None)
    parser.add_argument("--lifecycle-file", action="append", default=None)
    parser.add_argument("--include-shadow-score-rejects", action="store_true")
    parser.add_argument("--shadow-min-prob", type=float, default=None)
    parser.add_argument("--shadow-max-entry-score", type=float, default=None)
    parser.add_argument("--shadow-min-entry-volume-30s", type=float, default=None)
    parser.add_argument("--shadow-min-entry-price-volatility", type=float, default=None)
    parser.add_argument("--shadow-max-age-seconds", type=float, default=None)
    parser.add_argument("--group-bucket-seconds", type=int, default=30)
    parser.add_argument("--horizon-seconds", type=float, default=600.0)
    parser.add_argument("--quick-profit-seconds", type=float, default=120.0)
    parser.add_argument("--slow-min-plus25-seconds", type=float, default=180.0)
    parser.add_argument("--min-train-positives", type=int, default=5)
    parser.add_argument("--min-validation-positives", type=int, default=3)
    parser.add_argument("--min-final-positives", type=int, default=3)
    parser.add_argument("--min-live-positives", type=int, default=3)
    return parser.parse_args(argv)


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _validate_output_path(output_text: str) -> Path:
    normalized = _normalized_relative_text(output_text)
    protected_exact = {".env", ".env.example", "docs/goals/live-model-optimization-goal.md"}
    if normalized in protected_exact or normalized.startswith("docs/goals/"):
        raise ValueError(f"refusing output path: {output_text}")
    output = Path(output_text)
    return output.resolve() if output.is_absolute() else (PROJECT_ROOT / output).resolve()


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output = _validate_output_path(args.output)
        if output.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output}")
        from src.pipeline.runner_retention_label_probe import run_runner_retention_label_probe

        report = run_runner_retention_label_probe(
            model_dir=args.model_dir,
            lifecycle_dir=args.lifecycle_dir,
            live_attribution_path=args.live_attribution,
            output_path=str(output),
            train_split_ratio=args.train_split_ratio,
            validation_split_ratio=args.validation_split_ratio,
            min_validation_files=args.min_validation_files,
            min_eval_files=args.min_eval_files,
            max_samples_per_token=args.max_samples_per_token,
            sample_cache_dir=None if args.no_cache else args.sample_cache_dir,
            max_lifecycle_files=args.max_lifecycle_files,
            lifecycle_files=args.lifecycle_file,
            include_shadow_score_rejects=args.include_shadow_score_rejects,
            shadow_min_prob=args.shadow_min_prob,
            shadow_max_entry_score=args.shadow_max_entry_score,
            shadow_min_entry_volume_30s=args.shadow_min_entry_volume_30s,
            shadow_min_entry_price_volatility=args.shadow_min_entry_price_volatility,
            shadow_max_age_seconds=args.shadow_max_age_seconds,
            group_bucket_seconds=args.group_bucket_seconds,
            horizon_seconds=args.horizon_seconds,
            quick_profit_seconds=args.quick_profit_seconds,
            slow_min_plus25_seconds=args.slow_min_plus25_seconds,
            min_train_positives=args.min_train_positives,
            min_validation_positives=args.min_validation_positives,
            min_final_positives=args.min_final_positives,
            min_live_positives=args.min_live_positives,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output}")
    print(f"offline_status={report['support_gate']['offline_status']}")
    print(f"decision={report['go_no_go']['status']}")
    print(json.dumps(report["support_gate"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

