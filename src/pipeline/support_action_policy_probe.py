from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


POSITIVE_POLICIES = {"quick_take_profit", "conditional_slow_hold"}
HARD_ABSTAIN_RULE = {"field": "prob", "op": "<", "value": 0.94}
HARD_ABSTAIN_THRESHOLD_EPSILON = 1e-8
TARGET_FLOW_RULE_NAME = "high_prob_low_toxic_overlap"
REQUIRED_FLOW_RULE_FIELDS = (
    "flow_event_count_30s",
    "flow_buy_sell_overlap_ratio_60s",
    "flow_recent_seller_reentry_ratio_30s",
)

DECISION_TIME_FIELDS = {
    "prob",
    "pred_return",
    "volume_30s",
    "entry_volume_30s",
    "price_volatility",
    "entry_price_volatility",
    "token_age_seconds",
    "age_seconds",
    "feature_count",
    "features_hash",
    "entry_ranking_mode",
    "near_threshold_rescue_used",
    "use_pred_return_filter",
    "min_pred_return",
    "min_entry_volume_30s",
    "min_entry_price_volatility",
    "buy_near_threshold_min_prob",
    "buy_near_min_pred_return",
    "buy_near_min_entry_volume_30s",
    "buy_near_min_entry_price_volatility",
    "buy_near_min_age_seconds",
    "flow_metrics_available",
    "flow_buy_volume_10s",
    "flow_sell_volume_10s",
    "flow_total_volume_10s",
    "flow_event_count_10s",
    "flow_sell_pressure_10s",
    "flow_buy_sell_ratio_10s",
    "flow_signed_imbalance_10s",
    "flow_buy_volume_30s",
    "flow_sell_volume_30s",
    "flow_total_volume_30s",
    "flow_event_count_30s",
    "flow_sell_pressure_30s",
    "flow_buy_sell_ratio_30s",
    "flow_signed_imbalance_30s",
    "flow_buy_volume_60s",
    "flow_sell_volume_60s",
    "flow_total_volume_60s",
    "flow_event_count_60s",
    "flow_sell_pressure_60s",
    "flow_buy_sell_ratio_60s",
    "flow_signed_imbalance_60s",
    "flow_buy_sell_overlap_ratio_60s",
    "flow_recent_seller_reentry_ratio_30s",
    "flow_buyer_set_churn_10s_vs_prev50s",
    "runner_retention_train_boundary_match",
    "runner_retention_train_boundary_condition_fraction",
}

OPERATORS = {">=", ">", "<=", "<", "==", "!="}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any

    def __post_init__(self) -> None:
        if self.field not in DECISION_TIME_FIELDS:
            raise ValueError(f"{self.field} is not decision-time")
        if self.op not in OPERATORS:
            raise ValueError(f"unsupported operator {self.op}")


@dataclass(frozen=True)
class Rule:
    name: str
    conditions: tuple[Condition, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("rule name is required")
        _validate_conditions(self.conditions)


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _validate_conditions(conditions: Any) -> None:
    if type(conditions) is not tuple or not conditions:
        raise ValueError("conditions must be a non-empty tuple")
    for condition in conditions:
        _validate_condition(condition)


def _validate_condition(condition: Any) -> None:
    if type(condition) is not Condition:
        raise ValueError("conditions must be exact Condition instances")
    if condition.field not in DECISION_TIME_FIELDS:
        raise ValueError(f"{condition.field} is not decision-time")
    if condition.op not in OPERATORS:
        raise ValueError(f"unsupported operator {condition.op}")


def _validate_rule(rule: Any) -> None:
    if type(rule) is not Rule:
        raise ValueError("rules must be Rule instances")
    _validate_conditions(rule.conditions)


def _validated_rules(rules: Iterable[Rule] | None) -> list[Rule]:
    if rules is None:
        return default_rules()
    if type(rules) not in {list, tuple}:
        raise ValueError("rules must be a list or tuple")
    validated = list(rules)
    for rule in validated:
        _validate_rule(rule)
    return validated


def _condition_matches(condition: Condition, row: Mapping[str, Any]) -> bool:
    _validate_condition(condition)
    if condition.field not in row:
        return False

    left = row.get(condition.field)
    if condition.op in {">=", ">", "<=", "<"}:
        parsed_left = _finite_float(left)
        parsed_right = _finite_float(condition.value)
        if parsed_left is None or parsed_right is None:
            return False
        if condition.op == ">=":
            return parsed_left >= parsed_right
        if condition.op == ">":
            return parsed_left > parsed_right
        if condition.op == "<=":
            return parsed_left <= parsed_right
        return parsed_left < parsed_right

    if condition.op == "==":
        return left == condition.value
    return left != condition.value


def _candidate_rows(report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = report.get("candidates") or report.get("candidate_sample") or []
    return [row for row in rows if isinstance(row, Mapping)]


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


def evaluate_rule(rule: Rule, candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    _validate_rule(rule)
    selected = [
        row
        for row in candidates
        if all(_condition_matches(condition, row) for condition in rule.conditions)
    ]
    positives = [row for row in selected if row.get("recommended_policy") in POSITIVE_POLICIES]
    negatives = [row for row in selected if row.get("recommended_policy") not in POSITIVE_POLICIES]
    selected_count = len(selected)
    positive_count = len(positives)

    return {
        "rule": rule.name,
        "conditions": [
            {"field": condition.field, "op": condition.op, "value": condition.value}
            for condition in rule.conditions
        ],
        "selected_count": selected_count,
        "positive_count": positive_count,
        "negative_count": len(negatives),
        "precision": positive_count / selected_count if selected_count else 0.0,
        "selected_symbols": [str(row.get("symbol") or row.get("token")) for row in selected[:25]],
        "positive_symbols": [str(row.get("symbol") or row.get("token")) for row in positives[:25]],
        "negative_symbols": [str(row.get("symbol") or row.get("token")) for row in negatives[:25]],
    }


def _eligible_rule_result(row: Mapping[str, Any], min_selected: int) -> bool:
    return (
        not _is_hard_abstain_result(row)
        and int(row.get("selected_count") or 0) >= min_selected
        and int(row.get("positive_count") or 0) > 0
    )


def _is_hard_abstain_result(row: Mapping[str, Any]) -> bool:
    conditions = row.get("conditions") or []
    if row.get("rule") == "low_prob_hard_abstain":
        return True
    if not isinstance(conditions, list):
        return False
    hard_threshold = _finite_float(HARD_ABSTAIN_RULE["value"])
    if hard_threshold is None:
        return False
    for condition in conditions:
        if not isinstance(condition, Mapping):
            continue
        condition_value = _finite_float(condition.get("value"))
        if (
            condition.get("field") == HARD_ABSTAIN_RULE["field"]
            and condition.get("op") in {"<", "<="}
            and condition_value is not None
            and condition_value <= hard_threshold + HARD_ABSTAIN_THRESHOLD_EPSILON
        ):
            return True
    return False


def default_rules() -> list[Rule]:
    return [
        Rule(
            "low_prob_hard_abstain",
            (Condition("prob", "<", 0.94),),
        ),
        Rule(
            "high_prob_positive_pred",
            (Condition("prob", ">=", 0.985), Condition("pred_return", ">=", 5.0)),
        ),
        Rule(
            "v95_like_pred_rescue",
            (Condition("prob", ">=", 0.985), Condition("pred_return", ">=", 30.0)),
        ),
        Rule(
            "high_prob_volume_volatility",
            (
                Condition("prob", ">=", 0.985),
                Condition("entry_volume_30s", ">=", 1.25),
                Condition("entry_price_volatility", ">=", 0.08),
            ),
        ),
        Rule(
            "young_high_prob_positive_pred",
            (
                Condition("prob", ">=", 0.985),
                Condition("pred_return", ">=", 5.0),
                Condition("age_seconds", "<=", 60.0),
            ),
        ),
        Rule(
            "young_high_prob_clean_flow",
            (
                Condition("prob", ">=", 0.985),
                Condition("pred_return", ">=", 5.0),
                Condition("age_seconds", "<=", 60.0),
                Condition("flow_event_count_30s", ">=", 2),
                Condition("flow_sell_pressure_10s", "<=", 0.35),
                Condition("flow_signed_imbalance_30s", ">=", 0.0),
            ),
        ),
        Rule(
            "high_prob_low_toxic_overlap",
            (
                Condition("prob", ">=", 0.985),
                Condition("flow_event_count_30s", ">=", 2),
                Condition("flow_buy_sell_overlap_ratio_60s", "<=", 0.5),
                Condition("flow_recent_seller_reentry_ratio_30s", "<=", 0.5),
            ),
        ),
    ]


def _source_tagged_candidate_rows(report: Mapping[str, Any], source_name: str) -> list[Mapping[str, Any]]:
    rows = []
    for row in _candidate_rows(report):
        tagged = dict(row)
        tagged["source_report"] = str(source_name)
        rows.append(tagged)
    return rows


def _reported_candidate_count(report: Mapping[str, Any], fallback: int) -> int:
    candidate_counts = report.get("candidate_counts") or {}
    if not isinstance(candidate_counts, Mapping):
        candidate_counts = {}
    try:
        return int(candidate_counts.get("per_token_candidates", fallback) or fallback)
    except (TypeError, ValueError):
        return int(fallback)


def _flow_feature_presence(candidates: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(candidates)
    required = {}
    for field in REQUIRED_FLOW_RULE_FIELDS:
        present = sum(1 for row in rows if field in row)
        non_null = sum(1 for row in rows if row.get(field) is not None)
        finite = sum(1 for row in rows if _finite_float(row.get(field)) is not None)
        required[field] = {
            "present_count": present,
            "non_null_count": non_null,
            "finite_count": finite,
        }
    complete = bool(rows) and all(value["finite_count"] == len(rows) for value in required.values())
    return {
        "required_fields": required,
        "required_fields_complete": complete,
        "candidate_count": len(rows),
    }


def build_pooled_support_report(
    *,
    time_to_barrier_reports: Iterable[Mapping[str, Any]],
    source_names: Iterable[str] | None = None,
    rules: Iterable[Rule] | None = None,
    min_selected: int = 3,
    min_pooled_selected: int = 30,
    min_pooled_positive: int = 12,
    target_rule_name: str = TARGET_FLOW_RULE_NAME,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    reports = list(time_to_barrier_reports)
    names = list(source_names or [f"report_{index}" for index in range(len(reports))])
    if len(reports) != len(names):
        raise ValueError("source_names length must match time_to_barrier_reports")
    if not reports:
        raise ValueError("at least one time-to-barrier report is required")

    candidates: list[Mapping[str, Any]] = []
    reported_candidates = 0
    for report, source_name in zip(reports, names):
        source_rows = _source_tagged_candidate_rows(report, source_name)
        candidates.extend(source_rows)
        reported_candidates += _reported_candidate_count(report, len(source_rows))

    evaluated = [evaluate_rule(rule, candidates) for rule in _validated_rules(rules)]
    evaluated.sort(
        key=lambda row: (row["precision"], row["positive_count"], -row["negative_count"], row["rule"]),
        reverse=True,
    )
    target = next((row for row in evaluated if row["rule"] == target_rule_name), None)
    selected_count = int((target or {}).get("selected_count") or 0)
    positive_count = int((target or {}).get("positive_count") or 0)
    flow_presence = _flow_feature_presence(candidates)
    evidence_passes = (
        target is not None
        and flow_presence["required_fields_complete"]
        and selected_count >= int(min_pooled_selected)
        and positive_count >= int(min_pooled_positive)
    )
    if not flow_presence["required_fields_complete"]:
        decision = "missing_flow_feature_parity"
    elif evidence_passes:
        decision = "expanded_evidence_pass"
    else:
        decision = "diagnostic_only_small_sample"

    return {
        "generated_at": (
            generated_at
            or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None)
        ).isoformat(sep=" "),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "expanded_support_gate_for_replay_experiment",
        },
        "parameters": {
            "min_selected": min_selected,
            "min_pooled_selected": min_pooled_selected,
            "min_pooled_positive": min_pooled_positive,
            "target_rule": target_rule_name,
        },
        "candidate_counts": {
            "input_reports": len(reports),
            "input_candidates": len(candidates),
            "input_reported_candidates": reported_candidates,
            "sample_limited": reported_candidates > len(candidates),
            "unscored_reported_candidates": max(0, reported_candidates - len(candidates)),
            "positive_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") in POSITIVE_POLICIES
            ),
            "negative_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") not in POSITIVE_POLICIES
            ),
        },
        "flow_feature_presence": flow_presence,
        "rule_results": evaluated,
        "eligible_rule_results": [
            row for row in evaluated if _eligible_rule_result(row, min_selected)
        ],
        "evidence_gate": {
            "target_rule": target_rule_name,
            "selected_count": selected_count,
            "positive_count": positive_count,
            "min_selected": int(min_pooled_selected),
            "min_positive": int(min_pooled_positive),
            "passes": bool(evidence_passes),
        },
        "decision": decision,
    }


def build_support_report(
    *,
    time_to_barrier_report: Mapping[str, Any],
    rules: Iterable[Rule] | None = None,
    min_selected: int = 3,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    candidates = _candidate_rows(time_to_barrier_report)
    evaluated = [evaluate_rule(rule, candidates) for rule in _validated_rules(rules)]
    evaluated.sort(
        key=lambda row: (row["precision"], row["positive_count"], -row["negative_count"], row["rule"]),
        reverse=True,
    )

    candidate_counts = time_to_barrier_report.get("candidate_counts") or {}
    if not isinstance(candidate_counts, Mapping):
        candidate_counts = {}
    input_reported_candidates = candidate_counts.get("per_token_candidates", len(candidates))
    try:
        input_reported_candidates = int(input_reported_candidates)
    except (TypeError, ValueError):
        input_reported_candidates = len(candidates)
    unscored_reported_candidates = max(0, input_reported_candidates - len(candidates))

    return {
        "generated_at": (
            generated_at
            or dt.datetime.now(dt.timezone.utc).astimezone().replace(tzinfo=None)
        ).isoformat(sep=" "),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "requires_replay_before_live_change": True,
            "safe_for_live_switch": False,
            "causal_policy": False,
        },
        "evidence_scope": {
            "labels_use_ex_post_outcomes": True,
            "features_must_be_decision_time": True,
            "intended_use": "support_report_for_replay_experiment_design",
        },
        "parameters": {"min_selected": min_selected},
        "candidate_counts": {
            "input_candidates": len(candidates),
            "input_reported_candidates": input_reported_candidates,
            "sample_limited": unscored_reported_candidates > 0,
            "unscored_reported_candidates": unscored_reported_candidates,
            "positive_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") in POSITIVE_POLICIES
            ),
            "negative_candidates": sum(
                1 for row in candidates if row.get("recommended_policy") not in POSITIVE_POLICIES
            ),
        },
        "rule_results": evaluated,
        "eligible_rule_results": [
            row for row in evaluated if _eligible_rule_result(row, min_selected)
        ],
        "decision": "probe_only_replay_required",
    }
