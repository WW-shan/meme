#!/usr/bin/env python3
from __future__ import annotations

import itertools
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import run_support_rule_quick_tp_replay as _support

DEFAULT_OUTPUT = "data/replay_reports/delayed_confirmation_quick_tp_replay_20260527.json"


def candidate_grid():
    # Test the same support-rule quick-profit pocket, but require a short
    # post-signal hold before replay entry to avoid first-tick fakeouts.
    rule_shape = {
        "buy_quick_profit_overlay_min_prob": 0.985,
        "buy_quick_profit_overlay_min_pred_return": 30.0,
        "buy_quick_profit_overlay_max_pred_return": 35.0,
        "buy_quick_profit_overlay_min_entry_volume_30s": 1.25,
        "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
        "buy_quick_profit_overlay_max_age_seconds": 60.0,
        "buy_quick_profit_overlay_min_flow_event_count_30s": 2.0,
        "buy_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
        "buy_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
    }
    take_profits = [0.25, 0.35]
    confirmation_delays = [3.0, 5.0]
    max_drawdowns = [0.03, 0.06]
    max_chases = [0.12, 0.20]
    for take_profit, delay, max_drawdown, max_chase in itertools.product(
        take_profits,
        confirmation_delays,
        max_drawdowns,
        max_chases,
    ):
        yield {
            **rule_shape,
            "buy_quick_profit_overlay_take_profit_pct": take_profit,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            "buy_quick_profit_overlay_confirmation_delay_seconds": delay,
            "buy_quick_profit_overlay_max_confirmation_drawdown_pct": max_drawdown,
            "buy_quick_profit_overlay_max_confirmation_chase_pct": max_chase,
        }


def parse_args(argv=None):
    original_default = _support.DEFAULT_OUTPUT
    _support.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    try:
        return _support.parse_args(argv)
    finally:
        _support.DEFAULT_OUTPUT = original_default


def main(argv=None):
    original_grid = _support.candidate_grid
    original_default = _support.DEFAULT_OUTPUT
    _support.candidate_grid = candidate_grid
    _support.DEFAULT_OUTPUT = DEFAULT_OUTPUT
    try:
        return _support.main(argv)
    finally:
        _support.candidate_grid = original_grid
        _support.DEFAULT_OUTPUT = original_default


if __name__ == "__main__":
    main()
