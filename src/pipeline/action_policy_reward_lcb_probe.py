from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


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


def _selected_reward_rows(block: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = block.get("selected_rewards")
    if isinstance(rows, list) and rows:
        return [row for row in rows if isinstance(row, Mapping)]
    sample = block.get("selected_sample")
    if isinstance(sample, list) and sample:
        return [row for row in sample if isinstance(row, Mapping)]
    return []


def _family_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("source_family") or "") for row in rows)
    return dict(sorted(counts.items()))


def _reward_statistics(
    rows: Sequence[Mapping[str, Any]],
    *,
    bootstrap_samples: int,
    confidence_level: float,
    seed: int,
) -> dict[str, Any]:
    known_rewards = [
        _finite_float(row.get("replay_reward_pct"))
        for row in rows
        if row.get("replay_reward_known", True)
    ]
    known_rewards = [reward for reward in known_rewards if reward is not None]
    selected_count = len(rows)
    known_count = len(known_rewards)
    total_reward = float(sum(known_rewards))
    average_reward = total_reward / known_count if known_count else 0.0

    if known_count:
        rng = np.random.default_rng(seed)
        samples = rng.integers(0, known_count, size=(bootstrap_samples, known_count))
        boot_means = np.asarray([float(np.mean([known_rewards[index] for index in sample])) for sample in samples])
        lower = float(np.quantile(boot_means, max(0.0, 1.0 - confidence_level)))
        upper = float(np.quantile(boot_means, min(1.0, confidence_level)))
        mean = float(np.mean(boot_means))
    else:
        lower = 0.0
        upper = 0.0
        mean = 0.0

    return {
        "selected_count": selected_count,
        "selected_reward_known_count": known_count,
        "selected_family_counts": _family_counts(rows),
        "selected_reward_pct": total_reward,
        "selected_average_reward_pct": average_reward,
        "reward_lcb_pct": lower,
        "reward_lcb_average_reward_pct": lower,
        "reward_ci_average_reward_pct": {
            "confidence_level": float(confidence_level),
            "lower": lower,
            "upper": upper,
            "mean": mean,
        },
        "selected_rewards": [
            {
                "symbol": row.get("symbol") or row.get("token"),
                "source_family": row.get("source_family"),
                "source_group": row.get("source_group"),
                "evidence_class": row.get("evidence_class") or row.get("barrier_class") or row.get("classification"),
                "recommended_policy": row.get("recommended_policy"),
                "replay_reward_policy": row.get("replay_reward_policy"),
                "replay_reward_pct": row.get("replay_reward_pct"),
                "replay_reward_known": row.get("replay_reward_known", True),
                "meta_probability": _finite_float(row.get("meta_probability")),
            }
            for row in rows
        ],
    }


def _support_reasons(block: Mapping[str, Any], *, min_selected_per_family: int, prefix: str) -> list[str]:
    selected_counts = block.get("selected_family_counts") if isinstance(block, Mapping) else {}
    if not isinstance(selected_counts, Mapping):
        selected_counts = {}
    reasons = []
    for family in ("accepted", "rejected"):
        if int(selected_counts.get(family) or 0) < int(min_selected_per_family):
            reasons.append(f"{prefix}_{family}_selection_below_min")
    return reasons


def build_action_policy_reward_lcb_report(
    reward_report: Mapping[str, Any],
    *,
    bootstrap_samples: int = 2000,
    confidence_level: float = 0.95,
    min_selected_per_family: int = 1,
    seed: int = 7,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be positive")
    if not 0.0 < float(confidence_level) < 1.0:
        raise ValueError("confidence_level must be between 0 and 1")

    validation_rows = _selected_reward_rows(reward_report.get("validation") or {})
    final_rows = _selected_reward_rows(reward_report.get("final") or {})

    validation_block = _reward_statistics(
        validation_rows,
        bootstrap_samples=int(bootstrap_samples),
        confidence_level=float(confidence_level),
        seed=int(seed),
    )
    final_block = _reward_statistics(
        final_rows,
        bootstrap_samples=int(bootstrap_samples),
        confidence_level=float(confidence_level),
        seed=int(seed) + 1,
    )

    report: dict[str, Any] = {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "decision": "diagnostic_only_not_evaluated",
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "causal_policy": False,
        },
        "evidence_scope": {
            "intended_use": "bootstrap_lcb_shadow_reward_probe",
            "warning": "support-limited reward probe, not a deployable policy",
        },
        "parameters": {
            "bootstrap_samples": int(bootstrap_samples),
            "confidence_level": float(confidence_level),
            "min_selected_per_family": int(min_selected_per_family),
            "seed": int(seed),
        },
        "source_report": {
            "decision": reward_report.get("decision"),
            "validation_selected_count": reward_report.get("validation", {}).get("selected_count"),
            "final_selected_count": reward_report.get("final", {}).get("selected_count"),
        },
        "validation": validation_block,
        "final": final_block,
        "support_gate": {"passes": False, "reasons": []},
        "stability_gate": {"passes": False, "reasons": []},
    }

    support_reasons = _support_reasons(
        validation_block,
        min_selected_per_family=min_selected_per_family,
        prefix="validation",
    )
    support_reasons += _support_reasons(
        final_block,
        min_selected_per_family=min_selected_per_family,
        prefix="final",
    )
    if support_reasons:
        report["decision"] = "shadow_only_support_limited"
        report["support_gate"] = {"passes": False, "reasons": support_reasons}
        report["stability_gate"] = {"passes": False, "reasons": ["support_gate_failed"]}
        return report

    stability_reasons = []
    validation_lcb = _finite_float(validation_block.get("reward_lcb_average_reward_pct")) or 0.0
    final_lcb = _finite_float(final_block.get("reward_lcb_average_reward_pct")) or 0.0
    if validation_lcb <= 0.0:
        stability_reasons.append("validation_reward_lcb_non_positive")
    if final_lcb <= 0.0:
        stability_reasons.append("final_reward_lcb_non_positive")

    if stability_reasons:
        report["decision"] = "shadow_reward_non_positive_rejected"
        report["stability_gate"] = {"passes": False, "reasons": stability_reasons}
        report["support_gate"] = {"passes": True, "reasons": []}
        return report

    report["decision"] = "shadow_reward_positive_lcb_replay_required"
    report["support_gate"] = {"passes": True, "reasons": []}
    report["stability_gate"] = {"passes": True, "reasons": []}
    return report
