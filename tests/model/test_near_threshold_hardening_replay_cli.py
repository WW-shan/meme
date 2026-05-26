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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_near_threshold_hardening_replay.py"
    spec = importlib.util.spec_from_file_location("run_near_threshold_hardening_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, near_entries=1):
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
        "near_threshold_signal_count": near_entries,
        "near_threshold_entry_count": near_entries,
        "near_threshold_reject_count": 0,
    }


class TestNearThresholdHardeningReplayCli(unittest.TestCase):
    def test_candidate_grid_includes_disable_and_hardened_rescue_shapes(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreaterEqual(len(candidates), 4)
        self.assertIn({
            "buy_near_threshold_min_prob": None,
            "buy_near_min_pred_return": None,
            "buy_near_min_entry_volume_30s": None,
            "buy_near_min_entry_price_volatility": None,
            "buy_near_min_age_seconds": None,
        }, candidates)
        for candidate in candidates:
            self.assertEqual(set(candidate), {
                "buy_near_threshold_min_prob",
                "buy_near_min_pred_return",
                "buy_near_min_entry_volume_30s",
                "buy_near_min_entry_price_volatility",
                "buy_near_min_age_seconds",
            })
            if candidate["buy_near_threshold_min_prob"] is not None:
                self.assertGreaterEqual(candidate["buy_near_threshold_min_prob"], 0.965)
                self.assertLess(candidate["buy_near_threshold_min_prob"], 0.98)
                self.assertGreaterEqual(candidate["buy_near_min_pred_return"], 40.0)
                self.assertGreaterEqual(candidate["buy_near_min_entry_volume_30s"], 1.5)
                self.assertGreaterEqual(candidate["buy_near_min_entry_price_volatility"], 0.1)

    def test_main_writes_strict_report_and_requires_near_entry_reduction(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_near_threshold_min_prob": None,
                "buy_near_min_pred_return": None,
                "buy_near_min_entry_volume_30s": None,
                "buy_near_min_entry_price_volatility": None,
                "buy_near_min_age_seconds": None,
            }
        ])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_near_threshold_min_prob" in overrides
            return {
                "evaluation": _robust_evaluation(
                    net_profit_bnb=0.002 if is_candidate else 0.001,
                    near_entries=0 if is_candidate else 2,
                )
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            output_path = Path(tmpdir) / "near_threshold_hardening_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertFalse(saved["safe_for_live_switch"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        for call in calls:
            overrides = call["overrides"]
            self.assertEqual(overrides["position_fraction"], 0.1)
            self.assertEqual(overrides["max_position_fraction"], 0.1)
            self.assertIsNone(overrides["fixed_stake_bnb"])
            self.assertTrue(overrides["skip_all_in_replay"])
            self.assertEqual(overrides["max_open_positions"], 8)
        self.assertNotIn("buy_near_threshold_min_prob", calls[0]["overrides"])
        self.assertIsNone(calls[1]["overrides"]["buy_near_threshold_min_prob"])
        self.assertTrue(report["best_validation_candidate"]["gate_details"]["near_threshold_entry_count_reduced"])


if __name__ == "__main__":
    unittest.main()
