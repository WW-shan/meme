#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_LIFECYCLE_DIR = "data/training"
DEFAULT_OUTPUT = "data/replay_reports/post_target_exit_state_probe_20260521_v95.json"
PROTECTED_OUTPUT_NAMES = frozenset(
    (
        "hybrid_manifest.json",
        "bc.pt",
        "trade_log.jsonl",
        "buy_model.cbm",
        "buy_threshold.json",
        "feature_schema.json",
        "entry_value_model.cbm",
        "sell_policy.zip",
    )
)
PROTECTED_EXACT_RELATIVE_PATHS = frozenset((
    ".env",
    ".env.example",
    "docs/goals/live-model-optimization-goal.md",
))
PROTECTED_RELATIVE_DIRS = (("config",), ("src", "trader"))
ALLOWED_OUTPUT_RELATIVE_DIR = ("data", "replay_reports")


class _TrainSafeArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        namespace = super().parse_args(args, namespace)
        raw_args = list(sys.argv[1:] if args is None else args)
        if (
            namespace.split == "train"
            and namespace.recent_lifecycle_files != 0
            and not any(item == "--recent-lifecycle-files" or item.startswith("--recent-lifecycle-files=") for item in raw_args)
        ):
            namespace.recent_lifecycle_files = 0
        return namespace


def _read_path_snapshot(path: str | Path) -> tuple[dict, bytes]:
    resolved = Path(path)
    stat_before = resolved.stat() if resolved.exists() and resolved.is_file() else None
    data = resolved.read_bytes() if stat_before is not None else b""
    stat_after = resolved.stat() if resolved.exists() and resolved.is_file() else None
    fingerprint = {
        "path": str(resolved),
        "exists": stat_before is not None,
        "size_bytes": len(data),
        "path_size_bytes_before_read": int(stat_before.st_size) if stat_before is not None else 0,
        "path_size_bytes_after_read": int(stat_after.st_size) if stat_after is not None else 0,
        "mtime_ns": int(stat_before.st_mtime_ns) if stat_before is not None else None,
        "mtime_ns_after_read": int(stat_after.st_mtime_ns) if stat_after is not None else None,
        "changed_during_read": (
            stat_before is not None
            and stat_after is not None
            and (
                int(stat_before.st_size) != int(stat_after.st_size)
                or int(stat_before.st_mtime_ns) != int(stat_after.st_mtime_ns)
            )
        ),
        "snapshot_read_mode": "single_read_bytes",
        "sha256": None,
    }
    if not fingerprint["exists"] or not resolved.is_file():
        return fingerprint, data
    fingerprint["sha256"] = hashlib.sha256(data).hexdigest()
    return fingerprint, data


def _fingerprint_path(path: str | Path) -> dict:
    fingerprint, _data = _read_path_snapshot(path)
    return fingerprint


def _iter_jsonl_bytes(data: bytes):
    for line in data.decode("utf-8").splitlines():
        text = line.strip()
        if text:
            yield json.loads(text)


def _input_fingerprint_policy() -> dict:
    return {
        "mutable_live_inputs": True,
        "fingerprints_are_run_snapshot": True,
        "snapshot_read_mode": "single_read_bytes",
        "current_paths_may_change_after_run": True,
        "note": "Each lifecycle input file is read once into bytes; hashes and parsing use those same bytes. Replay/model paths may change after the report is written.",
    }


def _strict_position_fraction(value: str) -> float:
    parsed = float(value)
    if parsed != 0.10:
        raise argparse.ArgumentTypeError("position_fraction must be exactly 0.10")
    return parsed


def _strict_max_open_positions(value: str) -> int:
    parsed = int(value)
    if parsed != 8:
        raise argparse.ArgumentTypeError("max_open_positions must be exactly 8")
    return parsed


def _protected_output_violation(path: str | Path) -> str | None:
    output_path = Path(path)
    if output_path.name in PROTECTED_OUTPUT_NAMES:
        return f"refusing protected model artifact output path: {output_path}"

    resolved_root = PROJECT_ROOT.resolve(strict=False)
    resolved_output = output_path if output_path.is_absolute() else PROJECT_ROOT / output_path
    try:
        relative = resolved_output.resolve(strict=False).relative_to(resolved_root)
    except ValueError:
        return f"refusing probe report output outside project data/replay_reports: {output_path}"

    relative_text = relative.as_posix()
    if relative.parts[: len(ALLOWED_OUTPUT_RELATIVE_DIR)] != ALLOWED_OUTPUT_RELATIVE_DIR:
        return f"refusing probe report output outside data/replay_reports: {output_path}"
    if relative_text in PROTECTED_EXACT_RELATIVE_PATHS:
        return f"refusing protected project output path: {output_path}"
    relative_parts = relative.parts
    for protected_parts in PROTECTED_RELATIVE_DIRS:
        if relative_parts[: len(protected_parts)] == protected_parts:
            return f"refusing output path under protected project directory: {output_path}"
    return None


def _assert_safe_output_path(path: str | Path) -> None:
    violation = _protected_output_violation(path)
    if violation is not None:
        raise argparse.ArgumentTypeError(violation)


def _assert_output_writable(path: str | Path, *, force: bool = False) -> None:
    violation = _protected_output_violation(path)
    if violation is not None:
        raise SystemExit(violation)
    output_path = Path(path)
    if output_path.exists() and not force:
        raise SystemExit(f"refusing to overwrite existing probe report without --force: {output_path}")


def parse_args(argv=None):
    parser = _TrainSafeArgumentParser(description="Run a read-only post-target exit-state probe for accepted replay trades")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="Model directory for replay")
    parser.add_argument("--lifecycle-dir", default=DEFAULT_LIFECYCLE_DIR, help="Directory containing lifecycle JSONL files")
    parser.add_argument(
        "--recent-lifecycle-files",
        type=int,
        default=1,
        help="Number of latest lifecycle files to include from lifecycle-dir",
    )
    parser.add_argument(
        "--lifecycle-file",
        action="append",
        default=None,
        help="Explicit lifecycle JSONL file to include; may be repeated",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON report path")
    parser.add_argument("--split", choices=("train", "validation", "final"), default="validation", help="Replay split to probe")
    parser.add_argument(
        "--chunk-train-files",
        action="store_true",
        help="For --split train, replay one train lifecycle file at a time to reduce memory pressure",
    )
    parser.add_argument(
        "--max-train-file-size-mb",
        type=float,
        default=None,
        help="With --chunk-train-files, skip train lifecycle files larger than this diagnostic safety limit",
    )
    parser.add_argument("--target-pct", type=float, default=0.25, help="Target return ratio that activates post-target scoring")
    parser.add_argument(
        "--continuation-pct",
        type=float,
        default=0.60,
        help="Continuation return ratio that marks durable runners",
    )
    parser.add_argument("--collapse-pct", type=float, default=-0.18, help="Collapse return ratio from entry")
    parser.add_argument("--horizon-seconds", type=float, default=900.0, help="Path horizon in seconds from entry")
    parser.add_argument(
        "--position-fraction",
        type=_strict_position_fraction,
        default=0.10,
        help="Strict risk contract; must remain exactly 0.10",
    )
    parser.add_argument(
        "--max-open-positions",
        type=_strict_max_open_positions,
        default=8,
        help="Strict risk contract; must remain exactly 8",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing probe report")
    args = parser.parse_args(argv)
    if args.chunk_train_files and args.split != "train":
        parser.error("--chunk-train-files is only valid with --split train")
    if args.split == "train":
        if args.lifecycle_file:
            parser.error("--split train does not accept extra --lifecycle-file inputs")
        if args.recent_lifecycle_files != 0:
            parser.error("--split train requires --recent-lifecycle-files 0 to avoid non-train lifecycle leakage")
        args.recent_lifecycle_files = 0
    if args.max_train_file_size_mb is not None:
        if not args.chunk_train_files:
            parser.error("--max-train-file-size-mb requires --chunk-train-files")
        if args.max_train_file_size_mb <= 0 or not math.isfinite(float(args.max_train_file_size_mb)):
            parser.error("--max-train-file-size-mb must be positive")
    try:
        _assert_safe_output_path(args.output)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    return args


def _unique_paths(paths) -> list[Path]:
    unique = []
    seen = set()
    for path in paths:
        resolved = Path(path)
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def _load_lifecycles(*, probe, lifecycle_paths: list[Path]) -> tuple[dict, list[dict]]:
    lifecycle_maps = []
    lifecycle_fingerprints = []
    reentry_probe = probe.reentry_probe
    flow_probe = getattr(probe, "flow_activation_probe", None)
    lifecycle_extractor = (
        getattr(flow_probe, "extract_lifecycles_from_rows_for_flow", None)
        if flow_probe is not None
        else None
    )
    lifecycle_merger = (
        getattr(flow_probe, "merge_lifecycle_maps_for_flow", None)
        if flow_probe is not None
        else None
    )
    if lifecycle_extractor is None:
        lifecycle_extractor = reentry_probe.extract_lifecycles_from_rows
    if lifecycle_merger is None:
        lifecycle_merger = reentry_probe.merge_lifecycle_maps
    for lifecycle_path in lifecycle_paths:
        lifecycle_fingerprint, lifecycle_bytes = _read_path_snapshot(lifecycle_path)
        lifecycle_fingerprints.append(lifecycle_fingerprint)
        if lifecycle_fingerprint["exists"]:
            lifecycle_maps.append(lifecycle_extractor(_iter_jsonl_bytes(lifecycle_bytes)))
    return lifecycle_merger(*lifecycle_maps), lifecycle_fingerprints


def _trade_log_from_replay(replay_report: dict) -> list[dict]:
    evaluation = replay_report.get("evaluation") or {}
    trade_log = evaluation.get("trade_log") or replay_report.get("trade_log") or []
    return [dict(row) for row in trade_log]


def _replay_kwargs(args, *, diagnostic_lifecycle_paths=None) -> dict:
    kwargs = {
        "model_dir": args.model_dir,
        "lifecycle_dir": args.lifecycle_dir,
        "split": args.split,
        "max_open_positions": args.max_open_positions,
        "include_trade_log": True,
        "write_report": False,
        "cache_dir": None,
        "use_cache": False,
        "overrides": {
            "position_fraction": args.position_fraction,
            "max_position_fraction": args.position_fraction,
            "fixed_stake_bnb": None,
            "skip_all_in_replay": True,
        },
    }
    if diagnostic_lifecycle_paths is not None:
        kwargs["diagnostic_lifecycle_paths"] = list(diagnostic_lifecycle_paths)
    return kwargs


def _run_train_chunk_replay_in_subprocess(args, path: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        payload_path = tmpdir_path / "payload.json"
        output_path = tmpdir_path / "chunk_report.json"
        payload = {
            "model_dir": args.model_dir,
            "lifecycle_dir": args.lifecycle_dir,
            "diagnostic_lifecycle_path": str(path),
            "max_open_positions": args.max_open_positions,
            "position_fraction": args.position_fraction,
            "output_path": str(output_path),
        }
        payload_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        code = r'''
import json
import sys
from pathlib import Path
from src.pipeline import model_replay

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
chunk_path = Path(payload["diagnostic_lifecycle_path"])
report = model_replay.run_model_replay(
    model_dir=payload["model_dir"],
    lifecycle_dir=payload["lifecycle_dir"],
    split="train",
    max_open_positions=int(payload["max_open_positions"]),
    include_trade_log=True,
    write_report=False,
    cache_dir=None,
    use_cache=False,
    diagnostic_lifecycle_paths=[chunk_path],
    overrides={
        "position_fraction": float(payload["position_fraction"]),
        "max_position_fraction": float(payload["position_fraction"]),
        "fixed_stake_bnb": None,
        "skip_all_in_replay": True,
    },
)
evaluation = dict(report.get("evaluation") or {})
trade_log = list(evaluation.get("trade_log") or report.get("trade_log") or [])
Path(payload["output_path"]).write_text(
    json.dumps(
        {
            "evaluation": {"trade_log": trade_log},
            "lifecycle_paths": list(report.get("lifecycle_paths") or [str(chunk_path)]),
            "sample_count": int(report.get("sample_count") or 0),
            "split": report.get("split", "train"),
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    + "\n",
    encoding="utf-8",
)
'''
        completed = subprocess.run(
            [sys.executable, "-c", code, str(payload_path)],
            cwd=str(PROJECT_ROOT),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            stderr_tail = (completed.stderr or completed.stdout or "").strip()[-2000:]
            if "no eval episodes could be built from eval samples" in stderr_tail:
                return {
                    "evaluation": {"trade_log": []},
                    "lifecycle_paths": [str(path)],
                    "sample_count": 0,
                    "split": "train",
                    "skipped_train_file": {
                        "path": str(path),
                        "reason": "no_eval_episodes",
                    },
                }
            raise SystemExit(f"train chunk replay failed for {path}: {stderr_tail}")
        return json.loads(output_path.read_text(encoding="utf-8"))


def _run_replay(args, model_replay) -> dict:
    if not args.chunk_train_files:
        return model_replay.run_model_replay(**_replay_kwargs(args))

    manifest = model_replay.load_manifest(args.model_dir)
    replay_split = model_replay.resolve_replay_split(manifest, args.lifecycle_dir)
    train_files = [Path(path) for path in (getattr(replay_split, "train_files", None) or [])]
    if not train_files:
        raise SystemExit("chunked train probe requires explicit train lifecycle files")
    skipped_train_files = []
    if args.max_train_file_size_mb is not None:
        max_bytes = float(args.max_train_file_size_mb) * 1024.0 * 1024.0
        selected_train_files = []
        for path in train_files:
            size_bytes = path.stat().st_size if path.exists() and path.is_file() else 0
            if size_bytes <= 0:
                skipped_train_files.append(
                    {
                        "path": str(path),
                        "size_bytes": int(size_bytes),
                        "limit_mb": float(args.max_train_file_size_mb),
                        "reason": "empty_file",
                    }
                )
                continue
            if size_bytes > max_bytes:
                skipped_train_files.append(
                    {
                        "path": str(path),
                        "size_bytes": int(size_bytes),
                        "limit_mb": float(args.max_train_file_size_mb),
                        "reason": "file_size_above_limit",
                    }
                )
                continue
            selected_train_files.append(path)
        train_files = selected_train_files
        if not train_files:
            raise SystemExit("chunked train probe skipped every train lifecycle file")

    all_trades = []
    lifecycle_paths = []
    chunk_summaries = []
    sample_count = 0
    for path in train_files:
        chunk = _run_train_chunk_replay_in_subprocess(args, path)
        if chunk.get("skipped_train_file"):
            skipped_train_files.append(dict(chunk["skipped_train_file"]))
            continue
        chunk_trades = _trade_log_from_replay(chunk)
        all_trades.extend(chunk_trades)
        chunk_lifecycle_paths = [str(item) for item in (chunk.get("lifecycle_paths") or [path])]
        lifecycle_paths.extend(chunk_lifecycle_paths)
        chunk_sample_count = int(chunk.get("sample_count") or 0)
        sample_count += chunk_sample_count
        chunk_summaries.append(
            {
                "lifecycle_paths": chunk_lifecycle_paths,
                "sample_count": chunk_sample_count,
                "trade_log_count": len(chunk_trades),
            }
        )

    return {
        "model_dir": args.model_dir,
        "split": "train",
        "sample_count": sample_count,
        "lifecycle_paths": [str(path) for path in _unique_paths(lifecycle_paths)],
        "evaluation": {"trade_log": all_trades},
        "chunked_train_replay": True,
        "diagnostic_equivalent_to_full_train_replay": False,
        "diagnostic_note": (
            "Chunked train replay resets replay state per lifecycle file to avoid live-machine memory pressure; "
            "use only for rare-state discovery, not strict performance or deployment selection."
        ),
        "chunk_summaries": chunk_summaries,
        "skipped_train_files": skipped_train_files,
    }


def main(argv=None) -> int:
    args = parse_args(argv)
    _assert_output_writable(args.output, force=bool(args.force))
    probe = importlib.import_module("src.pipeline.post_target_exit_state_probe")
    model_replay = importlib.import_module("src.pipeline.model_replay")
    reentry_probe = probe.reentry_probe

    replay_report = _run_replay(args, model_replay)

    lifecycle_paths = list(args.lifecycle_file or [])
    lifecycle_paths.extend(replay_report.get("lifecycle_paths") or [])
    lifecycle_paths.extend(reentry_probe.latest_lifecycle_files(args.lifecycle_dir, limit=args.recent_lifecycle_files))
    lifecycle_paths = _unique_paths(lifecycle_paths)
    lifecycles, lifecycle_fingerprints = _load_lifecycles(probe=probe, lifecycle_paths=lifecycle_paths)
    model_dir_fingerprint = {
        "path": args.model_dir,
        "exists": Path(args.model_dir).exists(),
        "is_dir": Path(args.model_dir).is_dir(),
    }

    report = probe.build_probe_report(
        trades=_trade_log_from_replay(replay_report),
        lifecycles=lifecycles,
        target_pct=args.target_pct,
        continuation_pct=args.continuation_pct,
        collapse_pct=args.collapse_pct,
        horizon_seconds=args.horizon_seconds,
    )
    report["inputs"] = {
        "model_dir": args.model_dir,
        "lifecycle_dir": args.lifecycle_dir,
        "recent_lifecycle_files": args.recent_lifecycle_files,
        "lifecycle_files": [str(path) for path in lifecycle_paths],
        "split": args.split,
    }
    report["input_fingerprints"] = {
        "model_dir": model_dir_fingerprint,
        "lifecycle_files": lifecycle_fingerprints,
        "replay_lifecycle_paths": list(replay_report.get("lifecycle_paths") or []),
    }
    report["input_fingerprint_policy"] = _input_fingerprint_policy()
    report.setdefault("parameters", {})
    report["parameters"].update(
        {
            "position_fraction": args.position_fraction,
            "max_open_positions": args.max_open_positions,
            "split": args.split,
        }
    )
    report["replay_summary"] = {
        "sample_count": replay_report.get("sample_count"),
        "model_dir": replay_report.get("model_dir", args.model_dir),
        "split": replay_report.get("split", args.split),
        "chunked_train_replay": bool(replay_report.get("chunked_train_replay")),
        "diagnostic_equivalent_to_full_train_replay": replay_report.get("diagnostic_equivalent_to_full_train_replay"),
        "diagnostic_note": replay_report.get("diagnostic_note"),
        "chunk_count": len(replay_report.get("chunk_summaries") or []),
        "skipped_train_file_count": len(replay_report.get("skipped_train_files") or []),
        "skipped_train_files": list(replay_report.get("skipped_train_files") or []),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(probe.to_json_text(report), encoding="utf-8")
    print(f"wrote {output_path}")
    print(f"scored_candidates={report.get('candidate_counts', {}).get('scored_candidates', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
