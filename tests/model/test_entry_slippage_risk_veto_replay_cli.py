import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_entry_slippage_risk_veto_replay.py"
    spec = importlib.util.spec_from_file_location("run_entry_slippage_risk_veto_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestEntrySlippageRiskVetoReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertIsNone(args.max_candidates)
        self.assertIsNone(args.candidate_grid_json)
        self.assertFalse(args.confirm_best_raw)
        self.assertFalse(args.write_selected_trade_delta)
        self.assertTrue(args.use_cache)
        self.assertEqual(cli.parse_args(["--max-candidates", "8"]).max_candidates, 8)
        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.2"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-open-positions", "9"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.05"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-position-fraction", "0.05"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-candidates", "0"])

    def test_candidate_grid_uses_only_entry_slippage_risk_veto_params(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 64)
        for candidate in candidates:
            self.assertTrue(candidate)
            self.assertTrue(all(key.startswith("buy_entry_slippage_risk_veto_") for key in candidate))
            self.assertIn("buy_entry_slippage_risk_veto_min_recent_jump_pct", candidate)
            self.assertLessEqual(candidate["buy_entry_slippage_risk_veto_min_price_extension_pct"], 2.0)
            self.assertLessEqual(candidate["buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct"], 0.45)

    def test_candidate_grid_from_json_accepts_wrapped_grid_and_rejects_invalid_payloads(self):
        cli = _load_cli()
        candidate = {
            "buy_entry_slippage_risk_veto_min_age_seconds": 0,
            "buy_entry_slippage_risk_veto_extension_window_seconds": 30,
            "buy_entry_slippage_risk_veto_min_price_extension_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_entry_volume_30s": 0.0,
            "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.25,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            grid_path = Path(tmpdir) / "grid.json"
            grid_path.write_text(json.dumps({"candidates": [candidate]}), encoding="utf-8")
            self.assertEqual(cli.candidate_grid_from_json(grid_path), [candidate])

            empty_path = Path(tmpdir) / "empty.json"
            empty_path.write_text(json.dumps({"candidates": []}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                cli.candidate_grid_from_json(empty_path)

            invalid_path = Path(tmpdir) / "invalid.json"
            invalid_path.write_text(json.dumps({"candidates": ["not-an-object"]}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                cli.candidate_grid_from_json(invalid_path)

    def test_main_selects_validation_candidate_and_confirms_on_final(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_entry_slippage_risk_veto_min_age_seconds": 15,
                "buy_entry_slippage_risk_veto_extension_window_seconds": 30,
                "buy_entry_slippage_risk_veto_min_price_extension_pct": 1.0,
                "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.30,
                "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.10,
                "buy_entry_slippage_risk_veto_min_entry_volume_30s": 0.0,
                "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.10,
            },
            {
                "buy_entry_slippage_risk_veto_min_age_seconds": 15,
                "buy_entry_slippage_risk_veto_extension_window_seconds": 120,
                "buy_entry_slippage_risk_veto_min_price_extension_pct": 2.0,
                "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.20,
                "buy_entry_slippage_risk_veto_min_entry_volume_30s": 1.5,
                "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.18,
            },
        ])
        calls = []

        def evaluation_for(split, overrides):
            is_candidate = "buy_entry_slippage_risk_veto_min_age_seconds" in overrides
            is_second = overrides.get("buy_entry_slippage_risk_veto_min_price_extension_pct") == 2.0
            if not is_candidate:
                return {
                    "net_profit_bnb": 0.001,
                    "total_trades": 4,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": 5.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_execution",
                        "net_return_pct": 2.0,
                        "net_profit_bnb": 0.0002,
                        "max_drawdown_pct": -15.0,
                    }],
                    "entry_slippage_risk_veto_reject_count": 0,
                }
            return {
                "net_profit_bnb": 0.003 if is_second else 0.002,
                "total_trades": 4,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.75 if is_second else 0.25,
                "walk_forward_worst_net_return_pct": 7.0 if is_second else 1.0,
                "walk_forward_worst_max_drawdown_pct": -11.0,
                "stress_replay": [{
                    "name": "harsh_execution",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0003,
                    "max_drawdown_pct": -14.0,
                }],
                "entry_slippage_risk_veto_reject_count": 2,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "entry_slippage_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertEqual(report["decision"], "accept")
        self.assertFalse(report["live_switch_evidence"])
        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual(calls[0]["overrides"]["position_fraction"], 0.1)
        self.assertEqual(calls[0]["overrides"]["max_position_fraction"], 0.1)
        self.assertIsNone(calls[0]["overrides"]["fixed_stake_bnb"])
        self.assertTrue(calls[0]["overrides"]["one_entry_per_token"])
        self.assertEqual(calls[0]["overrides"]["max_trades_per_token"], 1)
        self.assertTrue(calls[0]["overrides"]["skip_all_in_replay"])

    def test_main_marks_rejected_grid_as_non_live_switch_evidence(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_entry_slippage_risk_veto_min_age_seconds": 15,
                "buy_entry_slippage_risk_veto_extension_window_seconds": 30,
                "buy_entry_slippage_risk_veto_min_price_extension_pct": 1.0,
                "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.30,
                "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.10,
                "buy_entry_slippage_risk_veto_min_entry_volume_30s": 0.0,
                "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.10,
            },
        ])

        def fake_run_model_replay(**kwargs):
            is_candidate = "buy_entry_slippage_risk_veto_min_age_seconds" in dict(kwargs.get("overrides") or {})
            evaluation = {
                "net_profit_bnb": 0.001 if not is_candidate else 0.0005,
                "total_trades": 4,
                "max_drawdown_pct": -10.0 if not is_candidate else -11.0,
                "win_rate": 0.5,
                "walk_forward_worst_net_return_pct": 5.0,
                "walk_forward_worst_max_drawdown_pct": -12.0,
                "stress_replay": [{
                    "name": "harsh_execution",
                    "net_return_pct": 2.0,
                    "net_profit_bnb": 0.0002,
                    "max_drawdown_pct": -15.0,
                }],
                "entry_slippage_risk_veto_reject_count": 1 if is_candidate else 0,
            }
            return {"evaluation": evaluation}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "entry_slippage_reject_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["decision"], "reject")
        self.assertIsNone(report["best_validation_accepted_candidate"])
        self.assertFalse(report["live_switch_evidence"])
        self.assertEqual(saved["decision"], "reject")
        self.assertFalse(saved["live_switch_evidence"])

    def test_main_limits_candidate_grid_for_diagnostics(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_entry_slippage_risk_veto_min_age_seconds": 15,
                "buy_entry_slippage_risk_veto_extension_window_seconds": 30,
                "buy_entry_slippage_risk_veto_min_price_extension_pct": 1.0,
                "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.30,
                "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.10,
                "buy_entry_slippage_risk_veto_min_entry_volume_30s": 0.0,
                "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.10,
            },
            {
                "buy_entry_slippage_risk_veto_min_age_seconds": 15,
                "buy_entry_slippage_risk_veto_extension_window_seconds": 120,
                "buy_entry_slippage_risk_veto_min_price_extension_pct": 2.0,
                "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.20,
                "buy_entry_slippage_risk_veto_min_entry_volume_30s": 1.5,
                "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.18,
            },
        ])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            is_candidate = "buy_entry_slippage_risk_veto_min_age_seconds" in dict(kwargs.get("overrides") or {})
            return {
                "evaluation": {
                    "net_profit_bnb": 0.001 if not is_candidate else 0.0005,
                    "total_trades": 4,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": 5.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_execution",
                        "net_return_pct": 2.0,
                        "net_profit_bnb": 0.0002,
                        "max_drawdown_pct": -15.0,
                    }],
                    "entry_slippage_risk_veto_reject_count": 1 if is_candidate else 0,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "entry_slippage_limited_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path), "--max-candidates", "1"])

        self.assertEqual(len(report["candidates"]), 1)
        self.assertEqual(report["candidate_limit"], 1)
        self.assertEqual([call["split"] for call in calls], ["validation", "validation"])
        self.assertIsNone(report["final_confirmation"])
        self.assertEqual(report["decision"], "reject")

    def test_main_can_confirm_best_raw_and_write_trade_delta(self):
        cli = _load_cli()
        calls = []
        candidate = {
            "buy_entry_slippage_risk_veto_min_age_seconds": 0,
            "buy_entry_slippage_risk_veto_extension_window_seconds": 30,
            "buy_entry_slippage_risk_veto_min_price_extension_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_recent_jump_pct": 0.0,
            "buy_entry_slippage_risk_veto_min_entry_volume_30s": 0.0,
            "buy_entry_slippage_risk_veto_min_entry_price_volatility": 0.25,
        }

        def evaluation_for(split, overrides, include_trade_log):
            is_candidate = "buy_entry_slippage_risk_veto_min_age_seconds" in overrides
            evaluation = {
                "net_profit_bnb": 0.002 if not is_candidate else 0.003,
                "total_trades": 4,
                "max_drawdown_pct": -10.0 if not is_candidate else -11.0,
                "win_rate": 0.5 if not is_candidate else 0.25,
                "walk_forward_worst_net_return_pct": 5.0 if not is_candidate else 4.0,
                "walk_forward_worst_max_drawdown_pct": -12.0,
                "stress_replay": [{
                    "name": "harsh_execution",
                    "net_return_pct": 2.0 if not is_candidate else 1.5,
                    "net_profit_bnb": 0.0002 if not is_candidate else 0.00015,
                    "max_drawdown_pct": -15.0,
                }],
                "entry_slippage_risk_veto_reject_count": 0 if not is_candidate else 1,
            }
            if include_trade_log:
                evaluation["trade_log"] = [{
                    "token": f"{split}-{'candidate' if is_candidate else 'baseline'}",
                    "entry_signal_time": 100,
                    "return_pct": 1.0 if is_candidate else -1.0,
                    "net_profit_bnb": 0.0001 if is_candidate else -0.0001,
                    "exit_reason": "TIME_EXIT",
                }]
            return evaluation

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {
                "evaluation": evaluation_for(
                    kwargs["split"],
                    dict(kwargs.get("overrides") or {}),
                    bool(kwargs.get("include_trade_log")),
                )
            }

        def fake_trade_delta_report(**kwargs):
            return {
                "delta_summary": {
                    "baseline_count": len(kwargs["baseline_trade_rows"]),
                    "candidate_count": len(kwargs["candidate_trade_rows"]),
                }
            }

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.run_model_replay = fake_run_model_replay
        fake_trade_delta = types.ModuleType("src.pipeline.replay_trade_delta_attribution")
        fake_trade_delta.build_trade_delta_attribution_report = fake_trade_delta_report

        with tempfile.TemporaryDirectory() as tmpdir:
            grid_path = Path(tmpdir) / "grid.json"
            grid_path.write_text(json.dumps({"candidates": [candidate]}), encoding="utf-8")
            output_path = Path(tmpdir) / "entry_slippage_raw_confirm_report.json"
            with patch_modules({
                "src.pipeline.model_replay": fake_model_replay,
                "src.pipeline.replay_trade_delta_attribution": fake_trade_delta,
            }):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main([
                        "--candidate-grid-json", str(grid_path),
                        "--output", str(output_path),
                        "--confirm-best-raw",
                        "--write-selected-trade-delta",
                    ])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["split"] for call in calls], [
            "validation",
            "validation",
            "final",
            "final",
            "validation",
            "validation",
            "final",
            "final",
        ])
        self.assertEqual([bool(call["include_trade_log"]) for call in calls], [
            False,
            False,
            False,
            False,
            True,
            True,
            True,
            True,
        ])
        self.assertIsNotNone(report["final_confirmation"])
        self.assertIsNone(report["best_validation_accepted_candidate"])
        self.assertEqual(report["decision"], "reject")
        self.assertTrue(report["confirm_best_raw"])
        self.assertEqual(report["candidate_grid"]["source"], str(grid_path))
        self.assertEqual(report["candidate_grid"]["candidate_count"], 1)
        self.assertEqual(
            report["selected_trade_delta_attribution"]["validation"]["delta_summary"]["candidate_count"],
            1,
        )
        self.assertEqual(
            saved["selected_trade_delta_attribution"]["final"]["delta_summary"]["baseline_count"],
            1,
        )


class patch_modules:
    def __init__(self, modules):
        self.modules = modules
        self._patch = None

    def __enter__(self):
        from unittest.mock import patch

        self._patch = patch.dict(sys.modules, self.modules)
        return self._patch.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self._patch.__exit__(exc_type, exc, tb)


if __name__ == "__main__":
    unittest.main()
