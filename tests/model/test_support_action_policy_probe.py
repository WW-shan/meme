import json
import math
import types
import unittest
from decimal import Decimal

from src.pipeline import support_action_policy_probe as p


class TestSupportActionPolicyProbe(unittest.TestCase):
    def test_evaluates_decision_time_rule_without_future_fields(self):
        candidates = [
            {
                "symbol": "Arnold",
                "recommended_policy": "quick_take_profit",
                "barrier_class": "fast_profit",
                "prob": 0.987,
                "pred_return": 32.0,
                "entry_volume_30s": 2.1,
                "entry_price_volatility": 0.29,
                "age_seconds": 289.0,
                "mfe_pct": 334.0,
            },
            {
                "symbol": "MEMES",
                "recommended_policy": "skip",
                "barrier_class": "stop_first",
                "prob": 0.987,
                "pred_return": -34.0,
                "entry_volume_30s": 7.2,
                "entry_price_volatility": 0.33,
                "age_seconds": 2.0,
                "mfe_pct": 89.0,
            },
        ]

        result = p.evaluate_rule(
            p.Rule(
                name="high_prob_positive_pred",
                conditions=(
                    p.Condition("prob", ">=", 0.985),
                    p.Condition("pred_return", ">=", 5.0),
                ),
            ),
            candidates,
        )

        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["positive_count"], 1)
        self.assertEqual(result["negative_count"], 0)
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["selected_symbols"], ["Arnold"])
        self.assertNotIn("mfe_pct", result["conditions"][0])

    def test_rejects_rules_that_use_ex_post_fields(self):
        for field in (
            "mfe_pct",
            "mae_pct",
            "time_to_profit_seconds",
            "time_to_stop_seconds",
            "first_barrier",
            "barrier_class",
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "not decision-time"):
                    p.Rule(name="leaky", conditions=(p.Condition(field, ">=", 25.0),))

    def test_rejects_unsupported_operators(self):
        with self.assertRaisesRegex(ValueError, "unsupported operator"):
            p.Rule(name="bad_op", conditions=(p.Condition("prob", "between", (0.9, 1.0)),))

    def test_rejects_non_condition_objects_that_try_to_use_ex_post_fields(self):
        with self.assertRaisesRegex(ValueError, "exact Condition"):
            p.Rule(
                name="namespace_leak",
                conditions=(types.SimpleNamespace(field="mfe_pct", op=">=", value=25.0),),
            )

        with self.assertRaisesRegex(ValueError, "rules must be Rule"):
            p.build_support_report(
                time_to_barrier_report={
                    "candidate_sample": [{"symbol": "LEAK", "recommended_policy": "skip", "mfe_pct": 99.0}]
                },
                rules=[types.SimpleNamespace(name="fake", conditions=(types.SimpleNamespace(field="mfe_pct", op=">=", value=25.0),))],
            )

    def test_rejects_condition_subclasses_and_condition_generators(self):
        class FakeCondition(p.Condition):
            def __post_init__(self):
                pass

        with self.assertRaisesRegex(ValueError, "exact Condition"):
            p.Rule(
                name="subclass_leak",
                conditions=(FakeCondition("mfe_pct", ">=", 25.0),),
            )

        with self.assertRaisesRegex(ValueError, "non-empty tuple"):
            p.Rule(
                name="generator_conditions",
                conditions=(p.Condition("prob", ">=", 0.5) for _ in range(1)),
            )

    def test_rejects_tuple_subclass_conditions_and_rule_subclasses(self):
        class FakeTuple(tuple):
            pass

        class FakeRule(p.Rule):
            pass

        condition = p.Condition("prob", ">=", 0.5)
        with self.assertRaisesRegex(ValueError, "non-empty tuple"):
            p.Rule(name="tuple_subclass", conditions=FakeTuple((condition,)))

        fake_rule = FakeRule("fake_rule", (condition,))
        with self.assertRaisesRegex(ValueError, "rules must be Rule"):
            p.evaluate_rule(fake_rule, [{"symbol": "A", "recommended_policy": "skip", "prob": 0.99}])

    def test_build_report_rejects_top_level_rule_generators(self):
        rules = (rule for rule in [p.Rule("prob_only", (p.Condition("prob", ">=", 0.5),))])

        with self.assertRaisesRegex(ValueError, "rules must be a list or tuple"):
            p.build_support_report(
                time_to_barrier_report={"candidate_sample": []},
                rules=rules,
            )

    def test_revalidates_mutated_condition_fields_at_match_time(self):
        condition = p.Condition("prob", ">=", 0.5)
        rule = p.Rule("mutated_condition", (condition,))
        object.__setattr__(condition, "field", "mfe_pct")

        with self.assertRaisesRegex(ValueError, "not decision-time"):
            p.evaluate_rule(rule, [{"symbol": "LEAK", "recommended_policy": "quick_take_profit", "mfe_pct": 99.0}])

        with self.assertRaisesRegex(ValueError, "not decision-time"):
            p.evaluate_rule(rule, [])

    def test_revalidates_mutated_rule_conditions_before_scanning_candidates(self):
        rule = p.Rule("mutated_rule", (p.Condition("prob", ">=", 0.5),))
        object.__setattr__(rule, "conditions", [])

        with self.assertRaisesRegex(ValueError, "non-empty tuple"):
            p.evaluate_rule(rule, [{"symbol": "MATCH_ALL", "recommended_policy": "quick_take_profit", "prob": 0.99}])

    def test_build_report_keeps_read_only_contract_and_ranks_rules(self):
        candidates = [
            {"symbol": "A", "recommended_policy": "quick_take_profit", "prob": 0.99, "pred_return": 10.0},
            {"symbol": "B", "recommended_policy": "skip", "prob": 0.99, "pred_return": -2.0},
            {"symbol": "C", "recommended_policy": "quick_take_profit", "prob": 0.97, "pred_return": 8.0},
        ]

        report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates, "candidate_counts": {"per_token_candidates": 3}},
            rules=[
                p.Rule("prob_pred", (p.Condition("prob", ">=", 0.985), p.Condition("pred_return", ">=", 5.0))),
                p.Rule("prob_only", (p.Condition("prob", ">=", 0.985),)),
            ],
            min_selected=1,
        )

        self.assertTrue(report["probe_contract"]["read_only"])
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertFalse(report["probe_contract"]["safe_for_live_switch"])
        self.assertEqual(report["rule_results"][0]["rule"], "prob_pred")
        self.assertEqual(report["rule_results"][0]["positive_count"], 1)
        report["nonfinite_check"] = {"nan": math.nan, "inf": math.inf, "neg_inf": -math.inf}
        text = p.to_json_text(report)
        self.assertNotIn("NaN", text)
        self.assertNotIn("Infinity", text)
        parsed = json.loads(text)
        self.assertIsNone(parsed["nonfinite_check"]["nan"])
        self.assertIsNone(parsed["nonfinite_check"]["inf"])
        self.assertIsNone(parsed["nonfinite_check"]["neg_inf"])

    def test_build_report_marks_truncated_candidate_samples(self):
        report = p.build_support_report(
            time_to_barrier_report={
                "candidate_sample": [
                    {"symbol": "A", "recommended_policy": "quick_take_profit", "prob": 0.99, "pred_return": 10.0},
                    {"symbol": "B", "recommended_policy": "skip", "prob": 0.99, "pred_return": -2.0},
                ],
                "candidate_counts": {"per_token_candidates": 5},
            },
            rules=[p.Rule("prob_only", (p.Condition("prob", ">=", 0.985),))],
            min_selected=1,
        )

        self.assertTrue(report["candidate_counts"]["sample_limited"])
        self.assertEqual(report["candidate_counts"]["unscored_reported_candidates"], 3)

    def test_default_rules_include_low_probability_hard_abstain_evidence(self):
        candidates = [
            {"symbol": "LOW_A", "recommended_policy": "skip", "prob": 0.939, "pred_return": 80.0},
            {"symbol": "LOW_B", "recommended_policy": "skip", "prob": 0.50, "pred_return": 12.0},
            {"symbol": "BOUNDARY", "recommended_policy": "quick_take_profit", "prob": 0.94, "pred_return": 8.0},
            {"symbol": "HIGH", "recommended_policy": "quick_take_profit", "prob": 0.99, "pred_return": 8.0},
        ]

        report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            min_selected=1,
        )

        hard_abstain = next(row for row in report["rule_results"] if row["rule"] == "low_prob_hard_abstain")
        self.assertEqual(hard_abstain["selected_count"], 2)
        self.assertEqual(hard_abstain["positive_count"], 0)
        self.assertEqual(hard_abstain["negative_count"], 2)
        self.assertEqual(hard_abstain["negative_symbols"], ["LOW_A", "LOW_B"])
        self.assertNotIn(
            "low_prob_hard_abstain",
            {row["rule"] for row in report["eligible_rule_results"]},
        )

    def test_allows_decision_time_flow_toxicity_rules(self):
        candidates = [
            {
                "symbol": "CLEAN_FLOW",
                "recommended_policy": "quick_take_profit",
                "prob": 0.988,
                "pred_return": 12.0,
                "flow_sell_pressure_10s": 0.10,
                "flow_signed_imbalance_30s": 0.60,
                "flow_buy_sell_overlap_ratio_60s": 0.10,
            },
            {
                "symbol": "TOXIC_FLOW",
                "recommended_policy": "skip",
                "prob": 0.989,
                "pred_return": 48.0,
                "flow_sell_pressure_10s": 0.80,
                "flow_signed_imbalance_30s": -0.70,
                "flow_buy_sell_overlap_ratio_60s": 0.95,
            },
        ]

        report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[
                p.Rule(
                    "clean_flow_high_prob",
                    (
                        p.Condition("prob", ">=", 0.985),
                        p.Condition("flow_sell_pressure_10s", "<=", 0.35),
                        p.Condition("flow_signed_imbalance_30s", ">=", 0.0),
                        p.Condition("flow_buy_sell_overlap_ratio_60s", "<=", 0.5),
                    ),
                )
            ],
            min_selected=1,
        )

        self.assertEqual(report["rule_results"][0]["selected_symbols"], ["CLEAN_FLOW"])
        self.assertEqual(report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(report["rule_results"][0]["negative_count"], 0)

    def test_low_probability_hard_abstain_is_never_eligible_even_with_positive_label(self):
        candidates = [
            {"symbol": "LOW_POSITIVE", "recommended_policy": "quick_take_profit", "prob": 0.939, "pred_return": 80.0},
            {"symbol": "LOW_SKIP", "recommended_policy": "skip", "prob": 0.50, "pred_return": 12.0},
        ]

        report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            min_selected=1,
        )

        hard_abstain = next(row for row in report["rule_results"] if row["rule"] == "low_prob_hard_abstain")
        self.assertEqual(hard_abstain["selected_count"], 2)
        self.assertEqual(hard_abstain["positive_count"], 1)
        self.assertNotIn(
            "low_prob_hard_abstain",
            {row["rule"] for row in report["eligible_rule_results"]},
        )

        renamed_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[p.Rule("renamed_low_prob_bucket", (p.Condition("prob", "<", 0.94),))],
            min_selected=1,
        )
        self.assertEqual(renamed_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(renamed_report["eligible_rule_results"], [])

        string_value_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[p.Rule("renamed_low_prob_string_bucket", (p.Condition("prob", "<", "0.94"),))],
            min_selected=1,
        )
        self.assertEqual(string_value_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(string_value_report["eligible_rule_results"], [])

        decimal_value_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[p.Rule("renamed_low_prob_decimal_bucket", (p.Condition("prob", "<", Decimal("0.94")),))],
            min_selected=1,
        )
        self.assertEqual(decimal_value_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(decimal_value_report["eligible_rule_results"], [])

        equivalent_threshold_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[p.Rule("renamed_low_prob_lte_bucket", (p.Condition("prob", "<=", 0.939999999),))],
            min_selected=1,
        )
        self.assertEqual(equivalent_threshold_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(equivalent_threshold_report["eligible_rule_results"], [])

        near_boundary_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[p.Rule("renamed_low_prob_float_bucket", (p.Condition("prob", "<", 0.940000001),))],
            min_selected=1,
        )
        self.assertEqual(near_boundary_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(near_boundary_report["eligible_rule_results"], [])

        narrowed_low_prob_report = p.build_support_report(
            time_to_barrier_report={"candidate_sample": candidates},
            rules=[
                p.Rule(
                    "renamed_low_prob_with_pred_bucket",
                    (p.Condition("prob", "<", 0.94), p.Condition("pred_return", ">=", 50.0)),
                )
            ],
            min_selected=1,
        )
        self.assertEqual(narrowed_low_prob_report["rule_results"][0]["positive_count"], 1)
        self.assertEqual(narrowed_low_prob_report["eligible_rule_results"], [])

    def test_build_pooled_report_tracks_source_counts_flow_presence_and_gate(self):
        report_a = {
            "candidate_sample": [
                {
                    "symbol": "A",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.989,
                    "flow_event_count_30s": 2,
                    "flow_buy_sell_overlap_ratio_60s": 0.10,
                    "flow_recent_seller_reentry_ratio_30s": 0.00,
                }
            ],
            "candidate_counts": {"per_token_candidates": 1},
        }
        report_b = {
            "candidate_sample": [
                {
                    "symbol": "B",
                    "recommended_policy": "quick_take_profit",
                    "prob": 0.990,
                    "flow_event_count_30s": 3,
                    "flow_buy_sell_overlap_ratio_60s": 0.20,
                    "flow_recent_seller_reentry_ratio_30s": 0.10,
                },
                {
                    "symbol": "C",
                    "recommended_policy": "skip",
                    "prob": 0.991,
                    "flow_event_count_30s": 4,
                    "flow_buy_sell_overlap_ratio_60s": 0.90,
                    "flow_recent_seller_reentry_ratio_30s": 0.80,
                },
            ],
            "candidate_counts": {"per_token_candidates": 2},
        }

        pooled = p.build_pooled_support_report(
            time_to_barrier_reports=[report_a, report_b],
            source_names=["day_a", "day_b"],
            min_selected=1,
            min_pooled_selected=2,
            min_pooled_positive=2,
        )

        self.assertEqual(pooled["candidate_counts"]["input_reports"], 2)
        self.assertEqual(pooled["candidate_counts"]["input_candidates"], 3)
        self.assertEqual(pooled["candidate_counts"]["positive_candidates"], 2)
        self.assertTrue(pooled["flow_feature_presence"]["required_fields_complete"])
        self.assertTrue(pooled["evidence_gate"]["passes"])
        self.assertEqual(pooled["evidence_gate"]["target_rule"], "high_prob_low_toxic_overlap")
        self.assertEqual(pooled["evidence_gate"]["selected_count"], 2)
        self.assertEqual(pooled["evidence_gate"]["positive_count"], 2)
        self.assertEqual(pooled["decision"], "expanded_evidence_pass")

    def test_build_pooled_report_downgrades_missing_flow_or_small_support(self):
        pooled = p.build_pooled_support_report(
            time_to_barrier_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "A",
                            "recommended_policy": "quick_take_profit",
                            "prob": 0.989,
                            "flow_event_count_30s": 2,
                        }
                    ],
                    "candidate_counts": {"per_token_candidates": 1},
                }
            ],
            source_names=["one_day"],
            min_selected=1,
            min_pooled_selected=30,
            min_pooled_positive=12,
        )

        self.assertFalse(pooled["flow_feature_presence"]["required_fields_complete"])
        self.assertFalse(pooled["evidence_gate"]["passes"])
        self.assertEqual(pooled["decision"], "missing_flow_feature_parity")

    def test_build_pooled_report_marks_complete_flow_small_support_as_diagnostic_only(self):
        pooled = p.build_pooled_support_report(
            time_to_barrier_reports=[
                {
                    "candidate_sample": [
                        {
                            "symbol": "A",
                            "recommended_policy": "quick_take_profit",
                            "prob": 0.989,
                            "flow_event_count_30s": 2,
                            "flow_buy_sell_overlap_ratio_60s": 0.10,
                            "flow_recent_seller_reentry_ratio_30s": 0.00,
                        },
                        {
                            "symbol": "B",
                            "recommended_policy": "skip",
                            "prob": 0.990,
                            "flow_event_count_30s": 3,
                            "flow_buy_sell_overlap_ratio_60s": 0.20,
                            "flow_recent_seller_reentry_ratio_30s": 0.10,
                        },
                    ],
                    "candidate_counts": {"per_token_candidates": 2},
                }
            ],
            source_names=["one_day"],
            min_selected=1,
            min_pooled_selected=30,
            min_pooled_positive=12,
        )

        self.assertTrue(pooled["flow_feature_presence"]["required_fields_complete"])
        self.assertFalse(pooled["evidence_gate"]["passes"])
        self.assertEqual(pooled["evidence_gate"]["selected_count"], 2)
        self.assertEqual(pooled["evidence_gate"]["positive_count"], 1)
        self.assertEqual(pooled["decision"], "diagnostic_only_small_sample")


if __name__ == "__main__":
    unittest.main()
