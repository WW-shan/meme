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
DEFAULT_OUTPUT = "data/replay_reports/flow_abstention_replay_20260526_v95.json"
REPLAY_REPORTS_DIR = Path("data/replay_reports")
LIVE_INITIAL_EQUITY_BNB = 0.002989815772142944
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
MAX_GRID_CANDIDATES = 200
MAX_TRADE_COUNT_REDUCTION_RATIO = 0.25
MAX_TRADE_COUNT_REDUCTION_MIN_MISSING = 1
PROTECTED_OUTPUTS = frozenset((
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
))
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
    parser = argparse.ArgumentParser(description="Run a bounded flow-abstention veto replay grid")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Directory containing trained model artifacts")
    parser.add_argument("--lifecycle-dir", default="data/training", help="Directory containing lifecycle files")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Replay grid JSON output path")
    parser.add_argument("--cache-dir", default=".cache/model_replay", help="Directory for replay sample cache files")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument(
        "--candidate-grid-json",
        help="Optional JSON file containing a list of candidate parameter dictionaries",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing replay report")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false", help="Rebuild replay samples instead of using cache")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def _flow_condition_candidates():
    for threshold in (0.75, 1.0, 1.05):
        yield {"buy_flow_abstention_max_buy_sell_ratio_30s": threshold}
    for threshold in (0.50, 0.55, 0.60):
        yield {"buy_flow_abstention_min_sell_pressure_30s": threshold}
    for threshold in (0.0, 0.05, 0.10):
        yield {"buy_flow_abstention_max_signed_imbalance_30s": threshold}
    for threshold in (15.0, 16.0, 18.0):
        yield {"buy_flow_abstention_min_event_count_10s": threshold}


def _default_candidate_grid():
    min_probs = [0.94, 0.98]
    max_ages = [60.0, 300.0]
    volume_floors = [0.0, 1.5]
    volatility_floors = [0.0, 0.08]
    for min_prob, max_age, min_volume, min_volatility in itertools.product(
        min_probs,
        max_ages,
        volume_floors,
        volatility_floors,
    ):
        for condition in _flow_condition_candidates():
            candidate = {
                "buy_flow_abstention_min_prob": min_prob,
                "buy_flow_abstention_max_age_seconds": max_age,
                "buy_flow_abstention_min_entry_volume_30s": min_volume,
                "buy_flow_abstention_min_entry_price_volatility": min_volatility,
            }
            candidate.update(condition)
            yield candidate


def candidate_grid():
    candidates = list(_default_candidate_grid())
    if len(candidates) > MAX_GRID_CANDIDATES:
        raise RuntimeError(f"flow abstention grid has {len(candidates)} candidates; max is {MAX_GRID_CANDIDATES}")
    return iter(candidates)


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
    if len(candidates) > MAX_GRID_CANDIDATES:
        raise SystemExit(
            f"--candidate-grid-json contains {len(candidates)} candidates; max is {MAX_GRID_CANDIDATES}"
        )
    return candidates


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
    rows = []
    for row in evaluation.get("stress_replay", []) or []:
        metrics = {
            key: _finite_metric(row, key)
            for key in ("net_return_pct", "net_profit_bnb", "max_drawdown_pct")
        }
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
    return {
        "has_primary_metrics": bool(has_primary_metrics),
        "net_profit_bnb": 0.0 if net_profit_bnb is None else float(net_profit_bnb),
        "total_trades": 0 if total_trades is None else int(total_trades),
        "max_drawdown_pct": 0.0 if max_drawdown_pct is None else float(max_drawdown_pct),
        "win_rate": 0.0 if win_rate is None else float(win_rate),
        "has_walk_forward_metrics": bool(has_walk_forward_metrics),
        "has_stress_replay": bool(_valid_stress_metrics(evaluation) and has_complete_stress_replay),
        "stress_replay_scenarios": stress_replay_scenarios,
        "walk_forward_worst_net_return_pct": walk_forward_worst_net_return_pct,
        "walk_forward_worst_max_drawdown_pct": walk_forward_worst_max_drawdown_pct,
        "stress_worst_net_return_pct": _stress_worst(evaluation, "net_return_pct"),
        "stress_worst_net_profit_bnb": _stress_worst(evaluation, "net_profit_bnb"),
        "stress_worst_max_drawdown_pct": _stress_worst(evaluation, "max_drawdown_pct"),
        "flow_abstention_veto_signal_count": _int_metric(evaluation, "flow_abstention_veto_signal_count"),
        "flow_abstention_veto_reject_count": _int_metric(evaluation, "flow_abstention_veto_reject_count"),
    }


def _acceptance_gate():
    return {
        "baseline": "current_v95_strict_live_sized_replay",
        "requires_net_profit_bnb_above_baseline": True,
        "requires_max_drawdown_pct_not_worse": True,
        "requires_total_trades_not_materially_lower": True,
        "max_trade_count_reduction_ratio": MAX_TRADE_COUNT_REDUCTION_RATIO,
        "max_trade_count_reduction_min_missing": MAX_TRADE_COUNT_REDUCTION_MIN_MISSING,
        "requires_total_trades_not_higher": True,
        "max_trade_count_expansion": 0,
        "requires_win_rate_not_lower": True,
        "requires_walk_forward_worst_net_return_pct_not_lower": True,
        "requires_walk_forward_worst_max_drawdown_pct_not_worse": True,
        "requires_stress_worst_net_return_pct_not_lower": True,
        "requires_stress_worst_net_profit_bnb_not_lower": True,
        "requires_stress_worst_max_drawdown_pct_not_worse": True,
        "requires_flow_abstention_veto_rejections": True,
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
    max_missing_trades = max(
        MAX_TRADE_COUNT_REDUCTION_MIN_MISSING,
        math.ceil(baseline_trades * MAX_TRADE_COUNT_REDUCTION_RATIO),
    )
    return {
        "has_primary_metrics": has_primary_metrics,
        "has_walk_forward_metrics": has_walk_forward_metrics,
        "has_stress_replay": has_stress_replay,
        "same_stress_replay_scenarios": same_stress_scenarios,
        "net_profit_bnb": has_primary_metrics and candidate_summary["net_profit_bnb"] > baseline_summary["net_profit_bnb"],
        "max_drawdown_pct": has_primary_metrics and candidate_summary["max_drawdown_pct"] >= baseline_summary["max_drawdown_pct"],
        "total_trades_not_materially_lower": (
            has_primary_metrics
            and candidate_summary["total_trades"] >= max(0, baseline_trades - max_missing_trades)
        ),
        "total_trades_not_higher": (
            has_primary_metrics
            and candidate_summary["total_trades"] <= baseline_trades
        ),
        "win_rate": has_primary_metrics and candidate_summary["win_rate"] >= baseline_summary["win_rate"],
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
        "flow_abstention_veto_reject_count": candidate_summary["flow_abstention_veto_reject_count"] > 0,
    }


def _raw_candidate_score(row):
    summary = row.get("summary", {})
    if not summary.get("has_primary_metrics"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    return (
        summary["net_profit_bnb"],
        summary["max_drawdown_pct"],
        summary["win_rate"],
        -row["candidate_index"],
    )


def _accepted_candidate_score(row):
    if not row.get("passes_acceptance_gate"):
        return (-math.inf, -math.inf, -math.inf, -row["candidate_index"])
    summary = row["summary"]
    return (
        summary["net_profit_bnb"],
        summary["walk_forward_worst_net_return_pct"],
        summary["win_rate"],
        -row["candidate_index"],
    )


def _assert_safe_output_path(model_dir, output_path):
    output_path = Path(output_path)
    if output_path.name not in PROTECTED_MODEL_ARTIFACT_NAMES:
        return
    try:
        output_path.resolve(strict=False).relative_to(Path(model_dir).resolve(strict=False))
    except ValueError:
        return
    raise SystemExit(f"refusing to write replay report to protected model artifact: {output_path}")


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _refuse_symlinked_replay_root(repo_root: Path, replay_root: Path) -> None:
    current = repo_root
    for part in replay_root.relative_to(repo_root).parts:
        current = current / part
        if current.is_symlink():
            raise SystemExit(f"refusing output path because {current} is a symlink")


def _validate_output_path(output_text: str) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in PROTECTED_OUTPUTS:
        raise SystemExit(f"refusing output path: {output_text}")

    repo_root = PROJECT_ROOT.resolve()
    replay_root = repo_root / REPLAY_REPORTS_DIR
    _refuse_symlinked_replay_root(repo_root, replay_root)
    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else repo_root / output_path
    resolved_output = logical_output.resolve()
    if not _is_relative_to(resolved_output, replay_root.resolve()):
        raise SystemExit(f"refusing output path outside {REPLAY_REPORTS_DIR}: {output_text}")
    return resolved_output


def _assert_output_writable(model_dir, output_path, *, force=False):
    output_path = _validate_output_path(str(output_path))
    _assert_safe_output_path(model_dir, output_path)
    if output_path.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing replay report without --force: {output_path}")
    return output_path


def main(argv=None):
    args = parse_args(argv)
    output_path = _assert_output_writable(args.model_dir, args.output, force=bool(args.force))

    from src.pipeline.model_replay import run_model_replay

    base_overrides = _base_overrides(args)
    validation_baseline_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="validation",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        use_cache=args.use_cache,
        overrides=base_overrides,
        write_report=False,
    )
    validation_baseline_summary = _summary(_evaluation(validation_baseline_report))

    grid_candidates = (
        candidate_grid_from_json(args.candidate_grid_json)
        if args.candidate_grid_json
        else list(candidate_grid())
    )
    candidates = []
    for index, params in enumerate(grid_candidates):
        candidate_overrides = dict(base_overrides)
        candidate_overrides.update(params)
        candidate_report = run_model_replay(
            model_dir=args.model_dir,
            lifecycle_dir=args.lifecycle_dir,
            output_path=None,
            cache_dir=args.cache_dir,
            split="validation",
            max_open_positions=args.max_open_positions,
            include_trade_log=False,
            use_cache=args.use_cache,
            overrides=candidate_overrides,
            write_report=False,
        )
        candidate_evaluation = _evaluation(candidate_report)
        summary = _summary(candidate_evaluation)
        gate_details = _gate_details(summary, validation_baseline_summary)
        candidates.append({
            "candidate_index": int(index),
            "params": dict(params),
            "summary": summary,
            "passes_acceptance_gate": all(gate_details.values()),
            "gate_details": gate_details,
            "evaluation": candidate_evaluation,
        })

    if not candidates:
        raise SystemExit("flow abstention replay grid produced no candidates")

    best_validation_raw_candidate = max(candidates, key=_raw_candidate_score)
    accepted = [candidate for candidate in candidates if candidate["passes_acceptance_gate"]]
    best_validation_accepted = max(accepted, key=_accepted_candidate_score, default=None)
    validation_selected = best_validation_accepted or best_validation_raw_candidate

    final_baseline_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="final",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        use_cache=args.use_cache,
        overrides=base_overrides,
        write_report=False,
    )
    final_baseline_summary = _summary(_evaluation(final_baseline_report))
    final_candidate_overrides = dict(base_overrides)
    final_candidate_overrides.update(validation_selected["params"])
    final_candidate_report = run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split="final",
        max_open_positions=args.max_open_positions,
        include_trade_log=False,
        use_cache=args.use_cache,
        overrides=final_candidate_overrides,
        write_report=False,
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
    }
    final_confirmation = {
        "baseline": {
            "summary": final_baseline_summary,
            "evaluation": _evaluation(final_baseline_report),
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
            "A decision-time flow-abstention veto skips high sell-pressure, non-positive-flow, "
            "or high short-window event-count entries without removing protected runners."
        ),
        "candidate_grid_json": args.candidate_grid_json,
        "strict_assumptions": base_overrides,
        "acceptance_gate": _acceptance_gate(),
        "baseline": {
            "split": "validation",
            "summary": validation_baseline_summary,
            "evaluation": _evaluation(validation_baseline_report),
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
