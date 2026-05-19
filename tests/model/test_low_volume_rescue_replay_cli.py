import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_low_volume_rescue_replay.py"
    spec = importlib.util.spec_from_file_location("run_low_volume_rescue_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestLowVolumeRescueReplayCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertTrue(args.use_cache)

    def test_main_writes_bounded_candidate_report(self):
        cli = _load_cli()
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            net_profit = 0.001 if "buy_low_volume_rescue_min_prob" in overrides else 0.002
            return {
                "evaluation": {
                    "net_profit_bnb": net_profit,
                    "total_trades": 2,
                    "max_drawdown_pct": -1.0,
                    "win_rate": 0.5,
                    "low_volume_rescue_entry_count": int("buy_low_volume_rescue_min_prob" in overrides),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    report = cli.main(["--output", str(output_path)])

            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("baseline", report)
        self.assertIn("candidates", report)
        self.assertIn("best_candidate", report)
        self.assertIn("decision", report)
        self.assertIn("acceptance_gate", report)
        self.assertEqual(saved["decision"], "reject")
        self.assertGreater(len(report["candidates"]), 0)
        self.assertEqual(calls[0]["overrides"]["position_fraction"], 0.1)
        self.assertEqual(calls[0]["overrides"]["max_position_fraction"], 0.1)
        self.assertIsNone(calls[0]["overrides"]["fixed_stake_bnb"])
        self.assertTrue(calls[0]["overrides"]["skip_all_in_replay"])
        self.assertFalse(calls[0]["include_trade_log"])
        self.assertTrue(calls[0]["use_cache"])

    def test_validation_selects_candidate_and_final_only_confirms_selected(self):
        cli = _load_cli()
        calls = []
        grid = [
            {"buy_low_volume_rescue_min_prob": 0.982},
            {"buy_low_volume_rescue_min_prob": 0.985},
        ]
        cli.candidate_grid = lambda: iter(grid)

        def evaluation_for(split, overrides):
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            is_second_candidate = overrides.get("buy_low_volume_rescue_min_prob") == 0.985
            if split == "validation" and not is_candidate:
                return {
                    "net_profit_bnb": 0.001,
                    "total_trades": 2,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": -4.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -5.0,
                        "net_profit_bnb": -0.0005,
                        "max_drawdown_pct": -14.0,
                    }],
                    "low_volume_rescue_entry_count": 0,
                }
            if split == "validation":
                return {
                    "net_profit_bnb": 0.002 if is_second_candidate else 0.004,
                    "total_trades": 3,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.6 if is_second_candidate else 0.4,
                    "walk_forward_worst_net_return_pct": -2.0 if is_second_candidate else -8.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0 if is_second_candidate else -18.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -3.0 if is_second_candidate else -9.0,
                        "net_profit_bnb": -0.0002 if is_second_candidate else -0.0009,
                        "max_drawdown_pct": -12.0 if is_second_candidate else -20.0,
                    }],
                    "low_volume_rescue_entry_count": 1,
                }
            if not is_candidate:
                return {
                    "net_profit_bnb": 0.0008,
                    "total_trades": 2,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": -4.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -5.0,
                        "net_profit_bnb": -0.0005,
                        "max_drawdown_pct": -14.0,
                    }],
                    "low_volume_rescue_entry_count": 0,
                }
            return {
                "net_profit_bnb": 0.0025,
                "total_trades": 3,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.6,
                "walk_forward_worst_net_return_pct": -2.0,
                "walk_forward_worst_max_drawdown_pct": -10.0,
                "stress_replay": [{
                    "name": "harsh_friction",
                    "net_return_pct": -3.0,
                    "net_profit_bnb": -0.0002,
                    "max_drawdown_pct": -12.0,
                }],
                "low_volume_rescue_entry_count": 1,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        final_calls = calls[-2:]
        self.assertNotIn("buy_low_volume_rescue_min_prob", final_calls[0]["overrides"])
        self.assertEqual(final_calls[1]["overrides"]["buy_low_volume_rescue_min_prob"], 0.985)
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_malformed_robustness_sections_fail_gate_even_against_negative_baseline(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            if "buy_low_volume_rescue_min_prob" not in overrides:
                return {
                    "evaluation": {
                        "net_profit_bnb": -0.002,
                        "total_trades": 1,
                        "max_drawdown_pct": -30.0,
                        "win_rate": 0.1,
                        "walk_forward_worst_net_return_pct": -20.0,
                        "walk_forward_worst_max_drawdown_pct": -30.0,
                        "stress_replay": [{
                            "name": "harsh_friction",
                            "net_return_pct": -25.0,
                            "net_profit_bnb": -0.003,
                            "max_drawdown_pct": -35.0,
                        }],
                        "low_volume_rescue_entry_count": 0,
                    }
                }
            return {
                "evaluation": {
                    "net_profit_bnb": -0.001,
                    "total_trades": 1,
                    "max_drawdown_pct": -20.0,
                    "win_rate": 0.2,
                    "walk_forward_worst_net_return_pct": None,
                    "walk_forward_worst_max_drawdown_pct": None,
                    "stress_replay": [{
                        "name": "harsh_friction",
                    }],
                    "low_volume_rescue_entry_count": 1,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["has_walk_forward_metrics"])
        self.assertFalse(candidate["gate_details"]["has_stress_replay"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_max_drawdown_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_profit_bnb"])
        self.assertFalse(candidate["gate_details"]["stress_worst_max_drawdown_pct"])
        self.assertEqual(report["decision"], "reject")

    def test_partially_malformed_stress_replay_fails_gate(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            stress_rows = [
                {
                    "name": "harsh_friction",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0005,
                    "max_drawdown_pct": -11.0,
                },
                {
                    "name": "harsh_execution",
                    "net_return_pct": 2.0,
                    "net_profit_bnb": 0.0004,
                    "max_drawdown_pct": -12.0,
                },
            ]
            if is_candidate:
                stress_rows[1] = {"name": "harsh_execution"}
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": stress_rows,
                    "low_volume_rescue_entry_count": int(is_candidate),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["summary"]["has_stress_replay"])
        self.assertFalse(candidate["gate_details"]["has_stress_replay"])
        self.assertEqual(report["decision"], "reject")

    def test_missing_primary_metrics_fail_gate_even_against_weak_baseline(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            if "buy_low_volume_rescue_min_prob" not in overrides:
                return {
                    "evaluation": {
                        "net_profit_bnb": -0.002,
                        "total_trades": 0,
                        "max_drawdown_pct": -30.0,
                        "win_rate": 0.0,
                        "walk_forward_worst_net_return_pct": -20.0,
                        "walk_forward_worst_max_drawdown_pct": -30.0,
                        "stress_replay": [{
                            "name": "harsh_friction",
                            "net_return_pct": -25.0,
                            "net_profit_bnb": -0.003,
                            "max_drawdown_pct": -35.0,
                        }],
                        "low_volume_rescue_entry_count": 0,
                    }
                }
            return {
                "evaluation": {
                    "walk_forward_worst_net_return_pct": -10.0,
                    "walk_forward_worst_max_drawdown_pct": -20.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -10.0,
                        "net_profit_bnb": -0.001,
                        "max_drawdown_pct": -20.0,
                    }],
                    "low_volume_rescue_entry_count": 1,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["has_primary_metrics"])
        self.assertEqual(report["decision"], "reject")

    def test_rejects_material_trade_count_expansion(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 20 if is_candidate else 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "low_volume_rescue_entry_count": int(is_candidate),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["total_trades_not_materially_higher"])
        self.assertEqual(report["decision"], "reject")

    def test_allows_small_trade_count_reduction_when_other_gates_pass(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 8 if is_candidate else 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "low_volume_rescue_entry_count": int(is_candidate),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertTrue(candidate["passes_acceptance_gate"])
        self.assertTrue(candidate["gate_details"]["total_trades_not_materially_lower"])
        self.assertEqual(report["decision"], "accept")

    def test_rejects_material_trade_count_reduction(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 6 if is_candidate else 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "low_volume_rescue_entry_count": int(is_candidate),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["total_trades_not_materially_lower"])
        self.assertEqual(report["decision"], "reject")

    def test_refuses_output_path_inside_model_dir_protected_artifact_name(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            output_path = model_dir / "hybrid_manifest.json"

            with self.assertRaises(SystemExit):
                cli.main(["--model-dir", str(model_dir), "--output", str(output_path)])

    def test_refuses_to_overwrite_existing_report_without_force(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            output_path.write_text("existing\n", encoding="utf-8")

            with self.assertRaises(SystemExit):
                cli.main(["--output", str(output_path)])

    def test_force_allows_overwriting_existing_report(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_low_volume_rescue_min_prob": 0.982}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "low_volume_rescue_entry_count": int(is_candidate),
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            output_path.write_text("existing\n", encoding="utf-8")

            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path), "--force"])

            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertEqual(report["decision"], "accept")
        self.assertEqual(saved["selected_candidate"]["candidate_index"], 0)

    def test_refuses_position_fraction_above_live_cap(self):
        cli = _load_cli()

        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.11"])

    def test_refuses_nonfinite_and_negative_position_fractions(self):
        cli = _load_cli()

        invalid_args = [
            ["--position-fraction", "nan"],
            ["--position-fraction", "-0.1"],
            ["--max-position-fraction", "inf"],
        ]
        for argv in invalid_args:
            with self.subTest(argv=argv):
                with self.assertRaises(SystemExit):
                    cli.parse_args(argv)

    def test_rejects_profit_improvement_when_robustness_worsens(self):
        cli = _load_cli()

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            if not is_candidate:
                return {
                    "evaluation": {
                        "net_profit_bnb": 0.001,
                        "total_trades": 10,
                        "max_drawdown_pct": -8.0,
                        "win_rate": 0.7,
                        "walk_forward_worst_net_return_pct": 4.0,
                        "walk_forward_worst_max_drawdown_pct": -10.0,
                        "stress_replay": [
                            {
                                "name": "harsh_friction",
                                "net_return_pct": 3.0,
                                "net_profit_bnb": 0.0005,
                                "max_drawdown_pct": -11.0,
                            }
                        ],
                        "low_volume_rescue_entry_count": 0,
                    }
                }
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.4,
                    "walk_forward_worst_net_return_pct": -6.0,
                    "walk_forward_worst_max_drawdown_pct": -16.0,
                    "stress_replay": [
                        {
                            "name": "harsh_friction",
                            "net_return_pct": -7.0,
                            "net_profit_bnb": -0.0002,
                            "max_drawdown_pct": -20.0,
                        }
                    ],
                    "low_volume_rescue_entry_count": 1,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "low_volume_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    cli.main(["--output", str(output_path)])

            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "reject")
        self.assertGreater(len(saved["candidates"]), 0)
        candidate = saved["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertIn("gate_details", candidate)
        self.assertFalse(candidate["gate_details"]["win_rate"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_max_drawdown_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_profit_bnb"])
        self.assertFalse(candidate["gate_details"]["stress_worst_max_drawdown_pct"])

    def test_refuses_max_open_positions_other_than_strict_live_cap(self):
        cli = _load_cli()

        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-open-positions", "9"])
