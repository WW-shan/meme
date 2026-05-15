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
    parser.add_argument("--execution-calibration-file", default=None, help="Optional JSON report used to seed live-style replay controls")

    parser.add_argument("--initial-equity-bnb", type=float, default=None, help="Override replay starting wallet balance in BNB")
    parser.add_argument("--position-fraction", type=float, default=None, help="Override fraction of available equity used per entry")
    parser.add_argument("--max-position-fraction", type=float, default=None, help="Override maximum equity fraction per entry")
    stake_group = parser.add_mutually_exclusive_group()
    stake_group.add_argument("--fixed-stake-bnb", type=float, default=None, help="Override fixed BNB stake per entry")
    stake_group.add_argument("--no-fixed-stake-bnb", action="store_true", help="Use fractional live sizing instead of a fixed BNB stake")

    parser.add_argument("--threshold", type=float, default=None, help="Override buy probability threshold")
    parser.add_argument("--stop-loss", type=float, default=None, help="Override hard stop-loss")
    parser.add_argument("--trailing-start-pct", type=float, default=None, help="Override profit threshold for trailing stop activation")
    parser.add_argument("--trailing-stop-pct", type=float, default=None, help="Override drawdown from peak that triggers trailing stop")
    parser.add_argument("--min-policy-hold-seconds", type=int, default=None, help="Override minimum age before policy sell signals can close")
    parser.add_argument("--entry-delay-seconds", type=int, default=None, help="Override delayed buy submit latency in seconds")
    parser.add_argument("--entry-max-fill-wait-seconds", type=int, default=None, help="Override maximum delayed buy fill lag")
    parser.add_argument("--exit-delay-seconds", type=int, default=None, help="Override delayed sell fill latency in seconds")
    parser.add_argument("--exit-max-fill-wait-seconds", type=int, default=None, help="Override maximum delayed sell fill lag")
    parser.add_argument("--entry-price-protection-pct", type=float, default=None, help="Override maximum delayed entry fill slippage fraction")
    parser.add_argument("--entry-execution-failure-rate", type=float, default=None, help="Override deterministic buy execution failure rate")
    parser.add_argument("--exit-execution-failure-rate", type=float, default=None, help="Override deterministic sell execution failure rate")
    parser.add_argument("--max-pending-entries", type=int, default=None, help="Override maximum simultaneous pending delayed buy fills")
    parser.add_argument("--min-entry-score", type=float, default=None, help="Override minimum predicted entry-value score required to buy")
    parser.add_argument("--min-entry-volume-30s", type=float, default=None, help="Override minimum 30s buy volume feature required to buy")
    parser.add_argument("--entry-fixed-cost-bnb", type=float, default=None, help="Override fixed BNB cost per buy transaction")
    parser.add_argument("--exit-fixed-cost-bnb", type=float, default=None, help="Override fixed BNB cost per sell transaction")
    parser.add_argument("--skip-all-in-replay", action="store_true", help="Skip the additional all-in comparison replay for faster iteration")
    parser.add_argument(
        "--entry-ranking-mode",
        choices=("chronological", "buy_prob", "entry_value"),
        default=None,
        help="Override replay entry ordering when simultaneous candidates compete for limited slots",
    )
    return parser.parse_args(argv)


def _load_execution_calibration(path):
    if not path:
        return {}
    calibration_path = Path(path)
    if not calibration_path.exists():
        raise FileNotFoundError(f"execution calibration file not found: {calibration_path}")
    with calibration_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        return {}
    overrides = payload.get("replay_overrides", {})
    return dict(overrides) if isinstance(overrides, dict) else {}


def _overrides_from_args(args):
    mapping = {
        "initial_equity_bnb": "initial_equity_bnb",
        "position_fraction": "position_fraction",
        "max_position_fraction": "max_position_fraction",
        "fixed_stake_bnb": "fixed_stake_bnb",
        "threshold": "buy_threshold",
        "stop_loss": "stop_loss",
        "trailing_start_pct": "trailing_start_pct",
        "trailing_stop_pct": "trailing_stop_pct",
        "min_policy_hold_seconds": "min_policy_hold_seconds",
        "entry_delay_seconds": "entry_delay_seconds",
        "entry_max_fill_wait_seconds": "entry_max_fill_wait_seconds",
        "exit_delay_seconds": "exit_delay_seconds",
        "exit_max_fill_wait_seconds": "exit_max_fill_wait_seconds",
        "entry_price_protection_pct": "entry_price_protection_pct",
        "entry_execution_failure_rate": "entry_execution_failure_rate",
        "exit_execution_failure_rate": "exit_execution_failure_rate",
        "max_pending_entries": "max_pending_entries",
        "min_entry_score": "min_entry_score",
        "min_entry_volume_30s": "min_entry_volume_30s",
        "entry_fixed_cost_bnb": "entry_fixed_cost_bnb",
        "exit_fixed_cost_bnb": "exit_fixed_cost_bnb",
        "entry_ranking_mode": "entry_ranking_mode",
        "skip_all_in_replay": "skip_all_in_replay",
    }
    overrides = _load_execution_calibration(getattr(args, "execution_calibration_file", None))
    overrides.update({
        override_key: getattr(args, arg_name)
        for arg_name, override_key in mapping.items()
        if getattr(args, arg_name) is not None
    })
    preserve_null_keys = set()
    if getattr(args, "no_fixed_stake_bnb", False):
        overrides["fixed_stake_bnb"] = None
        preserve_null_keys.add("fixed_stake_bnb")
    if not bool(getattr(args, "skip_all_in_replay", False)):
        overrides.pop("skip_all_in_replay", None)
    return {
        key: value
        for key, value in overrides.items()
        if value is not None or key in preserve_null_keys
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
