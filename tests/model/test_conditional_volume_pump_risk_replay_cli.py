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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_conditional_volume_pump_risk_replay.py"
    spec = importlib.util.spec_from_file_location("run_conditional_volume_pump_risk_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


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


class TestConditionalVolumePumpRiskReplayCli(unittest.TestCase):
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
            cli.parse_args(["--max-position-fraction", "0.2"])
        with self.assertRaises(SystemExit):
            cli.parse_args(["--max-open-positions", "9"])

    def test_candidate_grid_combines_near_rescue_disable_low_volume_rescue_and_pump_veto(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 72)
        for candidate in candidates:
            self.assertIn("buy_near_threshold_min_prob", candidate)
            self.assertIsNone(candidate["buy_near_threshold_min_prob"])
            self.assertIn("buy_low_volume_rescue_min_prob", candidate)
            self.assertIn("buy_low_volume_rescue_min_entry_volume_30s", candidate)
            self.assertIn("buy_low_volume_rescue_max_entry_volume_30s", candidate)
            self.assertIn("buy_late_pump_veto_min_age_seconds", candidate)
            self.assertIn("buy_late_pump_veto_min_price_extension_pct", candidate)
            self.assertLessEqual(candidate["buy_low_volume_rescue_max_entry_volume_30s"], 1.5)
            self.assertLessEqual(candidate["buy_late_pump_veto_min_entry_volume_30s"], 1.5)

    def test_main_selects_validation_candidate_and_confirms_on_final(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_near_threshold_min_prob": None,
                "buy_near_min_pred_return": None,
                "buy_near_min_entry_volume_30s": None,
                "buy_near_min_entry_price_volatility": None,
                "buy_near_min_age_seconds": None,
                "buy_low_volume_rescue_min_prob": 0.988,
                "buy_low_volume_rescue_min_entry_volume_30s": 0.75,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
                "buy_low_volume_rescue_min_entry_price_volatility": 0.08,
                "buy_low_volume_rescue_max_age_seconds": 90,
                "buy_low_volume_rescue_take_profit_pct": 0.35,
                "buy_late_pump_veto_min_age_seconds": 15,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 1.0,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 0.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.08,
            },
            {
                "buy_near_threshold_min_prob": None,
                "buy_near_min_pred_return": None,
                "buy_near_min_entry_volume_30s": None,
                "buy_near_min_entry_price_volatility": None,
                "buy_near_min_age_seconds": None,
                "buy_low_volume_rescue_min_prob": 0.99,
                "buy_low_volume_rescue_min_entry_volume_30s": 0.95,
                "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
                "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
                "buy_low_volume_rescue_max_age_seconds": 60,
                "buy_low_volume_rescue_take_profit_pct": 0.35,
                "buy_late_pump_veto_min_age_seconds": 15,
                "buy_late_pump_veto_extension_window_seconds": 30,
                "buy_late_pump_veto_min_price_extension_pct": 0.8,
                "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
                "buy_late_pump_veto_min_entry_volume_30s": 0.0,
                "buy_late_pump_veto_min_entry_price_volatility": 0.08,
            },
        ])
        calls = []

        def evaluation_for(overrides):
            is_candidate = "buy_low_volume_rescue_min_prob" in overrides
            is_second = overrides.get("buy_low_volume_rescue_min_prob") == 0.99
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
                    "low_volume_rescue_entry_count": 0,
                    "late_pump_veto_reject_count": 0,
                    "near_threshold_entry_count": 1,
                }
            return {
                "net_profit_bnb": 0.003 if is_second else 0.002,
                "total_trades": 4,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.75 if is_second else 0.5,
                "walk_forward_worst_net_return_pct": 7.0 if is_second else 4.0,
                "walk_forward_worst_max_drawdown_pct": -11.0,
                "stress_replay": [{
                    "name": "harsh_execution",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0003,
                    "max_drawdown_pct": -14.0,
                }],
                "low_volume_rescue_entry_count": 1,
                "late_pump_veto_reject_count": 2,
                "near_threshold_entry_count": 0,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "conditional_volume_pump_report.json"
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
        self.assertIsNone(calls[1]["overrides"]["buy_near_threshold_min_prob"])
        self.assertEqual(calls[1]["overrides"]["position_fraction"], 0.1)
        self.assertEqual(calls[1]["overrides"]["max_position_fraction"], 0.1)
        self.assertIsNone(calls[1]["overrides"]["fixed_stake_bnb"])
        self.assertTrue(calls[1]["overrides"]["skip_all_in_replay"])

    def test_main_rejects_candidate_without_both_live_triggered_activities(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": None,
            "buy_near_min_pred_return": None,
            "buy_near_min_entry_volume_30s": None,
            "buy_near_min_entry_price_volatility": None,
            "buy_near_min_age_seconds": None,
            "buy_low_volume_rescue_min_prob": 0.99,
            "buy_low_volume_rescue_min_entry_volume_30s": 0.95,
            "buy_low_volume_rescue_max_entry_volume_30s": 1.5,
            "buy_low_volume_rescue_min_entry_price_volatility": 0.10,
            "buy_low_volume_rescue_max_age_seconds": 60,
            "buy_low_volume_rescue_take_profit_pct": 0.35,
            "buy_late_pump_veto_min_age_seconds": 15,
            "buy_late_pump_veto_extension_window_seconds": 30,
            "buy_late_pump_veto_min_price_extension_pct": 0.8,
            "buy_late_pump_veto_min_drawdown_from_peak_pct": 0.45,
            "buy_late_pump_veto_min_entry_volume_30s": 0.0,
            "buy_late_pump_veto_min_entry_price_volatility": 0.08,
        }])

        def fake_run_model_replay(**kwargs):
            is_candidate = "buy_low_volume_rescue_min_prob" in dict(kwargs.get("overrides") or {})
            return {"evaluation": {
                "net_profit_bnb": 0.003 if is_candidate else 0.001,
                "total_trades": 4,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.75,
                "walk_forward_worst_net_return_pct": 7.0,
                "walk_forward_worst_max_drawdown_pct": -11.0,
                "stress_replay": [{
                    "name": "harsh_execution",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0003,
                    "max_drawdown_pct": -14.0,
                }],
                "low_volume_rescue_entry_count": 0,
                "late_pump_veto_reject_count": 2 if is_candidate else 0,
                "near_threshold_entry_count": 0,
            }}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "conditional_volume_pump_reject.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual(report["decision"], "reject")
        self.assertFalse(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertFalse(report["live_switch_evidence"])


if __name__ == "__main__":
    unittest.main()
