#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import run_replacement_oracle_upper_bound_diagnostic as diagnostic
from scripts import run_runner_retention_candidate_gate_replay as runner_cli
from src.pipeline import replacement_oracle_upper_bound as oracle
from src.pipeline import runner_retention_replay_gate as retention_gate


DEFAULT_OUTPUT = "data/replay_reports/replacement_pair_selector_probe.json"
ALLOWED_OUTPUT_ROOTS = (
    PROJECT_ROOT / "data" / "replay_reports",
    PROJECT_ROOT / "docs" / "research",
)
PROTECTED_EXACT_PATHS = {".env", ".env.example", "docs/goals/live-model-optimization-goal.md"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Probe a read-only decision-time selector over same-token replacement pairs"
    )
    parser.add_argument("--model-dir", default=runner_cli.DEFAULT_MODEL_DIR)
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", default=".cache/model_replay")
    parser.add_argument("--position-fraction", type=runner_cli._strict_live_fraction, default=runner_cli.LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=runner_cli._strict_live_fraction, default=runner_cli.LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=runner_cli._strict_max_open_positions, default=runner_cli.STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--lead-windows-seconds", type=diagnostic._csv_ints, default=diagnostic._csv_ints("20,60,120,300"))
    parser.add_argument("--selector-lead-windows-seconds", type=diagnostic._csv_ints, default=None)
    parser.add_argument("--splits", type=diagnostic._csv_splits, default=diagnostic._csv_splits("validation,final"))
    parser.add_argument("--selection-split", choices=("train", "validation", "final"), default=None)
    parser.add_argument("--horizon-seconds", type=diagnostic._positive_float)
    parser.add_argument("--take-profit-pct", type=diagnostic._strict_take_profit, default=25.0)
    parser.add_argument("--stop-loss-pct", type=diagnostic._strict_stop_loss, default=-18.0)
    parser.add_argument("--cost-pct", type=float, default=0.0)
    parser.add_argument("--candidate-grid-json")
    parser.add_argument("--include-flow-features", action="store_true")
    parser.add_argument("--loss-cost", type=float, default=3.0)
    parser.add_argument("--min-keep-count", type=diagnostic._positive_int, default=20)
    parser.add_argument("--min-reject-count", type=diagnostic._positive_int, default=20)
    parser.add_argument("--min-eval-keep-count", type=diagnostic._positive_int, default=10)
    parser.add_argument("--min-positive-rate", type=float, default=0.50)
    parser.add_argument("--max-conditions", type=diagnostic._positive_int, default=2)
    parser.add_argument("--beam-width", type=diagnostic._positive_int, default=80)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _validate_output_path(output_text: str, *, force: bool) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in PROTECTED_EXACT_PATHS or normalized.startswith("docs/goals/"):
        raise SystemExit(f"refusing output path: {output_text}")
    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else PROJECT_ROOT / output_path
    resolved_output = logical_output.resolve(strict=False)
    for root in ALLOWED_OUTPUT_ROOTS:
        try:
            resolved_output.relative_to(root.resolve(strict=False))
            break
        except ValueError:
            continue
    else:
        allowed = ", ".join(str(root) for root in ALLOWED_OUTPUT_ROOTS)
        raise SystemExit(f"refusing output path outside allowed roots ({allowed}): {output_text}")
    if resolved_output.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing report without --force: {resolved_output}")
    return resolved_output


def _candidate_params_grid(args) -> list[dict[str, Any]]:
    if args.candidate_grid_json:
        return list(runner_cli.candidate_grid_from_json(args.candidate_grid_json))
    return list(runner_cli.candidate_grid())


def _scored_pairs_for_split(
    *,
    split_context: Mapping[str, Any],
    buy_artifact: Mapping[str, Any],
    runtime_params: Mapping[str, Any],
    candidate_params_grid: Sequence[Mapping[str, Any]],
    max_lead_seconds: int,
    horizon_seconds: float,
    take_profit_pct: float,
    stop_loss_pct: float,
    cost_pct: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    samples = list(split_context["samples"])
    price_paths_by_token = split_context["price_paths_by_token"]
    baseline_pass_times_by_token = retention_gate._baseline_entry_pass_times_by_token(
        samples,
        buy_artifact,
        runtime_params,
    )
    candidate_rows = []
    for params in candidate_params_grid:
        candidate_runtime_params = dict(runtime_params)
        candidate_runtime_params.update(dict(params))
        candidate_rows.extend(
            retention_gate._candidate_gate_rows_with_indices(
                samples,
                buy_artifact,
                candidate_runtime_params,
            )
        )
    unique_candidate_rows = diagnostic._dedupe_candidate_rows(candidate_rows)
    pairs = oracle.build_replacement_pairs(
        candidate_rows=unique_candidate_rows,
        baseline_pass_times_by_token=baseline_pass_times_by_token,
        price_paths_by_token=price_paths_by_token,
        max_lead_seconds=int(max_lead_seconds),
    )
    scored = [
        oracle.score_pair_barrier_returns(
            pair,
            list(price_paths_by_token.get(str(pair.get("token") or "").strip().lower()) or []),
            horizon_seconds=float(horizon_seconds),
            take_profit_pct=float(take_profit_pct),
            stop_loss_pct=float(stop_loss_pct),
            cost_pct=float(cost_pct),
        )
        for pair in pairs
    ]
    return scored, {
        "sample_count": int(len(samples)),
        "candidate_row_count": int(len(candidate_rows)),
        "unique_candidate_row_count": int(len(unique_candidate_rows)),
        "baseline_token_count": int(len(baseline_pass_times_by_token)),
        "baseline_pass_count": int(sum(len(times) for times in baseline_pass_times_by_token.values())),
        "replacement_pair_count": int(len(pairs)),
        "scored_pair_count": int(len(scored)),
    }


def _window_report(
    *,
    window_seconds: int,
    scored_pairs_by_split: Mapping[str, Sequence[Mapping[str, Any]]],
    selection_split: str,
    args,
) -> dict[str, Any]:
    selected_by_split = {
        split: [
            pair
            for pair in pairs
            if int(oracle._finite_float(pair.get("lead_seconds")) or 0) <= int(window_seconds)
        ]
        for split, pairs in scored_pairs_by_split.items()
    }
    return oracle.build_pair_selector_report(
        train_pairs=selected_by_split.get(selection_split, []),
        validation_pairs=selected_by_split.get("validation", []),
        final_pairs=selected_by_split.get("final", []),
        selection_split_name=selection_split,
        loss_cost=float(args.loss_cost),
        min_keep_count=int(args.min_keep_count),
        min_reject_count=int(args.min_reject_count),
        min_eval_keep_count=int(args.min_eval_keep_count),
        min_positive_rate=float(args.min_positive_rate),
        max_conditions=int(args.max_conditions),
        beam_width=int(args.beam_width),
    )


def _best_window(window_reports: Mapping[str, Mapping[str, Any]]) -> str | None:
    if not window_reports:
        return None

    def score(item: tuple[str, Mapping[str, Any]]) -> tuple[int, float, float]:
        _window, report = item
        accepted = 1 if report.get("decision") == "research_alpha" else 0
        validation = report.get("validation") if isinstance(report.get("validation"), Mapping) else {}
        final = report.get("final") if isinstance(report.get("final"), Mapping) else {}
        return (
            accepted,
            float(validation.get("selected_vs_no_replacement_utility_delta") or 0.0),
            float(final.get("selected_vs_no_replacement_utility_delta") or 0.0),
        )

    return max(window_reports.items(), key=score)[0]


def main(argv=None):
    args = parse_args(argv)
    if not math.isclose(args.position_fraction, runner_cli.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"position_fraction must be exactly {runner_cli.LIVE_POSITION_CAP}")
    if not math.isclose(args.max_position_fraction, runner_cli.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"max_position_fraction must be exactly {runner_cli.LIVE_POSITION_CAP}")
    if args.max_open_positions != runner_cli.STRICT_MAX_OPEN_POSITIONS:
        raise SystemExit(f"max_open_positions must be exactly {runner_cli.STRICT_MAX_OPEN_POSITIONS}")
    output_path = _validate_output_path(args.output, force=bool(args.force))

    candidate_params_grid = _candidate_params_grid(args)
    base_overrides = runner_cli._base_overrides(args)
    if bool(args.include_flow_features) or runner_cli.candidate_grid_requires_flow_features(candidate_params_grid):
        base_overrides["include_flow_features"] = True
    context = diagnostic._load_oracle_context(args, base_overrides)
    horizon_seconds = args.horizon_seconds
    if horizon_seconds is None:
        horizon_seconds = diagnostic._horizon_seconds(args, context["runtime_params"])
    selector_windows = args.selector_lead_windows_seconds or args.lead_windows_seconds
    max_lead_seconds = max(max(args.lead_windows_seconds), max(selector_windows))
    selection_split = args.selection_split or ("train" if "train" in args.splits else "validation")
    if selection_split not in args.splits:
        raise SystemExit(f"--selection-split {selection_split!r} must be included in --splits")
    if "validation" not in args.splits or "final" not in args.splits:
        raise SystemExit("--splits must include validation and final for selector evaluation")

    scored_pairs_by_split = {}
    split_counts = {}
    for split in args.splits:
        scored, counts = _scored_pairs_for_split(
            split_context=context["splits"][split],
            buy_artifact=context["buy_artifact"],
            runtime_params=context["runtime_params"],
            candidate_params_grid=candidate_params_grid,
            max_lead_seconds=int(max_lead_seconds),
            horizon_seconds=float(horizon_seconds),
            take_profit_pct=float(args.take_profit_pct),
            stop_loss_pct=float(args.stop_loss_pct),
            cost_pct=float(args.cost_pct),
        )
        scored_pairs_by_split[split] = scored
        split_counts[split] = counts

    window_reports = {
        str(window): _window_report(
            window_seconds=int(window),
            scored_pairs_by_split=scored_pairs_by_split,
            selection_split=selection_split,
            args=args,
        )
        for window in selector_windows
    }
    best_window = _best_window(window_reports)
    best_report = window_reports.get(str(best_window), {}) if best_window is not None else {}
    decision = "research_alpha" if any(
        report.get("decision") == "research_alpha" for report in window_reports.values()
    ) else "reject"
    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "decision": decision,
        "outcome_tier": "Research Alpha" if decision == "research_alpha" else "Rejected",
        "best_window_seconds": int(best_window) if best_window is not None else None,
        "best_window_report": best_report,
        "window_reports": window_reports,
        "split_counts": split_counts,
        "model_dir": str(args.model_dir),
        "lifecycle_dir": str(args.lifecycle_dir),
        "strict_assumptions": base_overrides,
        "selection_split": selection_split,
        "candidate_grid": {
            "source": str(args.candidate_grid_json) if args.candidate_grid_json else "default_runner_retention_grid",
            "candidate_count": int(len(candidate_params_grid)),
            "requires_flow_features": runner_cli.candidate_grid_requires_flow_features(candidate_params_grid),
        },
        "barrier_config": {
            "horizon_seconds": float(horizon_seconds),
            "take_profit_pct": float(args.take_profit_pct),
            "stop_loss_pct": float(args.stop_loss_pct),
            "cost_pct": float(args.cost_pct),
            "cost_parity_applied": True,
        },
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "uses_ex_post_outcomes": True,
            "uses_decision_time_features_only": True,
            "not_deployable_policy": True,
            "max_outcome_tier": "Research Alpha",
            "selection_split": selection_split,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(
        "decision={decision} outcome={outcome} best_window={window} output={output}".format(
            decision=report["decision"],
            outcome=report["outcome_tier"],
            window=report["best_window_seconds"],
            output=output_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
