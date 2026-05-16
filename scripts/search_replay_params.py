#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MAX_LIVE_POSITION_FRACTION = 0.10


def _parse_float_list(raw, label="values"):
    try:
        values = [float(part.strip()) for part in str(raw).split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be comma-separated floats") from exc
    if not values:
        raise argparse.ArgumentTypeError(f"{label} must contain at least one value")
    return values


def _parse_trailing_pairs(raw):
    pairs = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise argparse.ArgumentTypeError("trailing pairs must use trailing_start:trailing_stop format")
        start, stop = part.split(":", 1)
        try:
            pairs.append((float(start), float(stop)))
        except ValueError as exc:
            raise argparse.ArgumentTypeError("trailing pairs must contain float values") from exc
    if not pairs:
        raise argparse.ArgumentTypeError("trailing pairs must contain at least one pair")
    return pairs


def _parse_entry_ranking_modes(raw):
    modes = [part.strip().lower() for part in str(raw).split(",") if part.strip()]
    if not modes:
        raise argparse.ArgumentTypeError("entry ranking modes must contain at least one value")
    allowed = {"chronological", "buy_prob", "entry_value"}
    invalid = sorted(set(modes) - allowed)
    if invalid:
        raise argparse.ArgumentTypeError(f"entry ranking modes must be one of: {', '.join(sorted(allowed))}")
    return modes


def _parse_min_entry_scores(raw):
    scores = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        if part.lower() in {"none", "null", "off"}:
            scores.append(None)
            continue
        try:
            scores.append(float(part))
        except ValueError as exc:
            raise argparse.ArgumentTypeError("min-entry-scores must be comma-separated floats or none") from exc
    if not scores:
        return [None]
    return scores


def _parse_min_policy_holds(raw):
    holds = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        if part.lower() in {"none", "null", "off"}:
            holds.append(None)
            continue
        try:
            holds.append(max(0, int(part)))
        except ValueError as exc:
            raise argparse.ArgumentTypeError("min-policy-holds must be comma-separated integers or none") from exc
    if not holds:
        return [None]
    return holds


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


def _validate_live_sizing_args(args, parser):
    for attr, option in (
        ("position_fraction", "--position-fraction"),
        ("max_position_fraction", "--max-position-fraction"),
    ):
        value = getattr(args, attr)
        if value is not None and float(value) > MAX_LIVE_POSITION_FRACTION + 1e-12:
            parser.error(f"{option} must be <= {MAX_LIVE_POSITION_FRACTION:.2f} for live model selection")

    if args.fixed_stake_bnb is None or args.initial_equity_bnb in (None, 0):
        return
    fixed_fraction = float(args.fixed_stake_bnb) / float(args.initial_equity_bnb)
    if fixed_fraction > MAX_LIVE_POSITION_FRACTION + 1e-12:
        parser.error(
            f"--fixed-stake-bnb must be <= {MAX_LIVE_POSITION_FRACTION:.2f} of --initial-equity-bnb "
            "for live model selection"
        )


def _candidate_grid(
    thresholds,
    stop_losses,
    trailing_pairs,
    max_open_positions,
    entry_ranking_modes=None,
    min_entry_scores=None,
    min_policy_holds=None,
):
    if not thresholds:
        raise argparse.ArgumentTypeError("thresholds must contain at least one value")
    if not stop_losses:
        raise argparse.ArgumentTypeError("stop-losses must contain at least one value")
    if not trailing_pairs:
        raise argparse.ArgumentTypeError("trailing pairs must contain at least one pair")

    modes = list(entry_ranking_modes or ["chronological"])
    scores = list(min_entry_scores or [None])
    holds = list(min_policy_holds or [None])
    candidates = []
    for threshold in thresholds:
        for stop_loss in stop_losses:
            for trailing_start, trailing_stop in trailing_pairs:
                for mode in modes:
                    for min_entry_score in scores:
                        for min_policy_hold in holds:
                            candidate = {
                                "buy_threshold": float(threshold),
                                "stop_loss": float(stop_loss),
                                "trailing_start_pct": float(trailing_start),
                                "trailing_stop_pct": float(trailing_stop),
                                "max_open_positions": int(max_open_positions),
                            }
                            if mode != "chronological":
                                candidate["entry_ranking_mode"] = str(mode)
                            if min_entry_score is not None:
                                candidate["min_entry_score"] = float(min_entry_score)
                            if min_policy_hold is not None:
                                candidate["min_policy_hold_seconds"] = int(min_policy_hold)
                            candidates.append(candidate)
    return candidates


def _build_parser():
    parser = argparse.ArgumentParser(description="Search replay parameters on validation split and report sealed final replay")
    parser.add_argument("--model-dir", required=True, help="Directory containing trained hybrid model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=None, help="Search report JSON path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for generated eval sample cache")
    parser.add_argument("--max-open-positions", type=int, default=8, help="Live capacity for replay search")
    parser.add_argument("--thresholds", default="0.75,0.8,0.825,0.85,0.875,0.9", help="Comma-separated buy thresholds")
    parser.add_argument("--stop-losses", default="-0.2,-0.25,-0.3", help="Comma-separated stop-loss values")
    parser.add_argument("--trailing-pairs", default="0.2:0.1,0.2:0.15,0.25:0.15", help="Comma-separated trailing_start:trailing_stop pairs")
    parser.add_argument("--entry-ranking-modes", default="chronological", help="Comma-separated entry ordering modes: chronological,buy_prob,entry_value")
    parser.add_argument("--min-entry-scores", default="none", help="Comma-separated minimum entry-value scores or none")
    parser.add_argument("--min-policy-holds", default="none", help="Comma-separated minimum policy hold seconds or none")
    parser.add_argument("--execution-calibration-file", default=None, help="Optional JSON report used to seed live-style replay controls")
    parser.add_argument("--initial-equity-bnb", type=float, default=None, help="Override replay starting wallet balance in BNB")
    parser.add_argument("--position-fraction", type=float, default=None, help="Override fraction of available equity used per entry")
    parser.add_argument("--max-position-fraction", type=float, default=None, help="Override maximum equity fraction per entry")
    stake_group = parser.add_mutually_exclusive_group()
    stake_group.add_argument("--fixed-stake-bnb", type=float, default=None, help="Override fixed BNB stake per entry")
    stake_group.add_argument("--no-fixed-stake-bnb", action="store_true", help="Use fractional live sizing instead of a fixed BNB stake")
    parser.add_argument("--entry-fixed-cost-bnb", type=float, default=None, help="Optional fixed BNB cost per buy transaction")
    parser.add_argument("--exit-fixed-cost-bnb", type=float, default=None, help="Optional fixed BNB cost per sell transaction")
    parser.add_argument("--fast-selection", action="store_true", help="Use lightweight validation replays for grid selection; final replay remains full quality")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild eval samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser


def parse_args(argv=None):
    return _build_parser().parse_args(argv)


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    _validate_live_sizing_args(args, parser)
    try:
        candidates = _candidate_grid(
            _parse_float_list(args.thresholds, "thresholds"),
            _parse_float_list(args.stop_losses, "stop-losses"),
            _parse_trailing_pairs(args.trailing_pairs),
            args.max_open_positions,
            _parse_entry_ranking_modes(args.entry_ranking_modes),
            _parse_min_entry_scores(args.min_entry_scores),
            _parse_min_policy_holds(args.min_policy_holds),
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    from src.pipeline.model_replay import run_parameter_search
    base_overrides = dict(_load_execution_calibration(args.execution_calibration_file))
    base_overrides.update({
        k: v for k, v in {
            "initial_equity_bnb": args.initial_equity_bnb,
            "position_fraction": args.position_fraction,
            "max_position_fraction": args.max_position_fraction,
            "fixed_stake_bnb": args.fixed_stake_bnb,
            "entry_fixed_cost_bnb": args.entry_fixed_cost_bnb,
            "exit_fixed_cost_bnb": args.exit_fixed_cost_bnb,
        }.items() if v is not None
    })
    if args.no_fixed_stake_bnb:
        base_overrides["fixed_stake_bnb"] = None

    result = run_parameter_search(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=args.output,
        cache_dir=args.cache_dir,
        candidates=candidates,
        max_open_positions=args.max_open_positions,
        base_overrides=base_overrides,
        fast_selection=args.fast_selection,
        use_cache=args.use_cache,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return result


if __name__ == "__main__":
    main()
