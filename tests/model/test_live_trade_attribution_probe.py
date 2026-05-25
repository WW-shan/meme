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

    def test_build_report_can_disable_restart_anchor_filter(self):
        rows = [
            {"action": "OPEN", "token": "0xOLD", "time": "2026-05-18 23:59:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xOLD", "time": "2026-05-19 00:01:00", "exit_price": 1.2, "reason": "PPO_SELL100", "net_profit": 0.02, "is_real_trade": True},
            {"action": "OPEN", "token": "0xNEW", "time": "2026-05-19 04:03:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xNEW", "time": "2026-05-19 04:04:00", "exit_price": 0.9, "reason": "TIME_EXIT", "net_profit": -0.01, "is_real_trade": True},
        ]

        report = p.build_attribution_report(
            trade_rows=rows,
            lifecycles={},
            restart_anchor=None,
        )

        self.assertEqual(report["trade_count"], 2)
        self.assertEqual(report["parameters"]["restart_anchor_applied"], False)

    def test_build_report_default_does_not_apply_hardcoded_restart_anchor(self):
        rows = [
            {"action": "OPEN", "token": "0xOLD", "time": "2026-05-18 23:59:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xOLD", "time": "2026-05-19 00:01:00", "exit_price": 1.2, "reason": "PPO_SELL100", "net_profit": 0.02, "is_real_trade": True},
            {"action": "OPEN", "token": "0xNEW", "time": "2026-05-19 04:03:00", "entry_price": 1.0, "prob": 0.99, "is_real_trade": True},
            {"action": "CLOSE", "token": "0xNEW", "time": "2026-05-19 04:04:00", "exit_price": 0.9, "reason": "TIME_EXIT", "net_profit": -0.01, "is_real_trade": True},
        ]

        report = p.build_attribution_report(
            trade_rows=rows,
            lifecycles={},
        )

        self.assertEqual(report["trade_count"], 2)
        self.assertEqual(report["restart_anchor"], None)
        self.assertEqual(report["parameters"]["restart_anchor_applied"], False)

    def test_build_report_default_is_model_agnostic(self):
        report = p.build_attribution_report(trade_rows=[], lifecycles={})

        self.assertIsNone(report["active_model"])

    def test_build_report_includes_rejected_signal_paths_and_ranked_directions(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        rows = [
            {"action": "OPEN", "token": "0xA", "symbol": "A", "time": anchor.isoformat(sep=" "), "entry_price": 1.0, "prob": 0.95, "is_real_trade": True},
            {
                "action": "CLOSE",
                "token": "0xA",
                "symbol": "A",
                "time": (anchor + dt.timedelta(seconds=120)).isoformat(sep=" "),
                "exit_price": 0.9,
                "reason": "TIME_EXIT",
                "net_profit": -0.02,
                "is_real_trade": True,
            },
        ]
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xB",
                "symbol": "B",
                "time": (anchor + dt.timedelta(seconds=10)).isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 30.0,
                "reason": "pred_return_below_min",
            }
        ]
        lifecycles = {
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": (anchor + dt.timedelta(seconds=5)).isoformat(sep=" "), "price": 1.0, "type": "anchor"},
                    {"timestamp": (anchor + dt.timedelta(seconds=35)).isoformat(sep=" "), "price": 1.3, "type": "buy"},
                ],
            }
        }

        report = p.build_attribution_report(
            trade_rows=rows,
            signal_rows=signal_rows,
            lifecycles=lifecycles,
            generated_at=anchor,
            since=anchor,
            until=anchor + dt.timedelta(seconds=60),
            minimum_same_shape_trades=1,
            max_candidate_sample=0,
        )

        self.assertEqual(report["rejected_signal_paths"]["class_counts"], {"fast_profit": 1})
        self.assertEqual(report["rejected_signal_paths"]["parameters"]["since"], anchor)
        self.assertEqual(report["rejected_signal_paths"]["parameters"]["until"], anchor + dt.timedelta(seconds=60))
        ranked = report["ranked_directions"]
        self.assertGreaterEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["source"], "live_trade_failure")
        self.assertEqual(ranked[0]["bucket"], "dead_flow_timeout")
        self.assertAlmostEqual(ranked[0]["sort_loss_bnb"], 0.02)
        expected_keys = {
            "direction_id",
            "source",
            "bucket",
            "count",
            "sort_loss_bnb",
            "sort_opportunity_count",
            "meets_minimum_same_shape_count",
            "evidence_value",
            "evidence_unit",
            "policy_hint",
        }
        self.assertTrue(expected_keys.issubset(ranked[0]))
        self.assertNotIn("evidence_score", ranked[0])
        self.assertEqual(ranked[0]["evidence_unit"], "bnb_loss")
        self.assertTrue(
            any(
                direction["source"] == "rejected_signal_path"
                and direction["bucket"] == "fast_profit"
                and direction["policy_hint"] == "quick_take_profit"
                and direction["evidence_unit"] == "candidate_count"
                for direction in ranked
            )
        )

    def test_markdown_renders_rejected_paths_and_ranked_directions(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        report = p.build_attribution_report(
            trade_rows=[],
            signal_rows=[
                {
                    "action": "SIGNAL_DECISION",
                    "decision": "rejected",
                    "token": "0xB",
                    "time": anchor.isoformat(sep=" "),
                    "prob": 0.99,
                    "pred_return": 30.0,
                    "reason": "pred_return_below_min",
                }
            ],
            lifecycles={},
            generated_at=anchor,
            minimum_same_shape_trades=1,
        )

        markdown = p.to_markdown_text(report)

        self.assertIn("## Rejected Signal Paths", markdown)
        self.assertIn("## Ranked Directions", markdown)
        self.assertIn("- Ranked directions total:", markdown)
        self.assertIn("```json", markdown)
        self.assertIn("missing_path", markdown)

    def test_ranked_directions_do_not_treat_skip_paths_as_actionable_support(self):
        anchor = dt.datetime(2026, 5, 21, 10, 0, 0)
        report = p.build_attribution_report(
            trade_rows=[],
            signal_rows=[
                {
                    "action": "SIGNAL_DECISION",
                    "decision": "rejected",
                    "token": "0xMISSING",
                    "time": anchor.isoformat(sep=" "),
                    "prob": 0.99,
                    "pred_return": 30.0,
                    "reason": "pred_return_below_min",
                }
            ],
            lifecycles={},
            generated_at=anchor,
            minimum_same_shape_trades=1,
        )

        skip_directions = [
            direction
            for direction in report["ranked_directions"]
            if direction["policy_hint"] == "skip"
        ]

        self.assertTrue(skip_directions)
        self.assertTrue(all(direction["evidence_value"] == 0.0 for direction in skip_directions))
        self.assertTrue(all(direction["sort_opportunity_count"] == 0 for direction in skip_directions))
        self.assertTrue(all(not direction["meets_minimum_same_shape_count"] for direction in skip_directions))


if __name__ == "__main__":
    unittest.main()
