#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_action_policy_candidate_gate_replay import (  # noqa: E402
    DEFAULT_MODEL_DIR,
    LIVE_INITIAL_EQUITY_BNB,
    LIVE_POSITION_CAP,
    STRICT_MAX_OPEN_POSITIONS,
    _base_overrides,
    _evaluation,
    _split_samples_for_replay,
    _strict_live_fraction,
    _strict_max_open_positions,
)
from src.pipeline.replay_trade_delta_attribution import FRESHNESS_POLICY_FEATURE_ALIASES  # noqa: E402


REPLAY_REPORTS_DIR = Path("data/replay_reports")
PROTECTED_OUTPUTS = {
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
}
DEFAULT_REQUIRED_INPUTS = {
    "freshness_latency_volume_risk": (
        "lifecycle_status_chain_lag_seconds",
        "signal_price_volatility",
        "signal_volume_30s",
    ),
    "freshness_latency_volatility_risk": (
        "lifecycle_status_chain_lag_seconds",
        "signal_price_volatility",
    ),
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit whether execution-freshness policy fields are present in strict replay context",
    )
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    parser.add_argument("--lifecycle-dir", default="data/training")
    parser.add_argument("--cache-dir", default=".cache/model_replay")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false")
    parser.add_argument("--position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-position-fraction", type=_strict_live_fraction, default=LIVE_POSITION_CAP)
    parser.add_argument("--max-open-positions", type=_strict_max_open_positions, default=STRICT_MAX_OPEN_POSITIONS)
    parser.add_argument("--rule-field", required=True)
    parser.add_argument("--rule-threshold", type=float, required=True)
    parser.add_argument(
        "--required-input",
        action="append",
        default=None,
        help="Required field for the selected rule; defaults to the rule field or known composite inputs",
    )
    parser.set_defaults(use_cache=True)
    return parser.parse_args(argv)


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _refuse_symlinked_replay_root(repo_root: Path, replay_root: Path) -> None:
    current = repo_root
    for part in replay_root.relative_to(repo_root).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing output path because {current} is a symlink")


def _validate_output_path(output_text: str, *, force: bool) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in PROTECTED_OUTPUTS:
        raise ValueError(f"refusing output path: {output_text}")

    repo_root = PROJECT_ROOT.resolve()
    replay_root = repo_root / REPLAY_REPORTS_DIR
    _refuse_symlinked_replay_root(repo_root, replay_root)
    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else repo_root / output_path
    resolved_output = logical_output.resolve()
    resolved_replay_root = replay_root.resolve()
    if not _is_relative_to(resolved_output, resolved_replay_root):
        raise ValueError(f"refusing output path outside {REPLAY_REPORTS_DIR}: {output_text}")
    if resolved_output.exists() and not force:
        raise ValueError(f"refusing to overwrite existing output without --force: {output_text}")
    return resolved_output


def _json_sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(item) for item in value]
    return value


def _json_text(report: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_sanitize(report),
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


def _feature_map(row: Mapping[str, Any], *, nested_features: bool) -> dict[str, Any]:
    values: dict[str, Any] = {}
    if nested_features and isinstance(row.get("features"), Mapping):
        values.update(dict(row.get("features") or {}))
    values.update({str(key): value for key, value in row.items() if key != "features"})
    return values


def _field_aliases(field: str) -> tuple[str, ...]:
    aliases = FRESHNESS_POLICY_FEATURE_ALIASES.get(field)
    if aliases:
        return tuple(str(alias) for alias in aliases)
    return (str(field),)


def _coverage_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    nested_features: bool,
) -> list[dict[str, Any]]:
    feature_rows = [_feature_map(row, nested_features=nested_features) for row in rows if isinstance(row, Mapping)]
    fields = sorted(set(FRESHNESS_POLICY_FEATURE_ALIASES) | {alias for aliases in FRESHNESS_POLICY_FEATURE_ALIASES.values() for alias in aliases})
    coverage = []
    for field in fields:
        aliases = _field_aliases(field)
        available_aliases = sorted({
            alias
            for feature_row in feature_rows
            for alias in aliases
            if _as_float(feature_row.get(alias)) is not None
        })
        covered = sum(
            1
            for feature_row in feature_rows
            if any(_as_float(feature_row.get(alias)) is not None for alias in aliases)
        )
        coverage.append({
            "field": field,
            "aliases": list(aliases),
            "available_aliases": available_aliases,
            "covered_sample_count": int(covered),
            "sample_count": int(len(feature_rows)),
            "coverage_ratio": float(covered / len(feature_rows)) if feature_rows else 0.0,
            "status": "available" if covered > 0 else "missing",
        })
    return coverage


def _trade_context_coverage(trade_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    fields = _coverage_rows(trade_rows, nested_features=False)
    for row in fields:
        row["covered_trade_count"] = row.pop("covered_sample_count")
        row["trade_count"] = row.pop("sample_count")
    return {
        "policy_family": "execution_freshness",
        "contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "uses_decision_time_features_only": True,
            "purpose": "report freshness proxy fields present in replay trade-log entry context",
        },
        "trade_count": int(len(trade_rows)),
        "matched_trade_count": int(len(trade_rows)),
        "unmatched_trade_count": 0,
        "fields": fields,
    }


def _coverage_available(coverage_rows: Sequence[Mapping[str, Any]], required_inputs: Sequence[str]) -> dict[str, bool]:
    by_field = {str(row.get("field")): row for row in coverage_rows}
    return {
        str(field): str((by_field.get(str(field)) or {}).get("status") or "") == "available"
        for field in required_inputs
    }


def _numeric_values(rows: Sequence[Mapping[str, Any]], *, nested_features: bool, field: str) -> list[float]:
    aliases = _field_aliases(field)
    values: list[float] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        feature_map = _feature_map(row, nested_features=nested_features)
        for alias in aliases:
            value = _as_float(feature_map.get(alias))
            if value is not None:
                values.append(value)
                break
    return values


def _numeric_summary(values: Sequence[float]) -> dict[str, Any]:
    finite = sorted(value for value in values if math.isfinite(float(value)))
    if not finite:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "p50": None,
            "p95": None,
            "unique_count": 0,
        }

    def quantile(q: float) -> float:
        index = min(len(finite) - 1, max(0, int((len(finite) - 1) * q)))
        return float(finite[index])

    return {
        "count": int(len(finite)),
        "min": float(finite[0]),
        "max": float(finite[-1]),
        "mean": float(sum(finite) / len(finite)),
        "p50": quantile(0.50),
        "p95": quantile(0.95),
        "unique_count": int(len(set(finite))),
    }


def _numeric_gte_match_count(values: Sequence[float], threshold: float) -> int:
    return sum(1 for value in values if math.isfinite(float(value)) and float(value) >= float(threshold))


def _required_inputs(rule_field: str, required_inputs: Sequence[str] | None) -> list[str]:
    if required_inputs:
        return [str(field) for field in required_inputs]
    return list(DEFAULT_REQUIRED_INPUTS.get(str(rule_field), (str(rule_field),)))


def _summary(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "net_profit_bnb",
        "net_return_pct",
        "total_trades",
        "max_drawdown_pct",
        "win_rate",
        "walk_forward_worst_net_return_pct",
        "walk_forward_worst_max_drawdown_pct",
    )
    summary: dict[str, Any] = {}
    for key in keys:
        value = _as_float(evaluation.get(key))
        if key == "total_trades":
            summary[key] = 0 if value is None else int(value)
        else:
            summary[key] = value
    return summary


def _run_replay_with_trade_log(run_model_replay, args, overrides, *, split: str, eval_samples):
    replay_overrides = dict(overrides or {})
    replay_overrides["eval_samples"] = list(eval_samples or [])
    replay_overrides["eval_samples_already_split_filtered"] = True
    return run_model_replay(
        model_dir=args.model_dir,
        lifecycle_dir=args.lifecycle_dir,
        output_path=None,
        cache_dir=args.cache_dir,
        split=split,
        max_open_positions=args.max_open_positions,
        include_trade_log=True,
        overrides=replay_overrides,
        use_cache=args.use_cache,
        write_report=False,
    )


def _split_report(
    *,
    split: str,
    samples: Sequence[Mapping[str, Any]],
    replay_report: Mapping[str, Any],
    required_inputs: Sequence[str],
    selected_rule: Mapping[str, Any],
) -> dict[str, Any]:
    evaluation = _evaluation(replay_report)
    trade_log = list(evaluation.get("trade_log") or [])
    sample_coverage = _coverage_rows(list(samples or []), nested_features=True)
    trade_context_coverage = _trade_context_coverage(trade_log)
    sample_available = _coverage_available(sample_coverage, required_inputs)
    trade_available = _coverage_available(trade_context_coverage["fields"], required_inputs)
    rule_field = str(selected_rule.get("field") or "")
    rule_threshold = _as_float(selected_rule.get("threshold"))
    sample_rule_values = _numeric_values(samples or [], nested_features=True, field=rule_field)
    trade_rule_values = _numeric_values(trade_log, nested_features=False, field=rule_field)
    sample_rule_match_count = (
        _numeric_gte_match_count(sample_rule_values, rule_threshold)
        if rule_threshold is not None
        else 0
    )
    trade_rule_match_count = (
        _numeric_gte_match_count(trade_rule_values, rule_threshold)
        if rule_threshold is not None
        else 0
    )
    return {
        "sample_count": int(len(samples or [])),
        "baseline_trade_log_count": int(len(trade_log)),
        "baseline_summary": _summary(evaluation),
        "sample_policy_feature_coverage": sample_coverage,
        "baseline_trade_policy_feature_coverage": trade_context_coverage,
        "rule_inputs_available_in_samples": sample_available,
        "rule_inputs_available_in_replay_trade_context": trade_available,
        "selected_proxy_rule_replayable_from_samples": all(sample_available.values()) if sample_available else False,
        "selected_proxy_rule_replayable_from_trade_context": all(trade_available.values()) if trade_available else False,
        "selected_proxy_rule_sample_match_count": int(sample_rule_match_count),
        "selected_proxy_rule_trade_context_match_count": int(trade_rule_match_count),
        "selected_proxy_rule_sample_value_summary": _numeric_summary(sample_rule_values),
        "selected_proxy_rule_trade_context_value_summary": _numeric_summary(trade_rule_values),
        "selected_proxy_rule_semantically_replayable_from_samples": int(sample_rule_match_count) > 0,
        "selected_proxy_rule_semantically_replayable_from_trade_context": int(trade_rule_match_count) > 0,
        "replay_metadata": {
            "generated_at": replay_report.get("generated_at"),
            "split": split,
            "sample_count": replay_report.get("sample_count"),
        },
    }


def build_report(args) -> dict[str, Any]:
    from src.pipeline.model_replay import run_model_replay

    base_overrides = _base_overrides(args)
    required_inputs = _required_inputs(args.rule_field, args.required_input)
    selected_rule = {
        "type": "numeric_gte",
        "field": str(args.rule_field),
        "threshold": float(args.rule_threshold),
        "label": f"{args.rule_field} >= {float(args.rule_threshold):g}",
    }
    context: dict[str, Any] = {}
    splits: dict[str, Any] = {}
    for split in ("validation", "final"):
        samples = _split_samples_for_replay(args, split, base_overrides, context)
        replay_report = _run_replay_with_trade_log(
            run_model_replay,
            args,
            base_overrides,
            split=split,
            eval_samples=samples,
        )
        splits[split] = _split_report(
            split=split,
            samples=samples,
            replay_report=replay_report,
            required_inputs=required_inputs,
            selected_rule=selected_rule,
        )

    all_samples = all(
        bool(block.get("selected_proxy_rule_replayable_from_samples"))
        for block in splits.values()
    )
    all_trade_context = all(
        bool(block.get("selected_proxy_rule_replayable_from_trade_context"))
        for block in splits.values()
    )
    all_sample_semantic = all(
        bool(block.get("selected_proxy_rule_semantically_replayable_from_samples"))
        for block in splits.values()
    )
    all_trade_context_semantic = all(
        bool(block.get("selected_proxy_rule_semantically_replayable_from_trade_context"))
        for block in splits.values()
    )
    decision = (
        "strict_replay_context_available"
        if all_samples and all_trade_context and all_sample_semantic and all_trade_context_semantic
        else (
            "rejected_strict_replay_context_degenerate"
            if all_samples and all_trade_context
            else "rejected_strict_replay_context_missing"
        )
    )
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": {
            "name": "execution_freshness_replay_context_audit",
            "purpose": (
                "check whether a selected execution-freshness policy rule can be computed from "
                "strict replay samples and replay trade-log entry context"
            ),
        },
        "probe_contract": {
            "read_only": True,
            "live_switch_evidence": False,
            "safe_for_live_switch": False,
            "runtime_behavior_changed": False,
            "strict_live_sizing_preserved": True,
            "position_fraction": LIVE_POSITION_CAP,
            "max_position_fraction": LIVE_POSITION_CAP,
            "max_open_positions": STRICT_MAX_OPEN_POSITIONS,
        },
        "strict_assumptions": {
            "initial_equity_bnb": LIVE_INITIAL_EQUITY_BNB,
            "position_fraction": LIVE_POSITION_CAP,
            "max_position_fraction": LIVE_POSITION_CAP,
            "fixed_stake_bnb": None,
            "skip_all_in_replay": True,
            "max_open_positions": STRICT_MAX_OPEN_POSITIONS,
        },
        "model_dir": str(args.model_dir),
        "lifecycle_dir": str(args.lifecycle_dir),
        "cache_dir": str(args.cache_dir),
        "use_cache": bool(args.use_cache),
        "selected_proxy_rule": selected_rule,
        "required_rule_inputs": required_inputs,
        "splits": splits,
        "outcome_tier": "Research Alpha" if decision == "strict_replay_context_available" else "Rejected",
        "decision": decision,
        "live_switch_evidence": False,
        "next_action": (
            "run strict replay gate using the replayable freshness field"
            if decision == "strict_replay_context_available"
            else (
                "find a non-degenerate decision-time freshness proxy or change the replay sample anchor"
                if decision == "rejected_strict_replay_context_degenerate"
                else "propagate missing decision-time lifecycle freshness fields into replay samples before strict replay gate"
            )
        ),
    }


def to_markdown(report: Mapping[str, Any], *, json_path: str | None = None) -> str:
    selected_rule = report.get("selected_proxy_rule") or {}

    def numeric_summary_text(summary: Mapping[str, Any]) -> str:
        return (
            f"count={summary.get('count')}, min={summary.get('min')}, "
            f"p50={summary.get('p50')}, p95={summary.get('p95')}, "
            f"max={summary.get('max')}, unique={summary.get('unique_count')}"
        )

    lines = [
        "# Execution Freshness Replay Context Audit",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Model: `{report.get('model_dir')}`",
        f"- Selected proxy rule: `{selected_rule.get('label')}`",
        f"- Outcome: `{report.get('outcome_tier')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Live switch evidence: `{str(report.get('live_switch_evidence')).lower()}`",
        f"- Runtime behavior changed: `{str((report.get('probe_contract') or {}).get('runtime_behavior_changed')).lower()}`",
        "",
        "## Split Coverage",
        "",
    ]
    required_inputs = list(report.get("required_rule_inputs") or [])
    for split, block in sorted((report.get("splits") or {}).items()):
        lines.extend([
            f"### {str(split).title()}",
            "",
            f"- Samples: `{block.get('sample_count')}`",
            f"- Baseline replay trades: `{block.get('baseline_trade_log_count')}`",
        ])
        baseline = block.get("baseline_summary") or {}
        lines.extend([
            f"- Baseline net profit BNB: `{baseline.get('net_profit_bnb')}`",
            f"- Baseline win rate: `{baseline.get('win_rate')}`",
        ])
        sample_by_field = {row.get("field"): row for row in block.get("sample_policy_feature_coverage") or []}
        trade_by_field = {
            row.get("field"): row
            for row in ((block.get("baseline_trade_policy_feature_coverage") or {}).get("fields") or [])
        }
        for field in required_inputs:
            sample = sample_by_field.get(field) or {}
            trade = trade_by_field.get(field) or {}
            lines.append(
                f"- Sample `{field}`: `{sample.get('status')}` via `{sample.get('available_aliases')}`"
            )
            lines.append(
                f"- Trade-context `{field}`: `{trade.get('status')}` via `{trade.get('available_aliases')}`"
            )
        lines.extend([
            f"- Selected rule replayable from samples: `{block.get('selected_proxy_rule_replayable_from_samples')}`",
            f"- Selected rule replayable from replay trade context: `{block.get('selected_proxy_rule_replayable_from_trade_context')}`",
            f"- Selected rule semantically replayable from samples: `{block.get('selected_proxy_rule_semantically_replayable_from_samples')}`",
            f"- Selected rule semantically replayable from replay trade context: `{block.get('selected_proxy_rule_semantically_replayable_from_trade_context')}`",
            f"- Selected rule sample match count: `{block.get('selected_proxy_rule_sample_match_count')}`",
            f"- Selected rule trade-context match count: `{block.get('selected_proxy_rule_trade_context_match_count')}`",
            f"- Selected rule sample values: `{numeric_summary_text(block.get('selected_proxy_rule_sample_value_summary') or {})}`",
            f"- Selected rule trade-context values: `{numeric_summary_text(block.get('selected_proxy_rule_trade_context_value_summary') or {})}`",
            "",
        ])
    decision = str(report.get("decision"))
    if decision == "strict_replay_context_available":
        lines.extend([
            "## Decision",
            "",
            "The selected freshness rule is available and non-degenerate in both strict replay samples and replay trade context for validation and final splits. This is a read-only Research Alpha audit, not live-switch evidence.",
        ])
    elif decision == "rejected_strict_replay_context_degenerate":
        lines.extend([
            "## Decision",
            "",
            "The required freshness fields are present, but degenerate under the current strict replay anchor: the selected threshold matches no validation/final samples or replay trade-context rows. This is a rejected read-only audit, not live-switch evidence.",
        ])
    else:
        lines.extend([
            "## Decision",
            "",
            "The selected freshness rule is not strict-replayable in the current replay surface because one or more required decision-time freshness fields are missing from validation/final samples or replay trade context.",
        ])
    if json_path:
        lines.extend(["", f"JSON report: `{json_path}`"])
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output_json = _validate_output_path(args.output_json, force=bool(args.force))
        output_md = _validate_output_path(args.output_md, force=bool(args.force)) if args.output_md else None
        report = build_report(args)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(_json_text(report), encoding="utf-8")
        if output_md is not None:
            output_md.parent.mkdir(parents=True, exist_ok=True)
            output_md.write_text(
                to_markdown(report, json_path=_normalized_relative_text(args.output_json)),
                encoding="utf-8",
            )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_json}")
    if output_md is not None:
        print(f"wrote {output_md}")
    print(f"outcome_tier={report.get('outcome_tier')}")
    print(f"decision={report.get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
