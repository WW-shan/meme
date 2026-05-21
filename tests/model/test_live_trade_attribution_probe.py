import datetime as dt
import unittest

from src.pipeline import reentry_probe
from src.pipeline import live_trade_attribution_probe as p


class TestLiveTradeAttributionProbe(unittest.TestCase):
    def test_pairs_only_real_open_close_trades_in_order(self):
        rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-21 10:00:00", "entry_price": 1.0, "is_real_trade": False},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-21 10:01:00", "exit_price": 0.9, "is_real_trade": False},
            {"action": "OPEN", "token": "0xA", "time": "2026-05-21 10:02:00", "entry_price": 1.0, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-21 10:03:00", "exit_price": 1.2, "net_profit": 0.01, "is_real_trade": True},
        ]

        pairs = list(p.pair_real_trades(rows))

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["token"], "0xa")
        self.assertTrue(pairs[0]["open"]["is_real_trade"])
        self.assertTrue(pairs[0]["close"]["is_real_trade"])

    def test_classifies_stop_first_before_later_mfe_as_stop_first_not_mfe_giveback(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        pair = {
            "token": "0xa",
            "symbol": "A",
            "open": {"time": anchor, "entry_price": 1.0, "prob": 0.981, "is_real_trade": True},
            "close": {"time": anchor + dt.timedelta(seconds=120), "exit_price": 0.8, "reason": "STOP_LOSS", "net_profit": -0.01, "is_real_trade": True},
        }
        path = [
            reentry_probe.PricePoint(anchor, 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=5), 0.81, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.30, "buy"),
        ]

        trade = p.score_trade_attribution(pair, path, near_min_prob=0.94, primary_min_prob=0.98)

        self.assertEqual(trade["failure_label"], "stop_first_after_entry")
        self.assertEqual(trade["entry_anchor"]["first_barrier"], "-18")

    def test_classifies_plus_25_before_stop_as_mfe_giveback(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        pair = {
            "token": "0xa",
            "symbol": "A",
            "open": {"time": anchor, "entry_price": 1.0, "prob": 0.981, "is_real_trade": True},
            "close": {"time": anchor + dt.timedelta(seconds=120), "exit_price": 0.8, "reason": "STOP_LOSS", "net_profit": -0.01, "is_real_trade": True},
        }
        path = [
            reentry_probe.PricePoint(anchor, 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=5), 1.26, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 0.80, "sell"),
        ]

        trade = p.score_trade_attribution(pair, path, near_min_prob=0.94, primary_min_prob=0.98)

        self.assertEqual(trade["failure_label"], "mfe_then_giveback")
        self.assertEqual(trade["entry_anchor"]["first_barrier"], "+25")

    def test_preserves_explicit_zero_hold_duration(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        pair = {
            "token": "0xa",
            "symbol": "A",
            "open": {"time": anchor, "entry_price": 1.0, "prob": 0.981, "is_real_trade": True},
            "close": {
                "time": anchor + dt.timedelta(seconds=10),
                "exit_price": 0.9,
                "reason": "ENTRY_SLIPPAGE_PROTECTION",
                "net_profit": -0.01,
                "hold_duration": 0.0,
                "is_real_trade": True,
            },
        }

        trade = p.score_trade_attribution(pair, [], near_min_prob=0.94, primary_min_prob=0.98)

        self.assertEqual(trade["hold_duration_seconds"], 0.0)

    def test_recomputes_near_threshold_from_probability_not_stale_field(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        pair = {
            "token": "0xa",
            "symbol": "A",
            "open": {
                "time": anchor,
                "entry_price": 1.0,
                "prob": 0.95,
                "near_threshold_like": False,
                "is_real_trade": True,
            },
            "close": {"time": anchor + dt.timedelta(seconds=30), "exit_price": 0.9, "reason": "TIME_EXIT", "net_profit": -0.01, "is_real_trade": True},
        }

        trade = p.score_trade_attribution(pair, [], near_min_prob=0.94, primary_min_prob=0.98)

        self.assertTrue(trade["near_threshold_like"])
        self.assertEqual(trade["near_threshold_rule"], "0.94<=prob<0.98")

    def test_entry_slippage_protection_reason_takes_entry_slippage_label(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        pair = {
            "token": "0xa",
            "symbol": "A",
            "open": {"time": anchor, "entry_price": 1.0, "prob": 0.981, "is_real_trade": True},
            "close": {"time": anchor + dt.timedelta(seconds=20), "exit_price": 0.8, "reason": "ENTRY_SLIPPAGE_PROTECTION", "net_profit": -0.01, "is_real_trade": True},
        }
        path = [
            reentry_probe.PricePoint(anchor, 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=5), 0.80, "sell"),
        ]

        trade = p.score_trade_attribution(pair, path, near_min_prob=0.94, primary_min_prob=0.98)

        self.assertEqual(trade["failure_label"], "entry_slippage_failure")

    def test_build_report_sets_read_only_no_live_switch_contract_and_counts_pnl(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        rows = [
            {"action": "OPEN", "token": "0xA", "symbol": "A", "time": anchor.isoformat(sep=" "), "entry_price": 1.0, "prob": 0.95, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xA", "symbol": "A", "time": (anchor + dt.timedelta(seconds=60)).isoformat(sep=" "), "exit_price": 1.1, "reason": "PPO_SELL100", "net_profit": 0.02, "is_real_trade": True},
        ]

        report = p.build_attribution_report(
            trade_rows=rows,
            lifecycles={},
            generated_at=anchor,
            near_min_prob=0.94,
            primary_min_prob=0.98,
        )

        self.assertEqual(report["contract"]["read_only"], True)
        self.assertEqual(report["contract"]["live_switch_evidence"], False)
        self.assertEqual(report["contract"]["safe_for_live_switch"], False)
        self.assertEqual(report["trade_count"], 1)
        self.assertEqual(report["win_count"], 1)
        self.assertAlmostEqual(report["net_profit_bnb"], 0.02)
        self.assertEqual(report["failure_label_counts"], {"profitable_exit": 1})

    def test_build_report_filters_trades_before_restart_anchor(self):
        rows = [
            {"action": "OPEN", "token": "0xOLD", "time": "2026-05-18 23:59:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xOLD", "time": "2026-05-19 00:01:00", "exit_price": 1.2, "reason": "PPO_SELL100", "net_profit": 0.02, "is_real_trade": True},
            {"action": "OPEN", "token": "0xNEW", "time": "2026-05-19 04:03:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xNEW", "time": "2026-05-19 04:04:00", "exit_price": 0.9, "reason": "TIME_EXIT", "net_profit": -0.01, "is_real_trade": True},
        ]

        report = p.build_attribution_report(
            trade_rows=rows,
            lifecycles={},
            restart_anchor="2026-05-19 04:02:23",
        )

        self.assertEqual(report["trade_count"], 1)
        self.assertEqual(report["trade_sample"][0]["token"], "0xnew")


if __name__ == "__main__":
    unittest.main()
