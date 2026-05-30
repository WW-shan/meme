#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/shadow_meta_gate_replay_20260520_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.005079303120051795
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
MAX_TRADE_COUNT_EXPANSION_RATIO = 0.25
MAX_TRADE_COUNT_EXPANSION_MIN_EXTRA = 1
MAX_TRADE_COUNT_REDUCTION_RATIO = 0.25
MAX_TRADE_COUNT_REDUCTION_MIN_MISSING = 1
PROTECTED_MODEL_ARTIFACT_NAMES = frozenset((
    "hybrid_manifest.json",
    "buy_model.cbm",
    "buy_threshold.json",
    "feature_schema.json",
    "entry_value_model.cbm",
    "sell_policy.zip",
    "bc.pt",
    "trade_log.jsonl",
))


def _strict_live_fraction(value):
    fraction = float(value)
    if not math.isfinite(fraction) or not math.isclose(fraction, LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise argparse.ArgumentTypeError(f"value must be exactly {LIVE_POSITION_CAP}")
    return fraction


def _strict_max_open_positions(value):
    positions = int(value)
    if positions != STRICT_MAX_OPEN_POSITIONS:
        raise argparse.ArgumentTypeError(f"value must be exactly {STRICT_MAX_OPEN_POSITIONS}")
    return positions


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a strict shadow meta-gate replay grid")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Replay grid JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument(
        "--write-selected-trade-delta",
        action="store_true",
        help="Rerun the selected candidate with trade logs and attach paired trade-delta attribution",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing replay report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def candidate_grid():
    min_scores = [0.35, 0.50, 0.65]
    min_probs = [0.988, 0.989]
    max_entry_scores = [5.0, 10.0]
    volume_floors = [2.0, 3.0]
    volatility_floors = [0.20, 0.25]
    max_ages = [60.0]
    for values in itertools.product(
        min_scores,
        min_probs,
        max_entry_scores,
        volume_floors,
        volatility_floors,
        max_ages,
    ):
        min_score, min_prob, max_entry_score, min_volume, min_volatility, max_age = values
        yield {
            "buy_shadow_meta_gate_min_score": min_score,
            "buy_shadow_meta_gate_min_prob": min_prob,
            "buy_shadow_meta_gate_max_entry_score": max_entry_score,
            "buy_shadow_meta_gate_min_entry_volume_30s": min_volume,
            "buy_shadow_meta_gate_min_entry_price_volatility": min_volatility,
            "buy_shadow_meta_gate_max_age_seconds": max_age,
        }


def _base_overrides(args):
    return {
        "initial_equity_bnb": LIVE_INITIAL_EQUITY_BNB,
        "position_fraction": float(args.position_fraction),
        "max_position_fraction": float(args.max_position_fraction),
        "fixed_stake_bnb": None,
        "skip_all_in_replay": True,
        "max_open_positions": int(args.max_open_positions),
    }


def _evaluation(report):
    return dict((report or {}).get("evaluation", {}) or {})


def _shadow_score_maps_summary(score_maps):
    maps = list(score_maps or [])
    scored_counts = []
    for row in maps:
        if isinstance(row, dict):
            scored_counts.append(len(row))
        else:
            scored_counts.append(0)
    return {
        "episode_count": len(maps),
        "non_empty_episode_count": sum(1 for count in scored_counts if count > 0),
        "scored_sample_count": sum(scored_counts),
        "max_episode_score_count": max(scored_counts, default=0),
    }


def _compact_replay_config(config):
    compact = dict(config or {})
    if "shadow_scores_by_episode" in compact:
        compact["shadow_scores_by_episode_summary"] = _shadow_score_maps_summary(
            compact.pop("shadow_scores_by_episode")
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


def _finite_metric(row, key):
    if not isinstance(row, dict) or key not in row:
        return None
    try:
        value = float(row[key])
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _valid_stress_metrics(evaluation):
    required = ("net_return_pct", "net_profit_bnb", "max_drawdown_pct")
    rows = []
    for row in evaluation.get("stress_replay", []) or []:
        metrics = {key: _finite_metric(row, key) for key in required}
        if all(value is not None for value in metrics.values()):
            rows.append(metrics)
    return rows


def _stress_worst(evaluation, key):
    values = [metrics[key] for metrics in _valid_stress_metrics(evaluation)]
    return min(values) if values else None


def _stress_replay_scenarios(evaluation):
    names = []
    seen = set()
    rows = list(evaluation.get("stress_replay", []) or [])
    if not rows:
        return [], False
    required = ("net_return_pct", "net_profit_bnb", "max_drawdown_pct")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return names, False
        name = str(row.get("name") or f"stress_{index}").strip()
        if not name or name in seen:
            return names, False
        seen.add(name)
        names.append(name)
        if any(_finite_metric(row, key) is None for key in required):
            return names, False
    return names, True


def _int_metric(evaluation, key):
    try:
        return int(evaluation.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


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
        "shadow_meta_gate_signal_count": _int_metric(evaluation, "shadow_meta_gate_signal_count"),
        "shadow_meta_gate_entry_count": _int_metric(evaluation, "shadow_meta_gate_entry_count"),
        "shadow_meta_gate_reject_count": _int_metric(evaluation, "shadow_meta_gate_reject_count"),
    }


def _acceptance_gate():
    return {
        "baseline": "current_v95_strict_live_sized_replay",
        "requires_net_profit_bnb_above_baseline": True,
        "min_net_profit_improvement_bnb": 0.0,
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
        "requires_shadow_meta_gate_entries": True,
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
    max_allowed_trades = baseline_trades + max_extra_trades
    min_allowed_trades = max(0, baseline_trades - max_missing_trades)
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
            and candidate_summary["total_trades"] >= min_allowed_trades
        ),
        "total_trades_not_materially_higher": (
            has_primary_metrics
            and candidate_summary["total_trades"] <= max_allowed_trades
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
        "shadow_meta_gate_entry_count": candidate_summary["shadow_meta_gate_entry_count"] > 0,
    }


def _passes_gate(candidate_summary, baseline_summary):
    return all(_gate_details(candidate_summary, baseline_summary).values())


def _candidate_score(row):
    if not row["summary"].get("has_primary_metrics"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    return (
        row["summary"]["net_profit_bnb"],
        row["summary"]["max_drawdown_pct"],
        row["summary"]["total_trades"],
        -row["candidate_index"],
    )


def _assert_safe_output_path(model_dir, output_path):
    output_path = Path(output_path)
    if output_path.name not in PROTECTED_MODEL_ARTIFACT_NAMES:
        return

    try:
        resolved_output_path = output_path.resolve(strict=False)
        resolved_model_dir = Path(model_dir).resolve(strict=False)
        resolved_output_path.relative_to(resolved_model_dir)
    except ValueError:
        return

    raise SystemExit(f"refusing to write replay report to protected model artifact: {output_path}")


def _assert_output_writable(model_dir, output_path, *, force=False):
    _assert_safe_output_path(model_dir, output_path)
    output_path = Path(output_path)
    if output_path.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing replay report without --force: {output_path}")


def _run_replay(run_model_replay, args, overrides, *, split):
    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=overrides,
        use_cache=args.use_cache,
        write_report=False,
    )


def _run_replay_with_trade_log(run_model_replay, args, overrides, *, split):
    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=True,
        overrides=dict(overrides),
        use_cache=args.use_cache,
        write_report=False,
    )


def _load_shadow_context(args, base_overrides):
    from src.pipeline.candidate_ranker_probe import runtime_params_with_buy_threshold
    from src.pipeline.model_replay import (
        apply_model_schema_feature_flags,
        live_replay_config_from_manifest,
        load_manifest,
        load_model_artifacts,
        load_or_build_samples,
        resolve_replay_split,
    )
    from src.pipeline.train_hybrid import _build_eval_episodes

    manifest = load_manifest(args.model_dir)
    config_overrides = dict(base_overrides)
    config_overrides.pop("buy_threshold", None)
    replay_config = live_replay_config_from_manifest(
        manifest,
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=config_overrides,
    )
    replay_config = apply_model_schema_feature_flags(replay_config, args.model_dir)
    replay_split = resolve_replay_split(manifest, args.lifecycle_dir)
    train_samples = load_or_build_samples(
        replay_config,
        replay_split.train_files,
        set(),
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    validation_samples = load_or_build_samples(
        replay_config,
        replay_split.validation_files,
        replay_split.excluded_validation_tokens,
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    final_samples = load_or_build_samples(
        replay_config,
        replay_split.eval_files,
        replay_split.excluded_final_tokens,
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    artifacts = load_model_artifacts(args.model_dir)
    buy_artifact = artifacts.buy_artifact
    runtime_params = runtime_params_with_buy_threshold(replay_config, buy_artifact)
    return {
        "train_samples": train_samples,
        "episodes_by_split": {
            "validation": _build_eval_episodes(validation_samples),
            "final": _build_eval_episodes(final_samples),
        },
        "buy_artifact": buy_artifact,
        "runtime_params": runtime_params,
    }


def _shadow_score_maps_for_candidate(args, params, *, split, base_overrides, context=None):
    from src.pipeline.candidate_ranker_probe import fit_shadow_ranker_and_score_episodes

    if context is None:
        loaded = _load_shadow_context(args, base_overrides)
    else:
        if "loaded" not in context:
            context["loaded"] = _load_shadow_context(args, base_overrides)
        loaded = context["loaded"]

    runtime_params = dict(loaded["runtime_params"])
    runtime_params.update(dict(params))
    return fit_shadow_ranker_and_score_episodes(
        loaded["train_samples"],
        loaded["episodes_by_split"][split],
        loaded["buy_artifact"],
        runtime_params,
    )


def _selected_trade_delta_attribution_for_split(
    run_model_replay,
    args,
    *,
    split,
    base_overrides,
    candidate_params,
    shadow_context,
):
    from src.pipeline.replay_trade_delta_attribution import build_trade_delta_attribution_report

    baseline_report = _run_replay_with_trade_log(
        run_model_replay,
        args,
        base_overrides,
        split=split,
    )
    candidate_overrides = dict(base_overrides)
    candidate_overrides.update(dict(candidate_params))
    candidate_overrides["shadow_scores_by_episode"] = _shadow_score_maps_for_candidate(
        args,
        candidate_params,
        split=split,
        base_overrides=base_overrides,
        context=shadow_context,
    )
    candidate_report = _run_replay_with_trade_log(
        run_model_replay,
        args,
        candidate_overrides,
        split=split,
    )
    return build_trade_delta_attribution_report(
        baseline_trade_rows=list(_evaluation(baseline_report).get("trade_log") or []),
        candidate_trade_rows=list(_evaluation(candidate_report).get("trade_log") or []),
        sample_rows=[],
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

    base_overrides = _base_overrides(args)
    shadow_context = {}
    validation_baseline_report = _run_replay(run_model_replay, args, base_overrides, split="validation")
    validation_baseline_summary = _summary(_evaluation(validation_baseline_report))

    candidates = []
    for index, params in enumerate(candidate_grid()):
        overrides = dict(base_overrides)
        overrides.update(params)
        shadow_scores_by_episode = _shadow_score_maps_for_candidate(
            args,
            params,
            split="validation",
            base_overrides=base_overrides,
            context=shadow_context,
        )
        overrides["shadow_scores_by_episode"] = shadow_scores_by_episode
        report = _run_replay(run_model_replay, args, overrides, split="validation")
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

    final_baseline_report = _run_replay(run_model_replay, args, base_overrides, split="final")
    final_baseline_summary = _summary(_evaluation(final_baseline_report))
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_overrides["shadow_scores_by_episode"] = _shadow_score_maps_for_candidate(
        args,
        validation_selected["params"],
        split="final",
        base_overrides=base_overrides,
        context=shadow_context,
    )
    final_candidate_report = _run_replay(run_model_replay, args, final_candidate_overrides, split="final")
    final_candidate_evaluation = _evaluation(final_candidate_report)
    final_candidate_summary = _summary(final_candidate_evaluation)
    final_gate_details = _gate_details(final_candidate_summary, final_baseline_summary)
    final_candidate_metadata = _report_metadata(final_candidate_report, args)
    final_candidate = {
        "candidate_index": validation_selected["candidate_index"],
        "params": validation_selected["params"],
        "summary": final_candidate_summary,
        "passes_acceptance_gate": all(final_gate_details.values()),
        "gate_details": final_gate_details,
        "evaluation": final_candidate_evaluation,
        "replay_metadata": final_candidate_metadata,
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
                shadow_context=shadow_context,
            ),
            "final": _selected_trade_delta_attribution_for_split(
                run_model_replay,
                args,
                split="final",
                base_overrides=base_overrides,
                candidate_params=validation_selected["params"],
                shadow_context=shadow_context,
            ),
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
        "acceptance_gate": _acceptance_gate(),
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
        "selected_trade_delta_attribution": selected_trade_delta_attribution,
        "replay_metadata": {
            "validation_baseline": _report_metadata(validation_baseline_report, args),
            "final_baseline": _report_metadata(final_baseline_report, args),
            "final_candidate": final_candidate_metadata,
        },
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
            count=len(candidates),
            output=str(output_path),
        )
    )
    return report


if __name__ == "__main__":
    main()
