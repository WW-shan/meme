import datetime as dt
import json
import unittest

from src.pipeline import low_volume_breakout_probe as p
from src.pipeline import reentry_probe
from tests.model.timezone_helpers import analysis_timestamp


class TestLowVolumeBreakoutProbe(unittest.TestCase):
    def _signal(self, token, symbol, anchor, **overrides):
        row = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": token,
            "symbol": symbol,
            "time": anchor.isoformat(sep=" "),
            "prob": 0.985,
            "pred_return": 4.0,
            "reason": "entry_volume_30s_below_min",
            "volume_30s": 1.1,
            "price_volatility": 0.09,
            "token_age_seconds": 10.0,
        }
        row.update(overrides)
        return row

    def test_score_marks_clean_low_volume_runner(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xA", "RUN", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.30, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=50), 1.65, "buy"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_runner")
        self.assertEqual(scored["recommended_policy"], "conditional_rescue_probe")
        self.assertEqual(scored["first_barrier"], "+25")
        self.assertEqual(scored["time_to_plus_60_seconds"], 50.0)

    def test_score_marks_low_volume_fakeout_when_stop_hits_first(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xB", "FAKE", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 0.80, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 1.28, "buy"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_fakeout")
        self.assertEqual(scored["recommended_policy"], "skip")
        self.assertEqual(scored["first_barrier"], "-18")

    def test_score_marks_fast_profit_then_stop(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xC", "SPIKE", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=40), 1.27, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=110), 0.78, "sell"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_fast_profit_then_stop")
        self.assertEqual(scored["recommended_policy"], "quick_take_profit_probe")

    def test_score_marks_missing_path(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xD", "MISS", anchor)

        scored = p.score_low_volume_signal(signal, [])

        self.assertEqual(scored["barrier_class"], "missing_path")
        self.assertEqual(scored["recommended_policy"], "skip")

    def test_score_marks_low_volume_flat_when_no_barrier_hits(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal = self._signal("0xE", "FLAT", anchor)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=30), 1.08, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 0.94, "sell"),
        ]

        scored = p.score_low_volume_signal(signal, path)

        self.assertEqual(scored["barrier_class"], "low_volume_flat")
        self.assertEqual(scored["recommended_policy"], "skip")
        self.assertIsNone(scored["first_barrier"])

    def test_build_probe_report_filters_low_volume_rejects_and_deduplicates_by_token(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal_rows = [
            self._signal("0xA", "RUN", anchor, prob=0.981, pred_return=1.0),
            self._signal("0xA", "RUN", anchor + dt.timedelta(seconds=2), prob=0.990, pred_return=2.0),
            self._signal("0xB", "BAD_REASON", anchor, reason="pred_return_below_min"),
            self._signal("0xC", "LOW_PROB", anchor, prob=0.970),
            self._signal("0xD", "LOW_VOLUME", anchor, volume_30s=0.70),
            self._signal("0xE", "HIGH_VOLUME", anchor, volume_30s=1.60),
            self._signal("0xF", "LOW_VOLATILITY", anchor, price_volatility=0.01),
            self._signal("0xG", "OLD", anchor, token_age_seconds=61.0),
            self._signal("0xH", "UNKNOWN_AGE", anchor, token_age_seconds=None),
            self._signal("0xI", "MISSING_AGE", anchor),
            self._signal("0xJ", "NAN_AGE", anchor, token_age_seconds=float("nan")),
            self._signal("0xK", "ACCEPTED", anchor, decision="accepted"),
            self._signal("0xL", "NOT_SIGNAL", anchor, action="MODEL_SCORE"),
        ]
        del signal_rows[9]["token_age_seconds"]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.4, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, since=anchor)

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["candidate_counts"]["raw_rejected_signal_decisions"], 11)
        self.assertEqual(report["candidate_counts"]["filtered_low_volume_signal_decisions"], 2)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 1)
        self.assertEqual(report["candidate_counts"]["dropped_duplicate_low_volume_signals"], 1)
        self.assertEqual(report["class_counts"]["low_volume_runner"], 1)
        self.assertEqual(report["candidate_sample"][0]["prob"], 0.99)
        self.assertEqual(
            report["parameters"],
            {
                "horizon_seconds": 600,
                "max_token_age_seconds": 60,
                "max_volume_30s": 1.5,
                "min_price_volatility": 0.05,
                "min_prob": 0.98,
                "min_volume_30s": 0.75,
                "quick_profit_seconds": 120,
                "since": anchor,
            },
        )
        json.loads(p.to_json_text(report))

    def test_build_probe_report_deduplicates_by_probability_pred_return_then_time(self):
        anchor = dt.datetime(2026, 5, 19, 11, 0, 0)
        signal_rows = [
            self._signal("0xA", "LOW_PRED", anchor, prob=0.99, pred_return=1.0),
            self._signal("0xA", "HIGH_PRED", anchor + dt.timedelta(seconds=1), prob=0.99, pred_return=3.0),
            self._signal("0xB", "EARLY", anchor, prob=0.985, pred_return=5.0),
            self._signal("0xB", "LATE", anchor + dt.timedelta(seconds=2), prob=0.985, pred_return=5.0),
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.4, "type": "buy"},
                ],
            },
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.4, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, since=anchor)

        sample_by_token = {candidate["token"]: candidate for candidate in report["candidate_sample"]}
        self.assertEqual(sample_by_token["0xa"]["symbol"], "HIGH_PRED")
        self.assertEqual(sample_by_token["0xb"]["symbol"], "LATE")


if __name__ == "__main__":
    unittest.main()
