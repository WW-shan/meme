#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import conditional_exit_feasibility_probe as probe


DEFAULT_LIVE_ATTRIBUTION = "docs/research/20260521-conditional-exit-flow-state/live_attribution.json"
DEFAULT_TRAIN_POST_TARGET = "data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json"
DEFAULT_VALIDATION_POST_TARGET = "data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json"
DEFAULT_FINAL_POST_TARGET = "data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json"
DEFAULT_DEAD_FLOW_SUPPORT = "docs/research/20260521-conditional-exit-flow-state/dead-flow-support.json"
DEFAULT_OUTPUT_JSON = "docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json"
DEFAULT_OUTPUT_MD = "docs/research/20260521-conditional-exit-flow-state/11-exit-state-attribution.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a read-only conditional-exit feasibility report")
    parser.add_argument("--live-attribution", default=DEFAULT_LIVE_ATTRIBUTION, help="Live attribution JSON path")
    parser.add_argument(
        "--train-post-target-report",
        default=DEFAULT_TRAIN_POST_TARGET,
        help="Post-target train replay report JSON path",
    )
    parser.add_argument(
        "--validation-post-target-report",
        default=DEFAULT_VALIDATION_POST_TARGET,
        help="Post-target validation replay report JSON path",
    )
    parser.add_argument(
        "--final-post-target-report",
        default=DEFAULT_FINAL_POST_TARGET,
        help="Post-target final replay report JSON path",
    )
    parser.add_argument(
        "--dead-flow-support-report",
        default=DEFAULT_DEAD_FLOW_SUPPORT,
        help="Optional dead-flow timeout support report JSON path",
    )
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON, help="Output JSON report path")
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD, help="Output markdown summary path")
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    return parser.parse_args(argv)


def _normalized_relative_text(path_text: str) -> str:
    text = Path(path_text).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _protected_exact_paths() -> set[str]:
    return {
        ".env",
        ".env.example",
        "docs/goals/live-model-optimization-goal.md",
    }


def _allowed_output_root() -> Path:
    return PROJECT_ROOT / "docs" / "research"


def _validate_output_path(output_text: str) -> Path:
    normalized = _normalized_relative_text(output_text)
    if normalized in _protected_exact_paths() or normalized.startswith("docs/goals/"):
        raise ValueError(f"refusing output path: {output_text}")

    output_path = Path(output_text)
    logical_output = output_path if output_path.is_absolute() else PROJECT_ROOT / output_path
    resolved_output = logical_output.resolve()
    allowed_root = _allowed_output_root().resolve()
    try:
        resolved_output.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError(f"refusing output path outside {allowed_root}: {output_text}") from exc
    return resolved_output


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output_json = _validate_output_path(args.output_json)
        output_md = _validate_output_path(args.output_md)
        if output_json.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_json}")
        if output_md.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_md}")

        live_attribution = _load_json(Path(args.live_attribution))
        live_attribution["_source_path"] = str(Path(args.live_attribution))
        train_report = _load_json(Path(args.train_post_target_report))
        train_report["_source_path"] = str(Path(args.train_post_target_report))
        validation_report = _load_json(Path(args.validation_post_target_report))
        validation_report["_source_path"] = str(Path(args.validation_post_target_report))
        final_report = _load_json(Path(args.final_post_target_report))
        final_report["_source_path"] = str(Path(args.final_post_target_report))
        dead_flow_support_report = None
        dead_flow_path = Path(args.dead_flow_support_report)
        if dead_flow_path.exists():
            dead_flow_support_report = _load_json(dead_flow_path)
            dead_flow_support_report["_source_path"] = str(dead_flow_path)

        report = probe.build_feasibility_report(
            live_attribution=live_attribution,
            train_post_target_report=train_report,
            validation_post_target_report=validation_report,
            final_post_target_report=final_report,
            dead_flow_support_report=dead_flow_support_report,
        )

        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(probe.to_json_text(report), encoding="utf-8")
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(probe.to_markdown_text(report), encoding="utf-8")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    print(f"support_gate={report['go_no_go']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
