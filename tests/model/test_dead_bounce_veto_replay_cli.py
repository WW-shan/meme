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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_dead_bounce_veto_replay.py"
    spec = importlib.util.spec_from_file_location("run_dead_bounce_veto_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(
    *,
    net_profit_bnb=0.001,
    total_trades=4,
    max_drawdown_pct=-10.0,
    win_rate=0.5,
    walk_forward_worst_net_return_pct=5.0,
    walk_forward_worst_max_drawdown_pct=-12.0,
    stress_worst_net_return_pct=2.0,
    stress_worst_net_profit_bnb=0.0002,
    stress_worst_max_drawdown_pct=-15.0,
    dead_bounce_veto_reject_count=0,
):
    return {
        "net_profit_bnb": net_profit_bnb,
        "total_trades": total_trades,
        "max_drawdown_pct": max_drawdown_pct,
        "win_rate": win_rate,
        "walk_forward_worst_net_return_pct": walk_forward_worst_net_return_pct,
        "walk_forward_worst_max_drawdown_pct": walk_forward_worst_max_drawdown_pct,
        "stress_replay": [{
            "name": "harsh_execution",
            "net_return_pct": stress_worst_net_return_pct,
            "net_profit_bnb": stress_worst_net_profit_bnb,
            "max_drawdown_pct": stress_worst_max_drawdown_pct,
        }],
        "dead_bounce_veto_reject_count": dead_bounce_veto_reject_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


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


class TestDeadBounceVetoReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/dead_bounce_veto_replay_20260521_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_uses_only_dead_bounce_veto_params_and_stays_bounded(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertGreater(len(candidates), 0)
        self.assertLessEqual(len(candidates), 64)
        self.assertEqual(candidates, list(cli.candidate_grid()))
        expected_keys = {
            "buy_dead_bounce_veto_max_age_seconds",
            "buy_dead_bounce_veto_min_peak_drawdown_pct",
            "buy_dead_bounce_veto_min_creator_sell_volume_bnb",
            "buy_dead_bounce_veto_max_buy_pressure",
            "buy_dead_bounce_veto_min_entry_volume_30s",
            "buy_dead_bounce_veto_min_entry_price_volatility",
        }
        for candidate in candidates:
            self.assertEqual(set(candidate), expected_keys)
            self.assertTrue(all(key.startswith("buy_dead_bounce_veto_") for key in candidate))
            self.assertLessEqual(candidate["buy_dead_bounce_veto_min_peak_drawdown_pct"], 0.80)

    def test_main_selects_validation_candidate_and_confirms_on_final(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_dead_bounce_veto_max_age_seconds": 15.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.50,
                "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 0.5,
                "buy_dead_bounce_veto_max_buy_pressure": 0.30,
                "buy_dead_bounce_veto_min_entry_volume_30s": 1.5,
                "buy_dead_bounce_veto_min_entry_price_volatility": 0.10,
            },
            {
                "buy_dead_bounce_veto_max_age_seconds": 30.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.60,
                "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 1.0,
                "buy_dead_bounce_veto_max_buy_pressure": 0.35,
                "buy_dead_bounce_veto_min_entry_volume_30s": 2.0,
                "buy_dead_bounce_veto_min_entry_price_volatility": 0.18,
            },
        ])
        calls = []

        def evaluation_for(split, overrides):
            is_candidate = "buy_dead_bounce_veto_max_age_seconds" in overrides
            is_second = overrides.get("buy_dead_bounce_veto_max_age_seconds") == 30.0
            if not is_candidate:
                return _robust_evaluation(net_profit_bnb=0.001 if split == "validation" else 0.0008)
            if not is_second:
                return _robust_evaluation(
                    net_profit_bnb=0.004,
                    max_drawdown_pct=-8.0,
                    win_rate=0.4,
                    walk_forward_worst_net_return_pct=1.0,
                    dead_bounce_veto_reject_count=2,
                )
            return _robust_evaluation(
                net_profit_bnb=0.003,
                max_drawdown_pct=-8.0,
                win_rate=0.75,
                walk_forward_worst_net_return_pct=7.0,
                walk_forward_worst_max_drawdown_pct=-11.0,
                stress_worst_net_return_pct=3.0,
                stress_worst_net_profit_bnb=0.0003,
                stress_worst_max_drawdown_pct=-14.0,
                dead_bounce_veto_reject_count=2,
            )

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dead_bounce_veto_report.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertEqual(report["decision"], "accept")
        self.assertFalse(report["live_switch_evidence"])
        self.assertFalse(report["safe_for_live_switch"])
        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertFalse(saved["safe_for_live_switch"])
        self.assertEqual(calls[0]["overrides"]["position_fraction"], 0.1)
        self.assertEqual(calls[0]["overrides"]["max_position_fraction"], 0.1)
        self.assertIsNone(calls[0]["overrides"]["fixed_stake_bnb"])
        self.assertTrue(calls[0]["overrides"]["skip_all_in_replay"])
        self.assertEqual(calls[0]["overrides"]["max_open_positions"], 8)
        self.assertEqual(calls[0]["max_open_positions"], 8)
        self.assertNotIn("buy_dead_bounce_veto_max_age_seconds", calls[-2]["overrides"])
        self.assertEqual(calls[-1]["overrides"]["buy_dead_bounce_veto_max_age_seconds"], 30.0)

    def test_acceptance_requires_dead_bounce_rejections(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.60,
            "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 1.0,
            "buy_dead_bounce_veto_max_buy_pressure": 0.35,
            "buy_dead_bounce_veto_min_entry_volume_30s": 2.0,
            "buy_dead_bounce_veto_min_entry_price_volatility": 0.18,
        }])

        def fake_run_model_replay(**kwargs):
            is_candidate = "buy_dead_bounce_veto_max_age_seconds" in dict(kwargs.get("overrides") or {})
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.003 if is_candidate else 0.001,
                max_drawdown_pct=-8.0 if is_candidate else -10.0,
                win_rate=0.75 if is_candidate else 0.5,
                walk_forward_worst_net_return_pct=7.0 if is_candidate else 5.0,
                walk_forward_worst_max_drawdown_pct=-11.0 if is_candidate else -12.0,
                stress_worst_net_return_pct=3.0 if is_candidate else 2.0,
                stress_worst_net_profit_bnb=0.0003 if is_candidate else 0.0002,
                stress_worst_max_drawdown_pct=-14.0 if is_candidate else -15.0,
                dead_bounce_veto_reject_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dead_bounce_veto_reject.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual(report["decision"], "reject")
        self.assertFalse(report["candidates"][0]["passes_acceptance_gate"])
        self.assertFalse(report["candidates"][0]["gate_details"]["dead_bounce_veto_reject_count"])
        self.assertFalse(report["live_switch_evidence"])
        self.assertFalse(report["safe_for_live_switch"])

    def test_acceptance_rejects_trade_count_expansion_and_material_reduction(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([
            {
                "buy_dead_bounce_veto_max_age_seconds": 15.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.50,
                "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 0.5,
                "buy_dead_bounce_veto_max_buy_pressure": 0.30,
                "buy_dead_bounce_veto_min_entry_volume_30s": 1.5,
                "buy_dead_bounce_veto_min_entry_price_volatility": 0.10,
            },
            {
                "buy_dead_bounce_veto_max_age_seconds": 45.0,
                "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.70,
                "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 2.0,
                "buy_dead_bounce_veto_max_buy_pressure": 0.35,
                "buy_dead_bounce_veto_min_entry_volume_30s": 2.0,
                "buy_dead_bounce_veto_min_entry_price_volatility": 0.18,
            },
        ])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_dead_bounce_veto_max_age_seconds" in overrides
            expanded = overrides.get("buy_dead_bounce_veto_max_age_seconds") == 15.0
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.003 if is_candidate else 0.001,
                total_trades=5 if expanded else (2 if is_candidate else 4),
                max_drawdown_pct=-8.0 if is_candidate else -10.0,
                win_rate=0.75 if is_candidate else 0.5,
                walk_forward_worst_net_return_pct=7.0 if is_candidate else 5.0,
                walk_forward_worst_max_drawdown_pct=-11.0 if is_candidate else -12.0,
                stress_worst_net_return_pct=3.0 if is_candidate else 2.0,
                stress_worst_net_profit_bnb=0.0003 if is_candidate else 0.0002,
                stress_worst_max_drawdown_pct=-14.0 if is_candidate else -15.0,
                dead_bounce_veto_reject_count=2 if is_candidate else 0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "dead_bounce_veto_trade_count.json"
            with patch_modules({"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual(report["decision"], "reject")
        self.assertFalse(report["candidates"][0]["gate_details"]["total_trades_not_higher"])
        self.assertFalse(report["candidates"][1]["gate_details"]["total_trades_not_materially_lower"])


if __name__ == "__main__":
    unittest.main()
