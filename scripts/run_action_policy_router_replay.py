#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_action_policy_candidate_gate_replay import (
    DEFAULT_MODEL_DIR,
    DEFAULT_TRAIN_ACCEPTED_REPORTS,
    DEFAULT_TRAIN_REJECTED_REPORTS,
    LIVE_POSITION_CAP,
    MAX_TRADE_COUNT_EXPANSION_MIN_EXTRA,
    MAX_TRADE_COUNT_EXPANSION_RATIO,
    MAX_TRADE_COUNT_REDUCTION_MIN_MISSING,
    MAX_TRADE_COUNT_REDUCTION_RATIO,
    STRICT_MAX_OPEN_POSITIONS,
    _assert_output_writable,
    _base_overrides,
    _evaluation,
    _finite_metric,
    _load_common_context,
    _load_json,
    _paths,
    _run_replay,
    _score_maps_summary,
    _split_samples_for_replay,
    _stress_replay_scenarios,
    _stress_worst,
    _strict_live_fraction,
    _strict_max_open_positions,
    _valid_stress_metrics,
)


DEFAULT_OUTPUT = "data/replay_reports/action_policy_router_replay_20260527_multiroute.json"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a strict replay grid for a multi-policy action router")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", default=".cache/model_replay")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false")
    parser.add_argument("--train-rejected-report", action="append", default=None)
    parser.add_argument("--train-accepted-report", action="append", default=None)
    parser.add_argument(
        "--candidate-grid-json",
        help="Optional JSON list or {'candidates': [...]} overriding the default router candidate grid",
    )
    parser.add_argument(
        "--write-selected-trade-delta",
        action="store_true",
        help="Rerun the selected validation/final candidate with trade logs and write baseline/candidate trade-delta attribution",
    )
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def candidate_grid():
    for confidence in (0.40, 0.55):
        for continue_hold_activation in (0.20, 0.25, 0.35):
            for continue_hold_release in (0.45, 0.60, 0.75):
                yield {
                    "buy_action_policy_router_min_confidence": float(confidence),
                    "buy_quick_profit_overlay_take_profit_pct": 0.25,
                    "buy_quick_profit_overlay_max_hold_seconds": 120.0,
                    "buy_action_policy_continue_hold_activation_pct": float(continue_hold_activation),
                    "buy_action_policy_continue_hold_release_pct": float(continue_hold_release),
                }


def candidate_grid_from_json(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("candidates")
    if not isinstance(payload, list):
        raise SystemExit("--candidate-grid-json must contain a list or {'candidates': [...]}")
    candidates = []
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise SystemExit(f"--candidate-grid-json candidate {index} must be an object")
        candidates.append(dict(row))
    if not candidates:
        raise SystemExit("--candidate-grid-json must contain at least one candidate")
    return candidates


def _summary(evaluation):
    net_profit_bnb = _finite_metric(evaluation, "net_profit_bnb")
    total_trades = _finite_metric(evaluation, "total_trades")
    max_drawdown_pct = _finite_metric(evaluation, "max_drawdown_pct")
    win_rate = _finite_metric(evaluation, "win_rate")
    has_primary_metrics = (
        net_profit_bnb is not None
        and total_trades is not None
        and total_trades >= 0.0
        and max_drawdown_pct is not None
        and win_rate is not None
    )
    walk_forward_worst_net_return_pct = _finite_metric(evaluation, "walk_forward_worst_net_return_pct")
    walk_forward_worst_max_drawdown_pct = _finite_metric(evaluation, "walk_forward_worst_max_drawdown_pct")
    has_walk_forward_metrics = (
        walk_forward_worst_net_return_pct is not None
        and walk_forward_worst_max_drawdown_pct is not None
    )
    stress_replay_scenarios, has_complete_stress_replay = _stress_replay_scenarios(evaluation)
    has_stress_replay = bool(_valid_stress_metrics(evaluation) and has_complete_stress_replay)
    return {
        "has_primary_metrics": bool(has_primary_metrics),
        "net_profit_bnb": 0.0 if net_profit_bnb is None else float(net_profit_bnb),
        "total_trades": 0 if total_trades is None else int(total_trades),
        "max_drawdown_pct": 0.0 if max_drawdown_pct is None else float(max_drawdown_pct),
        "win_rate": 0.0 if win_rate is None else float(win_rate),
        "has_walk_forward_metrics": bool(has_walk_forward_metrics),
        "has_stress_replay": bool(has_stress_replay),
        "stress_replay_scenarios": stress_replay_scenarios,
        "walk_forward_worst_net_return_pct": walk_forward_worst_net_return_pct,
        "walk_forward_worst_max_drawdown_pct": walk_forward_worst_max_drawdown_pct,
        "stress_worst_net_return_pct": _stress_worst(evaluation, "net_return_pct"),
        "stress_worst_net_profit_bnb": _stress_worst(evaluation, "net_profit_bnb"),
        "stress_worst_max_drawdown_pct": _stress_worst(evaluation, "max_drawdown_pct"),
        "action_policy_router_signal_count": int(evaluation.get("action_policy_router_signal_count", 0) or 0),
        "action_policy_router_entry_count": int(evaluation.get("action_policy_router_entry_count", 0) or 0),
        "action_policy_router_reject_count": int(evaluation.get("action_policy_router_reject_count", 0) or 0),
        "action_policy_router_passthrough_count": int(
            evaluation.get("action_policy_router_passthrough_count", 0) or 0
        ),
        "action_policy_router_quick_take_profit_entry_count": int(
            evaluation.get("action_policy_router_quick_take_profit_entry_count", 0) or 0
        ),
        "action_policy_router_continue_hold_entry_count": int(
            evaluation.get("action_policy_router_continue_hold_entry_count", 0) or 0
        ),
        "action_policy_continue_hold_take_profit_count": int(
            evaluation.get("action_policy_continue_hold_take_profit_count", 0) or 0
        ),
        "action_policy_continue_hold_forced_hold_count": int(
            evaluation.get("action_policy_continue_hold_forced_hold_count", 0) or 0
        ),
    }


def _acceptance_gate():
    return {
        "baseline": "current_v95_strict_live_sized_replay",
        "requires_net_profit_bnb_above_baseline": True,
        "requires_max_drawdown_pct_not_worse": True,
        "requires_total_trades_not_materially_lower": True,
        "max_trade_count_reduction_ratio": MAX_TRADE_COUNT_REDUCTION_RATIO,
        "max_trade_count_reduction_min_missing": MAX_TRADE_COUNT_REDUCTION_MIN_MISSING,
        "requires_total_trades_not_materially_higher": True,
        "max_trade_count_expansion_ratio": MAX_TRADE_COUNT_EXPANSION_RATIO,
        "max_trade_count_expansion_min_extra": MAX_TRADE_COUNT_EXPANSION_MIN_EXTRA,
        "requires_win_rate_not_lower": True,
        "requires_walk_forward_worst_net_return_pct_not_lower": True,
        "requires_walk_forward_worst_max_drawdown_pct_not_worse": True,
        "requires_stress_worst_net_return_pct_not_lower": True,
        "requires_stress_worst_net_profit_bnb_not_lower": True,
        "requires_stress_worst_max_drawdown_pct_not_worse": True,
        "requires_action_policy_router_activity": True,
        "requires_action_policy_continue_hold_forced_hold_count": True,
    }


def _gate_details(candidate_summary, baseline_summary):
    has_primary_metrics = bool(candidate_summary["has_primary_metrics"] and baseline_summary["has_primary_metrics"])
    has_walk_forward_metrics = bool(
        candidate_summary["has_walk_forward_metrics"] and baseline_summary["has_walk_forward_metrics"]
    )
    has_stress_replay = bool(candidate_summary["has_stress_replay"] and baseline_summary["has_stress_replay"])
    same_stress_scenarios = (
        list(candidate_summary.get("stress_replay_scenarios") or [])
        == list(baseline_summary.get("stress_replay_scenarios") or [])
    )
    has_stress_replay = bool(has_stress_replay and same_stress_scenarios)
    baseline_trades = int(baseline_summary["total_trades"])
    max_extra_trades = max(
        MAX_TRADE_COUNT_EXPANSION_MIN_EXTRA,
        math.ceil(baseline_trades * MAX_TRADE_COUNT_EXPANSION_RATIO),
    )
    max_missing_trades = max(
        MAX_TRADE_COUNT_REDUCTION_MIN_MISSING,
        math.ceil(baseline_trades * MAX_TRADE_COUNT_REDUCTION_RATIO),
    )
    router_activity = (
        int(candidate_summary.get("action_policy_router_signal_count") or 0) > 0
        and (
            int(candidate_summary.get("action_policy_router_entry_count") or 0) > 0
            or int(candidate_summary.get("action_policy_router_reject_count") or 0) > 0
        )
    )
    return {
        "has_primary_metrics": has_primary_metrics,
        "has_walk_forward_metrics": has_walk_forward_metrics,
        "has_stress_replay": has_stress_replay,
        "same_stress_replay_scenarios": same_stress_scenarios,
        "net_profit_bnb": (
            has_primary_metrics
            and candidate_summary["net_profit_bnb"] > baseline_summary["net_profit_bnb"]
        ),
        "max_drawdown_pct": (
            has_primary_metrics
            and candidate_summary["max_drawdown_pct"] >= baseline_summary["max_drawdown_pct"]
        ),
        "total_trades_not_materially_lower": (
            has_primary_metrics
            and candidate_summary["total_trades"] >= max(0, baseline_trades - max_missing_trades)
        ),
        "total_trades_not_materially_higher": (
            has_primary_metrics
            and candidate_summary["total_trades"] <= baseline_trades + max_extra_trades
        ),
        "win_rate": (
            has_primary_metrics
            and candidate_summary["win_rate"] >= baseline_summary["win_rate"]
        ),
        "walk_forward_worst_net_return_pct": (
            has_walk_forward_metrics
            and candidate_summary["walk_forward_worst_net_return_pct"]
            >= baseline_summary["walk_forward_worst_net_return_pct"]
        ),
        "walk_forward_worst_max_drawdown_pct": (
            has_walk_forward_metrics
            and candidate_summary["walk_forward_worst_max_drawdown_pct"]
            >= baseline_summary["walk_forward_worst_max_drawdown_pct"]
        ),
        "stress_worst_net_return_pct": (
            has_stress_replay
            and candidate_summary["stress_worst_net_return_pct"] >= baseline_summary["stress_worst_net_return_pct"]
        ),
        "stress_worst_net_profit_bnb": (
            has_stress_replay
            and candidate_summary["stress_worst_net_profit_bnb"] >= baseline_summary["stress_worst_net_profit_bnb"]
        ),
        "stress_worst_max_drawdown_pct": (
            has_stress_replay
            and candidate_summary["stress_worst_max_drawdown_pct"] >= baseline_summary["stress_worst_max_drawdown_pct"]
        ),
        "action_policy_router_activity": router_activity,
        "action_policy_continue_hold_forced_hold_count": (
            int(candidate_summary.get("action_policy_continue_hold_forced_hold_count") or 0) > 0
        ),
    }


def _candidate_score(row):
    if not row["summary"].get("has_primary_metrics"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    walk_forward_worst_net_return = row["summary"].get("walk_forward_worst_net_return_pct")
    if walk_forward_worst_net_return is None:
        walk_forward_worst_net_return = -math.inf
    walk_forward_worst_drawdown = row["summary"].get("walk_forward_worst_max_drawdown_pct")
    if walk_forward_worst_drawdown is None:
        walk_forward_worst_drawdown = -math.inf
    forced_hold_count = int(row["summary"].get("action_policy_continue_hold_forced_hold_count") or 0)
    return (
        row["summary"]["net_profit_bnb"],
        row["summary"]["max_drawdown_pct"],
        row["summary"]["win_rate"],
        walk_forward_worst_net_return,
        walk_forward_worst_drawdown,
        -forced_hold_count,
        row["summary"]["total_trades"],
        -row["candidate_index"],
    )


def _compact_replay_config(config):
    compact = dict(config or {})
    if "action_policy_routes_by_episode" in compact:
        compact["action_policy_routes_by_episode_summary"] = _score_maps_summary(
            compact.pop("action_policy_routes_by_episode")
        )
    return compact


def _report_metadata(report, args):
    report = dict(report or {})
    return {
        "generated_at": report.get("generated_at"),
        "split": report.get("split"),
        "selection_role": report.get("selection_role"),
        "git": report.get("git"),
        "model_checksums": report.get("model_checksums"),
        "replay_config": _compact_replay_config(report.get("replay_config")),
        "sample_count": report.get("sample_count"),
        "lifecycle_paths": list(report.get("lifecycle_paths") or []),
        "cache_dir": args.cache_dir,
        "use_cache": bool(args.use_cache),
    }


def _router_route_maps_for_split(args, *, split, base_overrides, train_inputs, context=None):
    from src.pipeline.action_policy_replay_gate import fit_action_policy_router_and_route_episodes

    if context is None:
        context = {}
    if "loaded" not in context:
        context["loaded"] = _load_common_context(args, base_overrides)
    loaded = context["loaded"]
    route_maps, metadata = fit_action_policy_router_and_route_episodes(
        train_rejected_reports=train_inputs["train_rejected_reports"],
        train_accepted_reports=train_inputs["train_accepted_reports"],
        eval_episodes=loaded["split_episodes"](split),
        buy_artifact=loaded["buy_artifact"],
        runtime_params=loaded["runtime_params"],
        train_rejected_source_names=train_inputs.get("train_rejected_source_names"),
        train_accepted_source_names=train_inputs.get("train_accepted_source_names"),
        max_depth=train_inputs.get("max_depth", 3),
        min_samples_leaf=train_inputs.get("min_samples_leaf", 10),
        min_common_features=train_inputs.get("min_common_features", 2),
    )
    return route_maps, metadata


def _router_base_overrides(args):
    overrides = _base_overrides(args)
    overrides["include_flow_features"] = True
    overrides["buy_action_policy_router_skip_passthrough"] = True
    return overrides


def _run_replay_with_trade_log(run_model_replay, args, overrides, *, split, eval_samples=None):
    replay_overrides = dict(overrides or {})
    if eval_samples is not None:
        replay_overrides["eval_samples"] = eval_samples
        replay_overrides["eval_samples_already_split_filtered"] = True
    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=True,
        overrides=replay_overrides,
        use_cache=args.use_cache,
        write_report=False,
    )


def _selected_trade_delta_attribution_for_split(
    run_model_replay,
    args,
    *,
    split,
    base_overrides,
    candidate_params,
    route_maps,
    eval_samples,
):
    from src.pipeline.replay_trade_delta_attribution import build_trade_delta_attribution_report

    baseline_report = _run_replay_with_trade_log(
        run_model_replay,
        args,
        base_overrides,
        split=split,
        eval_samples=eval_samples,
    )
    candidate_overrides = dict(base_overrides)
    candidate_overrides.update(dict(candidate_params))
    candidate_overrides["action_policy_routes_by_episode"] = route_maps
    candidate_report = _run_replay_with_trade_log(
        run_model_replay,
        args,
        candidate_overrides,
        split=split,
        eval_samples=eval_samples,
    )
    return build_trade_delta_attribution_report(
        baseline_trade_rows=list(_evaluation(baseline_report).get("trade_log") or []),
        candidate_trade_rows=list(_evaluation(candidate_report).get("trade_log") or []),
        sample_rows=list(eval_samples or []),
    )


def main(argv=None):
    args = parse_args(argv)
    if not math.isclose(args.position_fraction, LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"position_fraction must be exactly {LIVE_POSITION_CAP}")
    if not math.isclose(args.max_position_fraction, LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"max_position_fraction must be exactly {LIVE_POSITION_CAP}")
    if args.max_open_positions != STRICT_MAX_OPEN_POSITIONS:
        raise SystemExit(f"max_open_positions must be exactly {STRICT_MAX_OPEN_POSITIONS}")
    _assert_output_writable(args.model_dir, args.output, force=bool(args.force))

    from src.pipeline.model_replay import run_model_replay

    base_overrides = _router_base_overrides(args)
    candidate_params_grid = (
        candidate_grid_from_json(args.candidate_grid_json)
        if args.candidate_grid_json
        else list(candidate_grid())
    )
    train_inputs = {
        "train_rejected_reports": [_load_json(path) for path in _paths(args.train_rejected_report or DEFAULT_TRAIN_REJECTED_REPORTS)],
        "train_accepted_reports": [_load_json(path) for path in _paths(args.train_accepted_report or DEFAULT_TRAIN_ACCEPTED_REPORTS)],
        "train_rejected_source_names": [Path(path).stem for path in (args.train_rejected_report or DEFAULT_TRAIN_REJECTED_REPORTS)],
        "train_accepted_source_names": [Path(path).stem for path in (args.train_accepted_report or DEFAULT_TRAIN_ACCEPTED_REPORTS)],
        "max_depth": 3,
        "min_samples_leaf": 10,
        "min_common_features": 2,
    }
    score_context = {}
    validation_samples = _split_samples_for_replay(args, "validation", base_overrides, score_context)
    validation_baseline_report = _run_replay(
        run_model_replay,
        args,
        base_overrides,
        split="validation",
        eval_samples=validation_samples,
    )
    validation_baseline_summary = _summary(_evaluation(validation_baseline_report))
    validation_route_maps, validation_model_metadata = _router_route_maps_for_split(
        args,
        split="validation",
        base_overrides=base_overrides,
        train_inputs=train_inputs,
        context=score_context,
    )

    candidates = []
    for index, params in enumerate(candidate_params_grid):
        overrides = dict(base_overrides)
        overrides.update(params)
        overrides["action_policy_routes_by_episode"] = validation_route_maps
        report = _run_replay(
            run_model_replay,
            args,
            overrides,
            split="validation",
            eval_samples=validation_samples,
        )
        evaluation = _evaluation(report)
        summary = _summary(evaluation)
        gate_details = _gate_details(summary, validation_baseline_summary)
        candidates.append({
            "candidate_index": int(index),
            "params": params,
            "summary": summary,
            "passes_acceptance_gate": all(gate_details.values()),
            "gate_details": gate_details,
            "evaluation": evaluation,
            "replay_metadata": _report_metadata(report, args),
        })

    best_validation_raw_candidate = max(candidates, key=_candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=_candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_samples = _split_samples_for_replay(args, "final", base_overrides, score_context)
    final_baseline_report = _run_replay(
        run_model_replay,
        args,
        base_overrides,
        split="final",
        eval_samples=final_samples,
    )
    final_baseline_summary = _summary(_evaluation(final_baseline_report))
    final_route_maps, final_model_metadata = _router_route_maps_for_split(
        args,
        split="final",
        base_overrides=base_overrides,
        train_inputs=train_inputs,
        context=score_context,
    )
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_overrides["action_policy_routes_by_episode"] = final_route_maps
    final_candidate_report = _run_replay(
        run_model_replay,
        args,
        final_candidate_overrides,
        split="final",
        eval_samples=final_samples,
    )
    final_candidate_evaluation = _evaluation(final_candidate_report)
    final_candidate_summary = _summary(final_candidate_evaluation)
    final_gate_details = _gate_details(final_candidate_summary, final_baseline_summary)
    final_candidate = {
        "candidate_index": validation_selected["candidate_index"],
        "params": validation_selected["params"],
        "summary": final_candidate_summary,
        "passes_acceptance_gate": all(final_gate_details.values()),
        "gate_details": final_gate_details,
        "evaluation": final_candidate_evaluation,
        "replay_metadata": _report_metadata(final_candidate_report, args),
    }
    final_confirmation = {
        "baseline": {
            "summary": final_baseline_summary,
            "evaluation": _evaluation(final_baseline_report),
        },
        "candidate": final_candidate,
        "passes_acceptance_gate": bool(final_candidate["passes_acceptance_gate"]),
    }
    selected_trade_delta_attribution = None
    if bool(args.write_selected_trade_delta):
        selected_trade_delta_attribution = {
            "validation": _selected_trade_delta_attribution_for_split(
                run_model_replay,
                args,
                split="validation",
                base_overrides=base_overrides,
                candidate_params=validation_selected["params"],
                route_maps=validation_route_maps,
                eval_samples=validation_samples,
            ),
            "final": _selected_trade_delta_attribution_for_split(
                run_model_replay,
                args,
                split="final",
                base_overrides=base_overrides,
                candidate_params=validation_selected["params"],
                route_maps=final_route_maps,
                eval_samples=final_samples,
            ),
        }
    decision = (
        "accept"
        if best_validation_accepted is not None and final_confirmation["passes_acceptance_gate"]
        else "reject"
    )
    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model_dir": str(args.model_dir),
        "lifecycle_dir": str(args.lifecycle_dir),
        "strict_assumptions": base_overrides,
        "candidate_grid": {
            "source": str(args.candidate_grid_json) if args.candidate_grid_json else "default",
            "candidate_count": len(candidate_params_grid),
        },
        "acceptance_gate": _acceptance_gate(),
        "action_policy_router_model": {
            "validation": validation_model_metadata,
            "final": final_model_metadata,
        },
        "baseline": {
            "split": "validation",
            "summary": validation_baseline_summary,
            "evaluation": _evaluation(validation_baseline_report),
            "replay_metadata": _report_metadata(validation_baseline_report, args),
        },
        "candidates": candidates,
        "best_validation_raw_candidate": best_validation_raw_candidate,
        "best_validation_candidate": validation_selected,
        "best_validation_accepted_candidate": best_validation_accepted,
        "selected_candidate": validation_selected,
        "best_candidate": validation_selected,
        "best_accepted_candidate": best_validation_accepted,
        "final_confirmation": final_confirmation,
        "replay_metadata": {
            "validation_baseline": _report_metadata(validation_baseline_report, args),
            "final_baseline": _report_metadata(final_baseline_report, args),
            "final_candidate": _report_metadata(final_candidate_report, args),
        },
        "selected_trade_delta_attribution": selected_trade_delta_attribution,
        "decision": decision,
        "live_switch_evidence": False,
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
            count=len(candidate_params_grid),
            output=str(output_path),
        )
    )
    return report


if __name__ == "__main__":
    main()
