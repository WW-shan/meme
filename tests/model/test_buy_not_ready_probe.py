import datetime as dt
import unittest

from src.pipeline import buy_not_ready_probe as p
from src.pipeline import reentry_probe


class TestBuyNotReadyProbe(unittest.TestCase):
    def test_scores_missed_within_hold_profit_before_stop(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        event = {
            "action": "BUY_NOT_READY",
            "token": "0xA",
            "symbol": "AAA",
            "time": anchor,
            "reason": "Unsupported quote asset: 0xQuote",
            "token_quote": "0xQuote",
            "signal_price": 1.0,
            "prob": 0.97,
            "pred_return": 42.0,
        }
        path = [
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=5), 1.05, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.3, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 0.9, "sell"),
        ]

        scored = p.score_buy_not_ready_event(event, path, max_hold_seconds=120, horizon_seconds=300)

        self.assertEqual(scored["within_hold_label"], "missed_within_hold_profit")
        self.assertEqual(scored["extended_label"], "profit_within_hold")
        self.assertTrue(scored["supports_quote_universe_research"])
        self.assertEqual(scored["anchor_price_source"], "signal_price")
        self.assertEqual(scored["token_quote"], "0xQuote")

    def test_scores_late_profit_after_hold_as_not_support(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        event = {
            "action": "BUY_NOT_READY",
            "token": "0xB",
            "symbol": "BBB",
            "time": anchor,
            "reason": "Unsupported quote asset: 0xQuote",
            "token_quote": "0xQuote",
            "signal_price": 2.0,
        }
        path = [
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=60), 2.02, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=620), 2.7, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=900), 1.0, "sell"),
        ]

        scored = p.score_buy_not_ready_event(event, path, max_hold_seconds=560, horizon_seconds=1200)

        self.assertEqual(scored["within_hold_label"], "guarded_flat_timeout")
        self.assertEqual(scored["extended_label"], "late_profit_after_hold")
        self.assertFalse(scored["supports_quote_universe_research"])
        self.assertAlmostEqual(scored["timeout_point"]["return_pct"], 1.0)

    def test_build_report_rejects_when_support_below_min(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        signal_rows = [
            {
                "action": "BUY_NOT_READY",
                "token": "0xA",
                "symbol": "AAA",
                "time": anchor.isoformat(sep=" "),
                "reason": "Unsupported quote asset: 0xQuote",
                "token_quote": "0xQuote",
                "signal_price": 1.0,
            }
        ]
        lifecycles = {
            "0xA": {
                "token_address": "0xA",
                "symbol": "AAA",
                "price_history": [
                    {"timestamp": (anchor + dt.timedelta(seconds=60)).isoformat(sep=" "), "price": 1.02, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=620)).isoformat(sep=" "), "price": 1.4, "type": "buy"},
                ],
            }
        }

        report = p.build_buy_not_ready_outcome_report(
            signal_rows=signal_rows,
            lifecycles=lifecycles,
            generated_at=anchor,
            max_hold_seconds=560,
            horizon_seconds=1200,
            min_support=2,
            max_sample=0,
        )

        self.assertEqual(report["summary"]["event_count"], 1)
        self.assertEqual(report["summary"]["supports_quote_universe_research_count"], 0)
        self.assertEqual(report["summary"]["token_quote_counts"], {"0xQuote": 1})
        self.assertEqual(report["summary"]["extended_label_counts"], {"late_profit_after_hold": 1})
        self.assertEqual(report["decision"]["outcome_tier"], "Rejected")
        self.assertFalse(report["contract"]["live_switch_evidence"])

    def test_reason_filter_is_configurable(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        rows = [
            {"action": "BUY_NOT_READY", "token": "0xA", "time": anchor, "reason": "Unsupported quote asset: 0xQuote"},
            {"action": "BUY_NOT_READY", "token": "0xB", "time": anchor, "reason": "Helper query failed"},
        ]

        unsupported_only = list(p.iter_buy_not_ready_events(rows))
        all_events = list(p.iter_buy_not_ready_events(rows, reason_contains=None))

        self.assertEqual([row["token"] for row in unsupported_only], ["0xa"])
        self.assertEqual([row["token"] for row in all_events], ["0xa", "0xb"])


if __name__ == "__main__":
    unittest.main()
