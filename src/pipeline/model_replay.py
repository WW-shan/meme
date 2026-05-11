from __future__ import annotations

import hashlib
import json
from pathlib import Path

MODEL_ARTIFACT_FILES = ("buy_model.cbm", "buy_threshold.json", "feature_schema.json", "sell_policy.zip")


def file_sha1(path: Path) -> str:
    path = Path(path)
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_checksums(model_dir) -> dict:
    base = Path(model_dir)
    checksums = {}
    for name in MODEL_ARTIFACT_FILES:
        path = base / name
        if path.exists():
            checksums[name] = file_sha1(path)
    return checksums


def load_manifest(model_dir) -> dict:
    path = Path(model_dir) / "hybrid_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"missing hybrid manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _evaluation_value(manifest: dict, key: str, default=None):
    evaluation = manifest.get("evaluation", {}) if isinstance(manifest, dict) else {}
    if key in evaluation:
        return evaluation[key]
    selected = manifest.get("selected_runtime_params", {}) if isinstance(manifest, dict) else {}
    return selected.get(key, default)


def live_replay_config_from_manifest(
    manifest: dict,
    *,
    max_open_positions: int = 8,
    include_trade_log: bool = False,
    overrides: dict | None = None,
) -> dict:
    config = {
        "sample_mode": "trade_event",
        "future_windows": [300],
        "max_sample_age_seconds": int(_evaluation_value(manifest, "max_entry_age_seconds", 300) or 300),
        "max_entry_age_seconds": int(_evaluation_value(manifest, "max_entry_age_seconds", 300) or 300),
        "max_samples_per_token": 120,
        "target_label_column": manifest.get("artifacts", {}).get("buy_model", {}).get(
            "target_label_column", "live_risk_adjusted_return_pct"
        ),
        "target_threshold_value": manifest.get("artifacts", {}).get("buy_model", {}).get("target_threshold_value", 20),
        "min_entry_unique_buyers": int(_evaluation_value(manifest, "min_entry_unique_buyers", 3) or 3),
        "min_entry_buy_count": int(_evaluation_value(manifest, "min_entry_buy_count", 5) or 5),
        "stop_loss": float(_evaluation_value(manifest, "stop_loss", -0.25)),
        "position_fraction": float(_evaluation_value(manifest, "position_fraction", 0.1)),
        "max_position_fraction": _evaluation_value(manifest, "max_position_fraction", 0.1),
        "initial_equity_bnb": float(_evaluation_value(manifest, "initial_equity_bnb", 1.0)),
        "fixed_stake_bnb": _evaluation_value(manifest, "fixed_stake_bnb", 0.1),
        "fee_bps": float(_evaluation_value(manifest, "fee_bps", 100.0)),
        "slippage_bps": float(_evaluation_value(manifest, "slippage_bps", 200.0)),
        "one_entry_per_token": bool(_evaluation_value(manifest, "one_entry_per_token", True)),
        "max_trades_per_token": _evaluation_value(manifest, "max_trades_per_token", 1),
        "max_hold_seconds": _evaluation_value(manifest, "max_hold_seconds", 420),
        "min_policy_hold_seconds": int(_evaluation_value(manifest, "min_policy_hold_seconds", 0) or 0),
        "allow_partial_exits": bool(_evaluation_value(manifest, "allow_partial_exits", False)),
        "entry_delay_seconds": int(_evaluation_value(manifest, "entry_delay_seconds", 3) or 0),
        "exit_delay_seconds": int(_evaluation_value(manifest, "exit_delay_seconds", 3) or 0),
        "max_open_positions": int(max_open_positions),
        "entry_max_fill_wait_seconds": _evaluation_value(manifest, "entry_max_fill_wait_seconds", 3),
        "exit_max_fill_wait_seconds": _evaluation_value(manifest, "exit_max_fill_wait_seconds", 6),
        "entry_price_protection_pct": _evaluation_value(manifest, "entry_price_protection_pct", 0.4),
        "trailing_start_pct": _evaluation_value(manifest, "trailing_start_pct", 0.2),
        "trailing_stop_pct": _evaluation_value(manifest, "trailing_stop_pct", 0.1),
        "rug_sell_pressure": _evaluation_value(manifest, "rug_sell_pressure", 0.92),
        "walk_forward_segments": 3,
        "stress_replay": True,
        "include_trade_log": bool(include_trade_log),
        "label_entry_delay_seconds": int(_evaluation_value(manifest, "entry_delay_seconds", 3) or 0),
        "label_exit_delay_seconds": int(_evaluation_value(manifest, "exit_delay_seconds", 3) or 0),
        "label_fee_bps": float(_evaluation_value(manifest, "fee_bps", 100.0)),
        "label_slippage_bps": float(_evaluation_value(manifest, "slippage_bps", 200.0)),
    }
    config.update(dict(overrides or {}))
    return config


def git_metadata(repo_dir=".") -> dict:
    import subprocess

    root = Path(repo_dir)

    def _run(args):
        result = subprocess.run(
            args,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.stdout.strip()

    return {
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "branch": _run(["git", "branch", "--show-current"]),
        "dirty": bool(_run(["git", "status", "--short"])),
    }
