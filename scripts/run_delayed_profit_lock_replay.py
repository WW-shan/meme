#!/usr/bin/env python3
from __future__ import annotations

import itertools
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import run_fast_profit_lock_replay as _fast

DEFAULT_OUTPUT = "data/replay_reports/delayed_profit_lock_replay_20260521_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.003957285747499339


def candidate_grid():
    profit_targets = [0.25, 0.35, 0.45, 0.60]
    max_windows = [180.0, 240.0, 360.0, 480.0]
    for target, window in itertools.product(profit_targets, max_windows):
        yield {
            "profit_lock_take_profit_pct": target,
            "profit_lock_max_hold_seconds": window,
        }


def _argv_with_delayed_defaults(argv):
    args = list(sys.argv[1:] if argv is None else argv)
    has_output = any(arg == "--output" or arg.startswith("--output=") for arg in args)
    if not has_output:
        args = ["--output", DEFAULT_OUTPUT, *args]
    return args


def parse_args(argv=None):
    return _fast.parse_args(_argv_with_delayed_defaults(argv))


def main(argv=None):
    args = parse_args(argv)
    return _fast.run_profit_lock_replay_grid(
        args,
        candidate_grid_func=candidate_grid,
        initial_equity_bnb=LIVE_INITIAL_EQUITY_BNB,
    )


if __name__ == "__main__":
    main()
