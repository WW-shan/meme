import datetime as dt
import json
import unittest

from src.pipeline import reentry_probe
from src.pipeline import time_to_barrier_probe as p
from tests.model.timezone_helpers import analysis_timestamp


DECISION_FEATURE_FIELDS = {
    "volume_30s": 123.4,
    "price_volatility": 0.056,
    "token_age_seconds": 87.0,
    "feature_count": 42,
    "features_hash": "abc123",
    "entry_ranking_mode": "near_threshold",
    "near_threshold_rescue_used": True,
    "use_pred_return_filter": False,
    "min_pred_return": 20.0,
    "min_entry_volume_30s": 100.0,
    "min_entry_price_volatility": 0.02,
    "buy_near_threshold_min_prob": 0.97,
    "buy_near_min_pred_return": 8.0,
    "buy_near_min_entry_volume_30s": 60.0,
    "buy_near_min_entry_price_volatility": 0.01,
    "buy_near_min_age_seconds": 30.0,
}


def _rejected_signal_rows(count, *, anchor=None):
    if anchor is None:
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
    return [
        {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": f"0xTOKEN{index:03d}",
            "symbol": f"T{index:03d}",
            "time": (anchor + dt.timedelta(seconds=index)).isoformat(sep=" "),
            "prob": 0.99,
            "pred_return": 30.0,
            "reason": "pred_return_below_min",
        }
        for index in range(count)
    ]


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

    def test_score_signal_copies_decision_time_fields_and_aliases(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xFEATURES",
            "symbol": "FEATURES",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.99,
            "pred_return": 25.0,
            "reason": "pred_return_below_min",
            **DECISION_FEATURE_FIELDS,
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.26, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        for key, value in DECISION_FEATURE_FIELDS.items():
            self.assertIn(key, scored)
            self.assertEqual(scored[key], value)
        self.assertIn("entry_volume_30s", scored)
        self.assertIn("entry_price_volatility", scored)
        self.assertIn("age_seconds", scored)
        self.assertEqual(scored["entry_volume_30s"], DECISION_FEATURE_FIELDS["volume_30s"])
        self.assertEqual(scored["entry_price_volatility"], DECISION_FEATURE_FIELDS["price_volatility"])
        self.assertEqual(scored["age_seconds"], DECISION_FEATURE_FIELDS["token_age_seconds"])

    def test_score_signal_copies_decision_time_fields_and_aliases_for_missing_path(self):
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xMISSFEATURES",
            "symbol": "MISSFEATURES",
            "time": "2026-05-19 04:11:18",
            "prob": 0.99,
            "pred_return": 30.0,
            "reason": "pred_return_below_min",
            **DECISION_FEATURE_FIELDS,
        }

        scored = p.score_signal_time_to_barrier(signal, [])

        self.assertEqual(scored["barrier_class"], "missing_path")
        for key, value in DECISION_FEATURE_FIELDS.items():
            self.assertIn(key, scored)
            self.assertEqual(scored[key], value)
        self.assertIn("entry_volume_30s", scored)
        self.assertIn("entry_price_volatility", scored)
        self.assertIn("age_seconds", scored)
        self.assertEqual(scored["entry_volume_30s"], DECISION_FEATURE_FIELDS["volume_30s"])
        self.assertEqual(scored["entry_price_volatility"], DECISION_FEATURE_FIELDS["price_volatility"])
        self.assertEqual(scored["age_seconds"], DECISION_FEATURE_FIELDS["token_age_seconds"])

    def test_score_signal_normalizes_alias_only_decision_time_fields(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xALIAS",
            "symbol": "ALIAS",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.99,
            "pred_return": 25.0,
            "reason": "pred_return_below_min",
            "entry_volume_30s": 12.5,
            "entry_price_volatility": 0.12,
            "age_seconds": 45.0,
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.26, "buy"),
        ]

        scored = p.score_signal_time_to_barrier(signal, path)

        self.assertEqual(scored["volume_30s"], 12.5)
        self.assertEqual(scored["entry_volume_30s"], 12.5)
        self.assertEqual(scored["price_volatility"], 0.12)
        self.assertEqual(scored["entry_price_volatility"], 0.12)
        self.assertEqual(scored["token_age_seconds"], 45.0)
        self.assertEqual(scored["age_seconds"], 45.0)

    def test_score_signal_preserves_explicit_alias_values_when_both_names_exist(self):
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xBOTH",
            "symbol": "BOTH",
            "time": "2026-05-19 04:11:18",
            "prob": 0.99,
            "pred_return": 25.0,
            "reason": "pred_return_below_min",
            "volume_30s": 1.0,
            "entry_volume_30s": 2.0,
            "price_volatility": 0.1,
            "entry_price_volatility": 0.2,
            "token_age_seconds": 30.0,
            "age_seconds": 40.0,
        }

        scored = p.score_signal_time_to_barrier(signal, [])

        self.assertEqual(scored["volume_30s"], 1.0)
        self.assertEqual(scored["entry_volume_30s"], 2.0)
        self.assertEqual(scored["price_volatility"], 0.1)
        self.assertEqual(scored["entry_price_volatility"], 0.2)
        self.assertEqual(scored["token_age_seconds"], 30.0)
        self.assertEqual(scored["age_seconds"], 40.0)

    def test_score_signal_preserves_falsey_decision_time_fields(self):
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xFALSEY",
            "symbol": "FALSEY",
            "time": "2026-05-19 04:11:18",
            "prob": 0.0,
            "pred_return": 0.0,
            "reason": "pred_return_below_min",
            "volume_30s": 0.0,
            "price_volatility": 0.0,
            "token_age_seconds": 0.0,
            "near_threshold_rescue_used": False,
            "use_pred_return_filter": False,
            "min_pred_return": 0.0,
        }

        scored = p.score_signal_time_to_barrier(signal, [])

        self.assertEqual(scored["volume_30s"], 0.0)
        self.assertEqual(scored["entry_volume_30s"], 0.0)
        self.assertEqual(scored["price_volatility"], 0.0)
        self.assertEqual(scored["entry_price_volatility"], 0.0)
        self.assertEqual(scored["token_age_seconds"], 0.0)
        self.assertEqual(scored["age_seconds"], 0.0)
        self.assertFalse(scored["near_threshold_rescue_used"])
        self.assertFalse(scored["use_pred_return_filter"])
        self.assertEqual(scored["min_pred_return"], 0.0)

    def test_score_signal_adds_causal_signal_time_flow_fields_from_lifecycle(self):
        anchor = dt.datetime(2026, 5, 21, 15, 29, 25)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xFLOW",
            "symbol": "FLOW",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.987,
            "pred_return": 39.0,
            "reason": "entry_volume_30s_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.30, "buy"),
        ]
        lifecycle = {
            "token_address": "0xFLOW",
            "buys": [
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=5)), "account": "0xA", "bnb_amount": 2.0},
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=20)), "account": "0xB", "bnb_amount": 1.0},
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=40)), "account": "0xC", "bnb_amount": 0.5},
                {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=1)), "account": "0xFUTURE", "bnb_amount": 9.0},
            ],
            "sells": [
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=8)), "account": "0xD", "bnb_amount": 0.5},
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=45)), "account": "0xB", "bnb_amount": 0.2},
                {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=2)), "account": "0xA", "bnb_amount": 10.0},
            ],
        }

        scored = p.score_signal_time_to_barrier(signal, path, lifecycle=lifecycle)

        self.assertEqual(scored["flow_buy_volume_10s"], 2.0)
        self.assertEqual(scored["flow_sell_volume_10s"], 0.5)
        self.assertAlmostEqual(scored["flow_sell_pressure_10s"], 0.2)
        self.assertAlmostEqual(scored["flow_buy_sell_ratio_10s"], 4.0)
        self.assertEqual(scored["flow_buy_volume_30s"], 3.0)
        self.assertEqual(scored["flow_sell_volume_30s"], 0.5)
        self.assertAlmostEqual(scored["flow_signed_imbalance_30s"], (3.0 - 0.5) / 3.5)
        self.assertEqual(scored["flow_event_count_30s"], 3)
        self.assertEqual(scored["flow_buy_volume_60s"], 3.5)
        self.assertEqual(scored["flow_sell_volume_60s"], 0.7)
        self.assertAlmostEqual(scored["flow_buy_sell_overlap_ratio_60s"], 1.0 / 3.0)
        self.assertAlmostEqual(scored["flow_recent_seller_reentry_ratio_30s"], 0.5)
        self.assertAlmostEqual(scored["flow_buyer_set_churn_10s_vs_prev50s"], 1.0)

    def test_build_probe_report_passes_lifecycle_to_signal_flow_scoring(self):
        anchor = dt.datetime(2026, 5, 21, 15, 29, 25)
        signal_rows = [{
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xFLOW",
            "symbol": "FLOW",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.987,
            "pred_return": 39.0,
            "reason": "entry_volume_30s_below_min",
        }]
        lifecycles = {
            "0xflow": {
                "token_address": "0xFLOW",
                "buys": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=5)), "account": "0xA", "bnb_amount": 1.0},
                ],
                "sells": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=5)), "account": "0xB", "bnb_amount": 3.0},
                ],
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.3, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles)

        row = report["candidate_sample"][0]
        self.assertEqual(row["flow_buy_volume_10s"], 1.0)
        self.assertEqual(row["flow_sell_volume_10s"], 3.0)
        self.assertAlmostEqual(row["flow_sell_pressure_10s"], 0.75)

    def test_score_signal_uses_none_for_buy_sell_ratio_when_no_sells_exist(self):
        anchor = dt.datetime(2026, 5, 21, 15, 29, 25)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xNOSELL",
            "symbol": "NOSELL",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.987,
            "pred_return": 39.0,
            "reason": "entry_volume_30s_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.30, "buy"),
        ]
        lifecycle = {
            "token_address": "0xNOSELL",
            "buys": [
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=5)), "account": "0xA", "bnb_amount": 2.0},
            ],
            "sells": [],
        }

        scored = p.score_signal_time_to_barrier(signal, path, lifecycle=lifecycle)

        self.assertEqual(scored["flow_buy_volume_10s"], 2.0)
        self.assertEqual(scored["flow_sell_volume_10s"], 0.0)
        self.assertEqual(scored["flow_buy_sell_ratio_10s"], None)
        self.assertEqual(scored["flow_sell_pressure_10s"], 0.0)
        self.assertEqual(scored["flow_buy_sell_overlap_ratio_60s"], 0.0)
        self.assertEqual(scored["flow_recent_seller_reentry_ratio_30s"], 0.0)

    def test_score_signal_uses_zero_flow_overlap_for_empty_buyer_denominators(self):
        anchor = dt.datetime(2026, 5, 21, 15, 29, 25)
        signal = {
            "action": "SIGNAL_DECISION",
            "decision": "rejected",
            "token": "0xSELLONLY",
            "symbol": "SELLONLY",
            "time": anchor.isoformat(sep=" "),
            "prob": 0.987,
            "pred_return": 39.0,
            "reason": "entry_volume_30s_below_min",
        }
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=20), 1.30, "buy"),
        ]
        lifecycle = {
            "token_address": "0xSELLONLY",
            "buys": [],
            "sells": [
                {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=5)), "account": "0xA", "bnb_amount": 2.0},
            ],
        }

        scored = p.score_signal_time_to_barrier(signal, path, lifecycle=lifecycle)

        self.assertEqual(scored["flow_event_count_30s"], 1)
        self.assertEqual(scored["flow_buy_sell_overlap_ratio_60s"], 0.0)
        self.assertEqual(scored["flow_recent_seller_reentry_ratio_30s"], 0.0)
        self.assertEqual(scored["flow_buyer_set_churn_10s_vs_prev50s"], 0.0)

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
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=30)), "price": 1.3, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=100)), "price": 0.8, "type": "sell"},
                ],
            },
            "0xb": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=10)), "price": 0.8, "type": "sell"},
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
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.3, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, since=anchor)

        self.assertEqual(report["candidate_counts"]["signal_decisions"], 1)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 1)
        self.assertEqual(report["candidate_sample"][0]["symbol"], "NEW")

    def test_build_probe_report_filters_signals_after_until_time(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xIN",
                "symbol": "IN",
                "time": anchor.isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 25.0,
                "reason": "pred_return_below_min",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "token": "0xLATE",
                "symbol": "LATE",
                "time": (anchor + dt.timedelta(seconds=1)).isoformat(sep=" "),
                "prob": 0.99,
                "pred_return": 30.0,
                "reason": "pred_return_below_min",
            },
        ]
        lifecycles = {
            "0xin": {
                "token_address": "0xIN",
                "price_history": [
                    {"timestamp": analysis_timestamp(anchor - dt.timedelta(seconds=1)), "price": 1.0, "type": "buy"},
                    {"timestamp": analysis_timestamp(anchor + dt.timedelta(seconds=20)), "price": 1.3, "type": "buy"},
                ],
            },
        }

        report = p.build_probe_report(signal_rows=signal_rows, lifecycles=lifecycles, until=anchor)

        self.assertEqual(report["parameters"]["until"], anchor)
        self.assertEqual(report["candidate_counts"]["signal_decisions"], 1)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 1)
        self.assertEqual(report["candidate_sample"][0]["symbol"], "IN")

    def test_build_probe_report_marks_default_candidate_sample_limit(self):
        report = p.build_probe_report(signal_rows=_rejected_signal_rows(101), lifecycles={})

        self.assertEqual(report["parameters"]["max_candidate_sample"], 100)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 101)
        self.assertEqual(report["candidate_counts"]["emitted_candidate_count"], 100)
        self.assertTrue(report["candidate_counts"]["sample_limited"])
        self.assertEqual(report["candidate_counts"]["unemitted_candidate_count"], 1)
        self.assertEqual(len(report["candidate_sample"]), 100)

    def test_build_probe_report_honors_explicit_candidate_sample_limit(self):
        report = p.build_probe_report(
            signal_rows=_rejected_signal_rows(8),
            lifecycles={},
            max_candidate_sample=5,
        )

        self.assertEqual(report["parameters"]["max_candidate_sample"], 5)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 8)
        self.assertEqual(report["candidate_counts"]["emitted_candidate_count"], 5)
        self.assertTrue(report["candidate_counts"]["sample_limited"])
        self.assertEqual(report["candidate_counts"]["unemitted_candidate_count"], 3)
        self.assertEqual([row["symbol"] for row in report["candidate_sample"]], ["T000", "T001", "T002", "T003", "T004"])

    def test_build_probe_report_can_emit_all_candidates_for_expanded_evidence(self):
        report = p.build_probe_report(signal_rows=_rejected_signal_rows(101), lifecycles={}, max_candidate_sample=0)

        self.assertEqual(report["parameters"]["max_candidate_sample"], 0)
        self.assertEqual(report["candidate_counts"]["per_token_candidates"], 101)
        self.assertEqual(report["candidate_counts"]["emitted_candidate_count"], 101)
        self.assertFalse(report["candidate_counts"]["sample_limited"])
        self.assertEqual(report["candidate_counts"]["unemitted_candidate_count"], 0)
        self.assertEqual(len(report["candidate_sample"]), 101)

    def test_build_probe_report_rejects_negative_candidate_sample_limit(self):
        with self.assertRaises(ValueError):
            p.build_probe_report(signal_rows=[], lifecycles={}, max_candidate_sample=-1)

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
