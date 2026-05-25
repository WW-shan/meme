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


FLOW_ABSTENTION_KEYS = {
    "buy_flow_abstention_min_prob",
    "buy_flow_abstention_max_age_seconds",
    "buy_flow_abstention_min_entry_volume_30s",
    "buy_flow_abstention_min_entry_price_volatility",
    "buy_flow_abstention_max_buy_sell_ratio_30s",
    "buy_flow_abstention_min_sell_pressure_30s",
    "buy_flow_abstention_max_signed_imbalance_30s",
}


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_flow_abstention_replay.py"
    spec = importlib.util.spec_from_file_location("run_flow_abstention_replay", path)
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


class TestFlowAbstentionReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/flow_abstention_replay_20260526_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        self.assertEqual(cli.LIVE_INITIAL_EQUITY_BNB, 0.002989815772142944)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_is_bounded_and_uses_one_flow_condition_at_a_time(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 144)
        self.assertLessEqual(len(candidates), cli.MAX_GRID_CANDIDATES)
        for candidate in candidates:
            self.assertIn(candidate["buy_flow_abstention_min_prob"], {0.94, 0.98})
            self.assertIn(candidate["buy_flow_abstention_max_age_seconds"], {60.0, 300.0})
            self.assertIn(candidate["buy_flow_abstention_min_entry_volume_30s"], {0.0, 1.5})
            self.assertIn(candidate["buy_flow_abstention_min_entry_price_volatility"], {0.0, 0.08})
            active_conditions = FLOW_ABSTENTION_KEYS.intersection(candidate) - {
                "buy_flow_abstention_min_prob",
                "buy_flow_abstention_max_age_seconds",
                "buy_flow_abstention_min_entry_volume_30s",
                "buy_flow_abstention_min_entry_price_volatility",
            }
            self.assertEqual(len(active_conditions), 1)

    def test_main_writes_report_with_strict_live_sized_overrides(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([next(iter(cli._default_candidate_grid()))])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(FLOW_ABSTENTION_KEYS.intersection(overrides))
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.001 if is_candidate else 0.002,
                reject_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            output_path = Path(tmpdir) / "flow_abstention_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "reject")
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

    def test_validation_selects_accepted_candidate_and_final_only_confirms_selected(self):
        cli = _load_cli()
        calls = []
        grid = [
            {
                "buy_flow_abstention_min_prob": 0.98,
                "buy_flow_abstention_max_age_seconds": 60.0,
                "buy_flow_abstention_min_entry_volume_30s": 1.5,
                "buy_flow_abstention_min_entry_price_volatility": 0.08,
                "buy_flow_abstention_max_buy_sell_ratio_30s": 1.0,
            },
            {
                "buy_flow_abstention_min_prob": 0.94,
                "buy_flow_abstention_max_age_seconds": 300.0,
                "buy_flow_abstention_min_entry_volume_30s": 0.0,
                "buy_flow_abstention_min_entry_price_volatility": 0.0,
                "buy_flow_abstention_min_sell_pressure_30s": 0.55,
            },
        ]
        cli.candidate_grid = lambda: iter(grid)

        def evaluation_for(split, overrides):
            is_candidate = bool(FLOW_ABSTENTION_KEYS.intersection(overrides))
            is_second_candidate = overrides.get("buy_flow_abstention_min_prob") == 0.94
            if split == "validation" and not is_candidate:
                return _robust_evaluation(net_profit_bnb=0.001, total_trades=4, reject_count=0)
            if split == "validation":
                if not is_second_candidate:
                    row = _robust_evaluation(net_profit_bnb=0.004, total_trades=3, reject_count=1)
                    row["win_rate"] = 0.4
                    return row
                return _robust_evaluation(
                    net_profit_bnb=0.002,
                    total_trades=3,
                    reject_count=1,
                )
            if not is_candidate:
                return _robust_evaluation(net_profit_bnb=0.0008, total_trades=4, reject_count=0)
            return _robust_evaluation(net_profit_bnb=0.0025, total_trades=3, reject_count=1)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            output_path = Path(tmpdir) / "flow_abstention_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        final_calls = calls[-2:]
        self.assertFalse(FLOW_ABSTENTION_KEYS.intersection(final_calls[0]["overrides"]))
        self.assertEqual(final_calls[1]["overrides"]["buy_flow_abstention_min_prob"], 0.94)
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_refuses_output_outside_replay_reports(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow_abstention_report.json"

            with self.assertRaises(SystemExit) as raised:
                cli.main(["--output", str(output_path)])

        self.assertIn("outside data/replay_reports", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
