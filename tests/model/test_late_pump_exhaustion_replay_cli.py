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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_late_pump_exhaustion_replay.py"
    spec = importlib.util.spec_from_file_location("run_late_pump_exhaustion_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestLatePumpExhaustionReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.2"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-open-positions", "9"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--position-fraction", "0.05"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-position-fraction", "0.05"])

    def test_candidate_grid_uses_only_late_pump_veto_params(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 16)
        for candidate in candidates:
            self.assertTrue(candidate)
            self.assertTrue(all(key.startswith("buy_late_pump_veto_") for key in candidate))
            self.assertLessEqual(candidate["buy_late_pump_veto_min_price_extension_pct"], 1.0)
            self.assertLessEqual(candidate["buy_late_pump_veto_min_drawdown_from_peak_pct"], 0.75)

    def test_main_selects_validation_candidate_and_confirms_on_final(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_late_pump_veto_min_age_seconds": 180,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 0.8,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 3.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.20,
            },
            {
                "buy_late_pump_veto_min_age_seconds": 120,
                "buy_late_pump_veto_extension_window_seconds": 20,
                "buy_late_pump_veto_min_price_extension_pct": 0.6,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.35,
                "buy_late_pump_veto_min_entry_volume_30s": 2.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.18,
            },
        ])
        calls = []

        def evaluation_for(split, overrides):
            is_candidate = "buy_late_pump_veto_min_age_seconds" in overrides
            is_second = overrides.get("buy_late_pump_veto_min_age_seconds") == 120
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
                    "late_pump_veto_reject_count": 0,
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
                "late_pump_veto_reject_count": 2,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "late_pump_report.json"
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
                "buy_late_pump_veto_min_age_seconds": 15,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 1.0,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 2.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.18,
            },
        ])

        def fake_run_model_replay(**kwargs):
            is_candidate = "buy_late_pump_veto_min_age_seconds" in dict(kwargs.get("overrides") or {})
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
                "late_pump_veto_reject_count": 1 if is_candidate else 0,
            }
            return {"evaluation": evaluation}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "late_pump_reject_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["decision"], "reject")
        self.assertIsNone(report["best_validation_accepted_candidate"])
        self.assertFalse(report["live_switch_evidence"])
        self.assertEqual(saved["decision"], "reject")
        self.assertFalse(saved["live_switch_evidence"])


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
