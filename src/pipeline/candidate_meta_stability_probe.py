from __future__ import annotations

import datetime as dt
import itertools
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from src.pipeline import candidate_meta_label_probe as label_probe


def _as_list(values: Iterable[Any], *, name: str) -> list[Any]:
    result = list(values)
    if not result:
        raise ValueError(f"{name} must not be empty")
    return result


def _precision(selected_positive_count: int, selected_count: int) -> float:
    return selected_positive_count / selected_count if selected_count else 0.0


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _fold_block(report: Mapping[str, Any], *, end_index: int) -> dict[str, Any]:
    validation = report["validation"]
    train = report["train"]
    return {
        "end_index": end_index,
        "train_sources": list(report["split"]["train_sources"]),
        "validation_sources": list(report["split"]["validation_sources"]),
        "train_candidate_count": int(report["split"]["train_candidate_count"]),
        "validation_candidate_count": int(validation["candidate_count"]),
        "train_selected_count": int(train["selected_count"]),
        "train_selected_positive_count": int(train["selected_positive_count"]),
        "train_precision": float(train["precision"]),
        "validation_base_precision": float(validation["base_precision"]),
        "validation_selected_count": int(validation["selected_count"]),
        "validation_selected_positive_count": int(validation["selected_positive_count"]),
        "validation_precision": float(validation["precision"]),
        "validation_precision_lift_vs_base": float(validation["precision_lift_vs_base"]),
        "selected_symbols": list(validation["selected_symbols"]),
    }


def _summarize_grid_result(
    *,
    parameters: Mapping[str, Any],
    folds: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    min_validation_selected: int,
    min_train_selected: int,
    min_stable_precision: float,
) -> dict[str, Any]:
    eligible_folds = [
        fold
        for fold in folds
        if fold["validation_selected_count"] >= min_validation_selected
        and fold["train_selected_count"] >= min_train_selected
    ]
    validation_precisions = [float(fold["validation_precision"]) for fold in eligible_folds]
    selected_counts = [int(fold["validation_selected_count"]) for fold in eligible_folds]
    train_selected_counts = [int(fold["train_selected_count"]) for fold in eligible_folds]
    total_selected = sum(selected_counts)
    total_selected_positive = sum(int(fold["validation_selected_positive_count"]) for fold in eligible_folds)
    min_validation_precision = min(validation_precisions) if validation_precisions else 0.0
    min_validation_selected_count = min(selected_counts) if selected_counts else 0
    min_train_selected_count = min(train_selected_counts) if train_selected_counts else 0
    all_folds_eligible = len(eligible_folds) == len(folds) and not errors
    stable = all_folds_eligible and min_validation_precision >= min_stable_precision
    return {
        **dict(parameters),
        "fold_count": len(folds),
        "error_count": len(errors),
        "eligible_fold_count": len(eligible_folds),
        "all_folds_eligible": all_folds_eligible,
        "stable": stable,
        "min_validation_precision": min_validation_precision,
        "mean_validation_precision": _mean(validation_precisions),
        "pooled_precision": _precision(total_selected_positive, total_selected),
        "min_validation_selected_count": min_validation_selected_count,
        "min_train_selected_count": min_train_selected_count,
        "total_selected_count": total_selected,
        "total_selected_positive_count": total_selected_positive,
        "folds": folds,
        "errors": errors,
    }


def _ranked_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        results,
        key=lambda row: (
            bool(row["stable"]),
            float(row["min_validation_precision"]),
            float(row["pooled_precision"]),
            int(row["eligible_fold_count"]),
            int(row["total_selected_positive_count"]),
            int(row["total_selected_count"]),
        ),
        reverse=True,
    )
    return [{**row, "rank": index} for index, row in enumerate(ranked, start=1)]


def build_candidate_meta_stability_report(
    *,
    time_to_barrier_reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None = None,
    validation_report_counts: Iterable[int] = (1,),
    probability_thresholds: Iterable[float] = (0.5,),
    max_depths: Iterable[int] = (3,),
    min_samples_leaf_values: Iterable[int] = (3,),
    min_validation_selected: int = 3,
    min_train_selected: int = 3,
    min_stable_precision: float = 0.5,
    candidate_filters: Iterable[Mapping[str, Any] | Sequence[Any]] | None = None,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    reports = list(time_to_barrier_reports)
    if len(reports) < 3:
        raise ValueError("at least three source reports are required for rolling validation")
    names = list(source_names or [f"report_{index}" for index in range(len(reports))])
    if len(names) != len(reports):
        raise ValueError("source_names length must match time_to_barrier_reports")
    if min_validation_selected <= 0:
        raise ValueError("min_validation_selected must be positive")
    if min_train_selected <= 0:
        raise ValueError("min_train_selected must be positive")
    if not 0.0 <= min_stable_precision <= 1.0:
        raise ValueError("min_stable_precision must be between 0 and 1")

    validation_counts = [int(value) for value in _as_list(validation_report_counts, name="validation_report_counts")]
    thresholds = [float(value) for value in _as_list(probability_thresholds, name="probability_thresholds")]
    depth_values = [int(value) for value in _as_list(max_depths, name="max_depths")]
    leaf_values = [int(value) for value in _as_list(min_samples_leaf_values, name="min_samples_leaf_values")]
    if any(value <= 0 or value >= len(reports) for value in validation_counts):
        raise ValueError("validation_report_counts must leave at least one train and one validation source")
    normalized_filters = label_probe._normalize_candidate_filters(candidate_filters)

    grid_results: list[dict[str, Any]] = []
    for validation_count, threshold, max_depth, min_samples_leaf in itertools.product(
        validation_counts,
        thresholds,
        depth_values,
        leaf_values,
    ):
        parameters = {
            "validation_report_count": validation_count,
            "probability_threshold": threshold,
            "max_depth": max_depth,
            "min_samples_leaf": min_samples_leaf,
        }
        folds: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for end_index in range(validation_count + 1, len(reports) + 1):
            try:
                report = label_probe.build_candidate_meta_label_report(
                    time_to_barrier_reports=reports[:end_index],
                    source_names=names[:end_index],
                    validation_report_count=validation_count,
                    probability_threshold=threshold,
                    min_validation_selected=1,
                    max_depth=max_depth,
                    min_samples_leaf=min_samples_leaf,
                    candidate_filters=normalized_filters,
                )
            except ValueError as exc:
                errors.append({"end_index": end_index, "error": str(exc)})
                continue
            folds.append(_fold_block(report, end_index=end_index))

        grid_results.append(
            _summarize_grid_result(
                parameters=parameters,
                folds=folds,
                errors=errors,
                min_validation_selected=min_validation_selected,
                min_train_selected=min_train_selected,
                min_stable_precision=min_stable_precision,
            )
        )

    ranked_results = _ranked_results(grid_results)
    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "probe_only_replay_required",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": "rolling folds reuse decision-time meta-label features only",
        },
        "inputs": {"time_to_barrier_reports": names},
        "parameters": {
            "validation_report_counts": validation_counts,
            "probability_thresholds": thresholds,
            "max_depths": depth_values,
            "min_samples_leaf_values": leaf_values,
            "min_validation_selected": min_validation_selected,
            "min_train_selected": min_train_selected,
            "min_stable_precision": min_stable_precision,
            "candidate_filters": normalized_filters,
        },
        "candidate_counts": {
            "source_reports": len(reports),
            "grid_configurations": len(grid_results),
        },
        "top_stable_results": [row for row in ranked_results if row["stable"]][:20],
        "top_results": ranked_results[:20],
        "grid_results": ranked_results,
    }


def to_json_text(report: Mapping[str, Any]) -> str:
    return label_probe.to_json_text(report)
