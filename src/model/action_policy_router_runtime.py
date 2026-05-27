from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from src.pipeline import action_policy_replay_gate as replay_gate
from src.pipeline import action_policy_router_probe as router_probe
from src.pipeline import action_policy_reward_probe as reward_probe


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _load_report_objects(paths: Sequence[str | Path]) -> tuple[list[dict[str, Any]], list[str]]:
    reports: list[dict[str, Any]] = []
    names: list[str] = []
    for raw_path in paths or []:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"action policy router report not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, Mapping):
            reports.append(dict(payload))
            names.append(path.name)
        elif isinstance(payload, list):
            for index, item in enumerate(payload):
                if isinstance(item, Mapping):
                    reports.append(dict(item))
                    names.append(f"{path.name}#{index}")
        else:
            raise ValueError(f"unsupported action policy router report payload: {path}")
    return reports, names


@dataclass
class ActionPolicyRouterRuntime:
    enabled: bool
    models: dict[str, Any] = field(default_factory=dict)
    medians: dict[str, float] = field(default_factory=dict)
    feature_names: list[str] = field(default_factory=list)
    route_names: list[str] = field(default_factory=list)
    runtime_params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    min_confidence: float = 0.4
    min_live_features: int = 2

    @classmethod
    def from_report_paths(
        cls,
        *,
        train_rejected_report_paths: Sequence[str | Path],
        train_accepted_report_paths: Sequence[str | Path],
        runtime_params: Mapping[str, Any],
        min_confidence: float = 0.4,
        max_depth: int = 3,
        min_samples_leaf: int = 10,
        min_common_features: int = 2,
        min_live_features: int = 2,
    ) -> "ActionPolicyRouterRuntime":
        rejected_reports, rejected_source_names = _load_report_objects(train_rejected_report_paths)
        accepted_reports, accepted_source_names = _load_report_objects(train_accepted_report_paths)
        if not rejected_reports or not accepted_reports:
            raise ValueError("action policy router requires both rejected and accepted train reports")

        train_rejected, rejected_names = router_probe._normalize_rows(
            reports=rejected_reports,
            source_family="rejected",
            split="train",
            source_names=rejected_source_names,
            quick_take_profit_pct=25.0,
            stop_loss_pct=-18.0,
            post_target_window_seconds=60.0,
        )
        train_accepted, accepted_names = router_probe._normalize_rows(
            reports=accepted_reports,
            source_family="accepted",
            split="train",
            source_names=accepted_source_names,
            quick_take_profit_pct=25.0,
            stop_loss_pct=-18.0,
            post_target_window_seconds=60.0,
        )
        train_rows = train_rejected + train_accepted
        route_counts = router_probe._route_counts(train_rows)
        route_names = router_probe._route_names(train_rows)
        feature_names = reward_probe._feature_names(train_rows, train_rows)

        support_reasons: list[str] = []
        if len(route_counts) < 2:
            support_reasons.append("train_route_labels_below_two_classes")
        if sum(count for route, count in route_counts.items() if route != router_probe.SKIP_ROUTE) <= 0:
            support_reasons.append("train_positive_route_labels_missing")
        if len(feature_names) < int(min_common_features):
            support_reasons.append("common_decision_features_below_min")

        metadata: dict[str, Any] = {
            "trained": False,
            "route_names": route_names,
            "feature_names": feature_names,
            "route_counts": route_counts,
            "support_reasons": support_reasons,
            "source_groups": {
                "train_rejected": rejected_names,
                "train_accepted": accepted_names,
            },
            "intended_use": "action_policy_router_runtime_continue_hold_only",
            "live_switch_evidence": False,
        }
        if support_reasons:
            return cls(
                enabled=False,
                feature_names=feature_names,
                route_names=route_names,
                runtime_params=dict(runtime_params or {}),
                metadata=metadata,
                min_confidence=float(min_confidence),
                min_live_features=int(min_live_features),
            )

        models, medians, priors = router_probe._fit_route_models(
            train_rows,
            feature_names,
            route_names,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
        )
        by_route = router_probe._feature_importances_by_route(models, feature_names)
        metadata.update(
            {
                "trained": True,
                "route_priors": priors,
                "imputed_feature_medians": medians,
                "feature_importances": router_probe._aggregate_feature_importances(by_route),
                "feature_importances_by_route": by_route,
            }
        )
        return cls(
            enabled=True,
            models=models,
            medians=medians,
            feature_names=list(feature_names),
            route_names=list(route_names),
            runtime_params=dict(runtime_params or {}),
            metadata=metadata,
            min_confidence=float(min_confidence),
            min_live_features=int(min_live_features),
        )

    def predict(
        self,
        *,
        lifecycle: Mapping[str, Any],
        features: Mapping[str, Any],
        prob: float,
        pred_return: float | None,
        token_address: str | None = None,
        sample_time: float | None = None,
        create_timestamp: float | None = None,
    ) -> dict[str, Any]:
        if not self.enabled or not self.models or not self.route_names or not self.feature_names:
            return {
                "used": False,
                "route": "skip",
                "confidence": 0.0,
                "reason": "router_disabled",
                "live_feature_count": 0,
                "route_probabilities": {},
            }

        sample = {
            "features": dict(features or {}),
            "meta": {
                "token_address": token_address or lifecycle.get("token_address") or lifecycle.get("token") or "",
                "sample_time": int(sample_time if sample_time is not None else lifecycle.get("last_update") or 0),
                "create_timestamp": int(create_timestamp if create_timestamp is not None else lifecycle.get("create_timestamp") or 0),
            },
        }
        row = replay_gate._decision_row_from_sample(
            sample,
            buy_prob=float(prob),
            entry_score=float(pred_return if pred_return is not None else 0.0),
            runtime_params=self.runtime_params,
            original_index=0,
        )
        live_feature_count = sum(
            1
            for name in self.feature_names
            if _finite_float(row.get(name)) is not None
        )
        route_probabilities = {
            route: 0.0 for route in self.route_names
        }
        if live_feature_count < int(self.min_live_features):
            return {
                "used": False,
                "route": "skip",
                "confidence": 0.0,
                "reason": "live_feature_count_below_min",
                "live_feature_count": live_feature_count,
                "route_probabilities": route_probabilities,
            }

        probabilities = router_probe._predict_route_probabilities(
            self.models,
            self.medians,
            self.feature_names,
            self.route_names,
            [row],
        )
        probability_row = probabilities[0] if len(probabilities) else np.zeros(len(self.route_names), dtype=float)
        if len(probability_row):
            route_probabilities = {
                route: float(probability)
                for route, probability in zip(self.route_names, probability_row)
            }
            best_index = int(np.argmax(probability_row))
            route = self.route_names[best_index]
            confidence = float(probability_row[best_index])
        else:
            route = "skip"
            confidence = 0.0

        min_confidence = float(self.min_confidence)
        if route != "continue_hold":
            return {
                "used": False,
                "route": route,
                "confidence": confidence,
                "reason": "non_continue_hold_route",
                "live_feature_count": live_feature_count,
                "route_probabilities": route_probabilities,
            }
        if confidence < min_confidence:
            return {
                "used": False,
                "route": route,
                "confidence": confidence,
                "reason": "route_below_min_confidence",
                "live_feature_count": live_feature_count,
                "route_probabilities": route_probabilities,
            }
        return {
            "used": True,
            "route": route,
            "confidence": confidence,
            "reason": "continue_hold",
            "live_feature_count": live_feature_count,
            "route_probabilities": route_probabilities,
        }
