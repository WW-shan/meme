from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

from src.pipeline import added_trade_boundary_policy_probe as boundary_probe
from src.pipeline import reentry_probe
from src.pipeline import runner_retention_replay_gate as retention_gate
from src.pipeline import support_action_policy_probe as support_probe


PAIR_SELECTOR_DECISION_TIME_FIELDS = frozenset(support_probe.DECISION_TIME_FIELDS)


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _sample_time(row: Mapping[str, Any]) -> int:
    return int(_finite_float(row.get("decision_sample_time", row.get("sample_time"))) or 0)


def decision_time_features(row: Mapping[str, Any]) -> dict[str, float]:
    raw_features = row.get("features")
    feature_map = raw_features if isinstance(raw_features, Mapping) else {}
    result: dict[str, float] = {}
    for field in sorted(PAIR_SELECTOR_DECISION_TIME_FIELDS):
        value = row.get(field)
        parsed = _finite_float(value)
        if parsed is None:
            parsed = _finite_float(feature_map.get(field))
        if parsed is not None:
            result[field] = float(parsed)
    return result


def anchor_price_at_or_before(
    path: Iterable[reentry_probe.PricePoint],
    anchor_time: Any,
) -> float | None:
    return reentry_probe._anchor_price_at_or_before(path, reentry_probe.parse_time(anchor_time))


def _point_count_between(
    path: Sequence[reentry_probe.PricePoint],
    *,
    start_time: Any,
    end_time: Any,
) -> int:
    start = reentry_probe.parse_time(start_time)
    end = reentry_probe.parse_time(end_time)
    count = 0
    for point in path:
        point_time = reentry_probe.parse_time(point.time)
        if start <= point_time <= end:
            count += 1
    return count


def build_replacement_pairs(
    *,
    candidate_rows: Sequence[Mapping[str, Any]],
    baseline_pass_times_by_token: Mapping[str, Sequence[int]],
    price_paths_by_token: Mapping[str, Sequence[reentry_probe.PricePoint]],
    max_lead_seconds: int,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    max_lead = int(max_lead_seconds)
    for row in candidate_rows:
        token = str(row.get("token") or "").strip().lower()
        if not token:
            continue
        lead_seconds = retention_gate._next_baseline_entry_lead_seconds(row, baseline_pass_times_by_token)
        if lead_seconds is None or int(lead_seconds) <= 0 or int(lead_seconds) > max_lead:
            continue
        sample_time = _sample_time(row)
        candidate_time = reentry_probe.parse_time(sample_time)
        baseline_time = reentry_probe.parse_time(sample_time + int(lead_seconds))
        path = list(price_paths_by_token.get(token) or [])
        candidate_anchor_price = anchor_price_at_or_before(path, candidate_time)
        baseline_anchor_price = anchor_price_at_or_before(path, baseline_time)
        if (
            candidate_anchor_price is None
            or baseline_anchor_price is None
            or candidate_anchor_price <= 0.0
            or baseline_anchor_price <= 0.0
        ):
            continue
        pairs.append(
            {
                "token": token,
                "sample_time": int(sample_time),
                "baseline_sample_time": int(sample_time + int(lead_seconds)),
                "lead_seconds": int(lead_seconds),
                "candidate_anchor_price": float(candidate_anchor_price),
                "baseline_anchor_price": float(baseline_anchor_price),
                "pre_baseline_move_pct": (
                    (float(baseline_anchor_price) / float(candidate_anchor_price)) - 1.0
                )
                * 100.0,
                "features": decision_time_features(row),
                "point_count_to_baseline": _point_count_between(
                    path,
                    start_time=candidate_time,
                    end_time=baseline_time,
                ),
                "prob": _finite_float(row.get("prob")),
                "pred_return": _finite_float(row.get("pred_return")),
            }
        )
    return pairs


def _percentile(values: Sequence[float], q: float) -> float | None:
    finite = sorted(value for value in values if math.isfinite(float(value)))
    if not finite:
        return None
    if len(finite) == 1:
        return float(finite[0])
    position = (len(finite) - 1) * float(q)
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return float(finite[lower_index])
    lower = finite[lower_index]
    upper = finite[upper_index]
    return float(lower + (upper - lower) * (position - lower_index))


def _distribution(values: Sequence[float]) -> dict[str, Any]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return {
        "count": int(len(finite)),
        "min": min(finite) if finite else None,
        "p25": _percentile(finite, 0.25),
        "p50": _percentile(finite, 0.50),
        "p75": _percentile(finite, 0.75),
        "max": max(finite) if finite else None,
        "mean": (sum(finite) / len(finite)) if finite else None,
    }


def summarize_pairs_by_window(
    pairs: Sequence[Mapping[str, Any]],
    *,
    lead_windows_seconds: Sequence[int],
    sparse_point_floor: int = 3,
) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for window in sorted({int(value) for value in lead_windows_seconds}):
        selected = [
            pair
            for pair in pairs
            if int(_finite_float(pair.get("lead_seconds")) or 0) <= window
        ]
        sparse_count = sum(
            1
            for pair in selected
            if int(_finite_float(pair.get("point_count_to_baseline")) or 0) < int(sparse_point_floor)
        )
        count = len(selected)
        summary[str(window)] = {
            "lead_window_seconds": int(window),
            "qualifying_pair_count": int(count),
            "pre_baseline_move_pct": _distribution(
                [
                    float(pair["pre_baseline_move_pct"])
                    for pair in selected
                    if _finite_float(pair.get("pre_baseline_move_pct")) is not None
                ]
            ),
            "path_density": {
                "sparse_point_floor": int(sparse_point_floor),
                "sparse_pair_count": int(sparse_count),
                "sparse_pair_ratio": (float(sparse_count) / float(count)) if count else None,
            },
        }
    return summary


def _selector_return_pct(row: Mapping[str, Any]) -> float:
    trade = row.get("trade")
    payload = trade if isinstance(trade, Mapping) else row
    return _finite_float(payload.get("return_pct")) or 0.0


def _selector_utility(values: Sequence[float], *, loss_cost: float) -> float:
    return float(sum(value if value > 0.0 else float(loss_cost) * value for value in values))


def _selector_summary(rows: Sequence[Mapping[str, Any]], *, loss_cost: float) -> dict[str, Any]:
    returns = [_selector_return_pct(row) for row in rows]
    positives = [value for value in returns if value > 0.0]
    ties = [value for value in returns if value == 0.0]
    losses = [value for value in returns if value < 0.0]
    return {
        "pair_count": int(len(rows)),
        "positive_count": int(len(positives)),
        "tie_count": int(len(ties)),
        "loss_count": int(len(losses)),
        "positive_rate": float(len(positives) / len(rows)) if rows else 0.0,
        "return_pct_sum": float(sum(returns)),
        "return_pct_mean": float(sum(returns) / len(returns)) if returns else 0.0,
        "positive_return_pct_sum": float(sum(positives)),
        "negative_return_pct_sum": float(sum(losses)),
        "cost_adjusted_utility": _selector_utility(returns, loss_cost=loss_cost),
    }


def _selector_rows_from_pairs(pairs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        delta = _finite_float(pair.get("delta_realized_pct"))
        features = pair.get("features")
        if delta is None or not isinstance(features, Mapping):
            continue
        rows.append(
            {
                "trade": {"return_pct": float(delta)},
                "features": dict(features),
                "pair": {
                    "token": pair.get("token"),
                    "sample_time": pair.get("sample_time"),
                    "baseline_sample_time": pair.get("baseline_sample_time"),
                    "lead_seconds": pair.get("lead_seconds"),
                    "candidate_first_barrier": pair.get("candidate_first_barrier"),
                    "baseline_first_barrier": pair.get("baseline_first_barrier"),
                    "candidate_realized_pct": pair.get("candidate_realized_pct"),
                    "baseline_realized_pct": pair.get("baseline_realized_pct"),
                    "delta_realized_pct": float(delta),
                    "mfe_delta_pct": pair.get("mfe_delta_pct"),
                },
            }
        )
    return rows


def _evaluate_selector_rule(
    rows: Sequence[Mapping[str, Any]],
    rule: Mapping[str, Any] | None,
    *,
    loss_cost: float,
) -> dict[str, Any]:
    selected = [row for row in rows if boundary_probe._rule_matches(row, rule)]
    rejected = [row for row in rows if not boundary_probe._rule_matches(row, rule)]
    selected_summary = _selector_summary(selected, loss_cost=loss_cost)
    all_summary = _selector_summary(rows, loss_cost=loss_cost)
    positive_returns = sorted(
        (_selector_return_pct(row) for row in selected if _selector_return_pct(row) > 0.0),
        reverse=True,
    )

    def utility_after_top_positive_removal(top_n: int) -> float:
        remaining = [_selector_return_pct(row) for row in selected]
        for value in positive_returns[: max(0, int(top_n))]:
            try:
                remaining.remove(value)
            except ValueError:
                continue
        return _selector_utility(remaining, loss_cost=loss_cost)

    return {
        "all": all_summary,
        "selected": selected_summary,
        "rejected": _selector_summary(rejected, loss_cost=loss_cost),
        "selected_vs_no_replacement_utility_delta": float(selected_summary["cost_adjusted_utility"]),
        "selected_vs_blanket_replacement_utility_delta": float(
            selected_summary["cost_adjusted_utility"] - all_summary["cost_adjusted_utility"]
        ),
        "top_positive_dependency": {
            "top_positive_count": int(len(positive_returns)),
            "top1_removed_utility": utility_after_top_positive_removal(1),
            "top3_removed_utility": utility_after_top_positive_removal(3),
            "top1_removed_still_positive": utility_after_top_positive_removal(1) > 0.0,
            "top3_removed_still_positive": utility_after_top_positive_removal(3) > 0.0,
        },
    }


def _selector_sort_key(item: Mapping[str, Any]) -> tuple[float, float, float, int]:
    train = item["train"]
    selected = train["selected"]
    return (
        float(train["selected_vs_no_replacement_utility_delta"]),
        float(selected["positive_rate"]),
        float(selected["return_pct_sum"]),
        -int(selected["loss_count"]),
    )


def _select_pair_rule(
    train_rows: Sequence[Mapping[str, Any]],
    *,
    loss_cost: float,
    min_keep_count: int,
    min_reject_count: int,
    min_positive_rate: float,
    max_conditions: int,
    beam_width: int,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int, int]:
    rules, generated_count = boundary_probe._candidate_conjunction_rules(
        train_rows,
        loss_cost=float(loss_cost),
        max_conditions=max(1, int(max_conditions)),
        beam_width=max(1, int(beam_width)),
    )
    supported = []
    for rule in rules:
        evaluation = _evaluate_selector_rule(train_rows, rule, loss_cost=float(loss_cost))
        selected = evaluation["selected"]
        rejected = evaluation["rejected"]
        if int(selected["pair_count"]) < int(min_keep_count):
            continue
        if int(rejected["pair_count"]) < int(min_reject_count):
            continue
        if float(selected["positive_rate"]) < float(min_positive_rate):
            continue
        if int(selected["positive_count"]) <= 0:
            continue
        if evaluation["selected_vs_no_replacement_utility_delta"] <= 0.0:
            continue
        supported.append({"rule": rule, "train": evaluation})
    supported.sort(key=_selector_sort_key, reverse=True)
    return (supported[0]["rule"] if supported else None), supported[:25], len(supported), len(rules) or generated_count


def build_pair_selector_report(
    *,
    train_pairs: Sequence[Mapping[str, Any]],
    validation_pairs: Sequence[Mapping[str, Any]],
    final_pairs: Sequence[Mapping[str, Any]],
    selection_split_name: str = "train",
    loss_cost: float = 3.0,
    min_keep_count: int = 20,
    min_reject_count: int = 20,
    min_eval_keep_count: int = 10,
    min_positive_rate: float = 0.50,
    max_conditions: int = 2,
    beam_width: int = 80,
) -> dict[str, Any]:
    train_rows = _selector_rows_from_pairs(train_pairs)
    validation_rows = _selector_rows_from_pairs(validation_pairs)
    final_rows = _selector_rows_from_pairs(final_pairs)
    selected_rule, candidates, supported_count, generated_count = _select_pair_rule(
        train_rows,
        loss_cost=float(loss_cost),
        min_keep_count=int(min_keep_count),
        min_reject_count=int(min_reject_count),
        min_positive_rate=float(min_positive_rate),
        max_conditions=int(max_conditions),
        beam_width=int(beam_width),
    )
    train_eval = _evaluate_selector_rule(train_rows, selected_rule, loss_cost=float(loss_cost))
    validation_eval = _evaluate_selector_rule(validation_rows, selected_rule, loss_cost=float(loss_cost))
    final_eval = _evaluate_selector_rule(final_rows, selected_rule, loss_cost=float(loss_cost))
    rejection_reasons = []
    if selected_rule is None:
        rejection_reasons.append("no_train_supported_rule")
    for split, evaluation in (("validation", validation_eval), ("final", final_eval)):
        selected = evaluation["selected"]
        if int(selected["pair_count"]) < int(min_eval_keep_count):
            rejection_reasons.append(f"{split}_selected_pair_count_below_min")
        if evaluation["selected_vs_no_replacement_utility_delta"] <= 0.0:
            rejection_reasons.append(f"{split}_utility_delta_not_positive")
        if float(selected["positive_rate"]) < float(min_positive_rate):
            rejection_reasons.append(f"{split}_positive_rate_below_min")
    if not final_eval["top_positive_dependency"]["top1_removed_still_positive"]:
        rejection_reasons.append("final_top1_positive_dependent")
    decision = "reject" if rejection_reasons else "research_alpha"
    return {
        "decision": decision,
        "outcome_tier": "Rejected" if rejection_reasons else "Research Alpha",
        "rejection_reasons": rejection_reasons,
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "uses_ex_post_outcomes": True,
            "uses_decision_time_features_only": True,
            "not_deployable_policy": True,
            "selection_split": str(selection_split_name),
            "selection_selects_rule_before_validation_final_evaluation": True,
            "train_selects_rule_before_validation_final_evaluation": str(selection_split_name) == "train",
            "max_outcome_tier": "Research Alpha",
        },
        "config": {
            "loss_cost": float(loss_cost),
            "min_keep_count": int(min_keep_count),
            "min_reject_count": int(min_reject_count),
            "min_eval_keep_count": int(min_eval_keep_count),
            "min_positive_rate": float(min_positive_rate),
            "max_conditions": max(1, int(max_conditions)),
            "beam_width": max(1, int(beam_width)),
        },
        "selected_rule": selected_rule,
        "train": train_eval,
        "validation": validation_eval,
        "final": final_eval,
        "row_counts": {
            "selection": int(len(train_rows)),
            "train": int(len(train_rows)),
            "validation": int(len(validation_rows)),
            "final": int(len(final_rows)),
        },
        "candidate_rule_count": int(generated_count),
        "supported_candidate_count": int(supported_count),
        "top_supported_candidates": candidates,
        "falsification_rule": (
            "Reject unless the train-selected decision-time rule has positive validation and final "
            "replacement utility, sufficient selected-pair support, positive-rate discipline, and "
            "final utility that remains positive after removing the top selected positive delta."
        ),
    }


def _terminal_return_pct(
    path: Sequence[reentry_probe.PricePoint],
    *,
    anchor_time: Any,
    anchor_price: float,
    horizon_seconds: float,
) -> float | None:
    anchor = reentry_probe.parse_time(anchor_time)
    latest = None
    for point in sorted(path, key=lambda item: reentry_probe.parse_time(item.time)):
        seconds = (reentry_probe.parse_time(point.time) - anchor).total_seconds()
        if 0 <= seconds <= float(horizon_seconds):
            latest = point
    if latest is None or float(anchor_price) <= 0.0:
        return None
    return ((float(latest.price) / float(anchor_price)) - 1.0) * 100.0


def _barrier_realized_return_pct(
    metrics: Mapping[str, Any],
    *,
    terminal_return_pct: float | None,
    take_profit_pct: float,
    stop_loss_pct: float,
) -> float | None:
    first_barrier = metrics.get("first_barrier")
    if first_barrier in {"+25", "+60"}:
        return float(take_profit_pct)
    if first_barrier in {"-18", "-25"}:
        return float(stop_loss_pct)
    return terminal_return_pct


def score_pair_barrier_returns(
    pair: Mapping[str, Any],
    path: Sequence[reentry_probe.PricePoint],
    *,
    horizon_seconds: float,
    take_profit_pct: float = 25.0,
    stop_loss_pct: float = -18.0,
    cost_pct: float = 0.0,
) -> dict[str, Any]:
    candidate_time = reentry_probe.parse_time(pair.get("sample_time"))
    baseline_time = reentry_probe.parse_time(pair.get("baseline_sample_time"))
    candidate_anchor_price = float(pair.get("candidate_anchor_price"))
    baseline_anchor_price = float(pair.get("baseline_anchor_price"))
    candidate_metrics = reentry_probe.path_metrics(
        path,
        anchor_time=candidate_time,
        anchor_price=candidate_anchor_price,
        horizon_seconds=float(horizon_seconds),
    )
    baseline_metrics = reentry_probe.path_metrics(
        path,
        anchor_time=baseline_time,
        anchor_price=baseline_anchor_price,
        horizon_seconds=float(horizon_seconds),
    )
    candidate_terminal = _terminal_return_pct(
        path,
        anchor_time=candidate_time,
        anchor_price=candidate_anchor_price,
        horizon_seconds=float(horizon_seconds),
    )
    baseline_terminal = _terminal_return_pct(
        path,
        anchor_time=baseline_time,
        anchor_price=baseline_anchor_price,
        horizon_seconds=float(horizon_seconds),
    )
    candidate_realized = _barrier_realized_return_pct(
        candidate_metrics,
        terminal_return_pct=candidate_terminal,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    baseline_realized = _barrier_realized_return_pct(
        baseline_metrics,
        terminal_return_pct=baseline_terminal,
        take_profit_pct=take_profit_pct,
        stop_loss_pct=stop_loss_pct,
    )
    if candidate_realized is not None:
        candidate_realized -= float(cost_pct)
    if baseline_realized is not None:
        baseline_realized -= float(cost_pct)
    candidate_mfe = _finite_float(candidate_metrics.get("mfe_pct"))
    baseline_mfe = _finite_float(baseline_metrics.get("mfe_pct"))
    scored = dict(pair)
    scored.update(
        {
            "horizon_seconds": float(horizon_seconds),
            "take_profit_pct": float(take_profit_pct),
            "stop_loss_pct": float(stop_loss_pct),
            "cost_pct": float(cost_pct),
            "cost_parity_applied": True,
            "candidate_first_barrier": candidate_metrics.get("first_barrier"),
            "baseline_first_barrier": baseline_metrics.get("first_barrier"),
            "candidate_mfe_pct": candidate_mfe,
            "baseline_mfe_pct": baseline_mfe,
            "candidate_mae_pct": _finite_float(candidate_metrics.get("mae_pct")),
            "baseline_mae_pct": _finite_float(baseline_metrics.get("mae_pct")),
            "candidate_realized_pct": candidate_realized,
            "baseline_realized_pct": baseline_realized,
            "delta_realized_pct": (
                candidate_realized - baseline_realized
                if candidate_realized is not None and baseline_realized is not None
                else None
            ),
            "mfe_delta_pct": (
                candidate_mfe - baseline_mfe
                if candidate_mfe is not None and baseline_mfe is not None
                else None
            ),
        }
    )
    return scored


def _barrier_count(
    pairs: Sequence[Mapping[str, Any]],
    *,
    field: str,
    negative: bool,
) -> int:
    if negative:
        return sum(1 for pair in pairs if str(pair.get(field) or "").startswith("-"))
    return sum(1 for pair in pairs if str(pair.get(field) or "").startswith("+"))


def _ratio_block(count: int, denominator: int) -> dict[str, Any]:
    return {
        "count": int(count),
        "ratio": (float(count) / float(denominator)) if denominator else None,
    }


def summarize_scored_pairs_by_window(
    pairs: Sequence[Mapping[str, Any]],
    *,
    lead_windows_seconds: Sequence[int],
    sparse_point_floor: int = 3,
) -> dict[str, dict[str, Any]]:
    summary = summarize_pairs_by_window(
        pairs,
        lead_windows_seconds=lead_windows_seconds,
        sparse_point_floor=sparse_point_floor,
    )
    for window, cell in summary.items():
        selected = [
            pair
            for pair in pairs
            if int(_finite_float(pair.get("lead_seconds")) or 0) <= int(window)
        ]
        count = len(selected)
        cell.update(
            {
                "candidate_realized_pct": _distribution(
                    [
                        float(pair["candidate_realized_pct"])
                        for pair in selected
                        if _finite_float(pair.get("candidate_realized_pct")) is not None
                    ]
                ),
                "baseline_realized_pct": _distribution(
                    [
                        float(pair["baseline_realized_pct"])
                        for pair in selected
                        if _finite_float(pair.get("baseline_realized_pct")) is not None
                    ]
                ),
                "delta_realized_pct": _distribution(
                    [
                        float(pair["delta_realized_pct"])
                        for pair in selected
                        if _finite_float(pair.get("delta_realized_pct")) is not None
                    ]
                ),
                "mfe_delta_pct": _distribution(
                    [
                        float(pair["mfe_delta_pct"])
                        for pair in selected
                        if _finite_float(pair.get("mfe_delta_pct")) is not None
                    ]
                ),
                "candidate_stop_first": _ratio_block(
                    _barrier_count(selected, field="candidate_first_barrier", negative=True),
                    count,
                ),
                "baseline_stop_first": _ratio_block(
                    _barrier_count(selected, field="baseline_first_barrier", negative=True),
                    count,
                ),
                "candidate_profit_first": _ratio_block(
                    _barrier_count(selected, field="candidate_first_barrier", negative=False),
                    count,
                ),
                "baseline_profit_first": _ratio_block(
                    _barrier_count(selected, field="baseline_first_barrier", negative=False),
                    count,
                ),
            }
        )
    return summary


def build_decision(
    split_summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    *,
    required_splits: Sequence[str] = ("validation", "final"),
    min_pairs_per_split: int = 100,
    min_pre_move_p75_pct: float = 5.0,
) -> dict[str, Any]:
    windows = sorted(
        {
            str(window)
            for split_summary in split_summaries.values()
            for window in split_summary.keys()
        },
        key=lambda value: int(value),
    )
    window_decisions = {}
    support_failures = []
    pre_move_failures = []
    viable_windows = []
    for window in windows:
        split_checks = {}
        support_ok = True
        pre_move_ok = True
        for split in required_splits:
            cell = dict(split_summaries.get(split, {}).get(window, {}) or {})
            pair_count = int(cell.get("qualifying_pair_count") or 0)
            p75 = _finite_float(dict(cell.get("pre_baseline_move_pct") or {}).get("p75"))
            split_checks[split] = {
                "qualifying_pair_count": pair_count,
                "pre_baseline_move_pct_p75": p75,
                "support_ok": pair_count >= int(min_pairs_per_split),
                "pre_move_ok": p75 is not None and p75 >= float(min_pre_move_p75_pct),
            }
            support_ok = support_ok and split_checks[split]["support_ok"]
            pre_move_ok = pre_move_ok and split_checks[split]["pre_move_ok"]
        window_decisions[window] = {
            "support_ok": bool(support_ok),
            "pre_move_ok": bool(pre_move_ok),
            "continue_to_deployable_proxy": bool(support_ok and pre_move_ok),
            "splits": split_checks,
        }
        if support_ok and pre_move_ok:
            viable_windows.append(window)
        elif not support_ok:
            support_failures.append(window)
        else:
            pre_move_failures.append(window)
    if viable_windows:
        return {
            "decision": "continue",
            "reason": "replacement_oracle_support_and_pre_move_pass",
            "continue_to_deployable_proxy": True,
            "viable_windows": viable_windows,
            "window_decisions": window_decisions,
        }
    return {
        "decision": "reject",
        "reason": (
            "replacement_pair_support_below_min"
            if support_failures
            else "pre_baseline_move_p75_below_min"
        ),
        "continue_to_deployable_proxy": False,
        "viable_windows": [],
        "window_decisions": window_decisions,
        "support_failed_windows": support_failures,
        "pre_move_failed_windows": pre_move_failures,
    }


def build_barrier_decision(
    split_summaries: Mapping[str, Mapping[str, Mapping[str, Any]]],
    *,
    required_splits: Sequence[str] = ("validation", "final"),
    min_pairs_per_split: int = 100,
    min_delta_realized_p50_pct: float = 1.0,
    max_candidate_stop_first_ratio: float = 0.40,
) -> dict[str, Any]:
    windows = sorted(
        {
            str(window)
            for split_summary in split_summaries.values()
            for window in split_summary.keys()
        },
        key=lambda value: int(value),
    )
    window_decisions = {}
    support_failures = []
    delta_failures = []
    stop_failures = []
    viable_windows = []
    for window in windows:
        split_checks = {}
        support_ok = True
        delta_ok = True
        stop_ok = True
        for split in required_splits:
            cell = dict(split_summaries.get(split, {}).get(window, {}) or {})
            pair_count = int(cell.get("qualifying_pair_count") or 0)
            delta_p50 = _finite_float(dict(cell.get("delta_realized_pct") or {}).get("p50"))
            stop_ratio = _finite_float(dict(cell.get("candidate_stop_first") or {}).get("ratio"))
            split_checks[split] = {
                "qualifying_pair_count": pair_count,
                "delta_realized_pct_p50": delta_p50,
                "candidate_stop_first_ratio": stop_ratio,
                "support_ok": pair_count >= int(min_pairs_per_split),
                "delta_ok": delta_p50 is not None and delta_p50 >= float(min_delta_realized_p50_pct),
                "stop_ok": stop_ratio is not None and stop_ratio <= float(max_candidate_stop_first_ratio),
            }
            support_ok = support_ok and split_checks[split]["support_ok"]
            delta_ok = delta_ok and split_checks[split]["delta_ok"]
            stop_ok = stop_ok and split_checks[split]["stop_ok"]
        window_decisions[window] = {
            "support_ok": bool(support_ok),
            "delta_ok": bool(delta_ok),
            "stop_ok": bool(stop_ok),
            "continue_to_deployable_proxy": bool(support_ok and delta_ok and stop_ok),
            "splits": split_checks,
        }
        if support_ok and delta_ok and stop_ok:
            viable_windows.append(window)
        elif not support_ok:
            support_failures.append(window)
        elif not delta_ok:
            delta_failures.append(window)
        else:
            stop_failures.append(window)
    if viable_windows:
        return {
            "decision": "continue",
            "reason": "barrier_realized_delta_and_stop_risk_pass",
            "continue_to_deployable_proxy": True,
            "viable_windows": viable_windows,
            "window_decisions": window_decisions,
        }
    if support_failures:
        reason = "replacement_pair_support_below_min"
    elif delta_failures:
        reason = "delta_realized_p50_below_min"
    else:
        reason = "candidate_stop_first_ratio_above_max"
    return {
        "decision": "reject",
        "reason": reason,
        "continue_to_deployable_proxy": False,
        "viable_windows": [],
        "window_decisions": window_decisions,
        "support_failed_windows": support_failures,
        "delta_failed_windows": delta_failures,
        "stop_failed_windows": stop_failures,
    }
