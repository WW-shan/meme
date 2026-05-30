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

    def test_post_skip_followup_hazard_selects_train_rule_and_validates(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)

        def trade(index, net, prior_skip):
            token = f"0x{index:040x}"
            entry_time = anchor + dt.timedelta(minutes=index)
            open_row = {
                "action": "OPEN",
                "token": token,
                "symbol": f"T{index}",
                "entry_signal_time": entry_time.isoformat(sep=" "),
                "time": (entry_time + dt.timedelta(seconds=8)).isoformat(sep=" "),
                "is_real_trade": True,
                "prob": 0.98,
                "pred_return": 40.0,
                "price": 1.0,
            }
            close_row = {
                "action": "CLOSE",
                "token": token,
                "symbol": f"T{index}",
                "time": (entry_time + dt.timedelta(seconds=80)).isoformat(sep=" "),
                "reason": "TIME_EXIT" if net <= 0 else "TRAILING_STOP",
                "net_profit_bnb": net,
                "is_real_trade": True,
            }
            signal_row = None
            if prior_skip:
                signal_row = {
                    "action": "ENTRY_PRICE_PROTECTION_SKIP",
                    "token": token,
                    "symbol": f"T{index}",
                    "time": (entry_time - dt.timedelta(seconds=30)).isoformat(sep=" "),
                    "prob": 0.99,
                    "pred_return": 45.0,
                    "signal_price": 1.0,
                    "candidate_price": 1.4,
                    "entry_slippage_pct": 0.4,
                }
            return [open_row, close_row], signal_row

        specs = [
            (1, 0.0010, False),
            (2, -0.0040, True),
            (3, -0.0030, True),
            (4, -0.0025, True),
            (5, 0.0010, False),
            (6, -0.0015, True),
            (7, -0.0020, True),
            (8, 0.0010, False),
            (9, -0.0020, True),
            (10, 0.0008, False),
        ]
        trade_rows = []
        signal_rows = []
        for spec in specs:
            rows, signal = trade(*spec)
            trade_rows.extend(rows)
            if signal:
                signal_rows.append(signal)

        report = p.build_post_skip_followup_hazard_report(
            trade_rows=trade_rows,
            signal_rows=signal_rows,
            lifecycles={},
            generated_at=anchor,
            min_train_selected=3,
            min_train_loss_precision=1.0,
            max_train_winner_count=0,
            max_validation_winner_count=0,
            max_final_winner_count=0,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        selected = report["selected_candidate"]
        self.assertTrue(selected["passes_research_alpha_proxy_gate"])
        self.assertEqual(selected["rule"]["field"], "prior_skip_count")
        self.assertGreater(selected["validation"]["abstention_delta_bnb"], 0.0)
        self.assertGreaterEqual(selected["final"]["abstention_delta_bnb"], 0.0)
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertTrue(report["probe_contract"]["uses_only_pre_open_skip_history_as_policy"])

    def test_post_skip_followup_hazard_ignores_skip_after_entry_decision(self):
        anchor = dt.datetime(2026, 5, 30, 10, 0, 0)
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xA",
                "symbol": "AAA",
                "entry_signal_time": anchor.isoformat(sep=" "),
                "time": (anchor + dt.timedelta(seconds=5)).isoformat(sep=" "),
                "is_real_trade": True,
                "price": 1.0,
            },
            {
                "action": "CLOSE",
                "token": "0xA",
                "symbol": "AAA",
                "time": (anchor + dt.timedelta(seconds=60)).isoformat(sep=" "),
                "reason": "TIME_EXIT",
                "net_profit_bnb": -0.001,
                "is_real_trade": True,
            },
        ]
        signal_rows = [
            {
                "action": "ENTRY_PRICE_PROTECTION_SKIP",
                "token": "0xA",
                "symbol": "AAA",
                "time": (anchor + dt.timedelta(seconds=1)).isoformat(sep=" "),
                "signal_price": 1.0,
                "candidate_price": 1.5,
                "entry_slippage_pct": 0.5,
            }
        ]

        rows = p.post_skip_followup_rows(
            trade_rows=trade_rows,
            signal_rows=signal_rows,
            lifecycles={},
            lookback_seconds=120,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["prior_skip_count"], 0)


if __name__ == "__main__":
    unittest.main()
