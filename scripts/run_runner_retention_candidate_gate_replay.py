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

DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/runner_retention_candidate_gate_replay_20260526.json"
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


def _positive_int(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run a strict runner-retention candidate-gate replay grid")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Replay grid JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing replay report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.add_argument(
        "--candidate-grid-json",
        help="Optional JSON file containing a list of candidate parameter dictionaries",
    )
    parser.add_argument(
        "--include-flow-features",
        action="store_true",
        help="Build replay samples with flow features even when the model schema does not require them",
    )
    parser.add_argument(
        "--preserve-base-candidates",
        action="store_true",
        help="Assign passing scores to candidates already accepted by the base runtime stack",
    )
    parser.add_argument(
        "--early-replacement-max-lead-seconds",
        type=_positive_int,
        default=None,
        help=(
            "Train runner-retention labels only on rescue candidates that become a base accepted "
            "entry for the same token within this many seconds"
        ),
    )
    parser.add_argument(
        "--write-selected-trade-delta",
        action="store_true",
        help="Rerun the selected validation/final candidate with trade logs and write baseline/candidate trade-delta attribution",
    )
    parser.add_argument(
        "--added-trade-boundary-report",
        help=(
            "Optional added-trade boundary policy report; its selected_rule filters expanded "
            "runner-retention rescue candidates in replay score maps"
        ),
    )
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def candidate_grid():
    for near_prob in (0.85, 0.875):
        for near_pred_return in (32.0, 35.0):
            for path_state_score in (0.45, 0.60):
                yield {
                    "buy_near_threshold_min_prob": float(near_prob),
                    "buy_near_min_pred_return": float(near_pred_return),
                    "buy_near_min_entry_volume_30s": 0.6,
                    "buy_near_min_entry_price_volatility": 0.05,
                    "buy_near_min_age_seconds": 0.0,
                    "buy_path_state_meta_gate_min_score": float(path_state_score),
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


def candidate_grid_requires_flow_features(candidates):
    def is_flow_key(value):
        text = str(value)
        return "_flow_" in text or text.startswith("flow_")

    def contains_flow_key(value):
        if isinstance(value, dict):
            return any(
                is_flow_key(key) or contains_flow_key(row)
                for key, row in value.items()
            )
        if isinstance(value, list):
            return any(contains_flow_key(row) for row in value)
        if isinstance(value, str):
            if is_flow_key(value):
                return True
            try:
                return contains_flow_key(json.loads(value))
            except json.JSONDecodeError:
                return False
        return False

    for candidate in candidates or []:
        for key, value in candidate.items():
            if is_flow_key(key) or contains_flow_key(value):
                return True
    return False


def _base_overrides(args):
    return {
        "initial_equity_bnb": LIVE_INITIAL_EQUITY_BNB,
        "position_fraction": float(args.position_fraction),
        "max_position_fraction": float(args.max_position_fraction),
        "fixed_stake_bnb": None,
        "skip_all_in_replay": True,
        "max_open_positions": int(args.max_open_positions),
    }


def _load_added_trade_boundary_rule(path):
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("--added-trade-boundary-report must contain a JSON object")
    selected_rule = payload.get("selected_rule")
    if not isinstance(selected_rule, dict):
        raise SystemExit("--added-trade-boundary-report missing selected_rule")
    contract = payload.get("contract")
    if isinstance(contract, dict) and contract.get("uses_decision_time_features_only") is False:
        raise SystemExit("--added-trade-boundary-report must use decision-time features only")
    return {
        "source": str(path),
        "decision": payload.get("decision"),
        "config": payload.get("config") if isinstance(payload.get("config"), dict) else {},
        "selected_rule": selected_rule,
    }


def _evaluation(report):
    return dict((report or {}).get("evaluation", {}) or {})


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
        "path_state_meta_gate_signal_count": _int_metric(evaluation, "path_state_meta_gate_signal_count"),
        "path_state_meta_gate_entry_count": _int_metric(evaluation, "path_state_meta_gate_entry_count"),
        "path_state_meta_gate_reject_count": _int_metric(evaluation, "path_state_meta_gate_reject_count"),
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
        "requires_path_state_meta_gate_entries": True,
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
        "path_state_meta_gate_entry_count": candidate_summary["path_state_meta_gate_entry_count"] > 0,
    }


def _candidate_score(row):
    if not row["summary"].get("has_primary_metrics"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    return (
        row["summary"]["net_profit_bnb"],
        row["summary"]["max_drawdown_pct"],
        row["summary"]["total_trades"],
        -row["candidate_index"],
    )


def _score_maps_summary(score_maps):
    maps = list(score_maps or [])
    scored_counts = [
        sum(1 for key in row if isinstance(key, int) or (isinstance(key, str) and key.isdigit()))
        if isinstance(row, dict)
        else 0
        for row in maps
    ]
    return {
        "episode_count": len(maps),
        "non_empty_episode_count": sum(1 for count in scored_counts if count > 0),
        "scored_sample_count": sum(scored_counts),
        "max_episode_score_count": max(scored_counts, default=0),
    }


def _compact_replay_config(config):
    compact = dict(config or {})
    if "path_state_scores_by_episode" in compact:
        compact["path_state_scores_by_episode_summary"] = _score_maps_summary(
            compact.pop("path_state_scores_by_episode")
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


def _run_replay(run_model_replay, args, overrides, *, split, include_trade_log=False):
    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=bool(include_trade_log),
        overrides=overrides,
        use_cache=args.use_cache,
        write_report=False,
    )


def _load_common_context(args, base_overrides):
    from src.pipeline.candidate_ranker_probe import runtime_params_with_buy_threshold
    from src.pipeline.model_replay import (
        apply_model_schema_feature_flags,
        live_replay_config_from_manifest,
        load_manifest,
        load_model_artifacts,
        load_or_build_samples,
        resolve_replay_split,
    )
    from src.pipeline.runner_retention_replay_gate import load_train_price_paths_by_token
    from src.pipeline.train_hybrid import _build_eval_episodes

    manifest = load_manifest(args.model_dir)
    replay_config = live_replay_config_from_manifest(
        manifest,
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        overrides=dict(base_overrides),
    )
    replay_config = apply_model_schema_feature_flags(replay_config, args.model_dir)
    replay_split = resolve_replay_split(manifest, args.lifecycle_dir)
    artifacts = load_model_artifacts(args.model_dir)
    buy_artifact = artifacts.buy_artifact
    runtime_params = runtime_params_with_buy_threshold(replay_config, buy_artifact)

    train_samples = load_or_build_samples(
        replay_config,
        replay_split.train_files,
        set(),
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    train_price_paths_by_token = load_train_price_paths_by_token(replay_split.train_files)

    split_sample_cache = {}

    def split_samples(split):
        if split in split_sample_cache:
            return split_sample_cache[split]
        if split == "validation":
            files = replay_split.validation_files
            excluded_tokens = replay_split.excluded_validation_tokens
        elif split == "final":
            files = replay_split.eval_files
            excluded_tokens = replay_split.excluded_final_tokens
        else:
            raise ValueError(f"unsupported split for runner-retention scoring: {split}")
        samples = load_or_build_samples(
            replay_config,
            files,
            excluded_tokens,
            cache_dir=args.cache_dir,
            use_cache=args.use_cache,
        )
        split_sample_cache[split] = samples
        return samples

    def split_episodes(split):
        return _build_eval_episodes(split_samples(split))

    return {
        "buy_artifact": buy_artifact,
        "runtime_params": runtime_params,
        "split_samples": split_samples,
        "split_episodes": split_episodes,
        "train_samples": train_samples,
        "train_price_paths_by_token": train_price_paths_by_token,
    }


def _runner_retention_score_maps_for_split(
    args,
    *,
    split,
    base_overrides,
    candidate_params,
    context=None,
    preserve_base_candidates=False,
    early_replacement_max_lead_seconds=None,
    added_trade_boundary_rule=None,
):
    from src.pipeline.runner_retention_replay_gate import fit_runner_retention_candidate_gate_and_score_episodes

    if context is None:
        context = {}
    if "loaded" not in context:
        context["loaded"] = _load_common_context(args, base_overrides)
    loaded = context["loaded"]
    runtime_params = dict(loaded["runtime_params"])
    runtime_params.update(dict(candidate_params))
    base_runtime_params = (
        loaded["runtime_params"]
        if preserve_base_candidates or early_replacement_max_lead_seconds is not None
        else None
    )
    return fit_runner_retention_candidate_gate_and_score_episodes(
        train_samples=loaded["train_samples"],
        train_price_paths_by_token=loaded["train_price_paths_by_token"],
        eval_episodes=loaded["split_episodes"](split),
        buy_artifact=loaded["buy_artifact"],
        runtime_params=runtime_params,
        base_runtime_params=base_runtime_params,
        max_depth=3,
        min_samples_leaf=50,
        min_common_features=2,
        early_replacement_max_lead_seconds=early_replacement_max_lead_seconds,
        added_trade_boundary_rule=added_trade_boundary_rule,
    )


def _preloaded_eval_samples(context, split):
    return list(context["loaded"]["split_samples"](split))


def _selected_trade_delta_attribution_for_split(
    run_model_replay,
    args,
    *,
    split,
    base_overrides,
    candidate_params,
    score_context,
    preserve_base_candidates=False,
    early_replacement_max_lead_seconds=None,
    added_trade_boundary_rule=None,
):
    from src.pipeline.replay_trade_delta_attribution import build_trade_delta_attribution_report

    eval_samples = _preloaded_eval_samples(score_context, split)
    baseline_overrides = dict(base_overrides)
    baseline_overrides["eval_samples"] = eval_samples
    baseline_report = _run_replay(
        run_model_replay,
        args,
        baseline_overrides,
        split=split,
        include_trade_log=True,
    )
    score_maps, _metadata = _runner_retention_score_maps_for_split(
        args,
        split=split,
        base_overrides=base_overrides,
        candidate_params=candidate_params,
        context=score_context,
        preserve_base_candidates=bool(preserve_base_candidates),
        early_replacement_max_lead_seconds=early_replacement_max_lead_seconds,
        added_trade_boundary_rule=added_trade_boundary_rule,
    )
    candidate_overrides = dict(base_overrides)
    candidate_overrides.update(dict(candidate_params))
    candidate_overrides["path_state_scores_by_episode"] = score_maps
    candidate_overrides["eval_samples"] = eval_samples
    candidate_report = _run_replay(
        run_model_replay,
        args,
        candidate_overrides,
        split=split,
        include_trade_log=True,
    )
    return build_trade_delta_attribution_report(
        baseline_trade_rows=list(_evaluation(baseline_report).get("trade_log") or []),
        candidate_trade_rows=list(_evaluation(candidate_report).get("trade_log") or []),
        sample_rows=eval_samples,
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

    candidate_params_grid = (
        candidate_grid_from_json(args.candidate_grid_json)
        if args.candidate_grid_json
        else list(candidate_grid())
    )
    added_trade_boundary = _load_added_trade_boundary_rule(args.added_trade_boundary_report)
    added_trade_boundary_rule = (
        added_trade_boundary["selected_rule"] if isinstance(added_trade_boundary, dict) else None
    )
    base_overrides = _base_overrides(args)
    if bool(args.include_flow_features) or candidate_grid_requires_flow_features(candidate_params_grid):
        base_overrides["include_flow_features"] = True
    score_context = {"loaded": _load_common_context(args, base_overrides)}
    validation_baseline_overrides = dict(base_overrides)
    validation_baseline_overrides["eval_samples"] = _preloaded_eval_samples(score_context, "validation")
    validation_baseline_report = _run_replay(run_model_replay, args, validation_baseline_overrides, split="validation")
    validation_baseline_summary = _summary(_evaluation(validation_baseline_report))

    candidates = []
    for index, params in enumerate(candidate_params_grid):
        overrides = dict(base_overrides)
        overrides.update(params)
        score_maps, metadata = _runner_retention_score_maps_for_split(
            args,
            split="validation",
            base_overrides=base_overrides,
            candidate_params=params,
            context=score_context,
            preserve_base_candidates=bool(args.preserve_base_candidates),
            early_replacement_max_lead_seconds=args.early_replacement_max_lead_seconds,
            added_trade_boundary_rule=added_trade_boundary_rule,
        )
        overrides["path_state_scores_by_episode"] = score_maps
        overrides["eval_samples"] = _preloaded_eval_samples(score_context, "validation")
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
            "runner_retention_model": metadata,
        })

    best_validation_raw_candidate = max(candidates, key=_candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=_candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_baseline_overrides = dict(base_overrides)
    final_baseline_overrides["eval_samples"] = _preloaded_eval_samples(score_context, "final")
    final_baseline_report = _run_replay(run_model_replay, args, final_baseline_overrides, split="final")
    final_baseline_summary = _summary(_evaluation(final_baseline_report))
    final_score_maps, final_model_metadata = _runner_retention_score_maps_for_split(
        args,
        split="final",
        base_overrides=base_overrides,
        candidate_params=validation_selected["params"],
        context=score_context,
        preserve_base_candidates=bool(args.preserve_base_candidates),
        early_replacement_max_lead_seconds=args.early_replacement_max_lead_seconds,
        added_trade_boundary_rule=added_trade_boundary_rule,
    )
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_overrides["path_state_scores_by_episode"] = final_score_maps
    final_candidate_overrides["eval_samples"] = _preloaded_eval_samples(score_context, "final")
    final_candidate_report = _run_replay(run_model_replay, args, final_candidate_overrides, split="final")
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
                score_context=score_context,
                preserve_base_candidates=bool(args.preserve_base_candidates),
                early_replacement_max_lead_seconds=args.early_replacement_max_lead_seconds,
                added_trade_boundary_rule=added_trade_boundary_rule,
            ),
            "final": _selected_trade_delta_attribution_for_split(
                run_model_replay,
                args,
                split="final",
                base_overrides=base_overrides,
                candidate_params=validation_selected["params"],
                score_context=score_context,
                preserve_base_candidates=bool(args.preserve_base_candidates),
                early_replacement_max_lead_seconds=args.early_replacement_max_lead_seconds,
                added_trade_boundary_rule=added_trade_boundary_rule,
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
            "requires_flow_features": candidate_grid_requires_flow_features(candidate_params_grid),
        },
        "acceptance_gate": _acceptance_gate(),
        "precision_guard": {
            "preserve_base_candidates": bool(args.preserve_base_candidates),
            "early_replacement_max_lead_seconds": args.early_replacement_max_lead_seconds,
            "added_trade_boundary": added_trade_boundary,
            "description": (
                "When enabled, replay score maps assign score=1.0 to samples that already pass "
                "the base runtime entry stack, so runner-retention scores only decide expanded rescue candidates."
            ),
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
        "decision": decision,
        "live_switch_evidence": False,
        "selected_trade_delta_attribution": selected_trade_delta_attribution,
        "runner_retention_model": {
            "validation": validation_selected.get("runner_retention_model"),
            "final": final_model_metadata,
        },
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
            output=output_path,
        )
    )
    return report


if __name__ == "__main__":
    main()
