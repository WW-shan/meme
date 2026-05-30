from __future__ import annotations

import datetime as dt
import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from src.pipeline import reentry_probe


POLICY_NUMERIC_FIELDS = (
    "lifecycle_status_chain_lag_seconds",
    "lifecycle_status_staleness_seconds",
)
POLICY_CATEGORICAL_FIELDS = (
    "token_status_source",
)
POLICY_BOOLEAN_FIELDS = (
    "buy_fast_status_used",
)
DIAGNOSTIC_ONLY_FIELDS = (
    "signal_to_open_seconds",
    "entry_fill_lag_seconds",
    "entry_slippage_pct",
    "entry_submit_seconds",
    "buy_preflight_seconds",
    "buy_tx_submit_rpc_seconds",
)
MAX_THRESHOLD_VALUES = 40


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    rows: list[dict[str, Any]] = []
    with resolved.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def _json_default(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat(sep=" ")
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def to_json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
        default=_json_default,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _optional_time(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    try:
        parsed = reentry_probe.parse_time(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=reentry_probe.ANALYSIS_TZ)
    return parsed


def _sort_epoch(row: Mapping[str, Any]) -> float:
    for key in ("time", "entry_signal_time", "signal_time", "sell_started_at"):
        parsed = _optional_time(row.get(key))
        if parsed is not None:
            return float(parsed.timestamp())
    return 0.0


def _entry_signal_time(row: Mapping[str, Any]) -> dt.datetime | None:
    for key in ("entry_signal_time", "signal_time", "time"):
        parsed = _optional_time(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _in_window(row: Mapping[str, Any], *, since: str | None, until: str | None) -> bool:
    entry_time = _entry_signal_time(row)
    if entry_time is None:
        return False
    since_time = _optional_time(since)
    until_time = _optional_time(until)
    if since_time is not None and entry_time < since_time:
        return False
    if until_time is not None and entry_time > until_time:
        return False
    return True


def pair_real_trades(trade_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    open_by_token: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pairs: list[dict[str, Any]] = []
    real_rows = [dict(row) for row in trade_rows if row.get("is_real_trade")]
    for row in sorted(real_rows, key=_sort_epoch):
        action = str(row.get("action") or "").upper()
        token = reentry_probe.normalize_token(row.get("token") or row.get("token_address"))
        if not token:
            continue
        parsed = dict(row)
        parsed["token"] = token
        if action == "OPEN":
            open_by_token[token].append(parsed)
        elif action == "CLOSE":
            pending = open_by_token.get(token)
            if not pending:
                continue
            opened = pending.pop(0)
            pairs.append({
                "token": token,
                "symbol": parsed.get("symbol") or opened.get("symbol"),
                "open": opened,
                "close": parsed,
            })
    return pairs


def trade_outcome_rows(
    trade_rows: Iterable[Mapping[str, Any]],
    *,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for pair in pair_real_trades(trade_rows):
        opened = dict(pair.get("open") or {})
        close = dict(pair.get("close") or {})
        if not _in_window(opened, since=since, until=until):
            continue
        net_profit = _as_float(close.get("net_profit_bnb"))
        if net_profit is None:
            net_profit = _as_float(close.get("net_profit"))
        entry_time = _entry_signal_time(opened)
        if entry_time is None:
            continue
        token = reentry_probe.normalize_token(pair.get("token") or opened.get("token") or close.get("token"))
        if not token:
            continue
        outcome = {
            "token": token,
            "symbol": close.get("symbol") or opened.get("symbol") or pair.get("symbol"),
            "entry_signal_time": entry_time.isoformat(sep=" "),
            "open_time": opened.get("time"),
            "close_time": close.get("time"),
            "close_reason": close.get("reason"),
            "net_profit_bnb": float(net_profit or 0.0),
            "is_win": float(net_profit or 0.0) > 0.0,
            "prob": _as_float(opened.get("prob")),
            "pred_return": _as_float(opened.get("pred_return")),
            "primary_score_rescue_used": _as_bool(opened.get("primary_score_rescue_used")),
        }
        for field in POLICY_NUMERIC_FIELDS:
            outcome[field] = _as_float(opened.get(field))
        for field in POLICY_CATEGORICAL_FIELDS:
            value = opened.get(field)
            outcome[field] = str(value).strip().lower() if value is not None else None
        for field in POLICY_BOOLEAN_FIELDS:
            outcome[field] = _as_bool(opened.get(field))
        for field in DIAGNOSTIC_ONLY_FIELDS:
            outcome[field] = _as_float(opened.get(field))
        outcomes.append(outcome)
    outcomes.sort(key=lambda row: _optional_time(row.get("entry_signal_time")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc))
    return outcomes


def split_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> dict[str, list[dict[str, Any]]]:
    if not 0.0 < float(train_fraction) < 1.0:
        raise ValueError("train_fraction must be in (0, 1)")
    if not 0.0 < float(validation_fraction) < 1.0:
        raise ValueError("validation_fraction must be in (0, 1)")
    if float(train_fraction) + float(validation_fraction) >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be < 1")
    ordered = [dict(row) for row in rows]
    train_end = int(len(ordered) * float(train_fraction))
    validation_end = int(len(ordered) * (float(train_fraction) + float(validation_fraction)))
    return {
        "train": ordered[:train_end],
        "validation": ordered[train_end:validation_end],
        "final": ordered[validation_end:],
    }


def _quantile(sorted_values: Sequence[float], quantile: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = max(0.0, min(1.0, float(quantile))) * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(sorted_values[lower])
    fraction = position - lower
    return float(sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction)


def _numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    finite = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not finite:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None, "mean": None}
    return {
        "count": len(finite),
        "min": finite[0],
        "p25": _quantile(finite, 0.25),
        "median": _quantile(finite, 0.50),
        "p75": _quantile(finite, 0.75),
        "max": finite[-1],
        "mean": sum(finite) / len(finite),
    }


def _threshold_values(values: Sequence[float]) -> list[float]:
    unique = sorted({float(value) for value in values if math.isfinite(float(value))})
    if len(unique) <= MAX_THRESHOLD_VALUES:
        return unique
    indexes = {
        round(index * (len(unique) - 1) / (MAX_THRESHOLD_VALUES - 1))
        for index in range(MAX_THRESHOLD_VALUES)
    }
    return [unique[index] for index in sorted(indexes)]


def _rule_label(rule: Mapping[str, Any]) -> str:
    rule_type = str(rule.get("type") or "")
    if rule_type == "numeric_gte":
        return f"{rule.get('field')} >= {float(rule.get('threshold') or 0.0):g}"
    if rule_type == "categorical_eq":
        return f"{rule.get('field')} == {rule.get('value')}"
    if rule_type == "bool_eq":
        return f"{rule.get('field')} == {str(rule.get('value')).lower()}"
    if rule_type == "any_of":
        return " OR ".join(_rule_label(item) for item in rule.get("rules") or [])
    return rule_type or "unknown"


def _matches_rule(row: Mapping[str, Any], rule: Mapping[str, Any]) -> bool:
    rule_type = str(rule.get("type") or "")
    if rule_type == "numeric_gte":
        value = _as_float(row.get(str(rule.get("field") or "")))
        threshold = _as_float(rule.get("threshold"))
        return value is not None and threshold is not None and value >= threshold
    if rule_type == "categorical_eq":
        value = row.get(str(rule.get("field") or ""))
        return str(value).strip().lower() == str(rule.get("value") or "").strip().lower()
    if rule_type == "bool_eq":
        value = _as_bool(row.get(str(rule.get("field") or "")))
        expected = _as_bool(rule.get("value"))
        return value is not None and expected is not None and value is expected
    if rule_type == "any_of":
        rules = rule.get("rules")
        if not isinstance(rules, Sequence) or isinstance(rules, (str, bytes, bytearray)):
            return False
        return any(_matches_rule(row, item) for item in rules if isinstance(item, Mapping))
    raise ValueError(f"unsupported rule type: {rule_type}")


def _rule_identity(rule: Mapping[str, Any]) -> str:
    return json.dumps(_json_sanitize(rule), sort_keys=True, ensure_ascii=False)


def generate_rules(train_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(rule: dict[str, Any]) -> None:
        rule = dict(rule)
        rule["label"] = _rule_label(rule)
        identity = _rule_identity(rule)
        if identity not in seen:
            seen.add(identity)
            rules.append(rule)

    numeric_threshold_rules: list[dict[str, Any]] = []
    for field in POLICY_NUMERIC_FIELDS:
        values = [_as_float(row.get(field)) for row in train_rows]
        thresholds = _threshold_values([value for value in values if value is not None])
        for threshold in thresholds:
            rule = {"type": "numeric_gte", "field": field, "threshold": float(threshold)}
            add(rule)
            numeric_threshold_rules.append({**rule, "label": _rule_label(rule)})

    for field in POLICY_CATEGORICAL_FIELDS:
        values = {str(row.get(field)).strip().lower() for row in train_rows if row.get(field) is not None}
        if field == "token_status_source" and "helper" in values:
            add({"type": "categorical_eq", "field": field, "value": "helper"})

    for field in POLICY_BOOLEAN_FIELDS:
        values = {_as_bool(row.get(field)) for row in train_rows if _as_bool(row.get(field)) is not None}
        if field == "buy_fast_status_used" and False in values:
            add({"type": "bool_eq", "field": field, "value": False})

    helper_rule = {"type": "categorical_eq", "field": "token_status_source", "value": "helper"}
    fast_status_false_rule = {"type": "bool_eq", "field": "buy_fast_status_used", "value": False}
    for rule in numeric_threshold_rules:
        if rule.get("field") != "lifecycle_status_chain_lag_seconds":
            continue
        add({"type": "any_of", "rules": [rule, helper_rule]})
        add({"type": "any_of", "rules": [rule, fast_status_false_rule]})

    return rules


def _selected_samples(rows: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected = list(rows) if int(limit) == 0 else list(rows[: max(0, int(limit))])
    sample_fields = (
        "entry_signal_time",
        "symbol",
        "token",
        "net_profit_bnb",
        "close_reason",
        "prob",
        "pred_return",
        *POLICY_NUMERIC_FIELDS,
        *POLICY_CATEGORICAL_FIELDS,
        *POLICY_BOOLEAN_FIELDS,
        *DIAGNOSTIC_ONLY_FIELDS,
    )
    return [{field: row.get(field) for field in sample_fields if field in row} for row in selected]


def _split_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    net_values = [float(row.get("net_profit_bnb") or 0.0) for row in rows]
    wins = sum(1 for value in net_values if value > 0.0)
    return {
        "trade_count": len(rows),
        "net_profit_bnb": sum(net_values),
        "win_count": wins,
        "loss_count": sum(1 for value in net_values if value <= 0.0),
        "win_rate": wins / len(rows) if rows else None,
        "close_reason_counts": dict(sorted(Counter(str(row.get("close_reason") or "unknown") for row in rows).items())),
    }


def evaluate_rule(
    rows: Sequence[Mapping[str, Any]],
    rule: Mapping[str, Any],
    *,
    max_sample_rows: int = 25,
) -> dict[str, Any]:
    selected = [dict(row) for row in rows if _matches_rule(row, rule)]
    selected_net = [float(row.get("net_profit_bnb") or 0.0) for row in selected]
    skipped_winners = [value for value in selected_net if value > 0.0]
    skipped_losses = [value for value in selected_net if value <= 0.0]
    abstention_benefits = [-value for value in selected_net]
    positive_benefits = [value for value in abstention_benefits if value > 0.0]
    delta = sum(abstention_benefits)
    without_top = delta - max(positive_benefits) if positive_benefits else delta
    baseline = _split_metrics(rows)
    remaining_count = len(rows) - len(selected)
    remaining_win_count = int(baseline["win_count"]) - len(skipped_winners)
    remaining_net = float(baseline["net_profit_bnb"]) + delta
    return {
        "rule": {
            **dict(rule),
            "label": _rule_label(rule),
        },
        "baseline": baseline,
        "selected_count": len(selected),
        "selected_net_profit_bnb": sum(selected_net),
        "selected_winner_count": len(skipped_winners),
        "selected_loss_count": len(skipped_losses),
        "selected_loss_precision": len(skipped_losses) / len(selected) if selected else 0.0,
        "selected_winner_net_bnb": sum(skipped_winners),
        "selected_loss_net_bnb": sum(skipped_losses),
        "abstention_delta_bnb": delta,
        "abstention_delta_without_top_loss_benefit_bnb": without_top,
        "remaining_trade_count": remaining_count,
        "remaining_net_profit_bnb": remaining_net,
        "remaining_win_count": remaining_win_count,
        "remaining_win_rate": remaining_win_count / remaining_count if remaining_count else None,
        "selected_close_reason_counts": dict(sorted(Counter(str(row.get("close_reason") or "unknown") for row in selected).items())),
        "selected_symbols": [str(row.get("symbol") or row.get("token") or "") for row in selected[:25]],
        "selected_sample": _selected_samples(selected, max_sample_rows),
        "unemitted_selected_count": max(0, len(selected) - (len(selected) if int(max_sample_rows) == 0 else max(0, int(max_sample_rows)))),
    }


def _passes_train_gate(
    result: Mapping[str, Any],
    *,
    min_train_selected: int,
    min_train_loss_precision: float,
    max_train_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_train_selected)
        and float(result.get("selected_loss_precision") or 0.0) >= float(min_train_loss_precision)
        and int(result.get("selected_winner_count") or 0) <= int(max_train_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) > 0.0
    )


def _passes_validation_gate(
    result: Mapping[str, Any],
    *,
    min_validation_selected: int,
    max_validation_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_validation_selected)
        and int(result.get("selected_winner_count") or 0) <= int(max_validation_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) > 0.0
    )


def _passes_final_gate(
    result: Mapping[str, Any],
    *,
    min_final_selected: int,
    max_final_winner_count: int,
) -> bool:
    return (
        int(result.get("selected_count") or 0) >= int(min_final_selected)
        and int(result.get("selected_winner_count") or 0) <= int(max_final_winner_count)
        and float(result.get("abstention_delta_bnb") or 0.0) >= 0.0
    )


def _top_dependency_passes(result: Mapping[str, Any]) -> bool:
    without_top = result.get("abstention_delta_without_top_loss_benefit_bnb")
    if without_top is None:
        return True
    return float(without_top or 0.0) >= 0.0


def _rank_train(result: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(result.get("abstention_delta_bnb") or 0.0),
        -int(result.get("selected_loss_count") or 0),
        int(result.get("selected_winner_count") or 0),
        -float(result.get("selected_loss_precision") or 0.0),
        str(result.get("rule", {}).get("label") or ""),
    )


def _rank_eval(candidate: Mapping[str, Any]) -> tuple[Any, ...]:
    validation = candidate.get("validation") or {}
    final = candidate.get("final") or {}
    return (
        not bool(candidate.get("passes_research_alpha_proxy_gate")),
        -float(validation.get("abstention_delta_bnb") or 0.0),
        -float(final.get("abstention_delta_bnb") or 0.0),
        int(validation.get("selected_winner_count") or 0) + int(final.get("selected_winner_count") or 0),
        -int(validation.get("selected_count") or 0),
        str(candidate.get("rule", {}).get("label") or ""),
    )


def _feature_summaries(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for field in POLICY_NUMERIC_FIELDS:
        values = [_as_float(row.get(field)) for row in rows]
        summaries[field] = _numeric_summary([value for value in values if value is not None])
    for field in DIAGNOSTIC_ONLY_FIELDS:
        values = [_as_float(row.get(field)) for row in rows]
        summaries[field] = {
            **_numeric_summary([value for value in values if value is not None]),
            "policy_field": False,
        }
    for field in POLICY_CATEGORICAL_FIELDS:
        summaries[field] = dict(sorted(Counter(str(row.get(field) or "missing") for row in rows).items()))
    for field in POLICY_BOOLEAN_FIELDS:
        summaries[field] = dict(sorted(Counter(str(row.get(field)) for row in rows if row.get(field) is not None).items()))
    return summaries


def _strict_metric_coverage() -> dict[str, str]:
    return {
        "net_profit_bnb": "live_real_trade_proxy_only",
        "expected_utility": "abstention_delta_bnb_proxy_only",
        "trade_count": "live_real_trade_proxy_only",
        "win_rate": "live_real_trade_proxy_only",
        "max_drawdown_pct": "not_computed_proxy_requires_replay",
        "walk_forward": "not_computed_proxy_requires_replay",
        "stress": "not_computed_proxy_requires_replay",
        "paired_trade_delta": "not_computed_proxy_requires_replay",
    }


def build_execution_freshness_abstention_report(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    since: str | None = None,
    until: str | None = None,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    min_train_selected: int = 3,
    min_train_loss_precision: float = 0.60,
    max_train_winner_count: int = 4,
    min_validation_selected: int = 1,
    max_validation_winner_count: int = 0,
    min_final_selected: int = 1,
    max_final_winner_count: int = 1,
    max_sample_rows: int = 25,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    if not 0.0 <= float(min_train_loss_precision) <= 1.0:
        raise ValueError("min_train_loss_precision must be between 0 and 1")
    outcomes = trade_outcome_rows(trade_rows, since=since, until=until)
    splits = split_rows(outcomes, train_fraction=train_fraction, validation_fraction=validation_fraction)
    rules = generate_rules(splits["train"])
    train_results = [
        evaluate_rule(splits["train"], rule, max_sample_rows=max_sample_rows)
        for rule in rules
    ]
    train_results.sort(key=_rank_train)
    train_eligible = [
        result
        for result in train_results
        if _passes_train_gate(
            result,
            min_train_selected=min_train_selected,
            min_train_loss_precision=min_train_loss_precision,
            max_train_winner_count=max_train_winner_count,
        )
    ]

    evaluated_candidates = []
    for train_result in train_eligible:
        rule = dict(train_result.get("rule") or {})
        validation_result = evaluate_rule(splits["validation"], rule, max_sample_rows=max_sample_rows)
        final_result = evaluate_rule(splits["final"], rule, max_sample_rows=max_sample_rows)
        validation_passes = _passes_validation_gate(
            validation_result,
            min_validation_selected=min_validation_selected,
            max_validation_winner_count=max_validation_winner_count,
        )
        final_passes = _passes_final_gate(
            final_result,
            min_final_selected=min_final_selected,
            max_final_winner_count=max_final_winner_count,
        )
        top_dependency_passes = _top_dependency_passes(validation_result) and _top_dependency_passes(final_result)
        evaluated_candidates.append({
            "rule": rule,
            "train": train_result,
            "validation": validation_result,
            "final": final_result,
            "validation_passes": bool(validation_passes),
            "final_passes": bool(final_passes),
            "top_dependency_passes": bool(top_dependency_passes),
            "passes_research_alpha_proxy_gate": bool(validation_passes and final_passes and top_dependency_passes),
        })
    evaluated_candidates.sort(key=_rank_eval)
    selected = next(
        (candidate for candidate in evaluated_candidates if candidate["passes_research_alpha_proxy_gate"]),
        evaluated_candidates[0] if evaluated_candidates else None,
    )

    if selected and selected.get("passes_research_alpha_proxy_gate"):
        outcome_tier = "Research Alpha"
        decision = "research_alpha_proxy_requires_replay_and_signal_time_logging"
    elif train_eligible:
        outcome_tier = "Rejected"
        decision = "train_candidate_failed_validation_or_final_proxy_gate"
    else:
        outcome_tier = "Rejected"
        decision = "no_train_freshness_abstention_candidate"

    return {
        "generated_at": (generated_at or dt.datetime.now(dt.timezone.utc)).isoformat(),
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "requires_replay_before_live_change": True,
            "requires_signal_decision_freshness_logging_before_runtime_gate": True,
            "causal_policy": "rule scan uses only pre-fill token-status freshness fields recorded on OPEN rows",
            "diagnostic_only_fields": list(DIAGNOSTIC_ONLY_FIELDS),
        },
        "method": {
            "name": "execution_freshness_abstention_probe",
            "hypothesis": (
                "A subset of live entries made with stale lifecycle status, helper fallback, or slow chain lag "
                "has negative expectancy and can be abstained before order submission."
            ),
            "falsification_rule": (
                "Train-only freshness rules must improve validation abstention delta, avoid validation winner skips, "
                "and keep final abstention delta non-negative before promotion to replay-integrated feature work."
            ),
        },
        "parameters": {
            "since": since,
            "until": until,
            "train_fraction": float(train_fraction),
            "validation_fraction": float(validation_fraction),
            "min_train_selected": int(min_train_selected),
            "min_train_loss_precision": float(min_train_loss_precision),
            "max_train_winner_count": int(max_train_winner_count),
            "min_validation_selected": int(min_validation_selected),
            "max_validation_winner_count": int(max_validation_winner_count),
            "min_final_selected": int(min_final_selected),
            "max_final_winner_count": int(max_final_winner_count),
            "max_sample_rows": int(max_sample_rows),
        },
        "policy_fields": {
            "numeric": list(POLICY_NUMERIC_FIELDS),
            "categorical": list(POLICY_CATEGORICAL_FIELDS),
            "boolean": list(POLICY_BOOLEAN_FIELDS),
        },
        "candidate_counts": {
            "paired_real_trade_count": len(outcomes),
            "train_rows": len(splits["train"]),
            "validation_rows": len(splits["validation"]),
            "final_rows": len(splits["final"]),
            "scanned_rules": len(train_results),
            "train_eligible_rules": len(train_eligible),
            "evaluated_candidates": len(evaluated_candidates),
        },
        "split_baselines": {
            split_name: _split_metrics(split_rows)
            for split_name, split_rows in splits.items()
        },
        "feature_summaries": {
            split_name: _feature_summaries(split_rows)
            for split_name, split_rows in splits.items()
        },
        "train_top_rules": train_results[:100],
        "train_eligible_rules": train_eligible[:100],
        "evaluated_candidates": evaluated_candidates[:100],
        "selected_candidate": selected,
        "strict_metric_coverage": _strict_metric_coverage(),
        "outcome_tier": outcome_tier,
        "decision": decision,
    }
