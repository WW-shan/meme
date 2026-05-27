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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_delayed_confirmation_quick_tp_replay.py"
    spec = importlib.util.spec_from_file_location("run_delayed_confirmation_quick_tp_replay", path)
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
        "quick_profit_overlay_confirmation_reject_count": 0,
    }


class TestDelayedConfirmationQuickTpReplayCli(unittest.TestCase):
    def test_candidate_grid_adds_short_confirmation_delay_and_price_hold_filters(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 16)
        for candidate in candidates:
            self.assertIn(candidate["buy_quick_profit_overlay_confirmation_delay_seconds"], {3.0, 5.0})
            self.assertIn(candidate["buy_quick_profit_overlay_max_confirmation_drawdown_pct"], {0.03, 0.06})
            self.assertIn(candidate["buy_quick_profit_overlay_max_confirmation_chase_pct"], {0.12, 0.20})
            self.assertGreaterEqual(candidate["buy_quick_profit_overlay_min_prob"], 0.985)
            self.assertNotIn("buy_quick_profit_overlay_min_total_buys", candidate)

    def test_main_passes_confirmation_params_to_replay_candidates(self):
        cli = _load_cli()
        calls = []
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
            "buy_quick_profit_overlay_confirmation_delay_seconds": 5.0,
            "buy_quick_profit_overlay_max_confirmation_drawdown_pct": 0.06,
            "buy_quick_profit_overlay_max_confirmation_chase_pct": 0.20,
        }]
        cli.candidate_grid = lambda: iter(grid)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
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
        fake_module.load_or_build_samples = lambda config, files, excluded_tokens, **kwargs: [{"file": str(files[0])}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "delayed_confirmation_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["decision"], "accept")
        self.assertEqual(saved["selected_candidate"]["params"], grid[0])
        self.assertEqual(calls[1]["overrides"]["buy_quick_profit_overlay_confirmation_delay_seconds"], 5.0)
        self.assertEqual(calls[1]["overrides"]["buy_quick_profit_overlay_max_confirmation_drawdown_pct"], 0.06)
        self.assertEqual(calls[1]["overrides"]["buy_quick_profit_overlay_max_confirmation_chase_pct"], 0.20)
        self.assertNotIn("buy_quick_profit_overlay_confirmation_delay_seconds", calls[0]["overrides"])


if __name__ == "__main__":
    unittest.main()
