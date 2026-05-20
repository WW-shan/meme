import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
import unittest.mock
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_fast_profit_lock_replay.py"
    spec = importlib.util.spec_from_file_location("run_fast_profit_lock_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, profit_lock_count=1):
    return {
        "net_profit_bnb": net_profit_bnb,
        "total_trades": total_trades,
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
        "profit_lock_take_profit_count": profit_lock_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestFastProfitLockReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/fast_profit_lock_replay_20260520_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_is_bounded_to_profit_lock_params(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 12)
        self.assertEqual(
            candidates[0],
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": 30.0},
        )
        self.assertEqual(
            candidates[-1],
            {"profit_lock_take_profit_pct": 0.60, "profit_lock_max_hold_seconds": 120.0},
        )
        for candidate in candidates:
            self.assertEqual(set(candidate), {"profit_lock_take_profit_pct", "profit_lock_max_hold_seconds"})

    def test_main_writes_report_with_strict_replay_overrides(self):
        cli = _load_cli()
        calls = []
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 30.0,
        }])

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "profit_lock_take_profit_pct" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                profit_lock_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertEqual(report["decision"], "accept")
        self.assertEqual(len(report["candidates"]), 1)
        for call in calls:
            self.assertEqual(call["overrides"]["position_fraction"], 0.1)
            self.assertEqual(call["overrides"]["max_position_fraction"], 0.1)
            self.assertIsNone(call["overrides"]["fixed_stake_bnb"])
            self.assertTrue(call["overrides"]["skip_all_in_replay"])
            self.assertEqual(call["overrides"]["max_open_positions"], 8)
            self.assertEqual(call["max_open_positions"], 8)

    def test_validation_selects_gate_passing_candidate_and_final_confirms_only_selected(self):
        cli = _load_cli()
        calls = []
        grid = [
            {"profit_lock_take_profit_pct": 0.60, "profit_lock_max_hold_seconds": 30.0},
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": 60.0},
        ]
        cli.candidate_grid = lambda: iter(grid)

        def evaluation_for(split, overrides):
            is_candidate = "profit_lock_take_profit_pct" in overrides
            is_second_candidate = overrides.get("profit_lock_take_profit_pct") == 0.25
            if not is_candidate:
                return {
                    **_robust_evaluation(net_profit_bnb=0.001, profit_lock_count=0),
                    "walk_forward_worst_net_return_pct": -4.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -5.0,
                        "net_profit_bnb": -0.0005,
                        "max_drawdown_pct": -14.0,
                    }],
                }
            if split == "validation":
                evaluation = _robust_evaluation(
                    net_profit_bnb=0.002 if is_second_candidate else 0.004,
                    total_trades=10,
                    profit_lock_count=2,
                )
                if not is_second_candidate:
                    evaluation.update({
                        "win_rate": 0.4,
                        "walk_forward_worst_net_return_pct": -8.0,
                        "walk_forward_worst_max_drawdown_pct": -18.0,
                        "stress_replay": [{
                            "name": "harsh_friction",
                            "net_return_pct": -9.0,
                            "net_profit_bnb": -0.0009,
                            "max_drawdown_pct": -20.0,
                        }],
                    })
                return evaluation
            return _robust_evaluation(net_profit_bnb=0.0025, total_trades=10, profit_lock_count=2)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertNotIn("profit_lock_take_profit_pct", calls[-2]["overrides"])
        self.assertEqual(calls[-1]["overrides"]["profit_lock_take_profit_pct"], 0.25)
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_rejected_final_confirmation_keeps_top_level_selection_null(self):
        cli = _load_cli()
        calls = []
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 60.0,
        }])

        def evaluation_for(split, overrides):
            is_candidate = "profit_lock_take_profit_pct" in overrides
            if not is_candidate:
                return _robust_evaluation(net_profit_bnb=0.001, total_trades=10, profit_lock_count=0)
            if split == "validation":
                return _robust_evaluation(net_profit_bnb=0.002, total_trades=10, profit_lock_count=1)
            return _robust_evaluation(net_profit_bnb=0.0005, total_trades=10, profit_lock_count=1)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 0)
        self.assertIsNone(report["selected_candidate"])
        self.assertIsNone(report["best_candidate"])
        self.assertIsNone(report["best_accepted_candidate"])
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 0)
        self.assertFalse(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "reject")

    def test_requires_profit_lock_take_profit_count(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 60.0,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "profit_lock_take_profit_pct" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                profit_lock_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["profit_lock_take_profit_count"])
        self.assertEqual(report["decision"], "reject")

    def test_rejects_trade_count_drift(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 60.0,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "profit_lock_take_profit_pct" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                total_trades=11 if is_candidate else 10,
                profit_lock_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["total_trades_equal"])
        self.assertEqual(report["decision"], "reject")

    def test_acceptance_gate_describes_strict_profit_requirement(self):
        cli = _load_cli()

        gate = cli._acceptance_gate()

        self.assertTrue(gate["requires_net_profit_bnb_strictly_above_baseline"])
        self.assertTrue(gate["requires_total_trades_equal_baseline"])
        self.assertNotIn("min_net_profit_improvement_bnb", gate)

    def test_no_validation_gate_pass_does_not_select_raw_candidate_for_final(self):
        cli = _load_cli()
        calls = []
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 60.0,
        }])

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "profit_lock_take_profit_pct" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.001,
                profit_lock_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "fast_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation"])
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertIsNone(report["best_validation_candidate"])
        self.assertIsNone(report["best_validation_accepted_candidate"])
        self.assertIsNone(report["selected_candidate"])
        self.assertIsNone(report["best_candidate"])
        self.assertIsNone(report["best_accepted_candidate"])
        self.assertIsNone(report["final_confirmation"]["candidate"])
        self.assertFalse(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["final_confirmation"]["skipped_reason"], "no_validation_candidate_passed_acceptance_gate")
        self.assertEqual(report["decision"], "reject")

    def test_refuses_output_path_inside_model_dir_protected_artifact_name(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            output_path = model_dir / "hybrid_manifest.json"

            with self.assertRaises(SystemExit):
                cli.main(["--model-dir", str(model_dir), "--output", str(output_path)])


if __name__ == "__main__":
    unittest.main()
