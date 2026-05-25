import datetime as dt
import json
import unittest

from src.pipeline import reentry_probe
from src.pipeline import runner_retention_label_probe as p


class TestRunnerRetentionLabelProbe(unittest.TestCase):
    def _candidate(self, token="0xA", *, anchor=None):
        anchor = anchor or dt.datetime(2026, 5, 26, 1, 36, 3)
        return {
            "token": token,
            "symbol": "SLOW",
            "sample_time": anchor,
            "candidate_source": "shadow_score_reject",
            "buy_prob": 0.887,
            "entry_score": 11.3,
            "entry_volume_30s": 2.1,
            "entry_price_volatility": 0.08,
            "features": {"current_price": 1.0},
        }

    def test_scores_slow_runner_retention_when_plus60_arrives_late_before_stop(self):
        anchor = dt.datetime(2026, 5, 26, 1, 36, 3)
        path = [
            reentry_probe.PricePoint(anchor - dt.timedelta(seconds=1), 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=240), 1.26, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=390), 1.65, "buy"),
        ]

        scored = p.score_runner_retention_candidate(self._candidate(anchor=anchor), path)

        self.assertEqual(scored["retention_label"], "slow_runner_retention")
        self.assertEqual(scored["competing_event"], "runner_retention")
        self.assertTrue(scored["runner_retention_positive"])
        self.assertEqual(scored["time_to_plus_25_seconds"], 240.0)
        self.assertEqual(scored["time_to_plus_60_seconds"], 390.0)

    def test_scores_stop_first_as_competing_collapse(self):
        anchor = dt.datetime(2026, 5, 26, 1, 36, 3)
        path = [
            reentry_probe.PricePoint(anchor, 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=12), 0.80, "sell"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=90), 1.35, "buy"),
        ]

        scored = p.score_runner_retention_candidate(self._candidate(anchor=anchor), path)

        self.assertEqual(scored["retention_label"], "stop_first_collapse")
        self.assertEqual(scored["competing_event"], "stop_first")
        self.assertFalse(scored["runner_retention_positive"])

    def test_scores_flat_timeout_without_target_or_stop(self):
        anchor = dt.datetime(2026, 5, 26, 1, 36, 3)
        path = [
            reentry_probe.PricePoint(anchor, 1.0, "anchor"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=200), 1.08, "buy"),
            reentry_probe.PricePoint(anchor + dt.timedelta(seconds=500), 0.97, "sell"),
        ]

        scored = p.score_runner_retention_candidate(self._candidate(anchor=anchor), path)

        self.assertEqual(scored["retention_label"], "flat_timeout")
        self.assertEqual(scored["competing_event"], "flat_timeout")
        self.assertFalse(scored["runner_retention_positive"])

    def test_build_support_report_requires_live_support_even_when_offline_passes(self):
        offline = {
            "train": [{"token": f"0xtrain{i}", "runner_retention_positive": True} for i in range(5)],
            "validation": [{"token": f"0xval{i}", "runner_retention_positive": True} for i in range(3)],
            "final": [{"token": f"0xfinal{i}", "runner_retention_positive": True} for i in range(3)],
        }
        live_attribution = {
            "rejected_signal_paths": {
                "class_counts": {"slow_runner": 1, "flat_timeout": 13, "stop_first": 3},
                "policy_counts": {"conditional_slow_hold": 1, "skip": 16},
            }
        }

        report = p.build_support_report(
            offline_candidates_by_split=offline,
            live_attribution=live_attribution,
            min_train_positives=5,
            min_validation_positives=3,
            min_final_positives=3,
            min_live_positives=3,
        )

        self.assertEqual(report["support_gate"]["offline_status"], "PASS_OFFLINE_SUPPORT")
        self.assertTrue(report["support_gate"]["offline_token_passes_support_gate"])
        self.assertEqual(report["support_gate"]["validation_positive_tokens"], 3)
        self.assertEqual(report["go_no_go"]["status"], "NO_GO_FOR_LIVE_SWITCH")
        self.assertIn("live slow-runner support 1 < 3", report["go_no_go"]["reason"])
        self.assertEqual(report["live_support"]["slow_runner_count"], 1)

        text = p.to_json_text(report)
        self.assertNotIn("NaN", text)
        self.assertIsInstance(json.loads(text), dict)

    def test_build_support_report_fails_when_samples_duplicate_one_token(self):
        offline = {
            "train": [{"token": "0xdupe", "runner_retention_positive": True} for _ in range(5)],
            "validation": [{"token": "0xdupe", "runner_retention_positive": True} for _ in range(3)],
            "final": [{"token": "0xdupe", "runner_retention_positive": True} for _ in range(3)],
        }

        report = p.build_support_report(
            offline_candidates_by_split=offline,
            live_attribution={"rejected_signal_paths": {"class_counts": {"slow_runner": 3}}},
            min_train_positives=5,
            min_validation_positives=3,
            min_final_positives=3,
            min_live_positives=3,
        )

        self.assertEqual(report["support_gate"]["offline_status"], "NO_GO_OFFLINE_SUPPORT")
        self.assertFalse(report["support_gate"]["offline_token_passes_support_gate"])
        self.assertEqual(report["support_gate"]["train_positive_tokens"], 1)
