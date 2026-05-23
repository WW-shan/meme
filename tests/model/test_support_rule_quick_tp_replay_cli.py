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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_support_rule_quick_tp_replay.py"
    spec = importlib.util.spec_from_file_location("run_support_rule_quick_tp_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, entry_count=0):
    return {
        "net_profit_bnb": net_profit_bnb,
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
        "quick_profit_overlay_entry_count": entry_count,
    }


class TestSupportRuleQuickTpReplayCli(unittest.TestCase):
    def test_parse_args_defaults_to_support_rule_report_and_keeps_live_risk(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/support_rule_quick_tp_replay_20260522_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)

    def test_candidate_grid_uses_support_rule_shapes_without_total_buys_proxy(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 4)
        self.assertIn({
            "buy_quick_profit_overlay_min_prob": 0.985,
            "buy_quick_profit_overlay_min_pred_return": 30.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.25,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_min_flow_event_count_30s": 2.0,
            "buy_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
            "buy_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
        }, candidates)
        for candidate in candidates:
            self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_prob"], 0.985)
            self.assertEqual(candidate["buy_quick_profit_overlay_min_pred_return"], 30.0)
            self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_entry_volume_30s"], 1.25)
            self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_entry_price_volatility"], 0.08)
            self.assertEqual(candidate["buy_quick_profit_overlay_min_flow_event_count_30s"], 2.0)
            self.assertEqual(candidate["buy_quick_profit_overlay_max_buy_sell_overlap_ratio_60s"], 0.5)
            self.assertEqual(candidate["buy_quick_profit_overlay_max_recent_seller_reentry_ratio_30s"], 0.5)
            self.assertIn(candidate["buy_quick_profit_overlay_take_profit_pct"], {0.25, 0.35})
            self.assertIn(candidate["buy_quick_profit_overlay_max_hold_seconds"], {60.0, 120.0})
            self.assertNotIn("buy_quick_profit_overlay_min_total_buys", candidate)

    def test_main_uses_preloaded_samples_and_support_rule_grid(self):
        cli = _load_cli()
        calls = []
        sample_loads = []
        grid = [{
            "buy_quick_profit_overlay_min_prob": 0.985,
            "buy_quick_profit_overlay_min_pred_return": 30.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.25,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_min_flow_event_count_30s": 2.0,
            "buy_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
            "buy_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
        }]
        cli.candidate_grid = lambda: iter(grid)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            self.assertIn("eval_samples", overrides)
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay
        fake_module.load_manifest = lambda model_dir: {}
        fake_module.live_replay_config_from_manifest = lambda manifest, **kwargs: {}
        fake_module.apply_model_schema_feature_flags = lambda config, _model_dir: dict(config)
        fake_module.resolve_replay_split = lambda manifest, lifecycle_dir: types.SimpleNamespace(
            validation_files=["validation.json"],
            eval_files=["final.json"],
            excluded_validation_tokens=set(),
            excluded_final_tokens=set(),
        )

        def fake_load_or_build_samples(config, files, excluded_tokens, **kwargs):
            samples = [{
                "file": str(files[0]),
                "excluded": sorted(excluded_tokens or []),
            }]
            sample_loads.append({"files": tuple(files), "samples": samples})
            return samples

        fake_module.load_or_build_samples = fake_load_or_build_samples

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "support_rule_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["safe_for_live_switch"])
        self.assertEqual(report["decision"], "accept")
        self.assertFalse(report["safe_for_live_switch"])
        self.assertEqual([load["files"] for load in sample_loads], [("validation.json",), ("final.json",)])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertIs(calls[0]["overrides"]["eval_samples"], sample_loads[0]["samples"])
        self.assertIs(calls[1]["overrides"]["eval_samples"], sample_loads[0]["samples"])
        self.assertIs(calls[2]["overrides"]["eval_samples"], sample_loads[1]["samples"])
        self.assertIs(calls[3]["overrides"]["eval_samples"], sample_loads[1]["samples"])
        self.assertNotIn("buy_quick_profit_overlay_min_prob", calls[0]["overrides"])
        self.assertEqual(calls[1]["overrides"]["buy_quick_profit_overlay_min_pred_return"], 30.0)
        self.assertNotIn("buy_quick_profit_overlay_min_prob", calls[2]["overrides"])
        self.assertEqual(calls[3]["overrides"]["buy_quick_profit_overlay_min_pred_return"], 30.0)

    def test_main_can_stop_after_validation_when_requested(self):
        cli = _load_cli()
        calls = []
        sample_loads = []
        grid = [{
            "buy_quick_profit_overlay_min_prob": 0.985,
            "buy_quick_profit_overlay_min_pred_return": 30.0,
            "buy_quick_profit_overlay_max_pred_return": 35.0,
            "buy_quick_profit_overlay_min_entry_volume_30s": 1.25,
            "buy_quick_profit_overlay_min_entry_price_volatility": 0.08,
            "buy_quick_profit_overlay_max_age_seconds": 60.0,
            "buy_quick_profit_overlay_min_flow_event_count_30s": 2.0,
            "buy_quick_profit_overlay_max_buy_sell_overlap_ratio_60s": 0.5,
            "buy_quick_profit_overlay_max_recent_seller_reentry_ratio_30s": 0.5,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
        }]
        cli.candidate_grid = lambda: iter(grid)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            self.assertIn("eval_samples", overrides)
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay
        fake_module.load_manifest = lambda model_dir: {}
        fake_module.live_replay_config_from_manifest = lambda manifest, **kwargs: {}
        fake_module.apply_model_schema_feature_flags = lambda config, _model_dir: dict(config)
        fake_module.resolve_replay_split = lambda manifest, lifecycle_dir: types.SimpleNamespace(
            validation_files=["validation.json"],
            eval_files=["final.json"],
            excluded_validation_tokens=set(),
            excluded_final_tokens=set(),
        )

        def fake_load_or_build_samples(config, files, excluded_tokens, **kwargs):
            samples = [{
                "file": str(files[0]),
                "excluded": sorted(excluded_tokens or []),
            }]
            sample_loads.append({"files": tuple(files), "samples": samples})
            return samples

        fake_module.load_or_build_samples = fake_load_or_build_samples

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "support_rule_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path), "--validation-only"])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "validation_only")
        self.assertEqual(report["decision"], "validation_only")
        self.assertEqual([call["split"] for call in calls], ["validation", "validation"])
        self.assertNotIn("final_confirmation", saved)
        self.assertEqual([load["files"] for load in sample_loads], [("validation.json",)])


if __name__ == "__main__":
    unittest.main()
