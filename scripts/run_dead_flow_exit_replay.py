#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
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
DEFAULT_OUTPUT = "data/replay_reports/dead_flow_exit_replay_20260522_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.005079303120051795
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
MIN_NET_PROFIT_IMPROVEMENT_BNB = 0.0005
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
DEAD_FLOW_KEYS = frozenset((
    "buy_dead_flow_exit_min_hold_seconds",
    "buy_dead_flow_exit_max_mfe_pct",
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
    parser = argparse.ArgumentParser(description="Run a bounded dead-flow-exit-only replay grid")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Replay grid JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing replay report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def candidate_grid():
    min_hold_seconds = [90.0, 120.0, 180.0, 240.0]
    max_mfe_pcts = [0.03, 0.05, 0.08]
    for min_hold, max_mfe in itertools.product(min_hold_seconds, max_mfe_pcts):
        yield {
            "buy_dead_flow_exit_min_hold_seconds": min_hold,
            "buy_dead_flow_exit_max_mfe_pct": max_mfe,
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


def _finite_metric(row, key):
    if not isinstance(row, dict) or key not in row:
        return None
    try:
        value = float(row[key])
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _int_metric(row, key):
    try:
        return int((row or {}).get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


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


def _entry_signature(row):
    return (
        str(row.get("token") or "").strip().lower(),
        int(row.get("entry_time") or 0),
        int(row.get("entry_index") or 0),
    )


def _entry_signature_rows(trade_log):
    return [
        {
            "token": token,
            "entry_time": entry_time,
            "entry_index": entry_index,
        }
        for token, entry_time, entry_index in (_entry_signature(row) for row in (trade_log or []))
    ]


def _trade_by_signature(trade_log):
    return {_entry_signature(row): dict(row) for row in (trade_log or [])}


def _trade_diff_summary(baseline_trade_log, candidate_trade_log):
    baseline_keys = [_entry_signature(row) for row in (baseline_trade_log or [])]
    candidate_keys = [_entry_signature(row) for row in (candidate_trade_log or [])]
    baseline_set = set(baseline_keys)
    candidate_set = set(candidate_keys)
    baseline_by_key = _trade_by_signature(baseline_trade_log)
    candidate_by_key = _trade_by_signature(candidate_trade_log)
    worsened_profitable = []
    for key, baseline_trade in baseline_by_key.items():
        baseline_return = _finite_metric(baseline_trade, "return_pct")
        if baseline_return is None or baseline_return <= 0.0:
            continue
        candidate_trade = candidate_by_key.get(key)
        candidate_return = _finite_metric(candidate_trade or {}, "return_pct")
        if candidate_return is None or candidate_return + 1e-9 < baseline_return:
            worsened_profitable.append({
                "token": key[0],
                "entry_time": key[1],
                "baseline_return_pct": baseline_return,
                "candidate_return_pct": candidate_return,
                "baseline_exit_reason": baseline_trade.get("exit_reason"),
                "candidate_exit_reason": (candidate_trade or {}).get("exit_reason"),
            })
    return {
        "baseline_entry_signatures": _entry_signature_rows(baseline_trade_log),
        "candidate_entry_signatures": _entry_signature_rows(candidate_trade_log),
        "frozen_entries": baseline_keys == candidate_keys,
        "missing_entry_signatures": _entry_signature_rows(
            baseline_by_key[key] for key in sorted(baseline_set - candidate_set)
        ),
        "extra_entry_signatures": _entry_signature_rows(
            candidate_by_key[key] for key in sorted(candidate_set - baseline_set)
        ),
        "worsened_profitable_baseline_trades": worsened_profitable,
        "baseline_profitable_trades_not_worse": not worsened_profitable,
    }


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
        "dead_flow_exit_count": _int_metric(evaluation, "dead_flow_exit_count"),
    }


def _acceptance_gate():
    return {
        "baseline": "current_v95_strict_live_sized_replay",
        "requires_frozen_entry_set": True,
        "requires_no_worsened_baseline_profitable_trades": True,
        "requires_dead_flow_exit_activity": True,
        "requires_net_profit_bnb_above_baseline_by": MIN_NET_PROFIT_IMPROVEMENT_BNB,
        "requires_max_drawdown_pct_not_worse": True,
        "requires_total_trades_equal": True,
        "requires_win_rate_not_lower": True,
        "requires_walk_forward_worst_net_return_pct_not_lower": True,
        "requires_walk_forward_worst_max_drawdown_pct_not_worse": True,
        "requires_stress_worst_net_return_pct_not_lower": True,
        "requires_stress_worst_net_profit_bnb_not_lower": True,
        "requires_stress_worst_max_drawdown_pct_not_worse": True,
    }


def _gate_details(candidate_summary, baseline_summary, trade_diff):
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
    return {
        "has_primary_metrics": has_primary_metrics,
        "has_walk_forward_metrics": has_walk_forward_metrics,
        "has_stress_replay": has_stress_replay,
        "same_stress_replay_scenarios": same_stress_scenarios,
        "frozen_entries": bool(trade_diff.get("frozen_entries")),
        "baseline_profitable_trades_not_worse": bool(trade_diff.get("baseline_profitable_trades_not_worse")),
        "dead_flow_exit_activity": candidate_summary["dead_flow_exit_count"] > 0,
        "net_profit_bnb": (
            has_primary_metrics
            and candidate_summary["net_profit_bnb"] - baseline_summary["net_profit_bnb"]
            >= MIN_NET_PROFIT_IMPROVEMENT_BNB
        ),
        "max_drawdown_pct": (
            has_primary_metrics and candidate_summary["max_drawdown_pct"] >= baseline_summary["max_drawdown_pct"]
        ),
        "total_trades_equal": (
            has_primary_metrics and candidate_summary["total_trades"] == baseline_summary["total_trades"]
        ),
        "win_rate": (
            has_primary_metrics and candidate_summary["win_rate"] >= baseline_summary["win_rate"]
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
    }


def _candidate_score(row):
    if not row["summary"].get("has_primary_metrics"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    return (
        row["summary"]["net_profit_bnb"],
        row["summary"]["dead_flow_exit_count"],
        row["summary"]["max_drawdown_pct"],
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


def _eval_samples_for_split(model_replay, args, base_overrides, split, cache):
    if split in cache:
        return cache[split]
    required = (
        "load_manifest",
        "live_replay_config_from_manifest",
        "apply_model_schema_feature_flags",
        "resolve_replay_split",
        "load_or_build_samples",
    )
    if not all(hasattr(model_replay, name) for name in required):
        return None
    manifest = model_replay.load_manifest(args.model_dir)
    replay_config = model_replay.live_replay_config_from_manifest(
        manifest,
        max_open_positions=args.max_open_positions,
        include_trade_log=True,
        overrides=dict(base_overrides),
    )
    replay_config = model_replay.apply_model_schema_feature_flags(replay_config, args.model_dir)
    replay_split = model_replay.resolve_replay_split(manifest, args.lifecycle_dir)
    if split == "validation":
        files = replay_split.validation_files
        excluded_tokens = replay_split.excluded_validation_tokens
    elif split == "final":
        files = replay_split.eval_files
        excluded_tokens = replay_split.excluded_final_tokens
    else:
        raise ValueError(f"unsupported replay split: {split}")
    samples = model_replay.load_or_build_samples(
        replay_config,
        files,
        excluded_tokens,
        cache_dir=args.cache_dir,
        use_cache=args.use_cache,
    )
    cache[split] = samples
    return samples


def _run_replay(model_replay, args, *, split, overrides):
    return model_replay.run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=True,
        overrides=overrides,
        use_cache=args.use_cache,
        write_report=False,
    )


def _build_candidate(index, params, evaluation, baseline_summary, baseline_trade_log):
    summary = _summary(evaluation)
    trade_diff = _trade_diff_summary(baseline_trade_log, evaluation.get("trade_log") or [])
    gate_details = _gate_details(summary, baseline_summary, trade_diff)
    return {
        "candidate_index": int(index),
        "params": dict(params),
        "summary": summary,
        "trade_diff": trade_diff,
        "passes_acceptance_gate": all(gate_details.values()),
        "gate_details": gate_details,
        "evaluation": {key: value for key, value in evaluation.items() if key != "trade_log"},
    }


def main(argv=None):
    args = parse_args(argv)
    _assert_output_writable(args.model_dir, args.output, force=bool(args.force))

    model_replay = importlib.import_module("src.pipeline.model_replay")

    base_overrides = _base_overrides(args)
    sample_cache = {}
    validation_samples = _eval_samples_for_split(model_replay, args, base_overrides, "validation", sample_cache)
    final_samples = _eval_samples_for_split(model_replay, args, base_overrides, "final", sample_cache)

    validation_base_overrides = dict(base_overrides)
    if validation_samples is not None:
        validation_base_overrides["eval_samples"] = validation_samples
    validation_baseline_report = _run_replay(
        model_replay,
        args,
        split="validation",
        overrides=validation_base_overrides,
    )
    validation_baseline_evaluation = _evaluation(validation_baseline_report)
    validation_baseline_summary = _summary(validation_baseline_evaluation)
    validation_baseline_trade_log = list(validation_baseline_evaluation.get("trade_log") or [])

    candidates = []
    for index, params in enumerate(candidate_grid()):
        overrides = dict(base_overrides)
        overrides.update(params)
        if validation_samples is not None:
            overrides["eval_samples"] = validation_samples
        report = _run_replay(model_replay, args, split="validation", overrides=overrides)
        candidates.append(_build_candidate(
            index,
            params,
            _evaluation(report),
            validation_baseline_summary,
            validation_baseline_trade_log,
        ))

    best_validation_raw_candidate = max(candidates, key=_candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=_candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_base_overrides = dict(base_overrides)
    if final_samples is not None:
        final_base_overrides["eval_samples"] = final_samples
    final_baseline_report = _run_replay(model_replay, args, split="final", overrides=final_base_overrides)
    final_baseline_evaluation = _evaluation(final_baseline_report)
    final_baseline_summary = _summary(final_baseline_evaluation)
    final_baseline_trade_log = list(final_baseline_evaluation.get("trade_log") or [])

    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    if final_samples is not None:
        final_candidate_overrides["eval_samples"] = final_samples
    final_candidate_report = _run_replay(model_replay, args, split="final", overrides=final_candidate_overrides)
    final_candidate = _build_candidate(
        validation_selected["candidate_index"],
        validation_selected["params"],
        _evaluation(final_candidate_report),
        final_baseline_summary,
        final_baseline_trade_log,
    )
    final_confirmation = {
        "baseline": {
            "summary": final_baseline_summary,
            "evaluation": {key: value for key, value in final_baseline_evaluation.items() if key != "trade_log"},
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
        "acceptance_gate": _acceptance_gate(),
        "baseline": {
            "split": "validation",
            "summary": validation_baseline_summary,
            "entry_signatures": _entry_signature_rows(validation_baseline_trade_log),
            "evaluation": {key: value for key, value in validation_baseline_evaluation.items() if key != "trade_log"},
        },
        "candidates": candidates,
        "best_validation_raw_candidate": best_validation_raw_candidate,
        "best_validation_candidate": validation_selected,
        "best_validation_accepted_candidate": best_validation_accepted,
        "selected_candidate": validation_selected,
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
        "selected_validation_net_profit_bnb={selected:.12f} "
        "final_confirmation_passed={final_passed} candidates={count} output={output}".format(
            decision=report["decision"],
            baseline=validation_baseline_summary["net_profit_bnb"],
            selected=validation_selected["summary"]["net_profit_bnb"],
            final_passed=final_confirmation["passes_acceptance_gate"],
            count=len(candidates),
            output=str(output_path),
        )
    )
    return report


if __name__ == "__main__":
    main()
