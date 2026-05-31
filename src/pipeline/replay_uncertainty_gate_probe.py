from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


SPLITS = ("validation", "final")


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {key: _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _is_trade_delta_block(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    return isinstance(value.get("delta_summary"), Mapping) and any(
        isinstance(value.get(key), list)
        for key in ("common_trade_deltas", "added_candidate_trades", "removed_baseline_trades")
    )


def _find_report_trade_delta_split(report: Mapping[str, Any], split: str) -> tuple[Mapping[str, Any] | None, str]:
    selected = report.get("selected_trade_delta_attribution")
    if isinstance(selected, Mapping):
        block = selected.get(split)
        if _is_trade_delta_block(block):
            return block, f"selected_trade_delta_attribution.{split}"

    splits = report.get("splits")
    if isinstance(splits, Mapping):
        split_block = splits.get(split)
        if isinstance(split_block, Mapping):
            nested = split_block.get("trade_delta_attribution")
            if _is_trade_delta_block(nested):
                return nested, f"splits.{split}.trade_delta_attribution"
            if _is_trade_delta_block(split_block):
                return split_block, f"splits.{split}"

    return None, "missing"


def extract_trade_delta_splits(
    *,
    replay_report: Mapping[str, Any] | None = None,
    validation_trade_delta: Mapping[str, Any] | None = None,
    final_trade_delta: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Mapping[str, Any]], dict[str, str]]:
    splits: dict[str, Mapping[str, Any]] = {}
    sources: dict[str, str] = {}
    explicit = {
        "validation": validation_trade_delta,
        "final": final_trade_delta,
    }
    for split, block in explicit.items():
        if block is not None:
            if not _is_trade_delta_block(block):
                raise ValueError(f"{split}_trade_delta is not a trade-delta attribution block")
            splits[split] = block
            sources[split] = f"explicit_{split}_trade_delta"

    if replay_report is not None:
        for split in SPLITS:
            if split in splits:
                continue
            block, source = _find_report_trade_delta_split(replay_report, split)
            if block is not None:
                splits[split] = block
                sources[split] = source

    return splits, sources


def _return_pct(row: Mapping[str, Any]) -> float:
    for key in ("return_pct", "net_return_pct", "return_delta_pct"):
        value = _finite_float(row.get(key))
        if value is not None:
            return value
    return 0.0


def _contribution_rows(block: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in block.get("common_trade_deltas") or []:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "kind": "common_trade_delta",
                "token": str(row.get("token") or ""),
                "entry_signal_time": row.get("entry_signal_time"),
                "contribution_pct": _return_pct(row),
                "baseline_return_pct": _finite_float(row.get("baseline_return_pct")),
                "candidate_return_pct": _finite_float(row.get("candidate_return_pct")),
                "baseline_exit_reason": str(row.get("baseline_exit_reason") or ""),
                "candidate_exit_reason": str(row.get("candidate_exit_reason") or ""),
            }
        )

    for row in block.get("added_candidate_trades") or []:
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "kind": "added_candidate_trade",
                "token": str(row.get("token") or ""),
                "entry_signal_time": row.get("entry_signal_time"),
                "contribution_pct": _return_pct(row),
                "baseline_return_pct": None,
                "candidate_return_pct": _return_pct(row),
                "candidate_exit_reason": str(row.get("exit_reason") or ""),
            }
        )

    for row in block.get("removed_baseline_trades") or []:
        if not isinstance(row, Mapping):
            continue
        baseline_return = _return_pct(row)
        rows.append(
            {
                "kind": "removed_baseline_trade",
                "token": str(row.get("token") or ""),
                "entry_signal_time": row.get("entry_signal_time"),
                "contribution_pct": -baseline_return,
                "baseline_return_pct": baseline_return,
                "candidate_return_pct": None,
                "baseline_exit_reason": str(row.get("exit_reason") or ""),
            }
        )

    return rows


def _bootstrap_total_delta(
    values: Sequence[float],
    *,
    bootstrap_samples: int,
    confidence_level: float,
    seed: int,
) -> dict[str, Any]:
    if not values:
        return {
            "bootstrap_samples": int(bootstrap_samples),
            "confidence_level": float(confidence_level),
            "observed": 0.0,
            "mean": 0.0,
            "lower": 0.0,
            "upper": 0.0,
            "positive_probability": 0.0,
            "non_negative_probability": 1.0,
        }

    array = np.asarray(values, dtype=float)
    observed = float(np.sum(array))
    rng = np.random.default_rng(int(seed))
    indices = rng.integers(0, len(array), size=(int(bootstrap_samples), len(array)))
    totals = array[indices].sum(axis=1)
    alpha = (1.0 - float(confidence_level)) / 2.0
    return {
        "bootstrap_samples": int(bootstrap_samples),
        "confidence_level": float(confidence_level),
        "observed": observed,
        "mean": float(np.mean(totals)),
        "lower": float(np.quantile(totals, alpha)),
        "upper": float(np.quantile(totals, 1.0 - alpha)),
        "positive_probability": float(np.mean(totals > 0.0)),
        "non_negative_probability": float(np.mean(totals >= 0.0)),
    }


def _top_winner_dependency(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = [_finite_float(row.get("contribution_pct")) or 0.0 for row in rows]
    observed = float(sum(values))
    positives = sorted((value for value in values if value > 0.0), reverse=True)
    positive_total = float(sum(positives))

    def _remove_top(count: int) -> float:
        return float(observed - sum(positives[:count]))

    after_top1 = _remove_top(1) if positives else observed
    after_top3 = _remove_top(3) if len(positives) >= 3 else observed
    return {
        "observed_delta_pct": observed,
        "positive_contribution_count": len(positives),
        "positive_contribution_sum_pct": positive_total,
        "top1_contribution_pct": float(positives[0]) if positives else 0.0,
        "top3_contribution_pct": float(sum(positives[:3])) if positives else 0.0,
        "top1_share_of_positive_delta": float(positives[0] / positive_total) if positive_total > 0.0 else 0.0,
        "top3_share_of_positive_delta": float(sum(positives[:3]) / positive_total) if positive_total > 0.0 else 0.0,
        "delta_after_removing_top1_pct": after_top1,
        "delta_after_removing_top3_pct": after_top3,
        "top1_dependency": bool(observed > 0.0 and positives and after_top1 <= 0.0),
        "top3_dependency": bool(observed > 0.0 and len(positives) > 3 and after_top3 <= 0.0),
        "top_positive_contributions": sorted(
            (
                {
                    "kind": str(row.get("kind") or ""),
                    "token": str(row.get("token") or ""),
                    "entry_signal_time": row.get("entry_signal_time"),
                    "contribution_pct": _finite_float(row.get("contribution_pct")) or 0.0,
                }
                for row in rows
                if (_finite_float(row.get("contribution_pct")) or 0.0) > 0.0
            ),
            key=lambda row: row["contribution_pct"],
            reverse=True,
        )[:5],
    }


def _split_report(
    split: str,
    block: Mapping[str, Any],
    *,
    source: str,
    bootstrap_samples: int,
    confidence_level: float,
    seed: int,
) -> dict[str, Any]:
    rows = _contribution_rows(block)
    values = [_finite_float(row.get("contribution_pct")) or 0.0 for row in rows]
    positives = [value for value in values if value > 0.0]
    negatives = [value for value in values if value < 0.0]
    zeros = [value for value in values if value == 0.0]
    return {
        "split": split,
        "source": source,
        "delta_summary": block.get("delta_summary") if isinstance(block.get("delta_summary"), Mapping) else {},
        "contribution_summary": {
            "contribution_count": len(values),
            "positive_count": len(positives),
            "negative_count": len(negatives),
            "zero_count": len(zeros),
            "observed_delta_pct": float(sum(values)),
            "positive_sum_pct": float(sum(positives)),
            "negative_sum_pct": float(sum(negatives)),
            "largest_positive_pct": float(max(positives)) if positives else 0.0,
            "largest_negative_pct": float(min(negatives)) if negatives else 0.0,
        },
        "bootstrap_total_delta_pct": _bootstrap_total_delta(
            values,
            bootstrap_samples=int(bootstrap_samples),
            confidence_level=float(confidence_level),
            seed=int(seed),
        ),
        "top_winner_dependency": _top_winner_dependency(rows),
        "contribution_sample": sorted(rows, key=lambda row: row["contribution_pct"])[:5]
        + sorted(rows, key=lambda row: row["contribution_pct"], reverse=True)[:5],
    }


def _candidate_node(report: Mapping[str, Any], split: str) -> Mapping[str, Any]:
    if split == "validation":
        for key in ("best_validation_candidate", "best_validation_accepted_candidate", "selected_candidate"):
            value = report.get(key)
            if isinstance(value, Mapping):
                return value
    if split == "final":
        value = report.get("final_confirmation")
        if isinstance(value, Mapping):
            return value
    return {}


def _node_summary(node: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("summary", "candidate_summary", "selected_candidate_summary", "evaluation"):
        value = node.get(key)
        if isinstance(value, Mapping) and value:
            return value
    candidate = node.get("candidate")
    if isinstance(candidate, Mapping):
        for key in ("summary", "evaluation"):
            value = candidate.get(key)
            if isinstance(value, Mapping) and value:
                return value
    return {}


def _gate_context(report: Mapping[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {"available": False, "reason": "no_replay_report"}
    contract = report.get("probe_contract")
    if (
        isinstance(contract, Mapping)
        and bool(contract.get("requires_replay_before_live_change"))
        and not isinstance(report.get("acceptance_gate"), Mapping)
    ):
        return {"available": False, "reason": "proxy_report_requires_replay_before_live_change"}
    context: dict[str, Any] = {"available": True}
    for split in SPLITS:
        node = _candidate_node(report, split)
        details = node.get("gate_details") if isinstance(node.get("gate_details"), Mapping) else {}
        false_reasons = [str(key) for key, value in sorted(details.items()) if value is False]
        context[split] = {
            "passes_acceptance_gate": bool(node.get("passes_acceptance_gate")) if "passes_acceptance_gate" in node else None,
            "false_gate_reasons": false_reasons,
            "summary": _node_summary(node),
        }
    return context


def _classify(
    validation: Mapping[str, Any] | None,
    final: Mapping[str, Any] | None,
    *,
    gate_context: Mapping[str, Any],
    min_research_positive_probability: float,
    min_shadow_positive_probability: float,
    min_split_contributions: int,
) -> tuple[str, str, list[str], list[str]]:
    rejection_reasons: list[str] = []
    shadow_blockers: list[str] = []
    for split, block in (("validation", validation), ("final", final)):
        if block is None:
            rejection_reasons.append(f"{split}_trade_delta_missing")
            continue
        contribution_count = int(block.get("contribution_summary", {}).get("contribution_count") or 0)
        observed = _finite_float(block.get("contribution_summary", {}).get("observed_delta_pct")) or 0.0
        positive_probability = _finite_float(
            block.get("bootstrap_total_delta_pct", {}).get("positive_probability")
        ) or 0.0
        if contribution_count < int(min_split_contributions):
            shadow_blockers.append(f"{split}_contribution_count_below_shadow_min")
        if observed <= 0.0:
            rejection_reasons.append(f"{split}_observed_delta_non_positive")
        if positive_probability < float(min_research_positive_probability):
            rejection_reasons.append(f"{split}_positive_probability_below_research_min")
        if positive_probability < float(min_shadow_positive_probability):
            shadow_blockers.append(f"{split}_positive_probability_below_shadow_min")
        dependency = block.get("top_winner_dependency") if isinstance(block.get("top_winner_dependency"), Mapping) else {}
        if dependency.get("top1_dependency"):
            shadow_blockers.append(f"{split}_top1_winner_dependent")
        if dependency.get("top3_dependency"):
            shadow_blockers.append(f"{split}_top3_winner_dependent")

    if rejection_reasons:
        return "Rejected", "uncertainty_gate_rejected", rejection_reasons, shadow_blockers

    if not gate_context.get("available"):
        shadow_blockers.append("strict_replay_gate_context_missing")
    for split in SPLITS:
        split_gate = gate_context.get(split) if isinstance(gate_context.get(split), Mapping) else {}
        if split_gate.get("passes_acceptance_gate") is False:
            shadow_blockers.append(f"{split}_strict_acceptance_gate_failed")
        for reason in split_gate.get("false_gate_reasons") or []:
            shadow_blockers.append(f"{split}_gate_{reason}_false")

    if shadow_blockers:
        return "Research Alpha", "uncertain_research_alpha_not_shadow", [], shadow_blockers

    return "Shadow Candidate", "paired_delta_uncertainty_shadow_candidate", [], []


def build_replay_uncertainty_gate_report(
    *,
    replay_report: Mapping[str, Any] | None = None,
    validation_trade_delta: Mapping[str, Any] | None = None,
    final_trade_delta: Mapping[str, Any] | None = None,
    source_report_name: str | None = None,
    candidate_id: str = "unnamed_candidate",
    bootstrap_samples: int = 4000,
    confidence_level: float = 0.95,
    seed: int = 7,
    min_research_positive_probability: float = 0.55,
    min_shadow_positive_probability: float = 0.80,
    min_split_contributions: int = 10,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be positive")
    if not 0.0 < float(confidence_level) < 1.0:
        raise ValueError("confidence_level must be between 0 and 1")
    if not 0.0 <= float(min_research_positive_probability) <= 1.0:
        raise ValueError("min_research_positive_probability must be in [0, 1]")
    if not 0.0 <= float(min_shadow_positive_probability) <= 1.0:
        raise ValueError("min_shadow_positive_probability must be in [0, 1]")
    if min_split_contributions < 0:
        raise ValueError("min_split_contributions must be non-negative")

    split_blocks, split_sources = extract_trade_delta_splits(
        replay_report=replay_report,
        validation_trade_delta=validation_trade_delta,
        final_trade_delta=final_trade_delta,
    )
    validation = (
        _split_report(
            "validation",
            split_blocks["validation"],
            source=split_sources["validation"],
            bootstrap_samples=int(bootstrap_samples),
            confidence_level=float(confidence_level),
            seed=int(seed),
        )
        if "validation" in split_blocks
        else None
    )
    final = (
        _split_report(
            "final",
            split_blocks["final"],
            source=split_sources["final"],
            bootstrap_samples=int(bootstrap_samples),
            confidence_level=float(confidence_level),
            seed=int(seed) + 1,
        )
        if "final" in split_blocks
        else None
    )
    gates = _gate_context(replay_report)
    tier, decision, rejection_reasons, shadow_blockers = _classify(
        validation,
        final,
        gate_context=gates,
        min_research_positive_probability=float(min_research_positive_probability),
        min_shadow_positive_probability=float(min_shadow_positive_probability),
        min_split_contributions=int(min_split_contributions),
    )

    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "candidate_id": str(candidate_id),
        "outcome_tier": tier,
        "decision": decision,
        "rejection_reasons": rejection_reasons,
        "shadow_blockers": shadow_blockers,
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "max_outcome_tier": "Shadow Candidate",
            "requires_live_switch_gate_before_runtime_change": True,
        },
        "evidence_scope": {
            "intended_use": "uncertainty_aware_replay_gate_for_small_splits",
            "paired_delta_bootstrap": True,
            "top_winner_dependency_check": True,
            "does_not_change_model_or_runtime": True,
        },
        "parameters": {
            "bootstrap_samples": int(bootstrap_samples),
            "confidence_level": float(confidence_level),
            "seed": int(seed),
            "min_research_positive_probability": float(min_research_positive_probability),
            "min_shadow_positive_probability": float(min_shadow_positive_probability),
            "min_split_contributions": int(min_split_contributions),
        },
        "source_report": {
            "path": source_report_name,
            "decision": replay_report.get("decision") if isinstance(replay_report, Mapping) else None,
            "selected_candidate_index": replay_report.get("selected_candidate", {}).get("candidate_index")
            if isinstance(replay_report, Mapping) and isinstance(replay_report.get("selected_candidate"), Mapping)
            else None,
        },
        "gate_context": gates,
        "validation": validation,
        "final": final,
    }
