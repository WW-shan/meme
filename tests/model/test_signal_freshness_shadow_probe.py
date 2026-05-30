import datetime as dt
import unittest

from src.pipeline import signal_freshness_shadow_probe as probe


def signal(token, seconds, *, chain_lag, staleness=0.01, prob=0.99, pred_return=40.0):
    return {
        "action": "SIGNAL_DECISION",
        "decision": "rejected",
        "time": f"2026-05-30 00:00:{seconds:02d}",
        "token": token,
        "symbol": token.upper(),
        "prob": prob,
        "pred_return": pred_return,
        "volume_30s": 2.0,
        "price_volatility": 0.2,
        "token_age_seconds": 20.0,
        "lifecycle_status_chain_lag_seconds": chain_lag,
        "lifecycle_status_staleness_seconds": staleness,
        "lifecycle_status_fast_status_enabled": True,
        "lifecycle_status_fast_status_eligible": chain_lag <= 8.0,
        "lifecycle_status_has_chain_update": True,
        "lifecycle_status_has_local_update": True,
        "buy_fast_status_max_staleness_seconds": 3.0,
        "buy_fast_status_max_chain_lag_seconds": 8.0,
    }


def lifecycle(token, prices):
    return {
        token.lower(): {
            "token_address": token.lower(),
            "symbol": token.upper(),
            "price_history": [
                {"timestamp": timestamp, "price": price}
                for timestamp, price in prices
            ],
            "buys": [],
            "sells": [],
        }
    }


class SignalFreshnessShadowProbeTest(unittest.TestCase):
    def test_high_chain_lag_rule_can_be_research_alpha_in_shadow(self):
        rows = [
            signal("0xa1", 0, chain_lag=20.0),
            signal("0xa2", 1, chain_lag=21.0),
            signal("0xa3", 2, chain_lag=2.0),
            signal("0xa4", 3, chain_lag=3.0),
        ]
        lifecycles = {}
        lifecycles.update(lifecycle("0xa1", [("2026-05-30 00:00:00", 100), ("2026-05-30 00:00:10", 70)]))
        lifecycles.update(lifecycle("0xa2", [("2026-05-30 00:00:01", 100), ("2026-05-30 00:00:50", 100)]))
        lifecycles.update(lifecycle("0xa3", [("2026-05-30 00:00:02", 100), ("2026-05-30 00:00:20", 130)]))
        lifecycles.update(lifecycle("0xa4", [("2026-05-30 00:00:03", 100), ("2026-05-30 00:01:10", 130)]))

        report = probe.build_signal_freshness_shadow_report(
            signal_rows=rows,
            lifecycles=lifecycles,
            min_candidates=4,
            min_selected=2,
            generated_at=dt.datetime(2026, 5, 30, tzinfo=dt.timezone.utc),
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["decision"], "research_alpha_signal_freshness_shadow_candidate")
        self.assertEqual(report["selected_rule"]["selected_count"], 2)
        self.assertEqual(report["selected_rule"]["opportunity_miss_count"], 0)
        self.assertGreaterEqual(report["selected_rule"]["correct_skip_precision"], 1.0)

    def test_reports_insufficient_support_when_freshness_sample_is_too_small(self):
        rows = [signal("0xa1", 0, chain_lag=20.0)]
        lifecycles = lifecycle("0xa1", [("2026-05-30 00:00:00", 100), ("2026-05-30 00:00:10", 70)])

        report = probe.build_signal_freshness_shadow_report(
            signal_rows=rows,
            lifecycles=lifecycles,
            min_candidates=2,
            min_selected=1,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertEqual(report["decision"], "insufficient_signal_freshness_shadow_support")
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])

    def test_reports_insufficient_path_coverage_separately(self):
        rows = [
            signal("0xa1", 0, chain_lag=20.0),
            signal("0xa2", 1, chain_lag=21.0),
        ]

        report = probe.build_signal_freshness_shadow_report(
            signal_rows=rows,
            lifecycles={},
            min_candidates=2,
            min_selected=1,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertEqual(report["decision"], "insufficient_signal_freshness_path_coverage")
        self.assertEqual(report["candidate_counts"]["path_evaluable_candidate_count"], 0)
        self.assertEqual(report["candidate_counts"]["missing_path_count"], 2)


if __name__ == "__main__":
    unittest.main()
