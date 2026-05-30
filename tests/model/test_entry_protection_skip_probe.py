import datetime as dt
import unittest

from src.pipeline import entry_protection_skip_probe as p
from src.pipeline import reentry_probe


class TestEntryProtectionSkipProbe(unittest.TestCase):
    def test_scores_missed_within_hold_profit_before_stop(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        skip = {
            "action": "ENTRY_PRICE_PROTECTION_SKIP",
            "token": "0xA",
            "symbol": "AAA",
            "time": anchor,
            "signal_price": 1.0,
            "candidate_price": 1.5,
            "entry_slippage_pct": 0.5,
        }
        path = [
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=5), 1.6, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.9, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 1.1, "sell"),
        ]

        scored = p.score_skip_event(skip, path, max_hold_seconds=120, horizon_seconds=300)

        self.assertEqual(scored["within_hold_label"], "missed_within_hold_profit")
        self.assertEqual(scored["extended_label"], "profit_within_hold")
        self.assertTrue(scored["supports_relaxing_entry_protection"])
        self.assertAlmostEqual(scored["signal_to_candidate_jump_pct"], 50.0)
        self.assertAlmostEqual(scored["reported_entry_slippage_pct"], 50.0)

    def test_scores_late_profit_after_hold_as_not_relaxation_support(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        skip = {
            "action": "ENTRY_PRICE_PROTECTION_SKIP",
            "token": "0xB",
            "symbol": "BBB",
            "time": anchor,
            "signal_price": 1.0,
            "candidate_price": 2.0,
            "entry_slippage_pct": 1.0,
        }
        path = [
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=60), 2.02, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=620), 2.7, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=900), 1.0, "sell"),
        ]

        scored = p.score_skip_event(skip, path, max_hold_seconds=560, horizon_seconds=1200)

        self.assertEqual(scored["within_hold_label"], "protected_flat_timeout")
        self.assertEqual(scored["extended_label"], "late_profit_after_hold")
        self.assertFalse(scored["supports_relaxing_entry_protection"])
        self.assertAlmostEqual(scored["timeout_point"]["return_pct"], 1.0)

    def test_build_report_rejects_when_support_below_min(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        signal_rows = [
            {
                "action": "ENTRY_PRICE_PROTECTION_SKIP",
                "token": "0xA",
                "symbol": "AAA",
                "time": anchor.isoformat(sep=" "),
                "signal_price": 1.0,
                "candidate_price": 2.0,
                "entry_slippage_pct": 1.0,
            }
        ]
        lifecycles = {
            "0xA": {
                "token_address": "0xA",
                "symbol": "AAA",
                "price_history": [
                    {"timestamp": (anchor + dt.timedelta(seconds=60)).isoformat(sep=" "), "price": 2.02, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=620)).isoformat(sep=" "), "price": 2.7, "type": "buy"},
                ],
            }
        }

        report = p.build_skip_outcome_report(
            signal_rows=signal_rows,
            lifecycles=lifecycles,
            generated_at=anchor,
            max_hold_seconds=560,
            horizon_seconds=1200,
            min_support=2,
            max_sample=0,
        )

        self.assertEqual(report["summary"]["skip_count"], 1)
        self.assertEqual(report["summary"]["supports_relaxing_entry_protection_count"], 0)
        self.assertEqual(report["summary"]["extended_label_counts"], {"late_profit_after_hold": 1})
        self.assertEqual(report["decision"]["outcome_tier"], "Rejected")
        self.assertFalse(report["contract"]["live_switch_evidence"])


if __name__ == "__main__":
    unittest.main()
