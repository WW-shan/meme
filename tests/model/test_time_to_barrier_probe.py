import datetime as dt
import json
import unittest

from src.pipeline import reentry_probe
from src.pipeline import time_to_barrier_probe as p


class TestTimeToBarrierProbe(unittest.TestCase):
    def test_score_signal_marks_fast_profit_before_later_collapse(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xA",
            "symbol": "FAST",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.99,
            "pred_return": 25.0,
            "reason": "pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.26, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 0.80, "sell"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "fast_profit_then_collapse")
        self.assertEqual(scored["recommended_policy"], "quick_take_profit")
        self.assertEqual(scored["first_barrier"], "+25")
        self.assertEqual(scored["time_to_plus_25_seconds"], 20.0)
        self.assertEqual(scored["time_to_minus_18_seconds"], 90.0)
        self.assertTrue(scored["quick_take_profit_candidate"])
        self.assertFalse(scored["slow_runner_candidate"])

    def test_score_signal_marks_stop_first_as_collapse_skip(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xB",
            "symbol": "BAD",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.97,
            "pred_return": 8.0,
            "reason": "near_threshold_pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=12), 0.81, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=50), 1.30, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "stop_first")
        self.assertEqual(scored["recommended_policy"], "skip")
        self.assertEqual(scored["first_barrier"], "-18")
        self.assertFalse(scored["quick_take_profit_candidate"])

    def test_score_signal_marks_slow_runner_without_stop(self):
        anchor = dt.datetime(2026, 5, 19, 9, 32, 52)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xC",
            "symbol": "SLOW",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.978,
            "pred_return": 11.0,
            "reason": "near_threshold_pred_return_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=300), 1.30, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=540), 1.65, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["barrier_class"], "slow_runner")
        self.assertEqual(scored["recommended_policy"], "conditional_slow_hold")
        self.assertTrue(scored["slow_runner_candidate"])
        self.assertEqual(scored["time_to_plus_25_seconds"], 300.0)
        self.assertEqual(scored["time_to_plus_60_seconds"], 540.0)

    def test_score_signal_marks_missing_path(self):
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xD",
            "symbol": "MISS",
            "time": "2026-05-19 04:11:18",
            "prob": 0.99,
            "pred_return": 30.0,
            "reason": "pred_return_below_min",
        }

        scored = p.score_signal_time_to_barrier(signal, [])

        self.assertEqual(scored["barrier_class"], "missing_path")
        self.assertEqual(scored["recommended_policy"], "skip")

    def test_build_probe_report_deduplicates_by_token_and_counts_classes(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xA",
                "symbol": "A",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.95,
                "pred_return": 5.0,
                "reason": "near_threshold_pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xA",
                "symbol": "A",
                "time": (anchor + dt.timedelta(seconds=2)).isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 25.0,
                "reason": "pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xB",
                "symbol": "B",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.96,
                "pred_return": 7.0,
                "reason": "near_threshold_pred_return_below_min",
            },
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": (anchor + dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 1.3, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=100)).timestamp(), "price": 0.8, "type": "sell"},
                ],
            },
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": (anchor - dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=10)).timestamp(), "price": 0.8, "type": "sell"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["candidate_counts"]["signal_decisions"], 3)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 2)
        self.assertEqual(report["candidate_counts"]["dropped_duplicate_signal_decisions"], 1)
        self.assertEqual(report["class_counts"]["fast_profit_then_collapse"], 1)
        self.assertEqual(report["class_counts"]["stop_first"], 1)
        json.loads(p.to_json_text(report))

    def test_build_probe_report_filters_signals_before_since_time(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xOLD",
                "symbol": "OLD",
                "time": (anchor - dt.timedelta(seconds=1)).isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 30.0,
                "reason": "pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xNEW",
                "symbol": "NEW",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 25.0,
                "reason": "pred_return_below_min",
            },
        ]
        lifecycles = {
            "0xnew": {
                "token_address": "0xNEW",
                "price_history": [
                    {"timestamp": (anchor - dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=20)).timestamp(), "price": 1.3, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, since=anchor)

        self.assertEqual(report["candidate_counts"]["signal_decisions"], 1)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 1)
        self.assertEqual(report["candidate_sample"][0]["symbol"], "NEW")

    def test_build_probe_report_default_generated_at_uses_analysis_timezone(self):
        fixed = dt.datetime(2026, 5, 19, 3, 13, 3, tzinfo=dt.timezone.utc)

        class FixedDateTime(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return fixed.replace(tzinfo=None)
                return fixed.astimezone(tz)

        original_datetime = p.dt.datetime
        try:
            p.dt.datetime = FixedDateTime
            report = p.build_probe_report(signal_rows=[], lifecycles={})
        finally:
            p.dt.datetime = original_datetime

        self.assertEqual(report["generated_at"], dt.datetime(2026, 5, 19, 11, 13, 3))


if __name__ == "__main__":
    unittest.main()
