import datetime as dt
import json
import unittest

from src.pipeline import reentry_probe
from src.pipeline import post_target_exit_state_probe as p


class TestPostTargetExitStateProbe(unittest.TestCase):
    def test_scores_hit_then_collapse_as_lock_profit(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        path = [
            reentry_probe.PricePoint(anchor, 1.00, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=225), 1.26, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=240), 1.18, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=260), 0.82, "sell"),
        ]

        result = p.score_trade_post_target_exit_state(
            {"token": "0xA", "symbol": "CMC", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token_address": "0xA", "price_history": []},
            path=path,
            target_pct=0.25,
            continuation_pct=0.60,
            collapse_pct=-0.18,
        )

        self.assertEqual(result["classification"], "post_target_collapse")
        self.assertEqual(result["recommended_policy"], "lock_profit")
        self.assertTrue(result["target_hit"])
        self.assertEqual(result["time_to_target_seconds"], 225.0)
        self.assertEqual(result["time_to_post_target_collapse_seconds"], 260.0)

    def test_scores_continuation_before_collapse_as_continue_hold(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        path = [
            reentry_probe.PricePoint(anchor, 1.00, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.25, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=55), 1.62, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=120), 0.80, "sell"),
        ]

        result = p.score_trade_post_target_exit_state(
            {"token": "0xB", "symbol": "RUN", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token_address": "0xB", "price_history": []},
            path=path,
            target_pct=0.25,
            continuation_pct=0.60,
            collapse_pct=-0.18,
        )

        self.assertEqual(result["classification"], "post_target_continuation")
        self.assertEqual(result["recommended_policy"], "continue_hold")
        self.assertEqual(result["time_to_target_seconds"], 30.0)
        self.assertEqual(result["time_to_continuation_seconds"], 55.0)
        self.assertEqual(result["time_to_post_target_collapse_seconds"], 120.0)

    def test_scores_target_not_hit_as_no_action(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        path = [
            reentry_probe.PricePoint(anchor, 1.00, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.12, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=60), 1.03, "sell"),
        ]

        result = p.score_trade_post_target_exit_state(
            {"token": "0xC", "symbol": "FLAT", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token_address": "0xC", "price_history": []},
            path=path,
            target_pct=0.25,
        )

        self.assertEqual(result["classification"], "target_not_hit")
        self.assertEqual(result["recommended_policy"], "no_action")
        self.assertFalse(result["target_hit"])

    def test_scores_target_hit_without_continuation_or_collapse_as_unresolved(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        path = [
            reentry_probe.PricePoint(anchor, 1.00, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.27, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=120), 1.35, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=240), 1.28, "sell"),
        ]

        result = p.score_trade_post_target_exit_state(
            {"token": "0xU", "symbol": "UNRES", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token_address": "0xU", "price_history": []},
            path=path,
            target_pct=0.25,
            continuation_pct=0.60,
            collapse_pct=-0.18,
        )

        self.assertEqual(result["classification"], "post_target_unresolved")
        self.assertEqual(result["recommended_policy"], "monitor_after_target")
        self.assertTrue(result["target_hit"])
        self.assertIsNone(result["time_to_continuation_seconds"])
        self.assertIsNone(result["time_to_post_target_collapse_seconds"])

    def test_post_target_window_returns_do_not_read_beyond_horizon(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        path = [
            reentry_probe.PricePoint(anchor, 1.00, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 1.30, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=105), 1.80, "buy"),
        ]

        result = p.score_trade_post_target_exit_state(
            {"token": "0xH", "symbol": "HORIZ", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token_address": "0xH", "price_history": []},
            path=path,
            target_pct=0.25,
            continuation_pct=0.60,
            horizon_seconds=100.0,
            post_target_windows=(15.0,),
        )

        self.assertEqual(result["classification"], "post_target_unresolved")
        self.assertEqual(result["post_target_window_returns_pct"]["15"], 30.0)

    def test_uses_lifecycle_path_and_reports_post_target_window_returns_and_flow(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        lifecycle = {
            "token_address": "0xD",
            "price_history": [
                {"timestamp": anchor.timestamp(), "price": 1.0, "type": "buy"},
                {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 1.25, "type": "buy"},
                {"timestamp": (anchor + dt.timedelta(seconds=45)).timestamp(), "price": 1.40, "type": "buy"},
                {"timestamp": (anchor + dt.timedelta(seconds=90)).timestamp(), "price": 1.65, "type": "buy"},
            ],
            "buys": [
                {"timestamp": (anchor + dt.timedelta(seconds=10)).timestamp(), "bnb_amount": 2.0},
                {"timestamp": (anchor + dt.timedelta(seconds=20)).timestamp(), "bnb_amount": 1.0},
            ],
            "sells": [
                {"timestamp": (anchor + dt.timedelta(seconds=25)).timestamp(), "bnb_amount": 1.0},
            ],
        }

        result = p.score_trade_post_target_exit_state(
            {"token": "0xD", "symbol": "FLOW", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            lifecycle,
            target_pct=0.25,
            post_target_windows=(15.0, 60.0),
        )

        self.assertEqual(result["classification"], "post_target_continuation")
        self.assertEqual(result["post_target_window_returns_pct"]["15"], 40.0)
        self.assertEqual(result["post_target_window_returns_pct"]["60"], 65.0)
        self.assertEqual(result["flow"]["flow_event_count"], 3)
        self.assertAlmostEqual(result["flow"]["pre_buy_pressure"], 0.75)

    def test_build_probe_report_contract_counts_and_json(self):
        anchor = dt.datetime(2026, 5, 21, 2, 10, 0)
        trades = [
            {"token": "0xA", "symbol": "CMC", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
            {"token": "0xB", "symbol": "FLAT", "entry_time": anchor.isoformat(sep=" "), "entry_price": 1.0},
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": anchor.timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 1.25, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=60)).timestamp(), "price": 0.80, "type": "sell"},
                ],
            },
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": anchor.timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 1.10, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(trades=trades, lifecycles=lifecycles)

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertTrue(report["probe_contract"]["requires_replay_before_live_change"])
        self.assertEqual(report["candidate_counts"]["trade_log_rows"], 2)
        self.assertEqual(report["class_counts"]["post_target_collapse"], 1)
        self.assertEqual(report["class_counts"]["post_target_continuation"], 0)
        self.assertEqual(report["class_counts"]["post_target_unresolved"], 0)
        self.assertEqual(report["class_counts"]["target_not_hit"], 1)
        self.assertEqual(report["policy_counts"]["lock_profit"], 1)
        self.assertEqual(report["policy_counts"]["continue_hold"], 0)
        self.assertEqual(report["policy_counts"]["monitor_after_target"], 0)
        json.loads(p.to_json_text(report))


if __name__ == "__main__":
    unittest.main()
