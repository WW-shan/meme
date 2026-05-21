#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import run_primary_score_scalp_replay as _base

DEFAULT_OUTPUT = "data/replay_reports/active_flow_quick_profit_replay_20260522_v95.json"


def _has_output_flag(argv_list):
    for arg in argv_list:
        flag = str(arg).split("=", 1)[0]
        if flag.startswith("--") and "--output".startswith(flag):
            return True
    return False


def parse_args(argv=None):
    argv_list = list(sys.argv[1:] if argv is None else argv)
    args = _base.parse_args(argv_list)
    if not _has_output_flag(argv_list):
        args.output = DEFAULT_OUTPUT
    return args


def candidate_grid():
    # Deliberately only search the active-flow count proxy. Overlap/reentry filters
    # are deferred until replay missingness can match support-probe semantics.
    total_buys_floors = [6.0, 10.0, 14.0]
    for min_total_buys in total_buys_floors:
        yield {
            "buy_quick_profit_overlay_min_prob": 0.985,
            "buy_quick_profit_overlay_min_pred_return": 10.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.25,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            "buy_quick_profit_overlay_min_total_buys": min_total_buys,
        }


def _eval_samples_for_split(args, base_overrides, split, cache):
    if split in cache:
        return cache[split]

    from src.pipeline.model_replay import (
        apply_model_schema_feature_flags,
        live_replay_config_from_manifest,
        load_manifest,
        load_or_build_samples,
        resolve_replay_split,
    )

    manifest = load_manifest(args.model_dir)
    replay_config = live_replay_config_from_manifest(
        manifest,
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=dict(base_overrides),
    )
    replay_config = apply_model_schema_feature_flags(replay_config, args.model_dir)
    replay_split = resolve_replay_split(manifest, args.lifecycle_dir)
    if split == "validation":
        files = replay_split.validation_files
        excluded_tokens = replay_split.excluded_validation_tokens
    elif split == "final":
        files = replay_split.eval_files
        excluded_tokens = replay_split.excluded_final_tokens
    else:
        raise ValueError(f"unsupported replay split: {split}")

    samples = load_or_build_samples(
        replay_config,
        files,
        excluded_tokens,
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    cache[split] = samples
    return samples


def main(argv=None):
    args = parse_args(argv)
    if not math.isclose(args.position_fraction, _base.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"position_fraction must be exactly {_base.LIVE_POSITION_CAP}")
    if not math.isclose(args.max_position_fraction, _base.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"max_position_fraction must be exactly {_base.LIVE_POSITION_CAP}")
    if args.max_open_positions != _base.STRICT_MAX_OPEN_POSITIONS:
        raise SystemExit(f"max_open_positions must be exactly {_base.STRICT_MAX_OPEN_POSITIONS}")
    _base._assert_output_writable(args.model_dir, args.output, force=bool(args.force))

    from src.pipeline.model_replay import run_model_replay

    base_overrides = _base._base_overrides(args)
    eval_sample_cache = {}
    validation_eval_samples = _eval_samples_for_split(args, base_overrides, "validation", eval_sample_cache)
    final_eval_samples = _eval_samples_for_split(args, base_overrides, "final", eval_sample_cache)
    validation_base_overrides = dict(base_overrides)
    validation_base_overrides["eval_samples"] = validation_eval_samples
    final_base_overrides = dict(base_overrides)
    final_base_overrides["eval_samples"] = final_eval_samples
    validation_baseline_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="validation",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=validation_base_overrides,
        use_cache=args.use_cache,
        write_report=False,
    )
    validation_baseline_summary = _base._summary(_base._evaluation(validation_baseline_report))

    candidates = []
    for index, params in enumerate(candidate_grid()):
        overrides = dict(base_overrides)
        overrides.update(params)
        overrides["eval_samples"] = validation_eval_samples
        report = run_model_replay(
            model_dir=args.model_dir,
            lifecycle_dir=args.lifecycle_dir,
            output_path=None,
            cache_dir=args.cache_dir,
            split="validation",
            max_open_positions=args.max_open_positions,
            include_trade_log=False,
            overrides=overrides,
            use_cache=args.use_cache,
            write_report=False,
        )
        evaluation = _base._evaluation(report)
        summary = _base._summary(evaluation)
        gate_details = _base._gate_details(summary, validation_baseline_summary)
        candidates.append({
            "candidate_index": int(index),
            "params": params,
            "summary": summary,
            "passes_acceptance_gate": all(gate_details.values()),
            "gate_details": gate_details,
            "evaluation": evaluation,
        })

    best_validation_raw_candidate = max(candidates, key=_base._candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=_base._candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_baseline_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="final",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=final_base_overrides,
        use_cache=args.use_cache,
        write_report=False,
    )
    final_baseline_summary = _base._summary(_base._evaluation(final_baseline_report))
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_overrides["eval_samples"] = final_eval_samples
    final_candidate_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="final",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=final_candidate_overrides,
        use_cache=args.use_cache,
        write_report=False,
    )
    final_candidate_evaluation = _base._evaluation(final_candidate_report)
    final_candidate_summary = _base._summary(final_candidate_evaluation)
    final_gate_details = _base._gate_details(final_candidate_summary, final_baseline_summary)
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
            "evaluation": _base._evaluation(final_baseline_report),
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
        "strict_assumptions": base_overrides,
        "acceptance_gate": _base._acceptance_gate(),
        "baseline": {
            "split": "validation",
            "summary": validation_baseline_summary,
            "evaluation": _base._evaluation(validation_baseline_report),
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

    output_path = Path(args.output)
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
