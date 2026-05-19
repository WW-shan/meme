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


FLOW_KEYS = {
    "buy_flow_activation_min_prob",
    "buy_flow_activation_min_pred_return",
    "buy_flow_activation_max_age_seconds",
    "buy_flow_activation_lookback_seconds",
    "buy_flow_activation_min_volume_ramp_ratio",
    "buy_flow_activation_min_volume_ramp_delta",
    "buy_flow_activation_min_pred_return_delta",
    "buy_flow_activation_min_price_volatility_delta",
    "buy_flow_activation_min_current_volume_30s",
    "buy_dead_flow_exit_min_hold_seconds",
    "buy_dead_flow_exit_max_mfe_pct",
}


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_flow_activation_replay.py"
    spec = importlib.util.spec_from_file_location("run_flow_activation_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, entry_count=0, dead_flow_exit_count=None):
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
        "flow_activation_entry_count": entry_count,
        "dead_flow_exit_count": int(entry_count > 0) if dead_flow_exit_count is None else int(dead_flow_exit_count),
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestFlowActivationReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/flow_activation_replay_20260520_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        self.assertEqual(cli.LIVE_INITIAL_EQUITY_BNB, 0.005093225171475348)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_uses_only_flow_activation_params_and_stays_bounded(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 16)
        self.assertLessEqual(len(candidates), 300)
        for candidate in candidates:
            self.assertEqual(set(candidate), FLOW_KEYS)
            self.assertIn(candidate["buy_flow_activation_min_prob"], {0.988, 0.989})
            self.assertIn(candidate["buy_flow_activation_min_pred_return"], {35.0, 40.0})
            self.assertEqual(candidate["buy_flow_activation_max_age_seconds"], 60.0)
            self.assertEqual(candidate["buy_flow_activation_lookback_seconds"], 30.0)
            self.assertIn(candidate["buy_flow_activation_min_volume_ramp_ratio"], {1.8, 2.2})
            self.assertIn(candidate["buy_flow_activation_min_current_volume_30s"], {1.5, 2.0})
            self.assertEqual(candidate["buy_dead_flow_exit_min_hold_seconds"], 180.0)
            self.assertEqual(candidate["buy_dead_flow_exit_max_mfe_pct"], 0.05)

    def test_main_writes_report_with_strict_live_sized_overrides(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.001 if is_candidate else 0.002,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "reject")
        self.assertIn("baseline", report)
        self.assertIn("candidates", report)
        self.assertIn("final_confirmation", report)
        self.assertGreater(len(report["candidates"]), 0)
        for call in calls:
            self.assertEqual(call["overrides"]["position_fraction"], 0.1)
            self.assertEqual(call["overrides"]["max_position_fraction"], 0.1)
            self.assertIsNone(call["overrides"]["fixed_stake_bnb"])
            self.assertTrue(call["overrides"]["skip_all_in_replay"])
            self.assertEqual(call["overrides"]["max_open_positions"], 8)
            self.assertEqual(call["overrides"]["initial_equity_bnb"], 0.005093225171475348)
            self.assertEqual(call["max_open_positions"], 8)
            self.assertFalse(call["include_trade_log"])

    def test_validation_selects_accepted_candidate_and_final_only_confirms_selected(self):
        cli = _load_cli()
        calls = []
        grid = [
            {
                "buy_flow_activation_min_prob": 0.989,
                "buy_flow_activation_min_pred_return": 40.0,
                "buy_flow_activation_max_age_seconds": 60.0,
                "buy_flow_activation_lookback_seconds": 30.0,
                "buy_flow_activation_min_volume_ramp_ratio": 2.0,
                "buy_flow_activation_min_volume_ramp_delta": 1.0,
                "buy_flow_activation_min_pred_return_delta": 5.0,
                "buy_flow_activation_min_price_volatility_delta": 0.04,
                "buy_flow_activation_min_current_volume_30s": 2.0,
                "buy_dead_flow_exit_min_hold_seconds": 120.0,
                "buy_dead_flow_exit_max_mfe_pct": 0.03,
            },
            {
                "buy_flow_activation_min_prob": 0.989,
                "buy_flow_activation_min_pred_return": 35.0,
                "buy_flow_activation_max_age_seconds": 60.0,
                "buy_flow_activation_lookback_seconds": 30.0,
                "buy_flow_activation_min_volume_ramp_ratio": 1.8,
                "buy_flow_activation_min_volume_ramp_delta": 0.8,
                "buy_flow_activation_min_pred_return_delta": 4.0,
                "buy_flow_activation_min_price_volatility_delta": 0.03,
                "buy_flow_activation_min_current_volume_30s": 1.5,
                "buy_dead_flow_exit_min_hold_seconds": 180.0,
                "buy_dead_flow_exit_max_mfe_pct": 0.05,
            },
        ]
        cli.candidate_grid = lambda: iter(grid)

        def evaluation_for(split, overrides):
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            is_second_candidate = overrides.get("buy_flow_activation_min_pred_return") == 35.0
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
                    "flow_activation_entry_count": 0,
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
                    "flow_activation_entry_count": 1,
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
                    "flow_activation_entry_count": 0,
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
                "flow_activation_entry_count": 1,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        final_calls = calls[-2:]
        self.assertFalse(FLOW_KEYS.intersection(final_calls[0]["overrides"]))
        self.assertEqual(final_calls[1]["overrides"]["buy_flow_activation_min_pred_return"], 35.0)
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_requires_flow_activation_or_dead_flow_activity(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["flow_activation_or_dead_flow_activity"])
        self.assertEqual(report["decision"], "reject")

    def test_accepts_candidate_with_dead_flow_exit_only_when_other_gates_pass(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                total_trades=10,
                entry_count=0,
                dead_flow_exit_count=1 if is_candidate else 0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertTrue(candidate["passes_acceptance_gate"])
        self.assertTrue(candidate["gate_details"]["flow_activation_or_dead_flow_activity"])
        self.assertEqual(report["decision"], "accept")

    def test_rejects_profit_improvement_when_robustness_worsens(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            if not is_candidate:
                return {"evaluation": _robust_evaluation(net_profit_bnb=0.001)}
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.4,
                    "walk_forward_worst_net_return_pct": -6.0,
                    "walk_forward_worst_max_drawdown_pct": -16.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -7.0,
                        "net_profit_bnb": -0.0002,
                        "max_drawdown_pct": -20.0,
                    }],
                    "flow_activation_entry_count": 1,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["win_rate"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_max_drawdown_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_profit_bnb"])
        self.assertFalse(candidate["gate_details"]["stress_worst_max_drawdown_pct"])
        self.assertEqual(report["decision"], "reject")

    def test_rejects_material_trade_count_expansion(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                total_trades=20 if is_candidate else 10,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["total_trades_not_materially_higher"])
        self.assertEqual(report["decision"], "reject")

    def test_refuses_output_path_ending_in_protected_artifact_name(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            output_path = Path(tmpdir) / "hybrid_manifest.json"

            with self.assertRaises(SystemExit):
                cli.main(["--model-dir", str(model_dir), "--output", str(output_path)])


if __name__ == "__main__":
    unittest.main()
