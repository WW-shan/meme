import datetime as dt
import json
import math
import unittest

from src.pipeline import age_gate_exclusion_probe as p


def _row(symbol, policy, barrier_class, age_seconds, volume_30s, prob=0.989, pred_return=10.0):
    return {
        "symbol": symbol,
        "token": f"0x{symbol}",
        "recommended_policy": policy,
        "barrier_class": barrier_class,
        "first_barrier": "-18" if barrier_class == "stop_first" else "+25",
        "prob": prob,
        "pred_return": pred_return,
        "age_seconds": age_seconds,
        "token_age_seconds": age_seconds,
        "entry_volume_30s": volume_30s,
        "volume_30s": volume_30s,
        "time_to_plus_25_seconds": 8.0 if policy == "quick_take_profit" else None,
        "time_to_minus_18_seconds": 29.0 if barrier_class == "stop_first" else 82.0,
        "mfe_pct": 25.0 if policy == "quick_take_profit" else 0.9,
        "mae_pct": -18.5 if barrier_class == "stop_first" else -12.0,
    }


class TestAgeGateExclusionProbe(unittest.TestCase):
    def test_builds_pooled_age_gate_probe_with_age_and_volume_cells(self):
        first = {
            "candidate_counts": {"per_token_candidates": 3},
            "candidate_sample": [
                _row("AirTag", "skip", "stop_first", 5.0, 2.035),
                _row("cat", "quick_take_profit", "fast_profit_then_collapse", 3.0, 1.722),
                _row("rice", "quick_take_profit", "fast_profit", 0.0, 0.888),
            ],
        }
        second = {
            "candidate_counts": {"per_token_candidates": 4},
            "candidate_sample": [
                _row("diamond", "quick_take_profit", "fast_profit_then_collapse", 3.0, 1.428),
                _row("95152", "skip", "stop_first", 2.0, 2.025),
                _row("UncleDoge", "quick_take_profit", "fast_profit_then_collapse", 1.0, 0.991),
                _row("ZCP", "quick_take_profit", "fast_profit", 1.0, 0.789),
            ],
        }
        third = {
            "candidate_counts": {"per_token_candidates": 8},
            "candidate_sample": [
                _row("GM", "skip", "stop_first", 0.0, 2.475),
                _row("xiaoer", "quick_take_profit", "fast_profit", 3.0, 0.915),
                _row("diamondhand", "skip", "stop_first", 1.0, 0.86),
                _row("TripleB", "skip", "stop_first", 2.0, 1.209),
                _row("digitalid", "skip", "stop_first", 1.0, 1.27),
                _row("binancelevel", "quick_take_profit", "fast_profit_then_collapse", 1.0, 2.703),
                _row("DEMO", "skip", "stop_first", 1.0, 1.274),
                _row("tianzhou", "quick_take_profit", "fast_profit_then_collapse", 6.0, 2.526),
            ],
        }

        report = p.build_age_gate_probe_report(
            time_to_barrier_reports=[first, second, third],
            source_names=["first.json", "second.json", "third.json"],
            generated_at=dt.datetime(2026, 5, 23, 12, 13, 33),
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertEqual(report["candidate_counts"]["input_candidates"], 15)
        self.assertEqual(report["candidate_counts"]["positive_candidates"], 8)
        self.assertEqual(report["candidate_counts"]["negative_candidates"], 7)
        self.assertEqual(report["schema_normalization"]["canonical_age_field"], "age_seconds")

        age_sweep = {row["stratum"]: row for row in report["age_boundary_sweep"]}
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_0"]["selected_count"], 13)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_0"]["positive_count"], 7)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_1"]["selected_count"], 7)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_1"]["positive_count"], 4)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_2"]["selected_count"], 5)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_2"]["positive_count"], 4)
        self.assertEqual(age_sweep["high_prob_positive_pred_age_gt_2"]["negative_symbols"], ["AirTag"])

        strata = {row["stratum"]: row for row in report["strata"]}
        high_volume = strata["high_prob_positive_pred_age_gt_2_volume_gte_1.5"]
        self.assertEqual(high_volume["selected_count"], 3)
        self.assertEqual(high_volume["positive_count"], 2)
        self.assertEqual(high_volume["negative_symbols"], ["AirTag"])
        medium_volume = strata["high_prob_positive_pred_age_gt_2_volume_floor_to_1.5"]
        self.assertEqual(medium_volume["selected_count"], 2)
        self.assertEqual(medium_volume["positive_count"], 2)

        watchpoints = report["watchpoints"]
        self.assertEqual(watchpoints["age_zero"]["selected_count"], 2)
        self.assertEqual(watchpoints["age_zero"]["positive_symbols"], ["rice"])
        self.assertEqual(watchpoints["age_zero"]["negative_symbols"], ["GM"])
        self.assertEqual(watchpoints["age_le_primary_volume_gte_high"]["selected_count"], 3)
        self.assertEqual(watchpoints["age_le_primary_volume_gte_high"]["positive_symbols"], ["binancelevel"])
        self.assertEqual(
            watchpoints["age_le_primary_volume_gte_high"]["negative_symbols"],
            ["95152", "GM"],
        )
        self.assertEqual(report["decision"], "probe_only_age_gate_watchpoint")

    def test_build_report_validates_inputs(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            p.build_age_gate_probe_report(time_to_barrier_reports=[])

        with self.assertRaisesRegex(ValueError, "source_names length"):
            p.build_age_gate_probe_report(
                time_to_barrier_reports=[{"candidate_sample": []}],
                source_names=["one", "two"],
            )

        with self.assertRaisesRegex(ValueError, "age_cuts"):
            p.build_age_gate_probe_report(
                time_to_barrier_reports=[{"candidate_sample": []}],
                age_cuts=[],
            )

    def test_evaluate_stratum_rejects_ex_post_condition_fields(self):
        with self.assertRaisesRegex(ValueError, "not decision-time"):
            p.evaluate_stratum(
                name="leaky",
                conditions=[{"field": "barrier_class", "op": "==", "value": "stop_first"}],
                candidates=[],
            )

    def test_numeric_equality_matches_numeric_strings_for_age_zero_watchpoint(self):
        result = p.evaluate_stratum(
            name="age_zero",
            conditions=[{"field": "age_seconds", "op": "==", "value": 0.0}],
            candidates=[
                {"symbol": "GM", "age_seconds": "0", "recommended_policy": "skip"},
                {"symbol": "OLDER", "age_seconds": "1", "recommended_policy": "quick_take_profit"},
            ],
        )

        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["negative_symbols"], ["GM"])

    def test_to_json_text_sanitizes_nonfinite_values(self):
        text = p.to_json_text({"nan": math.nan, "nested": {"inf": math.inf, "ok": 1.0}})

        self.assertNotIn("NaN", text)
        self.assertNotIn("Infinity", text)
        parsed = json.loads(text)
        self.assertIsNone(parsed["nan"])
        self.assertIsNone(parsed["nested"]["inf"])
        self.assertEqual(parsed["nested"]["ok"], 1.0)


if __name__ == "__main__":
    unittest.main()
