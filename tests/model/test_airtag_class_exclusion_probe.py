import datetime as dt
import json
import math
import unittest

from src.pipeline import airtag_class_exclusion_probe as p


def _row(symbol, policy, barrier_class, prob, pred_return, volume_30s):
    return {
        "symbol": symbol,
        "token": f"0x{symbol}",
        "recommended_policy": policy,
        "barrier_class": barrier_class,
        "first_barrier": barrier_class,
        "prob": prob,
        "pred_return": pred_return,
        "entry_volume_30s": volume_30s,
        "time_to_plus_25_seconds": 6.0 if policy == "quick_take_profit" else None,
        "time_to_minus_18_seconds": 5.0 if barrier_class == "stop_first" else 82.0,
        "mfe_pct": 25.0 if policy == "quick_take_profit" else 0.9,
        "mae_pct": -18.5 if barrier_class == "stop_first" else -12.0,
    }


class TestAirTagClassExclusionProbe(unittest.TestCase):
    def test_builds_pooled_probe_with_airtag_class_high_volume_false_positives(self):
        first = {
            "candidate_counts": {"per_token_candidates": 3},
            "candidate_sample": [
                _row("AirTag", "skip", "stop_first", 0.987188, 5.2271, 2.0350),
                _row("cat", "quick_take_profit", "fast_profit_then_collapse", 0.987461, 7.3059, 1.7218),
                _row("rice", "quick_take_profit", "fast_profit", 0.986, 5.5, 1.1),
            ],
        }
        second = {
            "candidate_counts": {"per_token_candidates": 2},
            "candidate_sample": [
                _row("95152", "skip", "stop_first", 0.989431, 5.5426, 2.0247),
                _row("ZCP", "quick_take_profit", "fast_profit", 0.988, 9.0, 1.2),
            ],
        }

        report = p.build_exclusion_probe_report(
            time_to_barrier_reports=[first, second],
            source_names=["first.json", "second.json"],
            generated_at=dt.datetime(2026, 5, 23, 11, 43, 47),
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertEqual(report["candidate_counts"]["input_candidates"], 5)
        self.assertEqual(report["candidate_counts"]["positive_candidates"], 3)
        self.assertEqual(report["candidate_counts"]["negative_candidates"], 2)
        self.assertEqual(report["schema_normalization"]["canonical_volume_field"], "entry_volume_30s")

        strata = {row["stratum"]: row for row in report["strata"]}
        high_volume = strata["high_prob_positive_pred_volume_gte_high_cut"]
        self.assertEqual(high_volume["selected_count"], 3)
        self.assertEqual(high_volume["positive_count"], 1)
        self.assertEqual(high_volume["negative_symbols"], ["AirTag", "95152"])
        self.assertGreater(high_volume["precision_wilson_95"]["high"], high_volume["precision"])

        medium_volume = strata["high_prob_positive_pred_volume_floor_to_high_cut"]
        self.assertEqual(medium_volume["selected_count"], 2)
        self.assertEqual(medium_volume["positive_count"], 2)
        self.assertEqual(medium_volume["precision"], 1.0)

        watchpoint = report["airtag_class_watchpoint"]
        self.assertEqual(watchpoint["false_positive_symbols"], ["AirTag", "95152"])
        self.assertEqual(watchpoint["high_prob_positive_pred_high_volume_selected_count"], 3)
        self.assertEqual(report["decision"], "probe_only_small_sample_airtag_class_watchpoint")

        sweep = {row["stratum"]: row for row in report["volume_boundary_sweep"]}
        self.assertEqual(sweep["high_prob_positive_pred_volume_gte_1.5"]["selected_count"], 3)
        self.assertEqual(sweep["high_prob_positive_pred_volume_lt_1.5"]["selected_count"], 2)

    def test_build_report_validates_inputs(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            p.build_exclusion_probe_report(time_to_barrier_reports=[])

        with self.assertRaisesRegex(ValueError, "source_names length"):
            p.build_exclusion_probe_report(
                time_to_barrier_reports=[{"candidate_sample": []}],
                source_names=["one", "two"],
            )

        with self.assertRaisesRegex(ValueError, "volume_cuts"):
            p.build_exclusion_probe_report(
                time_to_barrier_reports=[{"candidate_sample": []}],
                volume_cuts=[],
            )

    def test_evaluate_stratum_rejects_ex_post_condition_fields(self):
        with self.assertRaisesRegex(ValueError, "not decision-time"):
            p.evaluate_stratum(
                name="leaky",
                conditions=[{"field": "barrier_class", "op": "==", "value": "stop_first"}],
                candidates=[],
            )

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
