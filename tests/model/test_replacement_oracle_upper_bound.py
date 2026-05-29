import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline import reentry_probe
from src.pipeline import replacement_oracle_upper_bound as oracle


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_replacement_oracle_upper_bound_diagnostic.py"
    spec = importlib.util.spec_from_file_location("run_replacement_oracle_upper_bound_diagnostic", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _point(seconds: float, price: float):
    return reentry_probe.PricePoint(
        reentry_probe.parse_time(1_800_000_000 + seconds),
        price,
        "test",
    )


class TestReplacementOracleUpperBound(unittest.TestCase):
    def test_anchor_price_excludes_future_points(self):
        anchor = reentry_probe.parse_time(1_800_000_000)
        path = [
            _point(-1, 1.00),
            _point(0.001, 1.25),
        ]

        self.assertEqual(oracle.anchor_price_at_or_before(path, anchor), 1.0)

    def test_pairs_require_future_same_token_baseline_entry(self):
        candidates = [
            {"token": "0xaaa", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
            {"token": "0xbbb", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
            {"token": "0xccc", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
        ]
        baseline_times = {
            "0xaaa": [1_800_000_030],
            "0xbbb": [1_799_999_990],
            "0xccc": [1_800_000_000],
        }
        paths = {
            "0xaaa": [_point(-1, 1.0), _point(30, 1.1)],
            "0xbbb": [_point(-1, 1.0)],
            "0xccc": [_point(-1, 1.0)],
        }

        pairs = oracle.build_replacement_pairs(
            candidate_rows=candidates,
            baseline_pass_times_by_token=baseline_times,
            price_paths_by_token=paths,
            max_lead_seconds=60,
        )

        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["token"], "0xaaa")
        self.assertEqual(pairs[0]["lead_seconds"], 30)
        self.assertAlmostEqual(pairs[0]["pre_baseline_move_pct"], 10.0)

    def test_pairs_keep_only_decision_time_selector_features(self):
        candidates = [
            {
                "token": "0xaaa",
                "sample_time": 1_800_000_000,
                "prob": 0.90,
                "pred_return": 36.0,
                "volume_30s": 1.25,
                "features": {"price_volatility": 0.20, "future_mfe_pct": 99.0},
                "lead_seconds": 30,
            }
        ]
        paths = {"0xaaa": [_point(-1, 1.0), _point(30, 1.1)]}

        pairs = oracle.build_replacement_pairs(
            candidate_rows=candidates,
            baseline_pass_times_by_token={"0xaaa": [1_800_000_030]},
            price_paths_by_token=paths,
            max_lead_seconds=60,
        )

        features = pairs[0]["features"]
        self.assertEqual(features["prob"], 0.90)
        self.assertEqual(features["pred_return"], 36.0)
        self.assertEqual(features["volume_30s"], 1.25)
        self.assertEqual(features["price_volatility"], 0.20)
        self.assertNotIn("future_mfe_pct", features)
        self.assertNotIn("lead_seconds", features)

    def test_summarizes_pairs_by_lead_window_and_flags_sparse_paths(self):
        pairs = [
            {"lead_seconds": 10, "pre_baseline_move_pct": 2.0, "point_count_to_baseline": 2},
            {"lead_seconds": 20, "pre_baseline_move_pct": 10.0, "point_count_to_baseline": 4},
            {"lead_seconds": 70, "pre_baseline_move_pct": 30.0, "point_count_to_baseline": 5},
        ]

        summary = oracle.summarize_pairs_by_window(pairs, lead_windows_seconds=[20, 120])

        self.assertEqual(summary["20"]["qualifying_pair_count"], 2)
        self.assertEqual(summary["20"]["path_density"]["sparse_pair_count"], 1)
        self.assertAlmostEqual(summary["20"]["pre_baseline_move_pct"]["p75"], 8.0)
        self.assertEqual(summary["120"]["qualifying_pair_count"], 3)
        self.assertAlmostEqual(summary["120"]["pre_baseline_move_pct"]["p50"], 10.0)

    def test_report_decision_rejects_when_required_split_lacks_power(self):
        report = oracle.build_decision(
            {
                "validation": {
                    "120": {
                        "qualifying_pair_count": 99,
                        "pre_baseline_move_pct": {"p75": 30.0},
                    }
                },
                "final": {
                    "120": {
                        "qualifying_pair_count": 200,
                        "pre_baseline_move_pct": {"p75": 30.0},
                    }
                },
            },
            required_splits=("validation", "final"),
            min_pairs_per_split=100,
            min_pre_move_p75_pct=5.0,
        )

        self.assertEqual(report["decision"], "reject")
        self.assertEqual(report["reason"], "replacement_pair_support_below_min")
        self.assertFalse(report["continue_to_deployable_proxy"])

    def test_barrier_realized_return_uses_stop_before_later_profit(self):
        pair = {
            "token": "0xaaa",
            "sample_time": 1_800_000_000,
            "baseline_sample_time": 1_800_000_030,
            "candidate_anchor_price": 1.0,
            "baseline_anchor_price": 1.0,
        }
        path = [
            _point(0, 1.0),
            _point(5, 0.81),
            _point(20, 1.30),
            _point(30, 1.0),
            _point(40, 1.30),
        ]

        scored = oracle.score_pair_barrier_returns(
            pair,
            path,
            horizon_seconds=60,
            take_profit_pct=25.0,
            stop_loss_pct=-18.0,
        )

        self.assertEqual(scored["candidate_first_barrier"], "-18")
        self.assertEqual(scored["candidate_realized_pct"], -18.0)
        self.assertEqual(scored["baseline_first_barrier"], "+25")
        self.assertEqual(scored["baseline_realized_pct"], 25.0)
        self.assertEqual(scored["delta_realized_pct"], -43.0)

    def test_barrier_realized_return_clamps_to_horizon_terminal_change(self):
        pair = {
            "token": "0xaaa",
            "sample_time": 1_800_000_000,
            "baseline_sample_time": 1_800_000_000,
            "candidate_anchor_price": 1.0,
            "baseline_anchor_price": 1.0,
        }
        path = [
            _point(0, 1.0),
            _point(50, 1.05),
            _point(61, 1.30),
        ]

        scored = oracle.score_pair_barrier_returns(
            pair,
            path,
            horizon_seconds=60,
            take_profit_pct=25.0,
            stop_loss_pct=-18.0,
        )

        self.assertIsNone(scored["candidate_first_barrier"])
        self.assertAlmostEqual(scored["candidate_realized_pct"], 5.0)

    def test_full_summary_reports_realized_delta_and_stop_first(self):
        scored_pairs = [
            {
                "lead_seconds": 10,
                "pre_baseline_move_pct": 10.0,
                "point_count_to_baseline": 3,
                "candidate_first_barrier": "+25",
                "baseline_first_barrier": None,
                "candidate_realized_pct": 25.0,
                "baseline_realized_pct": 5.0,
                "delta_realized_pct": 20.0,
                "mfe_delta_pct": 30.0,
            },
            {
                "lead_seconds": 10,
                "pre_baseline_move_pct": 20.0,
                "point_count_to_baseline": 3,
                "candidate_first_barrier": "-18",
                "baseline_first_barrier": "+25",
                "candidate_realized_pct": -18.0,
                "baseline_realized_pct": 25.0,
                "delta_realized_pct": -43.0,
                "mfe_delta_pct": -5.0,
            },
        ]

        summary = oracle.summarize_scored_pairs_by_window(scored_pairs, lead_windows_seconds=[20])

        self.assertEqual(summary["20"]["qualifying_pair_count"], 2)
        self.assertEqual(summary["20"]["candidate_stop_first"]["count"], 1)
        self.assertEqual(summary["20"]["candidate_stop_first"]["ratio"], 0.5)
        self.assertAlmostEqual(summary["20"]["delta_realized_pct"]["p50"], -11.5)

    def test_barrier_decision_rejects_nonpositive_realized_delta(self):
        decision = oracle.build_barrier_decision(
            {
                "validation": {
                    "60": {
                        "qualifying_pair_count": 120,
                        "delta_realized_pct": {"p50": -1.0},
                        "candidate_stop_first": {"ratio": 0.20},
                    }
                },
                "final": {
                    "60": {
                        "qualifying_pair_count": 140,
                        "delta_realized_pct": {"p50": 2.0},
                        "candidate_stop_first": {"ratio": 0.20},
                    }
                },
            },
            required_splits=("validation", "final"),
            min_pairs_per_split=100,
            min_delta_realized_p50_pct=1.0,
            max_candidate_stop_first_ratio=0.40,
        )

        self.assertEqual(decision["decision"], "reject")
        self.assertEqual(decision["reason"], "delta_realized_p50_below_min")
        self.assertFalse(decision["continue_to_deployable_proxy"])

    def test_pair_selector_promotes_research_alpha_for_stable_decision_time_rule(self):
        def pair(prob, delta):
            return {"delta_realized_pct": delta, "features": {"prob": prob}}

        report = oracle.build_pair_selector_report(
            train_pairs=[
                pair(0.95, 10.0),
                pair(0.94, 8.0),
                pair(0.70, -4.0),
                pair(0.69, -5.0),
            ],
            validation_pairs=[
                pair(0.96, 7.0),
                pair(0.94, 5.0),
                pair(0.68, -3.0),
                pair(0.67, -2.0),
            ],
            final_pairs=[
                pair(0.97, 6.0),
                pair(0.95, 4.0),
                pair(0.65, -3.0),
                pair(0.64, -4.0),
            ],
            loss_cost=1.0,
            min_keep_count=2,
            min_reject_count=2,
            min_eval_keep_count=2,
            min_positive_rate=0.50,
            max_conditions=1,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["decision"], "research_alpha")
        self.assertEqual(report["rejection_reasons"], [])
        self.assertIsNotNone(report["selected_rule"])

    def test_pair_selector_rejects_final_top_winner_dependency(self):
        def pair(prob, delta):
            return {"delta_realized_pct": delta, "features": {"prob": prob}}

        report = oracle.build_pair_selector_report(
            train_pairs=[
                pair(0.95, 10.0),
                pair(0.94, 8.0),
                pair(0.70, -4.0),
                pair(0.69, -5.0),
            ],
            validation_pairs=[
                pair(0.96, 7.0),
                pair(0.94, 5.0),
                pair(0.68, -3.0),
                pair(0.67, -2.0),
            ],
            final_pairs=[
                pair(0.97, 100.0),
                pair(0.95, -5.0),
                pair(0.65, -3.0),
                pair(0.64, -4.0),
            ],
            loss_cost=1.0,
            min_keep_count=2,
            min_reject_count=2,
            min_eval_keep_count=2,
            min_positive_rate=0.50,
            max_conditions=1,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertIn("final_top1_positive_dependent", report["rejection_reasons"])

    def test_cli_writes_phase1_non_deployable_report(self):
        cli = _load_cli()

        def fake_candidate_rows(samples, buy_artifact, runtime_params):
            return [
                {"token": "0xaaa", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
                {"token": "0xaaa", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
            ]

        def fake_baseline_times(samples, buy_artifact, runtime_params):
            return {"0xaaa": [1_800_000_030]}

        fake_context = {
            "buy_artifact": {},
            "runtime_params": {"buy_threshold": 0.98},
            "splits": {
                "validation": {
                    "samples": [{"meta": {"token_address": "0xaaa", "sample_time": 1_800_000_000}}],
                    "price_paths_by_token": {"0xaaa": [_point(-1, 1.0), _point(30, 1.02)]},
                    "lifecycle_paths": ["validation.jsonl"],
                },
                "final": {
                    "samples": [{"meta": {"token_address": "0xaaa", "sample_time": 1_800_000_000}}],
                    "price_paths_by_token": {"0xaaa": [_point(-1, 1.0), _point(30, 1.03)]},
                    "lifecycle_paths": ["final.jsonl"],
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "oracle.json"
            with patch.object(cli, "_load_oracle_context", return_value=fake_context), patch.object(
                cli.runner_cli,
                "candidate_grid",
                return_value=iter([{}]),
            ), patch.object(
                cli.retention_gate,
                "_candidate_gate_rows_with_indices",
                side_effect=fake_candidate_rows,
            ), patch.object(
                cli.retention_gate,
                "_baseline_entry_pass_times_by_token",
                side_effect=fake_baseline_times,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    cli.main([
                        "--output",
                        str(output_path),
                        "--lead-windows-seconds",
                        "20,60",
                        "--min-pairs-per-split",
                        "2",
                        "--min-pre-move-p75-pct",
                        "5",
                        "--force",
                    ])

            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["phase"], "pair_count_pre_move")
        self.assertEqual(saved["estimator_type"], "ex_post_path_simulation")
        self.assertTrue(saved["uses_ex_post_outcomes"])
        self.assertFalse(saved["live_switch_evidence"])
        self.assertTrue(saved["not_deployable_policy"])
        self.assertEqual(saved["decision"]["decision"], "reject")
        self.assertEqual(saved["decision"]["reason"], "replacement_pair_support_below_min")
        self.assertEqual(saved["splits"]["validation"]["candidate_row_count"], 2)
        self.assertEqual(saved["splits"]["validation"]["unique_candidate_row_count"], 1)

    def test_cli_phase2_writes_barrier_summary(self):
        cli = _load_cli()

        def fake_candidate_rows(samples, buy_artifact, runtime_params):
            return [
                {"token": "0xaaa", "sample_time": 1_800_000_000, "prob": 0.90, "pred_return": 36.0},
            ]

        def fake_baseline_times(samples, buy_artifact, runtime_params):
            return {"0xaaa": [1_800_000_030]}

        fake_context = {
            "buy_artifact": {},
            "runtime_params": {"buy_threshold": 0.98, "max_hold_seconds": 60},
            "splits": {
                "validation": {
                    "samples": [{"meta": {"token_address": "0xaaa", "sample_time": 1_800_000_000}}],
                    "price_paths_by_token": {"0xaaa": [_point(-1, 1.0), _point(5, 0.81), _point(30, 1.0), _point(40, 1.30)]},
                    "lifecycle_paths": ["validation.jsonl"],
                },
                "final": {
                    "samples": [{"meta": {"token_address": "0xaaa", "sample_time": 1_800_000_000}}],
                    "price_paths_by_token": {"0xaaa": [_point(-1, 1.0), _point(5, 0.81), _point(30, 1.0), _point(40, 1.30)]},
                    "lifecycle_paths": ["final.jsonl"],
                },
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "oracle_barrier.json"
            with patch.object(cli, "_load_oracle_context", return_value=fake_context), patch.object(
                cli.runner_cli,
                "candidate_grid",
                return_value=iter([{}]),
            ), patch.object(
                cli.retention_gate,
                "_candidate_gate_rows_with_indices",
                side_effect=fake_candidate_rows,
            ), patch.object(
                cli.retention_gate,
                "_baseline_entry_pass_times_by_token",
                side_effect=fake_baseline_times,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    cli.main([
                        "--output",
                        str(output_path),
                        "--phase",
                        "barrier",
                        "--lead-windows-seconds",
                        "60",
                        "--min-pairs-per-split",
                        "1",
                        "--force",
                    ])

            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["phase"], "barrier_respecting")
        self.assertIn("delta_realized_pct", saved["splits"]["validation"]["windows"]["60"])
        self.assertEqual(saved["decision"]["decision"], "reject")
        self.assertEqual(saved["decision"]["reason"], "delta_realized_p50_below_min")


if __name__ == "__main__":
    unittest.main()
