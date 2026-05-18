import datetime as dt
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

from src.pipeline import reentry_probe as p


class TestReentryProbe(unittest.TestCase):
    def test_parse_time_accepts_live_local_datetime_and_epoch(self):
        parsed = p.parse_time("2026-05-19 04:11:18.755211")
        self.assertEqual(parsed, dt.datetime(2026, 5, 19, 4, 11, 18, 755211))
        self.assertEqual(p.parse_time(1779135078), dt.datetime(2026, 5, 19, 4, 11, 18))

    def test_parse_time_normalizes_aware_iso_to_analysis_timezone_naive(self):
        self.assertEqual(
            p.parse_time("2026-05-19T04:11:18Z"),
            dt.datetime(2026, 5, 19, 12, 11, 18),
        )
        self.assertEqual(
            p.parse_time("2026-05-19T12:11:18+08:00"),
            dt.datetime(2026, 5, 19, 12, 11, 18),
        )

    def test_parse_time_numeric_string_uses_analysis_timezone_not_process_timezone(self):
        if not hasattr(time, "tzset"):
            self.skipTest("process timezone switching is unavailable")
        previous_tz = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "UTC"
            time.tzset()

            parsed = p.parse_time("1779135078")
        finally:
            if previous_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous_tz
            time.tzset()

        self.assertEqual(parsed, dt.datetime(2026, 5, 19, 4, 11, 18))

    def test_path_metrics_reports_barrier_order_from_anchor_price(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        path = [
            p.PricePoint(anchor, 1.00, "anchor"),
            p.PricePoint(anchor + dt.timedelta(seconds=10), 1.26, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=20), 1.70, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=30), 0.78, "sell"),
        ]

        metrics = p.path_metrics(path, anchor_time=anchor, anchor_price=1.0, horizon_seconds=90)

        self.assertAlmostEqual(metrics["mfe_pct"], 70.0)
        self.assertAlmostEqual(metrics["mae_pct"], -22.0)
        self.assertEqual(metrics["time_to_plus_25_seconds"], 10.0)
        self.assertEqual(metrics["time_to_plus_60_seconds"], 20.0)
        self.assertEqual(metrics["time_to_minus_18_seconds"], 30.0)
        self.assertEqual(metrics["first_barrier"], "+25")

    def test_path_metrics_marks_collapse_before_reclaim(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        path = [
            p.PricePoint(anchor, 1.00, "anchor"),
            p.PricePoint(anchor + dt.timedelta(seconds=4), 0.80, "sell"),
            p.PricePoint(anchor + dt.timedelta(seconds=12), 1.30, "buy"),
        ]

        metrics = p.path_metrics(path, anchor_time=anchor, anchor_price=1.0, horizon_seconds=90)

        self.assertEqual(metrics["time_to_minus_18_seconds"], 4.0)
        self.assertEqual(metrics["time_to_plus_25_seconds"], 12.0)
        self.assertEqual(metrics["first_barrier"], "-18")

    def test_signal_decision_parser_uses_action_and_time_fields(self):
        row = {
            "action": "SIGNAL_DECISION",
            "time": "2026-05-19 04:11:18.755211",
            "token": "0xABC",
            "symbol": "SZN",
            "decision": "rejected",
            "reason": "pred_return_below_min",
            "prob": 0.989,
            "pred_return": 25.04,
            "volume_30s": 3.5,
            "price_volatility": 0.32,
        }

        parsed = list(p.iter_signal_decisions([row]))

        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["token"], "0xabc")
        self.assertEqual(parsed[0]["time"], dt.datetime(2026, 5, 19, 4, 11, 18, 755211))
        self.assertEqual(parsed[0]["reason"], "pred_return_below_min")

    def test_signal_decision_parser_excludes_non_rejected_decisions(self):
        rows = [
            {"action": "SIGNAL_DECISION", "decision": "queued", "time": "2026-05-19 04:11:18", "token": "0xABC"},
            {"action": "SIGNAL_DECISION", "decision": "rejected", "time": "2026-05-19 04:11:19", "token": "0xDEF"},
        ]

        parsed = list(p.iter_signal_decisions(rows))

        self.assertEqual([row["token"] for row in parsed], ["0xdef"])

    def test_signal_decision_parser_records_age_time_without_overriding_audit_time(self):
        row = {
            "action": "SIGNAL_DECISION",
            "time": "2026-05-19 04:11:18.755211",
            "create_timestamp": 1779134826,
            "token_age_seconds": 251,
            "token": "0xABC",
            "decision": "rejected",
        }

        parsed = list(p.iter_signal_decisions([row]))

        self.assertEqual(parsed[0]["time"], dt.datetime(2026, 5, 19, 4, 11, 18, 755211))
        self.assertEqual(parsed[0]["age_anchor_time"], dt.datetime(2026, 5, 19, 4, 11, 17))

    def test_pair_live_trades_matches_open_and_close_by_token_order(self):
        rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-18 20:21:15", "entry_price": 1.0, "symbol": "A"},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-18 20:21:40", "exit_price": 0.75, "reason": "STOP_LOSS", "symbol": "A"},
        ]

        pairs = list(p.pair_live_trades(rows))

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["token"], "0xa")
        self.assertEqual(pairs[0]["open"]["entry_price"], 1.0)
        self.assertEqual(pairs[0]["close"]["reason"], "STOP_LOSS")

    def test_pair_live_trades_prefers_signal_time_and_close_receipt_time(self):
        rows = [
            {
                "action": "OPEN",
                "token": "0xA",
                "entry_signal_time": "2026-05-18 20:21:12",
                "time": "2026-05-18 20:21:15",
                "entry_price": 1.0,
            },
            {
                "action": "CLOSE",
                "token": "0xA",
                "sell_started_at": "2026-05-18 20:21:37",
                "time": "2026-05-18 20:21:40",
                "exit_price": 0.75,
                "reason": "STOP_LOSS",
            },
        ]

        pair = list(p.pair_live_trades(rows))[0]

        self.assertEqual(pair["open"]["time"], dt.datetime(2026, 5, 18, 20, 21, 12))
        self.assertEqual(pair["close"]["time"], dt.datetime(2026, 5, 18, 20, 21, 40))
        self.assertEqual(pair["close"]["sell_started_at"], dt.datetime(2026, 5, 18, 20, 21, 37))

    def test_exit_reclaim_anchors_to_receipt_time_when_using_exit_price(self):
        sell_started = dt.datetime(2026, 5, 18, 20, 21, 37)
        receipt_time = dt.datetime(2026, 5, 18, 20, 21, 42)
        rows = [
            {
                "action": "OPEN",
                "token": "0xA",
                "time": "2026-05-18 20:21:15",
                "entry_price": 1.0,
            },
            {
                "action": "CLOSE",
                "token": "0xA",
                "sell_started_at": sell_started.isoformat(sep=" "),
                "time": receipt_time.isoformat(sep=" "),
                "exit_price": 1.0,
                "reason": "STOP_LOSS",
            },
        ]
        path = [
            p.PricePoint(sell_started + dt.timedelta(seconds=1), 1.30, "pre-receipt"),
            p.PricePoint(receipt_time, 1.0, "receipt"),
            p.PricePoint(receipt_time + dt.timedelta(seconds=20), 1.30, "post-receipt"),
        ]

        pair = list(p.pair_live_trades(rows))[0]
        scored = p.score_stoploss_reentry_candidate(pair, path)

        self.assertEqual(pair["close"]["sell_started_at"], sell_started)
        self.assertEqual(pair["close"]["time"], receipt_time)
        self.assertEqual(scored["time_to_plus_25_seconds"], 20.0)

    def test_lifecycle_price_path_reads_active_runtime_state(self):
        state = {
            "active_lifecycles": [
                {
                    "token_address": "0xABC",
                    "symbol": "SZN",
                    "price_history": [
                        {"timestamp": 1779135078, "price": 1.0, "type": "buy"},
                        {"timestamp": 1779135088, "price": 1.3, "type": "buy"},
                    ],
                }
            ]
        }

        lifecycles = p.extract_lifecycles_from_runtime_state(state)
        path = p.price_path_for_token(lifecycles, "0xabc")

        self.assertEqual(len(path), 2)
        self.assertEqual(path[0].price, 1.0)

    def test_lifecycle_rows_merge_flushed_price_history_by_token(self):
        rows = [
            {
                "token_address": "0xABC",
                "symbol": "SZN",
                "price_history": [{"timestamp": 1779135078, "price": 1.0, "type": "buy"}],
            },
            {
                "token_address": "0xabc",
                "symbol": "SZN",
                "price_history": [{"timestamp": 1779135088, "price": 1.3, "type": "buy"}],
            },
        ]

        lifecycles = p.extract_lifecycles_from_rows(rows)
        path = p.price_path_for_token(lifecycles, "0xABC")

        self.assertEqual(len(path), 2)
        self.assertEqual([point.price for point in path], [1.0, 1.3])

    def test_load_lifecycles_merges_runtime_and_latest_incremental_file(self):
        state = {
            "active_lifecycles": [
                {
                    "token_address": "0xABC",
                    "symbol": "SZN",
                    "price_history": [{"timestamp": 1779135078, "price": 1.0, "type": "buy"}],
                }
            ]
        }
        flushed = {
            "token_address": "0xABC",
            "symbol": "SZN",
            "price_history": [{"timestamp": 1779135088, "price": 1.3, "type": "buy"}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            state_path = base / "collector_runtime_state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            lifecycle_path = base / "lifecycle_incremental_20260519_000000.jsonl"
            lifecycle_path.write_text(json.dumps(flushed) + "\n", encoding="utf-8")

            lifecycles = p.load_lifecycles(
                collector_state_path=state_path,
                lifecycle_paths=[lifecycle_path],
            )

        path = p.price_path_for_token(lifecycles, "0xABC")
        self.assertEqual([point.price for point in path], [1.0, 1.3])

    def test_latest_lifecycle_files_returns_most_recent_incremental(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            older = base / "lifecycle_incremental_20260518_000000.jsonl"
            newer = base / "lifecycle_incremental_20260519_000000.jsonl"
            older.write_text("{}", encoding="utf-8")
            newer.write_text("{}", encoding="utf-8")

            selected = p.latest_lifecycle_files(base, limit=1)

        self.assertEqual([path.name for path in selected], ["lifecycle_incremental_20260519_000000.jsonl"])

    def test_build_input_status_marks_missing_and_existing_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            paper = base / "paper.jsonl"
            paper.write_text("{}", encoding="utf-8")
            missing = base / "missing.jsonl"

            status = p.build_input_status(
                paper_trades=paper,
                signal_audit=missing,
                collector_state=missing,
                lifecycle_dir=base,
                lifecycle_paths=[paper, missing],
            )

        self.assertTrue(status["paper_trades"]["exists"])
        self.assertFalse(status["signal_audit"]["exists"])
        self.assertEqual(status["existing_lifecycle_path_count"], 1)

    def test_score_stoploss_reentry_requires_reclaim_before_collapse(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        close_pair = {
            "token": "0xabc",
            "symbol": "A",
            "close": {"time": anchor, "exit_price": 1.0, "reason": "STOP_LOSS"},
        }
        path = [
            p.PricePoint(anchor, 1.0, "exit"),
            p.PricePoint(anchor + dt.timedelta(seconds=20), 1.28, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=80), 1.70, "buy"),
        ]

        scored = p.score_stoploss_reentry_candidate(close_pair, path)

        self.assertTrue(scored["accepted_by_probe"])
        self.assertTrue(scored["accepted"])
        self.assertEqual(scored["decision"], "accepted")
        self.assertEqual(scored["time_to_plus_25_seconds"], 20.0)
        self.assertEqual(scored["first_barrier"], "+25")

    def test_score_stoploss_reentry_rejects_fast_post_reclaim_collapse(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        close_pair = {
            "token": "0xabc",
            "symbol": "A",
            "close": {"time": anchor, "exit_price": 1.0, "reason": "STOP_LOSS"},
        }
        path = [
            p.PricePoint(anchor, 1.0, "exit"),
            p.PricePoint(anchor + dt.timedelta(seconds=1), 1.30, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=40), 0.70, "sell"),
        ]

        scored = p.score_stoploss_reentry_candidate(close_pair, path)

        self.assertFalse(scored["accepted_by_probe"])
        self.assertFalse(scored["accepted"])
        self.assertEqual(scored["decision"], "rejected")
        self.assertTrue(scored["post_reclaim_collapse_failed"])

    def test_score_exit_reclaim_rejects_missing_exit_price_without_crashing(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        close_pair = {
            "token": "0xabc",
            "symbol": "A",
            "close": {"time": anchor, "reason": "STOP_LOSS"},
        }
        path = [
            p.PricePoint(anchor, 1.0, "exit"),
            p.PricePoint(anchor + dt.timedelta(seconds=20), 1.28, "buy"),
        ]

        scored = p.score_stoploss_reentry_candidate(close_pair, path)

        self.assertFalse(scored["accepted_by_probe"])
        self.assertFalse(scored["accepted"])
        self.assertEqual(scored["decision"], "rejected")
        self.assertTrue(scored["missing_anchor_price"])

    def test_score_exit_reclaim_supports_ppo_runner_retention(self):
        anchor = dt.datetime(2026, 5, 18, 0, 10, 14)
        close_pair = {
            "token": "0xabc",
            "symbol": "A",
            "close": {"time": anchor, "exit_price": 1.0, "reason": "PPO_SELL100"},
        }
        path = [
            p.PricePoint(anchor, 1.0, "exit"),
            p.PricePoint(anchor + dt.timedelta(seconds=31), 1.28, "buy"),
        ]

        scored = p.score_exit_reclaim_candidate(close_pair, path, accepted_reasons={"PPO_SELL100"})

        self.assertTrue(scored["accepted_by_probe"])
        self.assertEqual(scored["candidate_type"], "runner_retention")
        self.assertEqual(scored["first_barrier"], "+25")

    def test_score_signal_reclaim_uses_price_path_anchor(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "token": "0xabc",
            "symbol": "SZN",
            "time": anchor,
            "reason": "pred_return_below_min",
            "prob": 0.989,
            "pred_return": 25.04,
        }
        path = [
            p.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=78), 1.30, "buy"),
        ]

        scored = p.score_signal_reclaim_candidate(signal, path)

        self.assertTrue(scored["accepted_by_probe"])
        self.assertTrue(scored["accepted"])
        self.assertEqual(scored["decision"], "accepted")
        self.assertEqual(scored["candidate_type"], "rejected_signal_reclaim")
        self.assertEqual(scored["time_to_plus_25_seconds"], 78.0)

    def test_score_signal_reclaim_rejects_when_no_price_exists_at_or_before_signal(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "token": "0xabc",
            "symbol": "SZN",
            "time": anchor,
            "reason": "pred_return_below_min",
            "prob": 0.989,
            "pred_return": 25.04,
        }
        path = [
            p.PricePoint(anchor + dt.timedelta(seconds=5), 1.0, "future-only"),
            p.PricePoint(anchor + dt.timedelta(seconds=30), 1.3, "future-runner"),
        ]

        scored = p.score_signal_reclaim_candidate(signal, path)

        self.assertFalse(scored["accepted_by_probe"])
        self.assertTrue(scored["missing_path"])
        self.assertEqual(scored["decision"], "rejected")

    def test_score_signal_reclaim_filters_low_confidence_rows(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "token": "0xabc",
            "symbol": "SZN",
            "time": anchor,
            "reason": "buy_model_reject",
            "prob": 0.52,
            "pred_return": 6.0,
        }
        path = [
            p.PricePoint(anchor, 1.0, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=90), 1.5, "buy"),
        ]

        scored = p.score_signal_reclaim_candidate(signal, path)

        self.assertFalse(scored["accepted_by_probe"])
        self.assertFalse(scored["accepted"])
        self.assertEqual(scored["decision"], "rejected")
        self.assertTrue(scored["filtered_by_confidence"])

    def test_score_signal_reclaim_treats_non_finite_scores_as_unqualified(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal = {
            "token": "0xabc",
            "symbol": "SZN",
            "time": anchor,
            "reason": "buy_model_reject",
            "prob": "NaN",
            "pred_return": "Infinity",
        }
        path = [
            p.PricePoint(anchor, 1.0, "buy"),
            p.PricePoint(anchor + dt.timedelta(seconds=30), 2.0, "buy"),
        ]

        scored = p.score_signal_reclaim_candidate(signal, path)

        self.assertFalse(scored["accepted_by_probe"])
        self.assertEqual(scored["decision"], "rejected")
        self.assertTrue(scored["filtered_by_confidence"])

    def test_build_probe_report_is_json_serializable(self):
        anchor = dt.datetime(2026, 5, 18, 20, 21, 40)
        trade_rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-18 20:21:15", "entry_price": 1.2, "symbol": "A"},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-18 20:21:40", "exit_price": 1.0, "reason": "STOP_LOSS", "symbol": "A"},
        ]
        signal_rows = []
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "symbol": "A",
                "price_history": [
                    {"timestamp": anchor.timestamp(), "price": 1.0, "type": "exit"},
                    {"timestamp": (anchor + dt.timedelta(seconds=20)).timestamp(), "price": 1.3, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(trade_rows=trade_rows, signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertEqual(report["candidate_counts"]["stoploss_reentry"], 1)
        self.assertEqual(report["candidate_counts"]["accepted_stoploss_reentry"], 1)
        json.loads(p.to_json_text(report))

    def test_build_probe_report_limits_signal_sample_and_counts_rejected_reclaims(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "token": "0xA",
                "time": (anchor + dt.timedelta(seconds=i)).isoformat(sep=" "),
                "reason": "pred_return_below_min",
                "decision": "rejected",
                "prob": 0.99,
                "pred_return": 25.0,
            }
            for i in range(60)
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "symbol": "A",
                "price_history": [
                    {"timestamp": (anchor - dt.timedelta(seconds=1)).timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=90)).timestamp(), "price": 1.3, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(trade_rows=[], signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertEqual(report["candidate_counts"]["signal_decisions"], 60)
        self.assertEqual(report["candidate_counts"]["per_token_rejected_signal_reclaim"], 1)
        self.assertEqual(report["candidate_counts"]["dropped_rejected_signal_decisions_by_token_best"], 59)
        self.assertEqual(len(report["signal_decision_sample"]), 50)
        self.assertNotIn("signal_decisions", report)

    def test_build_probe_report_treats_non_numeric_scores_as_unqualified(self):
        anchor = dt.datetime(2026, 5, 19, 4, 11, 18)
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "token": "0xA",
                "time": anchor.isoformat(sep=" "),
                "reason": "buy_model_reject",
                "decision": "rejected",
                "prob": "n/a",
                "pred_return": None,
            }
        ]
        lifecycles = {
            "0xa": {
                "token_address": "0xA",
                "symbol": "A",
                "price_history": [
                    {"timestamp": anchor.timestamp(), "price": 1.0, "type": "buy"},
                    {"timestamp": (anchor + dt.timedelta(seconds=30)).timestamp(), "price": 2.0, "type": "buy"},
                ],
            }
        }

        report = p.build_probe_report(trade_rows=[], signal_rows=signal_rows, lifecycles=lifecycles)

        self.assertEqual(report["candidate_counts"]["per_token_rejected_signal_reclaim"], 1)
        self.assertEqual(report["candidate_counts"]["accepted_rejected_signal_reclaim"], 0)
        self.assertTrue(report["rejected_signal_reclaim_candidates"][0]["filtered_by_confidence"])
        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])

    def test_build_probe_report_counts_missing_paths(self):
        trade_rows = [
            {"action": "OPEN", "token": "0xA", "time": "2026-05-18 20:21:15", "entry_price": 1.2, "symbol": "A"},
            {"action": "CLOSE", "token": "0xA", "time": "2026-05-18 20:21:40", "exit_price": 1.0, "reason": "STOP_LOSS", "symbol": "A"},
        ]

        report = p.build_probe_report(trade_rows=trade_rows, signal_rows=[], lifecycles={})

        self.assertEqual(report["diagnostics"]["missing_lifecycle_path_stoploss"], 1)

    def test_build_probe_report_default_generated_at_uses_analysis_timezone(self):
        fixed = dt.datetime(2026, 5, 18, 20, 11, 18, tzinfo=dt.timezone.utc)
        with patch("src.pipeline.reentry_probe.dt.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed
            mock_datetime.fromtimestamp.side_effect = dt.datetime.fromtimestamp
            mock_datetime.fromisoformat.side_effect = dt.datetime.fromisoformat
            report = p.build_probe_report(trade_rows=[], signal_rows=[], lifecycles={})

        self.assertEqual(report["generated_at"], dt.datetime(2026, 5, 19, 4, 11, 18))
