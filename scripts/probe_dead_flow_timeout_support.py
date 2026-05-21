#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import dead_flow_timeout_probe as probe


DEFAULT_TRAIN_REPORT = "data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json"
DEFAULT_VALIDATION_REPORT = "data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json"
DEFAULT_FINAL_REPORT = "data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json"
DEFAULT_LIVE_ATTRIBUTION = "docs/research/20260521-conditional-exit-flow-state/live_attribution.json"
DEFAULT_OUTPUT_JSON = "docs/research/20260521-conditional-exit-flow-state/dead-flow-support.json"
DEFAULT_OUTPUT_MD = "docs/research/20260521-conditional-exit-flow-state/dead-flow-support.md"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a read-only dead-flow timeout support report")
    parser.add_argument("--train-report", default=DEFAULT_TRAIN_REPORT)
    parser.add_argument("--validation-report", default=DEFAULT_VALIDATION_REPORT)
    parser.add_argument("--final-report", default=DEFAULT_FINAL_REPORT)
    parser.add_argument("--live-attribution", default=DEFAULT_LIVE_ATTRIBUTION)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--force", action="store_true", help="Overwrite existing outputs")
    return parser.parse_args(argv)


def _allowed_output_root() -> Path:
    return PROJECT_ROOT / "docs" / "research" / "20260521-conditional-exit-flow-state"


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


def _validate_output_path(path_text: str) -> Path:
    normalized = _normalized_relative_text(path_text)
    if normalized in _protected_exact_paths():
        raise ValueError(f"refusing output path: {path_text}")

    output_path = Path(path_text)
    logical = output_path if output_path.is_absolute() else PROJECT_ROOT / output_path
    resolved = logical.resolve()
    allowed = _allowed_output_root().resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"refusing output path outside {allowed}: {path_text}") from exc
    return resolved


def _load_json(path_text: str) -> dict:
    path = Path(path_text)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data["_source_path"] = path_text
        return data
    raise ValueError(f"expected JSON object in {path_text}")


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        output_json = _validate_output_path(args.output_json)
        output_md = _validate_output_path(args.output_md)
        if output_json.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_json}")
        if output_md.exists() and not args.force:
            raise ValueError(f"refusing to overwrite existing output without --force: {output_md}")

        report = probe.build_support_report(
            train_report=_load_json(args.train_report),
            validation_report=_load_json(args.validation_report),
            final_report=_load_json(args.final_report),
            live_attribution=_load_json(args.live_attribution),
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
    print(f"support_gate={report['support_gate']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
