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

from scripts import run_runner_retention_candidate_gate_replay as runner_cli
from src.pipeline import replacement_oracle_upper_bound as oracle
from src.pipeline import runner_retention_replay_gate as retention_gate

DEFAULT_OUTPUT = "data/replay_reports/replacement_oracle_upper_bound_diagnostic_20260527.json"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be a positive finite float")
    return parsed


def _strict_take_profit(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not math.isclose(parsed, 25.0, rel_tol=0.0, abs_tol=1e-12):
        raise argparse.ArgumentTypeError("value must be exactly 25.0")
    return parsed


def _strict_stop_loss(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or not math.isclose(parsed, -18.0, rel_tol=0.0, abs_tol=1e-12):
        raise argparse.ArgumentTypeError("value must be exactly -18.0")
    return parsed


def _csv_ints(value: str) -> list[int]:
    parsed = []
    for item in str(value or "").split(","):
        text = item.strip()
        if not text:
            continue
        parsed.append(_positive_int(text))
    if not parsed:
        raise argparse.ArgumentTypeError("at least one positive integer is required")
    return sorted(set(parsed))


def _csv_splits(value: str) -> list[str]:
    supported = {"train", "validation", "final"}
    parsed = []
    for item in str(value or "").split(","):
        split = item.strip().lower()
        if not split:
            continue
        if split not in supported:
            raise argparse.ArgumentTypeError(f"unsupported split {split!r}; choose from train,validation,final")
        parsed.append(split)
    if not parsed:
        raise argparse.ArgumentTypeError("at least one split is required")
    return list(dict.fromkeys(parsed))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a replacement-only oracle upper-bound phase-1 diagnostic"
    )
    parser.add_argument("--model-dir", default=runner_cli.DEFAULT_MODEL_DIR)
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", default=".cache/model_replay")
    parser.add_argument("--position-fraction", type=runner_cli._strict_live_fraction, default=runner_cli.LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=runner_cli._strict_live_fraction, default=runner_cli.LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=runner_cli._strict_max_open_positions, default=runner_cli.STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--lead-windows-seconds", type=_csv_ints, default=_csv_ints("20,60,120,300"))
    parser.add_argument("--splits", type=_csv_splits, default=_csv_splits("validation,final"))
    parser.add_argument("--phase", choices=("pair", "barrier"), default="pair")
    parser.add_argument("--horizon-seconds", type=_positive_float)
    parser.add_argument("--take-profit-pct", type=_strict_take_profit, default=25.0)
    parser.add_argument("--stop-loss-pct", type=_strict_stop_loss, default=-18.0)
    parser.add_argument("--cost-pct", type=float, default=0.0)
    parser.add_argument("--candidate-grid-json")
    parser.add_argument("--include-flow-features", action="store_true")
    parser.add_argument("--min-pairs-per-split", type=_positive_int, default=100)
    parser.add_argument("--min-pre-move-p75-pct", type=_positive_float, default=5.0)
    parser.add_argument("--min-delta-realized-p50-pct", type=float, default=1.0)
    parser.add_argument("--max-candidate-stop-first-ratio", type=float, default=0.40)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false")
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def _load_oracle_context(args, base_overrides: Mapping[str, Any]) -> dict[str, Any]:
    from src.pipeline.candidate_ranker_probe import runtime_params_with_buy_threshold
    from src.pipeline.model_replay import (
        apply_model_schema_feature_flags,
        live_replay_config_from_manifest,
        load_manifest,
        load_model_artifacts,
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
    artifacts = load_model_artifacts(args.model_dir)
    buy_artifact = artifacts.buy_artifact
    runtime_params = runtime_params_with_buy_threshold(replay_config, buy_artifact)

    split_specs = {
        "train": (replay_split.train_files, set()),
        "validation": (replay_split.validation_files, replay_split.excluded_validation_tokens),
        "final": (replay_split.eval_files, replay_split.excluded_final_tokens),
    }
    splits = {}
    for split in args.splits:
        files, excluded_tokens = split_specs[split]
        splits[split] = {
            "samples": load_or_build_samples(
                replay_config,
                files,
                excluded_tokens,
                cache_dir=args.cache_dir,
                use_cache=args.use_cache,
            ),
            "price_paths_by_token": retention_gate.load_train_price_paths_by_token(files),
            "lifecycle_paths": [str(path) for path in files],
        }
    return {
        "buy_artifact": buy_artifact,
        "runtime_params": runtime_params,
        "splits": splits,
    }


def _candidate_grid(args) -> list[dict[str, Any]]:
    if args.candidate_grid_json:
        return list(runner_cli.candidate_grid_from_json(args.candidate_grid_json))
    return list(runner_cli.candidate_grid())


def _candidate_key(row: Mapping[str, Any]) -> tuple[str, int]:
    return (
        str(row.get("token") or "").strip().lower(),
        int(oracle._finite_float(row.get("decision_sample_time", row.get("sample_time"))) or 0),
    )


def _dedupe_candidate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        key = _candidate_key(row)
        if not key[0] or key[1] <= 0:
            continue
        unique.setdefault(key, dict(row))
    return [unique[key] for key in sorted(unique, key=lambda item: (item[1], item[0]))]


def _split_report(
    *,
    split: str,
    samples: Sequence[Mapping[str, Any]],
    price_paths_by_token,
    lifecycle_paths: Sequence[str],
    buy_artifact,
    base_runtime_params: Mapping[str, Any],
    candidate_params_grid: Sequence[Mapping[str, Any]],
    lead_windows_seconds: Sequence[int],
    phase: str,
    horizon_seconds: float,
    take_profit_pct: float,
    stop_loss_pct: float,
    cost_pct: float,
) -> dict[str, Any]:
    baseline_pass_times_by_token = retention_gate._baseline_entry_pass_times_by_token(
        samples,
        buy_artifact,
        base_runtime_params,
    )
    candidate_rows = []
    for params in candidate_params_grid:
        runtime_params = dict(base_runtime_params)
        runtime_params.update(dict(params))
        candidate_rows.extend(
            retention_gate._candidate_gate_rows_with_indices(
                samples,
                buy_artifact,
                runtime_params,
            )
        )
    unique_candidate_rows = _dedupe_candidate_rows(candidate_rows)
    pairs = oracle.build_replacement_pairs(
        candidate_rows=unique_candidate_rows,
        baseline_pass_times_by_token=baseline_pass_times_by_token,
        price_paths_by_token=price_paths_by_token,
        max_lead_seconds=max(lead_windows_seconds),
    )
    if phase == "barrier":
        scored_pairs = [
            oracle.score_pair_barrier_returns(
                pair,
                list(price_paths_by_token.get(str(pair.get("token") or "").strip().lower()) or []),
                horizon_seconds=horizon_seconds,
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
                cost_pct=cost_pct,
            )
            for pair in pairs
        ]
        windows = oracle.summarize_scored_pairs_by_window(
            scored_pairs,
            lead_windows_seconds=lead_windows_seconds,
        )
    else:
        scored_pairs = []
        windows = oracle.summarize_pairs_by_window(
            pairs,
            lead_windows_seconds=lead_windows_seconds,
        )
    return {
        "split": split,
        "sample_count": int(len(samples)),
        "lifecycle_paths": list(lifecycle_paths),
        "candidate_row_count": int(len(candidate_rows)),
        "unique_candidate_row_count": int(len(unique_candidate_rows)),
        "baseline_token_count": int(len(baseline_pass_times_by_token)),
        "baseline_pass_count": int(sum(len(times) for times in baseline_pass_times_by_token.values())),
        "replacement_pair_count": int(len(pairs)),
        "scored_pair_count": int(len(scored_pairs)),
        "windows": windows,
    }


def _horizon_seconds(args, runtime_params: Mapping[str, Any]) -> float:
    if args.horizon_seconds is not None:
        return float(args.horizon_seconds)
    value = oracle._finite_float(runtime_params.get("max_hold_seconds"))
    if value is None or value <= 0.0:
        raise SystemExit("runtime max_hold_seconds is required for --phase barrier; pass --horizon-seconds")
    return float(value)


def main(argv=None):
    args = parse_args(argv)
    if not math.isclose(args.position_fraction, runner_cli.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"position_fraction must be exactly {runner_cli.LIVE_POSITION_CAP}")
    if not math.isclose(args.max_position_fraction, runner_cli.LIVE_POSITION_CAP, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"max_position_fraction must be exactly {runner_cli.LIVE_POSITION_CAP}")
    if args.max_open_positions != runner_cli.STRICT_MAX_OPEN_POSITIONS:
        raise SystemExit(f"max_open_positions must be exactly {runner_cli.STRICT_MAX_OPEN_POSITIONS}")
    runner_cli._assert_output_writable(args.model_dir, args.output, force=bool(args.force))

    candidate_params_grid = _candidate_grid(args)
    base_overrides = runner_cli._base_overrides(args)
    if bool(args.include_flow_features) or runner_cli.candidate_grid_requires_flow_features(candidate_params_grid):
        base_overrides["include_flow_features"] = True
    context = _load_oracle_context(args, base_overrides)
    horizon_seconds = (
        _horizon_seconds(args, context["runtime_params"])
        if args.phase == "barrier"
        else float(args.horizon_seconds or oracle._finite_float(context["runtime_params"].get("max_hold_seconds")) or 0.0)
    )
    split_reports = {}
    for split in args.splits:
        split_context = context["splits"][split]
        split_reports[split] = _split_report(
            split=split,
            samples=list(split_context["samples"]),
            price_paths_by_token=split_context["price_paths_by_token"],
            lifecycle_paths=split_context["lifecycle_paths"],
            buy_artifact=context["buy_artifact"],
            base_runtime_params=context["runtime_params"],
            candidate_params_grid=candidate_params_grid,
            lead_windows_seconds=args.lead_windows_seconds,
            phase=args.phase,
            horizon_seconds=horizon_seconds,
            take_profit_pct=float(args.take_profit_pct),
            stop_loss_pct=float(args.stop_loss_pct),
            cost_pct=float(args.cost_pct),
        )
    split_summaries = {split: report["windows"] for split, report in split_reports.items()}
    required_splits = tuple(split for split in ("validation", "final") if split in split_summaries)
    if args.phase == "barrier":
        decision = oracle.build_barrier_decision(
            split_summaries,
            required_splits=required_splits,
            min_pairs_per_split=args.min_pairs_per_split,
            min_delta_realized_p50_pct=float(args.min_delta_realized_p50_pct),
            max_candidate_stop_first_ratio=float(args.max_candidate_stop_first_ratio),
        )
    else:
        decision = oracle.build_decision(
            split_summaries,
            required_splits=required_splits,
            min_pairs_per_split=args.min_pairs_per_split,
            min_pre_move_p75_pct=args.min_pre_move_p75_pct,
        )
    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model_dir": str(args.model_dir),
        "lifecycle_dir": str(args.lifecycle_dir),
        "strict_assumptions": base_overrides,
        "phase": "barrier_respecting" if args.phase == "barrier" else "pair_count_pre_move",
        "estimator_type": "ex_post_path_simulation",
        "uses_ex_post_outcomes": True,
        "live_switch_evidence": False,
        "not_deployable_policy": True,
        "candidate_grid": {
            "source": str(args.candidate_grid_json) if args.candidate_grid_json else "default_runner_retention_grid",
            "candidate_count": int(len(candidate_params_grid)),
            "requires_flow_features": runner_cli.candidate_grid_requires_flow_features(candidate_params_grid),
        },
        "lead_windows_seconds": list(args.lead_windows_seconds),
        "minimum_decision_thresholds": {
            "min_pairs_per_split": int(args.min_pairs_per_split),
            "min_pre_move_p75_pct": float(args.min_pre_move_p75_pct),
            "min_delta_realized_p50_pct": float(args.min_delta_realized_p50_pct),
            "max_candidate_stop_first_ratio": float(args.max_candidate_stop_first_ratio),
        },
        "barrier_config": {
            "horizon_seconds": float(horizon_seconds),
            "take_profit_pct": float(args.take_profit_pct),
            "stop_loss_pct": float(args.stop_loss_pct),
            "cost_pct": float(args.cost_pct),
            "cost_parity_applied": True,
        },
        "decision": decision,
        "splits": split_reports,
        "caveats": [
            "This is an ex-post path simulation, not a valid off-policy estimator.",
            "Candidate rows are replacement-only: they must precede a future same-token baseline pass.",
            "Phase 1 only measures support and pre-baseline price movement; it does not claim deployable PnL.",
        ],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(
        "decision={decision} reason={reason} output={output}".format(
            decision=decision["decision"],
            reason=decision["reason"],
            output=output_path,
        )
    )
    return report


if __name__ == "__main__":
    main()
