#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import run_flow_abstention_replay as base


DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/flow_volume_abstention_replay_20260531.json"
LIVE_INITIAL_EQUITY_BNB = 0.005079303120051795
MAX_GRID_CANDIDATES = 16


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a bounded high-volume flow-abstention replay grid")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Replay grid JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--position-fraction", type=base._strict_live_fraction, default=base.LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=base._strict_live_fraction, default=base.LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=base._strict_max_open_positions, default=base.STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing replay report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def candidate_grid():
    candidates = []
    for min_prob, max_age, toxic_volume in itertools.product(
        (0.94, 0.98),
        (60.0, 300.0),
        (3.0, 3.73949, 5.0),
    ):
        candidates.append({
            "buy_flow_abstention_min_prob": min_prob,
            "buy_flow_abstention_max_age_seconds": max_age,
            "buy_flow_abstention_min_entry_volume_30s": 1.5,
            "buy_flow_abstention_min_entry_price_volatility": 0.0,
            "buy_flow_abstention_min_toxic_entry_volume_30s": toxic_volume,
        })
    if len(candidates) > MAX_GRID_CANDIDATES:
        raise RuntimeError(f"flow volume abstention grid has {len(candidates)} candidates; max is {MAX_GRID_CANDIDATES}")
    return iter(candidates)


def _base_overrides(args):
    return {
        "initial_equity_bnb": LIVE_INITIAL_EQUITY_BNB,
        "position_fraction": float(args.position_fraction),
        "max_position_fraction": float(args.max_position_fraction),
        "fixed_stake_bnb": None,
        "skip_all_in_replay": True,
        "max_open_positions": int(args.max_open_positions),
        "one_entry_per_token": True,
        "max_trades_per_token": 1,
    }


def _run_replay(args, *, split, overrides):
    from src.pipeline.model_replay import run_model_replay

    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        use_cache=args.use_cache,
        overrides=overrides,
        write_report=False,
    )


def main(argv=None):
    args = parse_args(argv)
    output_path = base._assert_output_writable(args.model_dir, args.output, force=bool(args.force))
    base_overrides = _base_overrides(args)

    validation_baseline_report = _run_replay(args, split="validation", overrides=base_overrides)
    validation_baseline_summary = base._summary(base._evaluation(validation_baseline_report))

    candidates = []
    for index, params in enumerate(candidate_grid()):
        candidate_overrides = dict(base_overrides)
        candidate_overrides.update(params)
        candidate_report = _run_replay(args, split="validation", overrides=candidate_overrides)
        candidate_evaluation = base._evaluation(candidate_report)
        summary = base._summary(candidate_evaluation)
        gate_details = base._gate_details(summary, validation_baseline_summary)
        candidates.append({
            "candidate_index": int(index),
            "params": dict(params),
            "summary": summary,
            "passes_acceptance_gate": all(gate_details.values()),
            "gate_details": gate_details,
            "evaluation": candidate_evaluation,
        })

    if not candidates:
        raise SystemExit("flow volume abstention replay grid produced no candidates")

    best_validation_raw_candidate = max(candidates, key=base._raw_candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=base._accepted_candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_baseline_report = _run_replay(args, split="final", overrides=base_overrides)
    final_baseline_summary = base._summary(base._evaluation(final_baseline_report))
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_report = _run_replay(args, split="final", overrides=final_candidate_overrides)
    final_candidate_evaluation = base._evaluation(final_candidate_report)
    final_candidate_summary = base._summary(final_candidate_evaluation)
    final_gate_details = base._gate_details(final_candidate_summary, final_baseline_summary)
    final_candidate = {
        "candidate_index": validation_selected["candidate_index"],
        "params": validation_selected["params"],
        "summary": final_candidate_summary,
        "passes_acceptance_gate": all(final_gate_details.values()),
        "gate_details": final_gate_details,
        "evaluation": final_candidate_evaluation,
    }
    final_confirmation = {
        "baseline": {
            "summary": final_baseline_summary,
            "evaluation": base._evaluation(final_baseline_report),
        },
        "candidate": final_candidate,
        "passes_acceptance_gate": bool(final_candidate["passes_acceptance_gate"]),
    }

    decision = (
        "accept"
        if best_validation_accepted is not None and final_confirmation["passes_acceptance_gate"]
        else "reject"
    )
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_dir": str(args.model_dir),
        "lifecycle_dir": str(args.lifecycle_dir),
        "hypothesis": (
            "A decision-time high-volume flow-abstention veto tests whether the zero-winner "
            "accepted-trade freshness/volume proxy survives strict replay gates."
        ),
        "strict_assumptions": base_overrides,
        "acceptance_gate": base._acceptance_gate(),
        "baseline": {
            "split": "validation",
            "summary": validation_baseline_summary,
            "evaluation": base._evaluation(validation_baseline_report),
        },
        "candidates": candidates,
        "best_validation_raw_candidate": best_validation_raw_candidate,
        "best_validation_candidate": validation_selected,
        "best_validation_accepted_candidate": best_validation_accepted,
        "selected_candidate": validation_selected,
        "best_candidate": validation_selected,
        "best_accepted_candidate": best_validation_accepted,
        "final_confirmation": final_confirmation,
        "decision": decision,
        "live_switch_evidence": False,
        "safe_for_live_switch": False,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(
        "decision={decision} validation_baseline_net_profit_bnb={baseline:.12f} "
        "best_validation_net_profit_bnb={best:.12f} "
        "final_confirmation_passed={final_passed} candidates={count} output={output}".format(
            decision=report["decision"],
            baseline=validation_baseline_summary["net_profit_bnb"],
            best=validation_selected["summary"]["net_profit_bnb"],
            final_passed=final_confirmation["passes_acceptance_gate"],
            count=len(candidates),
            output=str(output_path),
        )
    )
    return report


if __name__ == "__main__":
    main()
