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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_action_policy_router_replay.py"
    spec = importlib.util.spec_from_file_location("run_action_policy_router_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, signal_count=1, entry_count=1, reject_count=1):
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
        "action_policy_router_signal_count": signal_count,
        "action_policy_router_entry_count": entry_count,
        "action_policy_router_reject_count": reject_count,
        "action_policy_router_quick_take_profit_entry_count": entry_count,
        "action_policy_router_continue_hold_entry_count": entry_count,
        "action_policy_continue_hold_forced_hold_count": entry_count,
    }


class TestActionPolicyRouterReplayCli(unittest.TestCase):
    def test_main_writes_strict_action_policy_router_report(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_action_policy_router_min_confidence": 0.55,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
            "buy_quick_profit_overlay_max_hold_seconds": 120.0,
            "buy_action_policy_continue_hold_activation_pct": 0.35,
            "buy_action_policy_continue_hold_release_pct": 0.75,
        }])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_action_policy_router_min_confidence" in overrides
            return {
                "generated_at": "2026-05-27T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": _robust_evaluation(
                    net_profit_bnb=0.002 if is_candidate else 0.001,
                    signal_count=int(is_candidate),
                    entry_count=int(is_candidate),
                    reject_count=int(is_candidate),
                ),
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        def frozen_samples(_args, split, _base_overrides, _context):
            return [{
                "features": {},
                "meta": {"token_address": f"0x{split}", "sample_time": 1},
            }]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "router_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), \
                 patch.object(cli, "_router_route_maps_for_split", return_value=([{
                     "__episode_meta__": {"token": "0xvalidation", "sample_count": 1, "start_time": 1, "end_time": 1},
                     "0": {"route": "continue_hold", "confidence": 0.8},
                 }], {"trained": True})), \
                 patch.object(cli, "_split_samples_for_replay", side_effect=frozen_samples):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["decision"], "accept")
        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertNotIn("action_policy_routes_by_episode", calls[0]["overrides"])
        self.assertTrue(calls[0]["overrides"]["include_flow_features"])
        self.assertTrue(calls[0]["overrides"]["buy_action_policy_router_skip_passthrough"])
        self.assertIn("action_policy_routes_by_episode", calls[1]["overrides"])
        self.assertTrue(calls[1]["overrides"]["include_flow_features"])
        self.assertTrue(calls[1]["overrides"]["buy_action_policy_router_skip_passthrough"])
        self.assertEqual(calls[1]["overrides"]["buy_action_policy_router_min_confidence"], 0.55)
        self.assertTrue(saved["selected_candidate"]["passes_acceptance_gate"])


if __name__ == "__main__":
    unittest.main()
