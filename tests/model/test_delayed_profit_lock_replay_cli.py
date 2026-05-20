import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
import unittest.mock
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_delayed_profit_lock_replay.py"
    spec = importlib.util.spec_from_file_location("run_delayed_profit_lock_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


def _robust_evaluation(*, net_profit_bnb, total_trades=10, profit_lock_count=1):
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
        "profit_lock_take_profit_count": profit_lock_count,
    }


class TestDelayedProfitLockReplayCli(unittest.TestCase):
    def test_candidate_grid_uses_delayed_windows_only(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 16)
        self.assertEqual(
            candidates[0],
            {"profit_lock_take_profit_pct": 0.25, "profit_lock_max_hold_seconds": 180.0},
        )
        self.assertEqual(
            candidates[-1],
            {"profit_lock_take_profit_pct": 0.60, "profit_lock_max_hold_seconds": 480.0},
        )
        for candidate in candidates:
            self.assertEqual(set(candidate), {"profit_lock_take_profit_pct", "profit_lock_max_hold_seconds"})
            self.assertGreater(candidate["profit_lock_max_hold_seconds"], 120.0)

    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.output, "data/replay_reports/delayed_profit_lock_replay_20260521_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_loading_delayed_cli_does_not_mutate_fast_cli_defaults(self):
        _load_cli()

        from scripts import run_fast_profit_lock_replay as module

        args = module.parse_args([])
        self.assertEqual(args.output, "data/replay_reports/fast_profit_lock_replay_20260520_v95.json")

    def test_main_uses_delayed_grid_and_equity_without_mutating_fast_grid_during_run(self):
        cli = _load_cli()
        from scripts import run_fast_profit_lock_replay as fast_cli

        calls = []
        observed_fast_windows = []
        cli.candidate_grid = lambda: iter([{
            "profit_lock_take_profit_pct": 0.25,
            "profit_lock_max_hold_seconds": 180.0,
        }])

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            observed_fast_windows.append(next(fast_cli.candidate_grid())["profit_lock_max_hold_seconds"])
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "profit_lock_take_profit_pct" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                profit_lock_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "delayed_profit_lock_report.json"
            with unittest.mock.patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report["decision"], "accept")
        self.assertEqual(saved["decision"], "accept")
        self.assertEqual(observed_fast_windows, [30.0, 30.0, 30.0, 30.0])
        self.assertEqual(calls[1]["overrides"]["profit_lock_max_hold_seconds"], 180.0)
        self.assertEqual(calls[1]["overrides"]["profit_lock_take_profit_pct"], 0.25)
        for call in calls:
            overrides = call["overrides"]
            self.assertEqual(overrides["initial_equity_bnb"], 0.003957285747499339)
            self.assertEqual(overrides["position_fraction"], 0.1)
            self.assertEqual(overrides["max_position_fraction"], 0.1)
            self.assertIsNone(overrides["fixed_stake_bnb"])
            self.assertTrue(overrides["skip_all_in_replay"])
            self.assertEqual(overrides["max_open_positions"], 8)


if __name__ == "__main__":
    unittest.main()
