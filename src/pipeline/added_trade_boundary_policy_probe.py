from __future__ import annotations

import datetime as dt
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _trade(row: Mapping[str, Any]) -> Mapping[str, Any]:
    trade = row.get("trade")
    return trade if isinstance(trade, Mapping) else {}


def _return_pct(row: Mapping[str, Any]) -> float:
    trade = _trade(row)
    return _finite_float(trade.get("return_pct") if "return_pct" in trade else trade.get("net_return_pct")) or 0.0


def _features(row: Mapping[str, Any]) -> Mapping[str, Any]:
    features = row.get("features")
    return features if isinstance(features, Mapping) else {}


def _feature_value(row: Mapping[str, Any], feature: str) -> float | None:
    return _finite_float(_features(row).get(feature))


def _feature_names(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    names = set()
    for row in rows:
        for name, value in _features(row).items():
            if _finite_float(value) is not None:
                names.add(str(name))
    return sorted(names)


def _rule_matches(row: Mapping[str, Any], rule: Mapping[str, Any] | None) -> bool:
    if rule is None:
        return True
    feature = str(rule.get("feature") or "")
    operator = str(rule.get("operator") or "")
    threshold = _finite_float(rule.get("threshold"))
    value = _feature_value(row, feature)
    if value is None or threshold is None:
        return False
    if operator == "<=":
        return value <= threshold
    if operator == ">=":
        return value >= threshold
    return False


def _summary(rows: Sequence[Mapping[str, Any]], *, loss_cost: float) -> dict[str, Any]:
    returns = [_return_pct(row) for row in rows]
    positive = [value for value in returns if value > 0.0]
    negative = [value for value in returns if value <= 0.0]
    utility = sum(value if value > 0.0 else loss_cost * value for value in returns)
    return {
        "trade_count": len(rows),
        "win_count": len(positive),
        "loss_count": len(negative),
        "win_rate": len(positive) / len(rows) if rows else 0.0,
        "return_pct_sum": float(sum(returns)),
        "return_pct_mean": float(sum(returns) / len(returns)) if returns else 0.0,
        "positive_return_pct_sum": float(sum(positive)),
        "negative_return_pct_sum": float(sum(negative)),
        "cost_adjusted_utility": float(utility),
    }


def _evaluate_rule(
    rows: Sequence[Mapping[str, Any]],
    rule: Mapping[str, Any] | None,
    *,
    loss_cost: float,
) -> dict[str, Any]:
    kept = [row for row in rows if _rule_matches(row, rule)]
    rejected = [row for row in rows if not _rule_matches(row, rule)]
    all_summary = _summary(rows, loss_cost=loss_cost)
    kept_summary = _summary(kept, loss_cost=loss_cost)
    rejected_summary = _summary(rejected, loss_cost=loss_cost)
    return {
        "all": all_summary,
        "kept": kept_summary,
        "rejected": rejected_summary,
        "cost_adjusted_utility_delta": float(
            kept_summary["cost_adjusted_utility"] - all_summary["cost_adjusted_utility"]
        ),
    }


def _thresholds(values: Sequence[float]) -> list[float]:
    unique = sorted(set(values))
    if len(unique) <= 1:
        return unique
    thresholds = list(unique)
    thresholds.extend((left + right) / 2.0 for left, right in zip(unique, unique[1:]))
    return sorted(set(thresholds))


def _candidate_rules(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for feature in _feature_names(rows):
        values = [_feature_value(row, feature) for row in rows]
        finite_values = [value for value in values if value is not None]
        for threshold in _thresholds(finite_values):
            for operator in ("<=", ">="):
                candidates.append(
                    {
                        "feature": feature,
                        "operator": operator,
                        "threshold": float(threshold),
                    }
                )
    return candidates


def _select_rule(
    validation_rows: Sequence[Mapping[str, Any]],
    *,
    loss_cost: float,
    min_keep_count: int,
    min_reject_count: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int]:
    evaluated = []
    for rule in _candidate_rules(validation_rows):
        result = _evaluate_rule(validation_rows, rule, loss_cost=loss_cost)
        keep_count = int(result["kept"]["trade_count"])
        reject_count = int(result["rejected"]["trade_count"])
        if keep_count < min_keep_count or reject_count < min_reject_count:
            continue
        if result["cost_adjusted_utility_delta"] <= 0.0:
            continue
        if int(result["kept"]["win_count"]) <= 0:
            continue
        evaluated.append(
            {
                "rule": rule,
                "validation": result,
            }
        )
    evaluated.sort(
        key=lambda item: (
            item["validation"]["cost_adjusted_utility_delta"],
            item["validation"]["kept"]["win_rate"],
            item["validation"]["kept"]["return_pct_sum"],
            -item["validation"]["kept"]["loss_count"],
        ),
        reverse=True,
    )
    return (evaluated[0]["rule"] if evaluated else None), evaluated[:25], len(evaluated)


def build_added_trade_boundary_policy_report(
    *,
    validation_rows: Sequence[Mapping[str, Any]],
    final_rows: Sequence[Mapping[str, Any]],
    loss_cost: float = 3.0,
    min_keep_count: int = 4,
    min_reject_count: int = 2,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    selected_rule, candidates, supported_candidate_count = _select_rule(
        validation_rows,
        loss_cost=float(loss_cost),
        min_keep_count=int(min_keep_count),
        min_reject_count=int(min_reject_count),
    )
    validation_eval = _evaluate_rule(validation_rows, selected_rule, loss_cost=float(loss_cost))
    final_eval = _evaluate_rule(final_rows, selected_rule, loss_cost=float(loss_cost))
    if selected_rule is None:
        decision = "reject_no_supported_rule"
    elif (
        final_eval["cost_adjusted_utility_delta"] > 0.0
        and final_eval["kept"]["loss_count"] < final_eval["all"]["loss_count"]
        and final_eval["kept"]["win_count"] > 0
    ):
        decision = "shadow_promote_to_replay"
    else:
        decision = "reject"
    return {
        "generated_at": (generated_at or dt.datetime.now(dt.timezone.utc)).isoformat(),
        "decision": decision,
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "uses_decision_time_features_only": True,
            "validation_selects_rule_before_final_evaluation": True,
        },
        "config": {
            "loss_cost": float(loss_cost),
            "min_keep_count": int(min_keep_count),
            "min_reject_count": int(min_reject_count),
            "rule_family": "single_feature_keep_rule",
        },
        "selected_rule": selected_rule,
        "validation": validation_eval,
        "final": final_eval,
        "candidate_rule_count": len(_candidate_rules(validation_rows)),
        "supported_candidate_count": supported_candidate_count,
        "top_supported_candidates": candidates,
        "falsification_rule": (
            "Reject unless the validation-selected rule improves final cost-adjusted added-trade "
            "utility versus keeping all added trades and reduces final added-trade loss count."
        ),
    }


def _added_rows_from_split(split_report: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    matched = split_report.get("matched_feature_rows")
    if isinstance(matched, Mapping):
        rows = matched.get("added_candidate_trades")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, Mapping)]
    return []


def build_report_from_trade_delta_payload(
    payload: Mapping[str, Any],
    *,
    loss_cost: float = 3.0,
    min_keep_count: int = 4,
    min_reject_count: int = 2,
) -> dict[str, Any]:
    attribution = payload.get("selected_trade_delta_attribution")
    if not isinstance(attribution, Mapping):
        raise ValueError("input report missing selected_trade_delta_attribution")
    validation = attribution.get("validation")
    final = attribution.get("final")
    if not isinstance(validation, Mapping) or not isinstance(final, Mapping):
        raise ValueError("input report missing validation/final trade-delta attribution")
    validation_rows = _added_rows_from_split(validation)
    final_rows = _added_rows_from_split(final)
    if not validation_rows:
        raise ValueError("input report has no validation matched added-trade feature rows")
    return build_added_trade_boundary_policy_report(
        validation_rows=validation_rows,
        final_rows=final_rows,
        loss_cost=loss_cost,
        min_keep_count=min_keep_count,
        min_reject_count=min_reject_count,
    )


def load_trade_delta_payload(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input report must be a JSON object")
    return payload


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
