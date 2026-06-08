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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_primary_score_scalp_replay.py"
    spec = importlib.util.spec_from_file_location("run_primary_score_scalp_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, entry_count=0):
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
        "quick_profit_overlay_entry_count": entry_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestPrimaryScoreScalpReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/primary_score_scalp_replay_20260519_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertIsNone(args.candidate_grid_json)
        self.assertFalse(args.write_selected_trade_delta)
        self.assertTrue(args.use_cache)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_uses_only_quick_profit_overlay_params_and_stays_bounded(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 108)
        for candidate in candidates:
            self.assertEqual(
                set(candidate),
                {
                    "buy_quick_profit_overlay_min_prob",
                    "buy_quick_profit_overlay_min_pred_return",
                    "buy_quick_profit_overlay_max_pred_return",
                    "buy_quick_profit_overlay_min_entry_volume_30s",
                    "buy_quick_profit_overlay_min_entry_price_volatility",
                    "buy_quick_profit_overlay_max_age_seconds",
                    "buy_quick_profit_overlay_take_profit_pct",
                    "buy_quick_profit_overlay_max_hold_seconds",
                },
            )
            self.assertEqual(candidate["buy_quick_profit_overlay_max_pred_return"], 35.0)
            self.assertEqual(candidate["buy_quick_profit_overlay_max_age_seconds"], 60.0)
            self.assertEqual(candidate["buy_quick_profit_overlay_max_hold_seconds"], 120.0)

    def test_main_writes_bounded_candidate_report_with_strict_replay_overrides(self):
        cli = _load_cli()
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.001 if is_candidate else 0.002,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("baseline", report)
        self.assertIn("candidates", report)
        self.assertIn("best_candidate", report)
        self.assertIn("decision", report)
        self.assertIn("acceptance_gate", report)
        self.assertIn("candidate_grid", report)
        self.assertEqual(saved["decision"], "reject")
        self.assertEqual(saved["candidate_grid"]["source"], "default")
        self.assertGreater(len(report["candidates"]), 0)
        self.assertFalse(calls[0]["include_trade_log"])
        self.assertTrue(calls[0]["use_cache"])
        for call in calls:
            self.assertEqual(call["overrides"]["position_fraction"], 0.1)
            self.assertEqual(call["overrides"]["max_position_fraction"], 0.1)
            self.assertIsNone(call["overrides"]["fixed_stake_bnb"])
            self.assertTrue(call["overrides"]["skip_all_in_replay"])
            self.assertEqual(call["overrides"]["max_open_positions"], 8)
            self.assertEqual(call["max_open_positions"], 8)

    def test_validation_selects_candidate_and_final_only_confirms_selected(self):
        cli = _load_cli()
        calls = []
        grid = [
            {
                "buy_quick_profit_overlay_min_prob": 0.988,
                "buy_quick_profit_overlay_min_pred_return": 32.0,
                "buy_quick_profit_overlay_take_profit_pct": 0.25,
            },
            {
                "buy_quick_profit_overlay_min_prob": 0.988,
                "buy_quick_profit_overlay_min_pred_return": 25.0,
                "buy_quick_profit_overlay_take_profit_pct": 0.25,
            },
        ]
        cli.candidate_grid = lambda: iter(grid)

        def evaluation_for(split, overrides):
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            is_second_candidate = overrides.get("buy_quick_profit_overlay_min_pred_return") == 25.0
            if split == "validation" and not is_candidate:
                return {
                    "net_profit_bnb": 0.001,
                    "total_trades": 2,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": -4.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -5.0,
                        "net_profit_bnb": -0.0005,
                        "max_drawdown_pct": -14.0,
                    }],
                    "quick_profit_overlay_entry_count": 0,
                }
            if split == "validation":
                return {
                    "net_profit_bnb": 0.002 if is_second_candidate else 0.004,
                    "total_trades": 3,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.6 if is_second_candidate else 0.4,
                    "walk_forward_worst_net_return_pct": -2.0 if is_second_candidate else -8.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0 if is_second_candidate else -18.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -3.0 if is_second_candidate else -9.0,
                        "net_profit_bnb": -0.0002 if is_second_candidate else -0.0009,
                        "max_drawdown_pct": -12.0 if is_second_candidate else -20.0,
                    }],
                    "quick_profit_overlay_entry_count": 1,
                }
            if not is_candidate:
                return {
                    "net_profit_bnb": 0.0008,
                    "total_trades": 2,
                    "max_drawdown_pct": -10.0,
                    "win_rate": 0.5,
                    "walk_forward_worst_net_return_pct": -4.0,
                    "walk_forward_worst_max_drawdown_pct": -12.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -5.0,
                        "net_profit_bnb": -0.0005,
                        "max_drawdown_pct": -14.0,
                    }],
                    "quick_profit_overlay_entry_count": 0,
                }
            return {
                "net_profit_bnb": 0.0025,
                "total_trades": 3,
                "max_drawdown_pct": -8.0,
                "win_rate": 0.6,
                "walk_forward_worst_net_return_pct": -2.0,
                "walk_forward_worst_max_drawdown_pct": -10.0,
                "stress_replay": [{
                    "name": "harsh_friction",
                    "net_return_pct": -3.0,
                    "net_profit_bnb": -0.0002,
                    "max_drawdown_pct": -12.0,
                }],
                "quick_profit_overlay_entry_count": 1,
            }

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        final_calls = calls[-2:]
        self.assertNotIn("buy_quick_profit_overlay_min_prob", final_calls[0]["overrides"])
        self.assertEqual(final_calls[1]["overrides"]["buy_quick_profit_overlay_min_pred_return"], 25.0)
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_candidate"]["candidate_index"], 1)
        self.assertEqual(report["best_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_requires_quick_profit_overlay_entries(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["quick_profit_overlay_entry_count"])
        self.assertEqual(report["decision"], "reject")

    def test_rejects_profit_improvement_when_robustness_worsens(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            if not is_candidate:
                return {"evaluation": _robust_evaluation(net_profit_bnb=0.001)}
            return {
                "evaluation": {
                    "net_profit_bnb": 0.002,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.4,
                    "walk_forward_worst_net_return_pct": -6.0,
                    "walk_forward_worst_max_drawdown_pct": -16.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": -7.0,
                        "net_profit_bnb": -0.0002,
                        "max_drawdown_pct": -20.0,
                    }],
                    "quick_profit_overlay_entry_count": 1,
                }
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["win_rate"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["walk_forward_worst_max_drawdown_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_return_pct"])
        self.assertFalse(candidate["gate_details"]["stress_worst_net_profit_bnb"])
        self.assertFalse(candidate["gate_details"]["stress_worst_max_drawdown_pct"])
        self.assertEqual(report["decision"], "reject")

    def test_rejects_material_trade_count_expansion(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                total_trades=20 if is_candidate else 10,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["total_trades_not_materially_higher"])
        self.assertEqual(report["decision"], "reject")

    def test_refuses_output_path_inside_model_dir_protected_artifact_name(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            output_path = model_dir / "hybrid_manifest.json"

            with self.assertRaises(SystemExit):
                cli.main(["--model-dir", str(model_dir), "--output", str(output_path)])

    def test_force_allows_overwriting_existing_report(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            output_path.write_text("existing\n", encoding="utf-8")

            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path), "--force"])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertEqual(report["decision"], "accept")
        self.assertEqual(saved["selected_candidate"]["candidate_index"], 0)

    def test_candidate_grid_json_overrides_default_grid(self):
        cli = _load_cli()
        calls = []

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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            grid_path = Path(tmpdir) / "grid.json"
            grid_path.write_text(
                json.dumps({
                    "candidates": [{
                        "buy_quick_profit_overlay_min_prob": 0.982,
                        "buy_quick_profit_overlay_min_pred_return": 0.0,
                        "buy_quick_profit_overlay_max_pred_return": 15.0,
                        "buy_quick_profit_overlay_take_profit_pct": 0.25,
                    }]
                }),
                encoding="utf-8",
            )
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main([
                        "--output", str(output_path),
                        "--candidate-grid-json", str(grid_path),
                    ])

        self.assertEqual(report["candidate_grid"]["source"], str(grid_path))
        self.assertEqual(report["candidate_grid"]["candidate_count"], 1)
        self.assertEqual(len(report["candidates"]), 1)
        self.assertEqual(
            calls[1]["overrides"]["buy_quick_profit_overlay_max_pred_return"],
            15.0,
        )

    def test_can_write_selected_trade_delta_attribution(self):
        cli = _load_cli()
        calls = []
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            evaluation = _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )
            if kwargs.get("include_trade_log"):
                base_trade = {
                    "token": "0xaaa",
                    "entry_signal_time": 100,
                    "return_pct": 10.0,
                    "exit_reason": "BASE",
                }
                candidate_trade = {
                    "token": "0xaaa",
                    "entry_signal_time": 100,
                    "return_pct": 25.0 if is_candidate else 10.0,
                    "exit_reason": "CANDIDATE" if is_candidate else "BASE",
                }
                evaluation["trade_log"] = [candidate_trade if is_candidate else base_trade]
            return {"evaluation": evaluation}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay
        fake_module.load_manifest = lambda _model_dir: {"manifest": True}
        fake_module.live_replay_config_from_manifest = (
            lambda _manifest, **kwargs: dict(kwargs.get("overrides") or {})
        )
        fake_module.apply_model_schema_feature_flags = lambda config, _model_dir: config
        fake_module.resolve_replay_split = lambda _manifest, _lifecycle_dir: types.SimpleNamespace(
            validation_files=["validation-file"],
            excluded_validation_tokens=set(),
            eval_files=["final-file"],
            excluded_final_tokens=set(),
        )
        fake_module.load_or_build_samples = lambda *_args, **_kwargs: []

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main([
                        "--output", str(output_path),
                        "--write-selected-trade-delta",
                    ])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("selected_trade_delta_attribution", saved)
        self.assertEqual(
            report["selected_trade_delta_attribution"]["validation"]["delta_summary"]["common_trades"]["improved_count"],
            1,
        )
        trade_log_calls = [call for call in calls if call.get("include_trade_log")]
        self.assertEqual(len(trade_log_calls), 4)
        self.assertTrue(all(call["overrides"]["position_fraction"] == 0.1 for call in trade_log_calls))

    def test_selected_trade_delta_attribution_uses_preloaded_eval_samples(self):
        cli = _load_cli()
        calls = []
        captured_sample_rows = []
        cli.candidate_grid = lambda: iter([{
            "buy_quick_profit_overlay_min_prob": 0.988,
            "buy_quick_profit_overlay_min_pred_return": 25.0,
            "buy_quick_profit_overlay_take_profit_pct": 0.25,
        }])

        validation_samples = [{"meta": {"token_address": "0xvalidation"}}]
        final_samples = [{"meta": {"token_address": "0xfinal"}}]

        def fake_load_or_build_samples(_config, files, excluded_tokens, **_kwargs):
            if files == ["validation-file"]:
                self.assertEqual(excluded_tokens, {"validation-excluded"})
                return validation_samples
            if files == ["final-file"]:
                self.assertEqual(excluded_tokens, {"final-excluded"})
                return final_samples
            self.fail(f"unexpected replay files: {files}")

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_quick_profit_overlay_min_prob" in overrides
            evaluation = _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )
            if kwargs.get("include_trade_log"):
                evaluation["trade_log"] = [{
                    "token": "0xaaa",
                    "entry_signal_time": 100,
                    "return_pct": 10.0,
                    "exit_reason": "CANDIDATE" if is_candidate else "BASE",
                }]
            return {"evaluation": evaluation}

        def fake_build_trade_delta_attribution_report(**kwargs):
            sample_rows = list(kwargs.get("sample_rows") or [])
            captured_sample_rows.append(sample_rows)
            return {
                "delta_summary": {"common_trades": {"improved_count": 0}},
                "matched_feature_rows": {"sample_row_count": len(sample_rows)},
            }

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.run_model_replay = fake_run_model_replay
        fake_model_replay.load_manifest = lambda _model_dir: {"manifest": True}
        fake_model_replay.live_replay_config_from_manifest = (
            lambda _manifest, **kwargs: dict(kwargs.get("overrides") or {})
        )
        fake_model_replay.apply_model_schema_feature_flags = lambda config, _model_dir: config
        fake_model_replay.resolve_replay_split = lambda _manifest, _lifecycle_dir: types.SimpleNamespace(
            validation_files=["validation-file"],
            excluded_validation_tokens={"validation-excluded"},
            eval_files=["final-file"],
            excluded_final_tokens={"final-excluded"},
        )
        fake_model_replay.load_or_build_samples = fake_load_or_build_samples

        fake_delta = types.ModuleType("src.pipeline.replay_trade_delta_attribution")
        fake_delta.build_trade_delta_attribution_report = fake_build_trade_delta_attribution_report

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "primary_score_scalp_report.json"
            with patch.dict(
                sys.modules,
                {
                    "src.pipeline.model_replay": fake_model_replay,
                    "src.pipeline.replay_trade_delta_attribution": fake_delta,
                },
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main([
                        "--output", str(output_path),
                        "--write-selected-trade-delta",
                    ])

        self.assertEqual(captured_sample_rows, [validation_samples, final_samples])
        self.assertEqual(
            report["selected_trade_delta_attribution"]["validation"]["matched_feature_rows"]["sample_row_count"],
            1,
        )
        self.assertEqual(
            report["selected_trade_delta_attribution"]["final"]["matched_feature_rows"]["sample_row_count"],
            1,
        )
        trade_log_calls = [call for call in calls if call.get("include_trade_log")]
        self.assertEqual(len(trade_log_calls), 4)
        for call in trade_log_calls:
            overrides = call["overrides"]
            self.assertIn("eval_samples", overrides)
            self.assertTrue(overrides["eval_samples_already_split_filtered"])


if __name__ == "__main__":
    unittest.main()
