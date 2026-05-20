import datetime as dt
import json
import math
import unittest

from src.pipeline import counterfactual_action_probe as p


class TestCounterfactualActionProbe(unittest.TestCase):
    def test_classifies_rejected_fast_profit_as_rescue_quick_tp_only_when_quality_gate_passes(self):
        candidate = {
            "token": "0xA",
            "symbol": "Arnold",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "fast_profit",
            "recommended_policy": "quick_take_profit",
            "reason": "pred_return_below_min",
            "prob": 0.9879,
            "pred_return": 32.17,
            "mfe_pct": 334.6,
            "mae_pct": -9.7,
            "time_to_plus_25_seconds": 56.9,
            "time_to_minus_18_seconds": None,
        }

        result = p.classify_time_to_barrier_action(candidate)

        self.assertEqual(result["action"], "rescue_quick_tp")
        self.assertEqual(result["evidence_class"], "fast_profit")
        self.assertTrue(result["eligible"])
        self.assertEqual(result["risk_policy"], "quick_take_profit_only")

    def test_keeps_high_mfe_stop_first_or_negative_score_as_skip(self):
        stop_first = {
            "token": "0xB",
            "symbol": "MEMES",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "stop_first",
            "recommended_policy": "skip",
            "prob": 0.987,
            "pred_return": -34.0,
            "mfe_pct": 89.0,
            "mae_pct": -23.0,
            "time_to_plus_25_seconds": 10.8,
            "time_to_minus_18_seconds": 1.8,
        }

        result = p.classify_time_to_barrier_action(stop_first)

        self.assertEqual(result["action"], "skip")
        self.assertFalse(result["eligible"])
        self.assertIn("stop_first", result["reject_reasons"])

    def test_classifies_slow_runner_as_conditional_slow_hold(self):
        slow_runner = {
            "token": "0xS",
            "symbol": "SLOW",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "slow_runner",
            "recommended_policy": "conditional_slow_hold",
            "prob": 0.986,
            "pred_return": 31.0,
            "mfe_pct": 120.0,
            "mae_pct": -6.0,
            "time_to_plus_25_seconds": 180.0,
        }

        result = p.classify_time_to_barrier_action(slow_runner)

        self.assertEqual(result["action"], "conditional_slow_hold")
        self.assertTrue(result["eligible"])
        self.assertEqual(result["risk_policy"], "conditional_hold_probe_only")
        self.assertEqual(result["reject_reasons"], [])

    def test_classifies_post_target_collapse_as_lock_and_continuation_as_hold(self):
        collapse = {
            "token": "0xC",
            "symbol": "CMC",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "post_target_collapse",
            "recommended_policy": "lock_profit",
            "target_hit": True,
            "time_to_target_seconds": 225.0,
            "time_to_post_target_collapse_seconds": 260.0,
        }
        continuation = {
            "token": "0xD",
            "symbol": "RUN",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "post_target_continuation",
            "recommended_policy": "continue_hold",
            "target_hit": True,
            "time_to_target_seconds": 30.0,
            "time_to_continuation_seconds": 55.0,
        }

        self.assertEqual(p.classify_post_target_action(collapse)["action"], "post_target_lock")
        self.assertEqual(p.classify_post_target_action(continuation)["action"], "continue_hold")

    def test_target_not_hit_maps_to_declared_monitor_action_not_extra_action(self):
        target_not_hit = {
            "token": "0xN",
            "symbol": "NO_TARGET",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "target_not_hit",
            "recommended_policy": "no_action",
            "target_hit": False,
        }

        result = p.classify_post_target_action(target_not_hit)

        self.assertEqual(result["action"], "monitor_after_target")
        self.assertFalse(result["eligible"])

    def test_nonfinite_mae_rejects_candidate_and_serializes_strict_json(self):
        candidate = {
            "token": "0xNAN",
            "symbol": "NAN",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "fast_profit",
            "recommended_policy": "quick_take_profit",
            "prob": 0.99,
            "pred_return": 35.0,
            "mfe_pct": math.inf,
            "mae_pct": math.nan,
            "time_to_plus_25_seconds": 20.0,
        }

        result = p.classify_time_to_barrier_action(candidate)
        text = p.to_json_text({"result": result})

        self.assertEqual(result["action"], "skip")
        self.assertIn("mae_missing_or_nonfinite", result["reject_reasons"])
        self.assertNotIn("NaN", text)
        self.assertNotIn("Infinity", text)
        self.assertIsNone(json.loads(text)["result"]["mae_pct"])

    def test_nonfinite_profit_evidence_rejects_time_to_barrier_candidate(self):
        for field in ("mfe_pct", "time_to_plus_25_seconds"):
            with self.subTest(field=field):
                candidate = {
                    "token": "0xBAD",
                    "symbol": "BAD",
                    "candidate_type": "rejected_signal_time_to_barrier",
                    "barrier_class": "fast_profit",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.99,
                    "pred_return": 35.0,
                    "mfe_pct": 80.0,
                    "mae_pct": -5.0,
                    "time_to_plus_25_seconds": 12.0,
                }
                candidate[field] = math.inf

                result = p.classify_time_to_barrier_action(candidate)

                self.assertEqual(result["action"], "skip")
                self.assertFalse(result["eligible"])
                self.assertIn(f"{field}_missing_or_nonfinite", result["reject_reasons"])

    def test_missing_path_rejects_time_to_barrier_candidate_before_eligible_action(self):
        candidate = {
            "token": "0xMISS",
            "symbol": "MISS",
            "candidate_type": "rejected_signal_time_to_barrier",
            "barrier_class": "fast_profit",
            "recommended_policy": "quick_take_profit",
            "prob": 0.99,
            "pred_return": 35.0,
            "mfe_pct": 80.0,
            "mae_pct": -5.0,
            "time_to_plus_25_seconds": 12.0,
            "missing_path": True,
        }

        result = p.classify_time_to_barrier_action(candidate)

        self.assertEqual(result["action"], "skip")
        self.assertFalse(result["eligible"])
        self.assertIn("missing_path", result["reject_reasons"])

    def test_nonfinite_post_target_timings_reject_post_target_action(self):
        cases = [
            (
                "collapse_target_time",
                {
                    "classification": "post_target_collapse",
                    "target_hit": True,
                    "time_to_target_seconds": math.inf,
                    "time_to_post_target_collapse_seconds": 260.0,
                },
                "time_to_target_seconds_missing_or_nonfinite",
            ),
            (
                "collapse_time",
                {
                    "classification": "post_target_collapse",
                    "target_hit": True,
                    "time_to_target_seconds": 225.0,
                    "time_to_post_target_collapse_seconds": math.nan,
                },
                "time_to_post_target_collapse_seconds_missing_or_nonfinite",
            ),
            (
                "continuation_time",
                {
                    "classification": "post_target_continuation",
                    "target_hit": True,
                    "time_to_target_seconds": 30.0,
                    "time_to_continuation_seconds": math.inf,
                },
                "time_to_continuation_seconds_missing_or_nonfinite",
            ),
        ]
        for name, candidate, reason in cases:
            with self.subTest(name=name):
                result = p.classify_post_target_action(candidate)

                self.assertEqual(result["action"], "monitor_after_target")
                self.assertFalse(result["eligible"])
                self.assertIn(reason, result["reject_reasons"])

    def test_missing_path_rejects_post_target_action_before_eligible_action(self):
        candidate = {
            "token": "0xMISS",
            "symbol": "MISS",
            "candidate_type": "accepted_trade_post_target_exit_state",
            "classification": "post_target_collapse",
            "target_hit": True,
            "time_to_target_seconds": 225.0,
            "time_to_post_target_collapse_seconds": 260.0,
            "missing_path": True,
        }

        result = p.classify_post_target_action(candidate)

        self.assertEqual(result["action"], "monitor_after_target")
        self.assertFalse(result["eligible"])
        self.assertIn("missing_path", result["reject_reasons"])

    def test_build_action_report_counts_sources_actions_and_keeps_read_only_contract(self):
        report = p.build_action_report(
            time_to_barrier_report={
                "probe_contract": {"read_only": True, "live_switch_evidence": False},
                "candidate_sample": [
                    {
                        "token": "0xA",
                        "symbol": "Arnold",
                        "candidate_type": "rejected_signal_time_to_barrier",
                        "barrier_class": "fast_profit",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.9879,
                        "pred_return": 32.17,
                        "mfe_pct": 334.6,
                        "mae_pct": -9.7,
                        "time_to_plus_25_seconds": 56.9,
                    },
                    {
                        "token": "0xB",
                        "symbol": "MEMES",
                        "candidate_type": "rejected_signal_time_to_barrier",
                        "barrier_class": "stop_first",
                        "recommended_policy": "skip",
                        "prob": 0.987,
                        "pred_return": -34.0,
                        "mfe_pct": 89.0,
                        "mae_pct": -23.0,
                    },
                ],
            },
            post_target_report={
                "probe_contract": {"read_only": True, "live_switch_evidence": False},
                "candidate_sample": [
                    {
                        "token": "0xC",
                        "symbol": "CMC",
                        "candidate_type": "accepted_trade_post_target_exit_state",
                        "classification": "post_target_collapse",
                        "recommended_policy": "lock_profit",
                        "target_hit": True,
                        "time_to_target_seconds": 225.0,
                        "time_to_post_target_collapse_seconds": 260.0,
                    }
                ],
            },
            generated_at=dt.datetime(2026, 5, 21, 7, 0, 0),
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["causal_policy"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertTrue(report["evidence_scope"]["action_labels_use_ex_post_outcomes"])
        self.assertEqual(report["evidence_scope"]["intended_use"], "oracle_taxonomy_for_replay_experiment_design")
        self.assertEqual(report["source_counts"]["time_to_barrier_candidates"], 2)
        self.assertEqual(report["source_counts"]["post_target_candidates"], 1)
        self.assertEqual(report["action_counts"]["rescue_quick_tp"], 1)
        self.assertEqual(report["action_counts"]["skip"], 1)
        self.assertEqual(report["action_counts"]["post_target_lock"], 1)
        self.assertEqual(report["action_counts"]["conditional_slow_hold"], 0)
        self.assertEqual(
            report["action_taxonomy"],
            [
                "skip",
                "rescue_quick_tp",
                "conditional_slow_hold",
                "post_target_lock",
                "continue_hold",
                "monitor_after_target",
            ],
        )
        self.assertEqual(report["decision"], "probe_only_replay_required")
        json.loads(p.to_json_text(report))

    def test_build_action_report_marks_truncated_candidate_sample_as_sample_limited(self):
        report = p.build_action_report(
            time_to_barrier_report={
                "candidate_counts": {"per_token_candidates": 101},
                "candidate_sample": [
                    {
                        "token": "0xA",
                        "symbol": "A",
                        "barrier_class": "fast_profit",
                        "prob": 0.99,
                        "pred_return": 31.0,
                        "mae_pct": -1.0,
                    }
                ],
            },
            post_target_report={"candidate_sample": []},
            generated_at=dt.datetime(2026, 5, 21, 7, 0, 0),
        )

        self.assertEqual(report["decision"], "probe_only_sample_limited")
        self.assertEqual(report["source_counts"]["time_to_barrier_candidates"], 1)
        self.assertEqual(report["source_counts"]["time_to_barrier_reported_candidates"], 101)
        self.assertEqual(report["input_warnings"][0]["warning"], "input_report_only_contains_truncated_candidate_sample")

    def test_build_action_report_marks_truncated_action_sample_explicitly(self):
        report = p.build_action_report(
            time_to_barrier_report={
                "candidates": [
                    {
                        "token": f"0x{i}",
                        "symbol": f"T{i}",
                        "barrier_class": "flat_timeout",
                        "prob": 0.1,
                        "pred_return": 0.0,
                        "mfe_pct": 0.0,
                        "mae_pct": 0.0,
                    }
                    for i in range(205)
                ],
            },
            post_target_report={"candidates": []},
            generated_at=dt.datetime(2026, 5, 21, 7, 0, 0),
        )

        self.assertEqual(report["actions_total"], 205)
        self.assertEqual(len(report["actions"]), 200)
        self.assertEqual(report["action_sample"]["included"], 200)
        self.assertEqual(report["action_sample"]["total"], 205)
        self.assertTrue(report["action_sample"]["truncated"])
        self.assertEqual(report["action_sample"]["warning"], "actions_field_is_truncated_sample")


if __name__ == "__main__":
    unittest.main()
