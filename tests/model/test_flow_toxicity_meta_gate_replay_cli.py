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


FLOW_TOXICITY_KEYS = {
    "buy_flow_abstention_min_prob",
    "buy_flow_abstention_max_age_seconds",
    "buy_flow_abstention_min_entry_volume_30s",
    "buy_flow_abstention_min_entry_price_volatility",
    "buy_flow_abstention_max_buy_sell_ratio_60s",
    "buy_flow_abstention_min_sell_pressure_60s",
    "buy_flow_abstention_max_signed_imbalance_60s",
    "buy_flow_abstention_min_buy_sell_overlap_ratio_60s",
}

FLOW_TOXICITY_CONDITION_KEYS = {
    "buy_flow_abstention_max_buy_sell_ratio_60s",
    "buy_flow_abstention_min_sell_pressure_60s",
    "buy_flow_abstention_max_signed_imbalance_60s",
    "buy_flow_abstention_min_buy_sell_overlap_ratio_60s",
}


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_flow_toxicity_meta_gate_replay.py"
    spec = importlib.util.spec_from_file_location("run_flow_toxicity_meta_gate_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, reject_count=0):
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
        "flow_abstention_veto_signal_count": reject_count,
        "flow_abstention_veto_reject_count": reject_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestFlowToxicityMetaGateReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(
            args.output,
            "data/replay_reports/flow_toxicity_meta_gate_replay_20260526_dead_flow_toxicity_meta_gate_round.json",
        )
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_is_bounded_and_uses_one_60s_condition_at_a_time(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 64)
        self.assertLessEqual(len(candidates), cli.MAX_GRID_CANDIDATES)
        for candidate in candidates:
            self.assertEqual(set(candidate) - FLOW_TOXICITY_KEYS, set())
            self.assertIn(candidate["buy_flow_abstention_min_prob"], {0.94, 0.98})
            self.assertIn(candidate["buy_flow_abstention_max_age_seconds"], {60.0, 300.0})
            self.assertIn(candidate["buy_flow_abstention_min_entry_volume_30s"], {0.0, 1.5})
            self.assertIn(candidate["buy_flow_abstention_min_entry_price_volatility"], {0.0, 0.08})
            active_conditions = FLOW_TOXICITY_CONDITION_KEYS.intersection(candidate)
            self.assertEqual(len(active_conditions), 1)

    def test_main_writes_report_with_strict_live_sized_overrides(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_TOXICITY_CONDITION_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.001 if is_candidate else 0.002,
                reject_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            output_path = Path(tmpdir) / "flow_toxicity_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "reject")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertFalse(saved["safe_for_live_switch"])
        self.assertIn("baseline", report)
        self.assertIn("candidates", report)
        self.assertIn("final_confirmation", report)
        for call in calls:
            self.assertEqual(call["overrides"]["position_fraction"], 0.1)
            self.assertEqual(call["overrides"]["max_position_fraction"], 0.1)
            self.assertIsNone(call["overrides"]["fixed_stake_bnb"])
            self.assertTrue(call["overrides"]["skip_all_in_replay"])
            self.assertEqual(call["overrides"]["max_open_positions"], 8)
            self.assertEqual(call["overrides"]["initial_equity_bnb"], 0.002989815772142944)
            self.assertEqual(call["max_open_positions"], 8)
            self.assertFalse(call["include_trade_log"])


if __name__ == "__main__":
    unittest.main()
