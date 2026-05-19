import datetime as dt
import unittest

from src.pipeline.flow_activation_probe import (
    SignalEvent,
    build_flow_activation_report,
    classify_flow_activation_candidate,
    extract_lifecycles_from_rows_for_flow,
)
from src.pipeline.reentry_probe import PricePoint


class TestFlowActivationProbe(unittest.TestCase):
    def _signal(
        self,
        seconds: int,
        *,
        token: str = "0xA",
        symbol: str = "TOK",
        decision: str = "rejected",
        prob: float = 0.97,
        pred_return: float = 25.0,
        volume_30s: float = 1.0,
        volatility: float = 0.1,
        near: bool = False,
    ) -> SignalEvent:
        return SignalEvent(
            token_address=token,
            symbol=symbol,
            timestamp=dt.datetime(2026, 5, 19, 12, 0, seconds),
            decision=decision,
            buy_probability=prob,
            pred_return=pred_return,
            volume_30s=volume_30s,
            price_volatility=volatility,
            near_threshold_rescue_used=near,
        )

    def _price_path(self, token: str, points: list[tuple[int, float, str]]):
        base = dt.datetime(2026, 5, 19, 12, 0, 30)
        return [
            PricePoint(base + dt.timedelta(seconds=seconds), price, kind)
            for seconds, price, kind in points
        ]

    def _flow_events(self, points: list[tuple[int, str, float, float]]):
        base = dt.datetime(2026, 5, 19, 12, 0, 30)
        return [
            {
                "timestamp": base + dt.timedelta(seconds=seconds),
                "type": kind,
                "bnb_amount": amount,
                "price": price,
            }
            for seconds, kind, amount, price in points
        ]

    def test_clean_activation_requires_ramping_signal_and_buy_pressure(self):
        history = [
            self._signal(10, pred_return=22.0, volume_30s=0.62, volatility=0.10),
            self._signal(18, pred_return=35.0, volume_30s=1.05, volatility=0.14),
            self._signal(25, pred_return=45.0, volume_30s=1.42, volatility=0.17),
        ]
        anchor = self._signal(
            30,
            decision="queued",
            prob=0.9901,
            pred_return=65.7,
            volume_30s=1.79,
            volatility=0.193,
        )
        path = self._price_path("0xA", [(0, 1.0, "anchor"), (6, 1.28, "buy"), (18, 1.45, "buy")])
        flow = self._flow_events(
            [(-18, "buy", 0.40, 0.95), (-9, "buy", 0.35, 1.00), (-4, "sell", 0.10, 0.98)]
        )

        result = classify_flow_activation_candidate(
            anchor=anchor,
            signal_history=history,
            price_path=path,
            flow_events=flow,
        )

        self.assertEqual(result["classification"], "flow_activation_clean_profit")
        self.assertTrue(result["accepted_by_probe"])
        self.assertEqual(result["recommended_policy"], "allow_flow_activation")
        self.assertEqual(result["classification_basis"], "retrospective_post_anchor_path")
        self.assertFalse(result["live_gate_safe"])
        self.assertEqual(result["recommended_policy_scope"], "offline_probe_only")
        self.assertGreater(result["trajectory"]["volume_ramp_ratio"], 2.0)
        self.assertGreater(result["flow"]["pre_buy_pressure"], 0.80)
        self.assertEqual(result["path"]["first_barrier"], "+25")

    def test_sell_pressure_fakeout_rejects_volume_ramp(self):
        history = [
            self._signal(8, pred_return=21.0, volume_30s=0.70, volatility=0.09),
            self._signal(18, pred_return=34.0, volume_30s=1.45, volatility=0.16),
        ]
        anchor = self._signal(
            30,
            decision="queued",
            pred_return=39.5,
            volume_30s=3.20,
            volatility=0.24,
        )
        path = self._price_path("0xA", [(0, 1.0, "anchor"), (7, 0.81, "sell"), (20, 1.10, "buy")])
        flow = self._flow_events(
            [(-22, "buy", 0.20, 0.95), (-12, "sell", 0.55, 0.92), (-2, "sell", 0.45, 0.88)]
        )

        result = classify_flow_activation_candidate(
            anchor=anchor,
            signal_history=history,
            price_path=path,
            flow_events=flow,
        )

        self.assertEqual(result["classification"], "sell_pressure_fakeout")
        self.assertFalse(result["accepted_by_probe"])
        self.assertEqual(result["recommended_policy"], "skip_or_tight_exit")
        self.assertLess(result["flow"]["pre_buy_pressure"], 0.50)
        self.assertEqual(result["path"]["first_barrier"], "-18")

    def test_near_rescue_without_new_flow_is_dead_flow(self):
        history = [
            self._signal(12, pred_return=34.0, volume_30s=1.20, volatility=0.10, prob=0.945),
        ]
        anchor = self._signal(
            30,
            decision="queued",
            prob=0.976,
            pred_return=40.0,
            volume_30s=1.35,
            volatility=0.12,
            near=True,
        )
        path = self._price_path("0xA", [(0, 1.0, "anchor"), (12, 1.03, "buy"), (80, 0.99, "sell")])
        flow = self._flow_events([(-25, "sell", 0.12, 0.99)])

        result = classify_flow_activation_candidate(
            anchor=anchor,
            signal_history=history,
            price_path=path,
            flow_events=flow,
        )

        self.assertEqual(result["classification"], "dead_flow_rescue")
        self.assertFalse(result["accepted_by_probe"])
        self.assertEqual(result["recommended_policy"], "skip_near_rescue_without_flow")
        self.assertIsNone(result["path"]["time_to_plus_25_seconds"])

    def test_report_contract_is_read_only_and_counts_classes(self):
        signals = [
            self._signal(10, token="0xA", pred_return=22.0, volume_30s=0.62, volatility=0.10),
            self._signal(25, token="0xA", pred_return=45.0, volume_30s=1.42, volatility=0.17),
            self._signal(
                30,
                token="0xA",
                decision="queued",
                prob=0.9901,
                pred_return=65.7,
                volume_30s=1.79,
                volatility=0.193,
            ),
            self._signal(12, token="0xB", pred_return=21.0, volume_30s=0.70, volatility=0.09),
            self._signal(
                30,
                token="0xB",
                decision="queued",
                pred_return=39.5,
                volume_30s=3.20,
                volatility=0.24,
            ),
            self._signal(12, token="0xC", pred_return=34.0, volume_30s=1.20, volatility=0.10),
            self._signal(
                30,
                token="0xC",
                decision="queued",
                prob=0.976,
                pred_return=40.0,
                volume_30s=1.35,
                volatility=0.12,
                near=True,
            ),
        ]
        lifecycle_by_token = {
            "0xA": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:00:36", "price": 1.28, "type": "buy"},
                ],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 0.1, "price": 0.98}],
            },
            "0xB": {
                "token_address": "0xB",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:00:37", "price": 0.81, "type": "sell"},
                ],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.2, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 1.0, "price": 0.88}],
            },
            "0xC": {
                "token_address": "0xC",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:01:10", "price": 1.02, "type": "sell"},
                ],
                "buys": [],
                "sells": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.12, "price": 0.99}],
            },
        }

        report = build_flow_activation_report(
            signal_events=signals,
            lifecycle_by_token=lifecycle_by_token,
            generated_at=dt.datetime(2026, 5, 19, 12, 5, 0),
        )

        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertTrue(report["probe_contract"]["requires_replay_before_live_change"])
        self.assertEqual(report["summary"]["classification_counts"]["flow_activation_clean_profit"], 1)
        self.assertEqual(report["summary"]["classification_counts"]["sell_pressure_fakeout"], 1)
        self.assertEqual(report["summary"]["classification_counts"]["dead_flow_rescue"], 1)
        self.assertEqual(report["summary"]["accepted_by_probe"], 1)
        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertTrue(report["probe_contract"]["post_anchor_path_labels_are_retrospective"])
        self.assertFalse(report["probe_contract"]["safe_for_live_gate"])

    def test_report_merges_buy_sell_flow_from_lifecycle_when_collector_state_has_same_token(self):
        signals = [
            self._signal(10, token="0xA", pred_return=22.0, volume_30s=0.62, volatility=0.10),
            self._signal(
                30,
                token="0xA",
                decision="queued",
                prob=0.9901,
                pred_return=65.7,
                volume_30s=1.79,
                volatility=0.193,
            ),
        ]
        collector_lifecycles = {
            "0xA": {
                "token_address": "0xA",
                "price_history": [],
                "buys": [],
                "sells": [],
            }
        }
        lifecycle_by_token = {
            "0xA": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:00:36", "price": 1.28, "type": "buy"},
                ],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 0.1, "price": 0.98}],
            }
        }

        report = build_flow_activation_report(
            signal_events=signals,
            lifecycle_by_token=lifecycle_by_token,
            collector_lifecycles=collector_lifecycles,
            generated_at=dt.datetime(2026, 5, 19, 12, 5, 0),
        )

        candidate = report["candidates"][0]
        self.assertEqual(candidate["flow"]["flow_event_count"], 2)
        self.assertAlmostEqual(candidate["flow"]["pre_buy_volume_bnb"], 0.5)
        self.assertAlmostEqual(candidate["flow"]["pre_sell_volume_bnb"], 0.1)
        self.assertGreater(candidate["flow"]["pre_buy_pressure"], 0.8)

    def test_pre_anchor_flow_excludes_exact_anchor_time_events(self):
        anchor = self._signal(30, decision="queued", pred_return=65.7, volume_30s=1.79, volatility=0.193)
        result = classify_flow_activation_candidate(
            anchor=anchor,
            signal_history=[self._signal(10, pred_return=22.0, volume_30s=0.62, volatility=0.10)],
            price_path=self._price_path("0xA", [(0, 1.0, "anchor"), (6, 1.28, "buy")]),
            flow_events=[
                {
                    "timestamp": dt.datetime(2026, 5, 19, 12, 0, 29),
                    "type": "buy",
                    "bnb_amount": 0.2,
                    "price": 0.98,
                },
                {
                    "timestamp": dt.datetime(2026, 5, 19, 12, 0, 30),
                    "type": "buy",
                    "bnb_amount": 0.9,
                    "price": 1.0,
                },
            ],
        )

        self.assertEqual(result["flow"]["flow_event_count"], 1)
        self.assertAlmostEqual(result["flow"]["pre_buy_volume_bnb"], 0.2)

    def test_path_metrics_require_anchor_price_at_or_before_signal(self):
        anchor = self._signal(30, decision="queued", pred_return=65.7, volume_30s=1.79, volatility=0.193)
        result = classify_flow_activation_candidate(
            anchor=anchor,
            signal_history=[self._signal(10, pred_return=22.0, volume_30s=0.62, volatility=0.10)],
            price_path=[PricePoint(dt.datetime(2026, 5, 19, 12, 0, 31), 1.0, "future")],
            flow_events=[],
        )

        self.assertTrue(result["path"]["missing_path"])
        self.assertEqual(result["classification"], "missing_path")
        for field in [
            "mfe_pct",
            "mae_pct",
            "first_barrier",
            "time_to_plus_25_seconds",
            "time_to_plus_60_seconds",
            "time_to_minus_18_seconds",
            "time_to_minus_25_seconds",
        ]:
            self.assertIn(field, result["path"])

    def test_since_filters_anchor_candidates_without_dropping_lookback_history(self):
        signals = [
            self._signal(10, token="0xA", pred_return=22.0, volume_30s=0.62, volatility=0.10),
            self._signal(
                30,
                token="0xA",
                decision="queued",
                prob=0.9901,
                pred_return=65.7,
                volume_30s=1.79,
                volatility=0.193,
            ),
        ]
        lifecycle_by_token = {
            "0xA": {
                "token_address": "0xA",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:00:36", "price": 1.28, "type": "buy"},
                ],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [],
            }
        }

        report = build_flow_activation_report(
            signal_events=signals,
            lifecycle_by_token=lifecycle_by_token,
            since=dt.datetime(2026, 5, 19, 12, 0, 30),
            generated_at=dt.datetime(2026, 5, 19, 12, 5, 0),
        )

        self.assertEqual(report["candidate_counts"]["flow_activation_candidates"], 1)
        self.assertEqual(report["candidates"][0]["trajectory"]["history_count"], 1)
        self.assertTrue(report["candidates"][0]["trajectory"]["ramping_signal"])

    def test_extract_lifecycles_from_rows_preserves_buy_sell_flow_across_duplicate_token_rows(self):
        rows = [
            {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [{"timestamp": "2026-05-19 12:00:10", "price": 1.0, "type": "buy"}],
                "buys": [],
                "sells": [],
            },
            {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [{"timestamp": "2026-05-19 12:00:30", "price": 1.2, "type": "buy"}],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 0.1, "price": 0.98}],
            },
        ]

        lifecycles = extract_lifecycles_from_rows_for_flow(rows)

        self.assertEqual(len(lifecycles["0xa"]["price_history"]), 2)
        self.assertEqual(len(lifecycles["0xa"]["buys"]), 1)
        self.assertEqual(len(lifecycles["0xa"]["sells"]), 1)

    def test_report_sequence_lifecycle_input_preserves_buy_sell_flow_across_duplicate_rows(self):
        signals = [
            self._signal(10, token="0xA", pred_return=22.0, volume_30s=0.62, volatility=0.10),
            self._signal(
                30,
                token="0xA",
                decision="queued",
                prob=0.9901,
                pred_return=65.7,
                volume_30s=1.79,
                volatility=0.193,
            ),
        ]
        lifecycle_rows = [
            {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [{"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"}],
                "buys": [],
                "sells": [],
            },
            {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [{"timestamp": "2026-05-19 12:00:36", "price": 1.28, "type": "buy"}],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 0.1, "price": 0.98}],
            },
        ]

        report = build_flow_activation_report(
            signal_events=signals,
            lifecycle_by_token={"0xA": lifecycle_rows},
            generated_at=dt.datetime(2026, 5, 19, 12, 5, 0),
        )

        self.assertEqual(report["candidates"][0]["flow"]["flow_event_count"], 2)
        self.assertGreater(report["candidates"][0]["flow"]["pre_buy_pressure"], 0.8)


if __name__ == "__main__":
    unittest.main()
