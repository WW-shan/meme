import datetime as dt
import unittest

from src.pipeline import signal_freshness_shadow_probe as probe


def signal(
    token,
    seconds,
    *,
    chain_lag,
    staleness=0.01,
    prob=0.99,
    pred_return=40.0,
    fast_status_eligible=None,
    has_chain_update=True,
    has_local_update=True,
):
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
        "lifecycle_status_fast_status_eligible": chain_lag <= 8.0 if fast_status_eligible is None else fast_status_eligible,
        "lifecycle_status_has_chain_update": has_chain_update,
        "lifecycle_status_has_local_update": has_local_update,
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

    def test_split_report_requires_train_rule_to_survive_holdouts(self):
        rows = [
            signal("0xa1", 0, chain_lag=20.0, staleness=0.02),
            signal("0xa2", 1, chain_lag=21.0, staleness=0.02),
            signal("0xa3", 2, chain_lag=22.0, staleness=0.02),
            signal("0xa4", 3, chain_lag=2.0, staleness=0.001),
            signal("0xa5", 4, chain_lag=23.0, staleness=0.02),
            signal("0xa6", 5, chain_lag=3.0, staleness=0.001),
            signal("0xa7", 6, chain_lag=24.0, staleness=0.02),
            signal("0xa8", 7, chain_lag=4.0, staleness=0.001),
            signal("0xa9", 8, chain_lag=25.0, staleness=0.02),
        ]
        lifecycles = {}
        for index in (1, 2, 3, 5, 7, 9):
            lifecycles.update(lifecycle(f"0xa{index}", [(f"2026-05-30 00:00:0{index - 1}", 100), ("2026-05-30 00:01:00", 100)]))
        for index in (4, 6, 8):
            lifecycles.update(lifecycle(f"0xa{index}", [(f"2026-05-30 00:00:0{index - 1}", 100), ("2026-05-30 00:00:20", 130)]))

        report = probe.build_signal_freshness_split_report(
            signal_rows=rows,
            lifecycles=lifecycles,
            min_candidates=6,
            min_split_candidates=2,
            min_selected=2,
            min_split_selected=1,
            train_fraction=0.5,
            validation_fraction=0.25,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["decision"], "research_alpha_signal_freshness_split_stable")
        self.assertGreaterEqual(report["stable_rule_count"], 1)
        self.assertGreaterEqual(report["selected_rule"]["train"]["selected_count"], 2)
        self.assertGreaterEqual(report["selected_rule"]["validation"]["selected_count"], 1)
        self.assertGreaterEqual(report["selected_rule"]["final"]["selected_count"], 1)
        self.assertEqual(report["selected_rule"]["validation"]["opportunity_miss_count"], 0)
        self.assertEqual(report["selected_rule"]["final"]["opportunity_miss_count"], 0)

    def test_split_report_rejects_train_rule_that_fails_holdout(self):
        rows = [
            signal("0xb1", 0, chain_lag=20.0, staleness=0.02),
            signal("0xb2", 1, chain_lag=21.0, staleness=0.02),
            signal("0xb3", 2, chain_lag=22.0, staleness=0.02),
            signal("0xb4", 3, chain_lag=2.0, staleness=0.001),
            signal("0xb5", 4, chain_lag=23.0, staleness=0.02),
            signal("0xb6", 5, chain_lag=3.0, staleness=0.001),
            signal("0xb7", 6, chain_lag=24.0, staleness=0.02),
            signal("0xb8", 7, chain_lag=4.0, staleness=0.001),
        ]
        lifecycles = {}
        for index in (1, 2, 3, 7):
            lifecycles.update(lifecycle(f"0xb{index}", [(f"2026-05-30 00:00:0{index - 1}", 100), ("2026-05-30 00:01:00", 100)]))
        for index in (4, 5, 6, 8):
            lifecycles.update(lifecycle(f"0xb{index}", [(f"2026-05-30 00:00:0{index - 1}", 100), ("2026-05-30 00:00:20", 130)]))

        report = probe.build_signal_freshness_split_report(
            signal_rows=rows,
            lifecycles=lifecycles,
            min_candidates=6,
            min_split_candidates=2,
            min_selected=2,
            min_split_selected=1,
            train_fraction=0.5,
            validation_fraction=0.25,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertEqual(report["decision"], "signal_freshness_train_rule_failed_holdout")
        self.assertGreaterEqual(report["train_eligible_rule_count"], 1)
        self.assertGreater(report["selected_rule"]["validation"]["opportunity_miss_count"], 0)

    def test_split_report_selects_rule_by_train_before_holdout(self):
        rows = [
            signal("0xc1", 0, chain_lag=20.0, staleness=None, has_chain_update=None),
            signal("0xc2", 1, chain_lag=21.0, staleness=None, has_chain_update=None),
            signal("0xc3", 2, chain_lag=22.0, staleness=None, has_chain_update=None),
            signal("0xc4", 3, chain_lag=23.0, staleness=None, has_chain_update=None),
            signal("0xc5", 4, chain_lag=2.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc6", 5, chain_lag=3.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc7", 6, chain_lag=4.0, staleness=None, has_chain_update=None),
            signal("0xc8", 7, chain_lag=5.0, staleness=None, has_chain_update=None),
            signal("0xc9", 8, chain_lag=20.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc10", 9, chain_lag=2.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc11", 10, chain_lag=3.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc12", 11, chain_lag=4.0, staleness=None, has_chain_update=None),
            signal("0xc13", 12, chain_lag=20.0, staleness=None, has_chain_update=None),
            signal("0xc14", 13, chain_lag=2.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc15", 14, chain_lag=3.0, staleness=None, has_chain_update=None, has_local_update=False),
            signal("0xc16", 15, chain_lag=4.0, staleness=None, has_chain_update=None),
        ]
        lifecycles = {}
        opportunity_tokens = {"0xc7", "0xc8", "0xc12", "0xc16"}
        for index in range(1, 17):
            path = [(f"2026-05-30 00:00:{index - 1:02d}", 100), ("2026-05-30 00:01:00", 100)]
            if f"0xc{index}" in opportunity_tokens:
                path = [(f"2026-05-30 00:00:{index - 1:02d}", 100), ("2026-05-30 00:00:20", 130)]
            lifecycles.update(lifecycle(f"0xc{index}", path))

        report = probe.build_signal_freshness_split_report(
            signal_rows=rows,
            lifecycles=lifecycles,
            min_candidates=6,
            min_split_candidates=2,
            min_selected=2,
            min_split_selected=1,
            train_fraction=0.5,
            validation_fraction=0.25,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["decision"], "research_alpha_signal_freshness_split_stable")
        self.assertEqual(report["selected_rule"]["rule"]["field"], "lifecycle_status_chain_lag_seconds")
        self.assertEqual(report["selected_rule"]["rule"]["threshold"], 20.0)
        self.assertEqual(report["selected_rule"]["train"]["selected_count"], 4)


if __name__ == "__main__":
    unittest.main()
