from __future__ import annotations

import datetime as dt
import math
from collections.abc import Mapping, Sequence
from typing import Any

from src.pipeline import accepted_entry_feature_contrast as contrast


FRESHNESS_POLICY_FEATURE_ALIASES = {
    "lifecycle_status_chain_lag_seconds": ("lifecycle_status_chain_lag_seconds",),
    "lifecycle_status_staleness_seconds": ("lifecycle_status_staleness_seconds",),
    "lifecycle_status_fast_status_eligible": ("lifecycle_status_fast_status_eligible",),
    "signal_price_volatility": ("signal_price_volatility", "price_volatility", "entry_price_volatility"),
    "signal_volume_30s": ("signal_volume_30s", "volume_30s", "entry_volume_30s"),
    "freshness_latency_volatility_risk": ("freshness_latency_volatility_risk",),
    "freshness_latency_volume_risk": ("freshness_latency_volume_risk",),
}


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _token_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _time_key(value: Any) -> str:
    if value is None:
        return ""
    parsed = _finite_float(value)
    if parsed is not None:
        return str(int(round(parsed)))
    return str(value).strip()


def _trade_key(trade: Mapping[str, Any]) -> tuple[str, str]:
    token = _token_key(trade.get("token") or trade.get("token_address"))
    signal_time = _time_key(
        trade.get("entry_signal_time")
        if "entry_signal_time" in trade
        else trade.get("signal_time")
        if "signal_time" in trade
        else trade.get("entry_time")
    )
    return token, signal_time


def _trade_view(trade: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "token": _token_key(trade.get("token") or trade.get("token_address")),
        "entry_signal_time": trade.get("entry_signal_time") if "entry_signal_time" in trade else trade.get("signal_time"),
        "entry_time": trade.get("entry_time"),
        "return_pct": _finite_float(trade.get("return_pct") if "return_pct" in trade else trade.get("net_return_pct")) or 0.0,
        "exit_reason": str(trade.get("exit_reason") or trade.get("close_reason") or ""),
    }


def _index_trades(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    indexed: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        key = _trade_key(row)
        if not key[0] or not key[1]:
            continue
        indexed.setdefault(key, row)
    return indexed


def _return_pct(trade: Mapping[str, Any]) -> float:
    return _finite_float(trade.get("return_pct") if "return_pct" in trade else trade.get("net_return_pct")) or 0.0


def _net_profit_bnb(trade: Mapping[str, Any]) -> float | None:
    for key in ("net_profit_bnb", "net_profit", "profit_bnb", "pnl_bnb"):
        value = _finite_float(trade.get(key))
        if value is not None:
            return value
    return None


def _group_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    returns = [_return_pct(row) for row in rows]
    net_profits = [_net_profit_bnb(row) for row in rows]
    finite_profits = [value for value in net_profits if value is not None]
    wins = sum(1 for value in returns if value > 0.0)
    return {
        "trade_count": len(rows),
        "win_count": int(wins),
        "loss_count": int(len(rows) - wins),
        "win_rate": wins / len(rows) if rows else 0.0,
        "return_pct_sum": float(sum(returns)),
        "return_pct_mean": float(sum(returns) / len(returns)) if returns else 0.0,
        "net_profit_bnb_sum": float(sum(finite_profits)) if finite_profits else None,
    }


def _common_trade_deltas(
    *,
    baseline_index: Mapping[tuple[str, str], Mapping[str, Any]],
    candidate_index: Mapping[tuple[str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for key in sorted(set(baseline_index) & set(candidate_index)):
        baseline_trade = baseline_index[key]
        candidate_trade = candidate_index[key]
        baseline_return = _return_pct(baseline_trade)
        candidate_return = _return_pct(candidate_trade)
        rows.append(
            {
                "token": key[0],
                "entry_signal_time": baseline_trade.get("entry_signal_time")
                if "entry_signal_time" in baseline_trade
                else baseline_trade.get("signal_time"),
                "baseline_return_pct": baseline_return,
                "candidate_return_pct": candidate_return,
                "return_delta_pct": float(candidate_return - baseline_return),
                "baseline_exit_reason": str(baseline_trade.get("exit_reason") or baseline_trade.get("close_reason") or ""),
                "candidate_exit_reason": str(candidate_trade.get("exit_reason") or candidate_trade.get("close_reason") or ""),
            }
        )
    return rows


def _common_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    deltas = [_finite_float(row.get("return_delta_pct")) or 0.0 for row in rows]
    return {
        "trade_count": len(rows),
        "improved_count": sum(1 for value in deltas if value > 0.0),
        "worsened_count": sum(1 for value in deltas if value < 0.0),
        "unchanged_count": sum(1 for value in deltas if value == 0.0),
        "return_delta_pct_sum": float(sum(deltas)),
        "return_delta_pct_mean": float(sum(deltas) / len(deltas)) if deltas else 0.0,
    }


def _feature_contrast_report(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
    name: str,
    top_n: int,
) -> dict[str, Any]:
    return contrast.build_contrast_report(
        trade_rows=trade_rows,
        sample_rows=sample_rows,
        trade_log_sources=[name],
        sample_sources=["preloaded_eval_samples"],
        top_n=top_n,
    )


def _matched_feature_rows(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sample_index, _indexed_sample_count = contrast._build_sample_index(sample_rows)
    matched_rows, _unmatched_trades = contrast._matched_trade_rows(
        trade_rows=trade_rows,
        sample_index=sample_index,
    )
    rows: list[dict[str, Any]] = []
    for row in matched_rows:
        trade = row.get("trade") if isinstance(row.get("trade"), Mapping) else {}
        rows.append(
            {
                "trade": _trade_view(trade),
                "matched_sample_time": row.get("matched_sample_time"),
                "features": dict(row.get("features") or {}),
                "labels": dict(row.get("labels") or {}),
            }
        )
    return rows


def _trade_context_feature_values(trade: Mapping[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    aliases = {
        alias
        for field_aliases in FRESHNESS_POLICY_FEATURE_ALIASES.values()
        for alias in field_aliases
    }
    for alias in sorted(aliases):
        value = _finite_float(trade.get(alias))
        if value is not None:
            values[alias] = value
    return values


def _policy_feature_rows(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sample_index, _indexed_sample_count = contrast._build_sample_index(sample_rows)
    rows: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for trade in trade_rows:
        token = contrast._token_key(trade.get("token") or trade.get("token_address"))
        features: dict[str, float] = {}
        matched_time = None
        for trade_time in contrast._trade_times(trade):
            match = sample_index.get((token, trade_time))
            if match is not None:
                matched_time = trade_time
                features.update(contrast._sample_feature_values(match))
                break
        features.update(_trade_context_feature_values(trade))
        if features:
            rows.append(
                {
                    "trade": _trade_view(trade),
                    "matched_sample_time": matched_time,
                    "features": features,
                }
            )
        else:
            unmatched.append(_trade_view(trade))
    return rows, unmatched


def _policy_feature_coverage(
    *,
    trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    matched_rows, unmatched_trades = _policy_feature_rows(
        trade_rows=trade_rows,
        sample_rows=sample_rows,
    )
    matched_count = len(matched_rows)
    fields = []
    for field, aliases in FRESHNESS_POLICY_FEATURE_ALIASES.items():
        aliases = tuple(str(alias) for alias in aliases)
        available_aliases = sorted({
            alias
            for row in matched_rows
            for alias in aliases
            if alias in (row.get("features") or {})
        })
        covered = sum(
            1
            for row in matched_rows
            if any(alias in (row.get("features") or {}) for alias in aliases)
        )
        fields.append(
            {
                "field": field,
                "aliases": list(aliases),
                "available_aliases": available_aliases,
                "covered_trade_count": int(covered),
                "matched_trade_count": int(matched_count),
                "coverage_ratio": float(covered / matched_count) if matched_count else 0.0,
                "status": "available" if covered > 0 else "missing",
            }
        )
    return {
        "policy_family": "execution_freshness",
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "uses_decision_time_features_only": True,
            "purpose": (
                "report which freshness proxy fields are present in strict replay matched sample features "
                "or replay trade-log entry context"
            ),
        },
        "trade_count": int(len(trade_rows)),
        "matched_trade_count": int(matched_count),
        "unmatched_trade_count": int(len(unmatched_trades)),
        "fields": fields,
    }


def build_trade_delta_attribution_report(
    *,
    baseline_trade_rows: Sequence[Mapping[str, Any]],
    candidate_trade_rows: Sequence[Mapping[str, Any]],
    sample_rows: Sequence[Mapping[str, Any]],
    top_n: int = 25,
    generated_at: dt.datetime | None = None,
) -> dict[str, Any]:
    baseline_index = _index_trades(baseline_trade_rows)
    candidate_index = _index_trades(candidate_trade_rows)
    baseline_keys = set(baseline_index)
    candidate_keys = set(candidate_index)

    added_candidate = [candidate_index[key] for key in sorted(candidate_keys - baseline_keys)]
    removed_baseline = [baseline_index[key] for key in sorted(baseline_keys - candidate_keys)]
    common_deltas = _common_trade_deltas(
        baseline_index=baseline_index,
        candidate_index=candidate_index,
    )

    return {
        "generated_at": (generated_at or dt.datetime.now()).isoformat(),
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "uses_decision_time_features_only": True,
        },
        "match_key": "token + entry_signal_time",
        "delta_summary": {
            "baseline": _group_summary(list(baseline_index.values())),
            "candidate": _group_summary(list(candidate_index.values())),
            "added_candidate_trades": _group_summary(added_candidate),
            "removed_baseline_trades": _group_summary(removed_baseline),
            "common_trades": _common_summary(common_deltas),
        },
        "added_candidate_trades": [_trade_view(row) for row in added_candidate],
        "removed_baseline_trades": [_trade_view(row) for row in removed_baseline],
        "common_trade_deltas": common_deltas,
        "feature_contrast": {
            "added_candidate_trades": _feature_contrast_report(
                trade_rows=added_candidate,
                sample_rows=sample_rows,
                name="added_candidate_trades",
                top_n=top_n,
            ),
            "removed_baseline_trades": _feature_contrast_report(
                trade_rows=removed_baseline,
                sample_rows=sample_rows,
                name="removed_baseline_trades",
                top_n=top_n,
            ),
        },
        "matched_feature_rows": {
            "added_candidate_trades": _matched_feature_rows(
                trade_rows=added_candidate,
                sample_rows=sample_rows,
            ),
            "removed_baseline_trades": _matched_feature_rows(
                trade_rows=removed_baseline,
                sample_rows=sample_rows,
            ),
        },
        "policy_feature_coverage": {
            "added_candidate_trades": _policy_feature_coverage(
                trade_rows=added_candidate,
                sample_rows=sample_rows,
            ),
            "removed_baseline_trades": _policy_feature_coverage(
                trade_rows=removed_baseline,
                sample_rows=sample_rows,
            ),
        },
    }
