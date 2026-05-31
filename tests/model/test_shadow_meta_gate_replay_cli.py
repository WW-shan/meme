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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_shadow_meta_gate_replay.py"
    spec = importlib.util.spec_from_file_location("run_shadow_meta_gate_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, entry_count=1):
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
        "shadow_meta_gate_entry_count": entry_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestShadowMetaGateReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/shadow_meta_gate_replay_20260520_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        self.assertFalse(args.write_selected_trade_delta)
        self.assertEqual(args.shadow_ranker_relevance_mode, "tiered_runner")
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_shadow_score_maps_for_candidate_passes_relevance_mode(self):
        cli = _load_cli()
        args = cli.parse_args(["--shadow-ranker-relevance-mode", "risk_adjusted_return"])
        calls = []

        fake_candidate_ranker = types.ModuleType("src.pipeline.candidate_ranker_probe")

        def fake_fit(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return [{1: 0.75}]

        fake_candidate_ranker.fit_shadow_ranker_and_score_episodes = fake_fit

        context = {
            "loaded": {
                "train_samples": ["train"],
                "episodes_by_split": {"validation": [["eval"]]},
                "buy_artifact": {"model": object()},
                "runtime_params": {"buy_threshold": 0.98},
            }
        }

        with patch.dict(sys.modules, {"src.pipeline.candidate_ranker_probe": fake_candidate_ranker}):
            out = cli._shadow_score_maps_for_candidate(
                args,
                {"buy_shadow_meta_gate_min_score": 0.5},
                split="validation",
                base_overrides={},
                context=context,
            )

        self.assertEqual(out, [{1: 0.75}])
        self.assertEqual(calls[0]["kwargs"]["relevance_mode"], "risk_adjusted_return")
        self.assertEqual(calls[0]["args"][0], ["train"])

    def test_candidate_grid_uses_only_shadow_meta_gate_params(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 48)
        expected_keys = {
            "buy_shadow_meta_gate_min_score",
            "buy_shadow_meta_gate_min_prob",
            "buy_shadow_meta_gate_max_entry_score",
            "buy_shadow_meta_gate_min_entry_volume_30s",
            "buy_shadow_meta_gate_min_entry_price_volatility",
            "buy_shadow_meta_gate_max_age_seconds",
        }
        for candidate in candidates:
            self.assertEqual(set(candidate), expected_keys)
            self.assertEqual(candidate["buy_shadow_meta_gate_max_age_seconds"], 60.0)

    def test_replay_metadata_compacts_shadow_score_maps(self):
        cli = _load_cli()
        report = {
            "generated_at": "2026-05-20T00:00:00+00:00",
            "split": "final",
            "selection_role": "report_only",
            "git": {"commit": "abc123"},
            "model_checksums": {"buy_model.cbm": "sha256"},
            "sample_count": 2,
            "lifecycle_paths": ["data/training/a.json"],
            "replay_config": {
                "position_fraction": 0.1,
                "shadow_scores_by_episode": [{0: 0.7, 3: 0.4}, {}, {1: 0.9}],
            },
        }
        args = cli.parse_args(["--cache-dir", ".cache/test"])

        metadata = cli._report_metadata(report, args)

        self.assertEqual(metadata["git"], {"commit": "abc123"})
        self.assertEqual(metadata["model_checksums"], {"buy_model.cbm": "sha256"})
        self.assertEqual(metadata["sample_count"], 2)
        self.assertEqual(metadata["lifecycle_paths"], ["data/training/a.json"])
        self.assertEqual(metadata["cache_dir"], ".cache/test")
        self.assertTrue(metadata["use_cache"])
        self.assertNotIn("shadow_scores_by_episode", metadata["replay_config"])
        self.assertEqual(
            metadata["replay_config"]["shadow_scores_by_episode_summary"],
            {
                "episode_count": 3,
                "non_empty_episode_count": 2,
                "scored_sample_count": 3,
                "max_episode_score_count": 2,
            },
        )

    def test_main_writes_candidate_report_with_strict_replay_overrides(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_shadow_meta_gate_min_score": 0.5,
            "buy_shadow_meta_gate_min_prob": 0.988,
            "buy_shadow_meta_gate_max_entry_score": 10.0,
            "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
            "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
            "buy_shadow_meta_gate_max_age_seconds": 60.0,
        }])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_shadow_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-20T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": _robust_evaluation(
                    net_profit_bnb=0.002 if is_candidate else 0.001,
                    entry_count=int(is_candidate),
                ),
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "shadow_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_shadow_score_maps_for_candidate", return_value=[{0: 0.75}]
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertNotIn("buy_shadow_meta_gate_min_score", calls[0]["overrides"])
        self.assertIn("shadow_scores_by_episode", calls[1]["overrides"])
        for call in calls:
            self.assertEqual(call["overrides"]["position_fraction"], 0.1)
            self.assertEqual(call["overrides"]["max_position_fraction"], 0.1)
            self.assertIsNone(call["overrides"]["fixed_stake_bnb"])
            self.assertTrue(call["overrides"]["skip_all_in_replay"])
            self.assertEqual(call["overrides"]["max_open_positions"], 8)
            self.assertEqual(call["max_open_positions"], 8)
        self.assertIn("acceptance_gate", report)
        self.assertIn("final_confirmation", report)
        self.assertIn("replay_metadata", saved)
        self.assertIsNone(saved["selected_trade_delta_attribution"])
        self.assertIn("replay_metadata", saved["candidates"][0])
        self.assertEqual(saved["candidates"][0]["replay_metadata"]["git"], {"commit": "abc123"})
        self.assertNotIn(
            "shadow_scores_by_episode",
            saved["candidates"][0]["replay_metadata"]["replay_config"],
        )
        self.assertEqual(saved["replay_metadata"]["final_candidate"]["git"], {"commit": "abc123"})
        self.assertNotIn(
            "shadow_scores_by_episode",
            saved["replay_metadata"]["final_candidate"]["replay_config"],
        )
        self.assertEqual(
            saved["replay_metadata"]["final_candidate"]["replay_config"]["shadow_scores_by_episode_summary"],
            {
                "episode_count": 1,
                "non_empty_episode_count": 1,
                "scored_sample_count": 1,
                "max_episode_score_count": 1,
            },
        )

    def test_validation_selects_accepted_candidate_and_final_only_confirms_selected(self):
        cli = _load_cli()
        grid = [
            {
                "buy_shadow_meta_gate_min_score": 0.35,
                "buy_shadow_meta_gate_min_prob": 0.988,
                "buy_shadow_meta_gate_max_entry_score": 10.0,
                "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
                "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
                "buy_shadow_meta_gate_max_age_seconds": 60.0,
            },
            {
                "buy_shadow_meta_gate_min_score": 0.50,
                "buy_shadow_meta_gate_min_prob": 0.988,
                "buy_shadow_meta_gate_max_entry_score": 10.0,
                "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
                "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
                "buy_shadow_meta_gate_max_age_seconds": 60.0,
            },
        ]
        cli.candidate_grid = lambda: iter(grid)
        calls = []

        def evaluation_for(split, overrides):
            is_candidate = "buy_shadow_meta_gate_min_score" in overrides
            is_second = overrides.get("buy_shadow_meta_gate_min_score") == 0.50
            if not is_candidate:
                return _robust_evaluation(net_profit_bnb=0.001, total_trades=10, entry_count=0)
            if split == "validation" and not is_second:
                row = _robust_evaluation(net_profit_bnb=0.004, total_trades=10, entry_count=1)
                row["win_rate"] = 0.4
                return row
            return _robust_evaluation(net_profit_bnb=0.002, total_trades=10, entry_count=1)

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            return {"evaluation": evaluation_for(kwargs["split"], dict(kwargs.get("overrides") or {}))}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "shadow_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_shadow_score_maps_for_candidate", return_value=[{0: 0.75}]
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_write_selected_trade_delta_reruns_selected_with_trade_logs(self):
        cli = _load_cli()
        candidate = {
            "buy_shadow_meta_gate_min_score": 0.5,
            "buy_shadow_meta_gate_min_prob": 0.988,
            "buy_shadow_meta_gate_max_entry_score": 10.0,
            "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
            "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
            "buy_shadow_meta_gate_max_age_seconds": 60.0,
        }
        cli.candidate_grid = lambda: iter([candidate])
        calls = []
        delta_calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_shadow_meta_gate_min_score" in overrides
            evaluation = _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
            )
            if kwargs.get("include_trade_log"):
                evaluation["trade_log"] = [{
                    "token": "candidate" if is_candidate else "baseline",
                    "return_pct": 10.0 if is_candidate else 5.0,
                }]
            return {"evaluation": evaluation}

        def fake_build_trade_delta_attribution_report(**kwargs):
            delta_calls.append(kwargs)
            return {
                "delta_summary": {
                    "baseline_trade_count": len(kwargs["baseline_trade_rows"]),
                    "candidate_trade_count": len(kwargs["candidate_trade_rows"]),
                },
                "common_trade_deltas": [{"token": "0x1", "return_delta_pct": 5.0}],
            }

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.run_model_replay = fake_run_model_replay
        fake_delta = types.ModuleType("src.pipeline.replay_trade_delta_attribution")
        fake_delta.build_trade_delta_attribution_report = fake_build_trade_delta_attribution_report

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "shadow_meta_gate_report.json"
            with patch.dict(
                sys.modules,
                {
                    "src.pipeline.model_replay": fake_model_replay,
                    "src.pipeline.replay_trade_delta_attribution": fake_delta,
                },
            ), patch.object(cli, "_shadow_score_maps_for_candidate", return_value=[{0: 0.75}]):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main([
                        "--output",
                        str(output_path),
                        "--write-selected-trade-delta",
                    ])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("selected_trade_delta_attribution", report)
        self.assertEqual(set(saved["selected_trade_delta_attribution"]), {"validation", "final"})
        self.assertEqual(len(delta_calls), 2)
        trade_log_calls = [call for call in calls if call.get("include_trade_log")]
        self.assertEqual([call["split"] for call in trade_log_calls], ["validation", "validation", "final", "final"])
        self.assertNotIn("buy_shadow_meta_gate_min_score", trade_log_calls[0]["overrides"])
        self.assertIn("shadow_scores_by_episode", trade_log_calls[1]["overrides"])
        self.assertNotIn("buy_shadow_meta_gate_min_score", trade_log_calls[2]["overrides"])
        self.assertIn("shadow_scores_by_episode", trade_log_calls[3]["overrides"])
        self.assertEqual(
            saved["selected_trade_delta_attribution"]["validation"]["delta_summary"],
            {"baseline_trade_count": 1, "candidate_trade_count": 1},
        )

    def test_requires_shadow_meta_gate_entries(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_shadow_meta_gate_min_score": 0.5,
            "buy_shadow_meta_gate_min_prob": 0.988,
            "buy_shadow_meta_gate_max_entry_score": 10.0,
            "buy_shadow_meta_gate_min_entry_volume_30s": 2.0,
            "buy_shadow_meta_gate_min_entry_price_volatility": 0.20,
            "buy_shadow_meta_gate_max_age_seconds": 60.0,
        }])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_shadow_meta_gate_min_score" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "shadow_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_shadow_score_maps_for_candidate", return_value=[{}]
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["shadow_meta_gate_entry_count"])
        self.assertEqual(report["decision"], "reject")

    def test_shadow_context_passes_schema_flow_flag_to_all_sample_loads(self):
        cli = _load_cli()
        args = cli.parse_args([])
        base_overrides = cli._base_overrides(args)
        load_calls = []

        class ReplaySplit:
            train_files = ["train.json"]
            validation_files = ["validation.json"]
            eval_files = ["final.json"]
            excluded_validation_tokens = {"0xtrain"}
            excluded_final_tokens = {"0xtrain", "0xvalidation"}

        class Artifacts:
            buy_artifact = {"model": object()}

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.load_manifest = lambda _model_dir: {"selected_runtime_params": {}}
        fake_model_replay.live_replay_config_from_manifest = lambda *args, **kwargs: {"buy_threshold": 0.98}
        fake_model_replay.apply_model_schema_feature_flags = lambda config, _model_dir: {
            **dict(config),
            "include_flow_features": True,
        }
        fake_model_replay.resolve_replay_split = lambda *_args, **_kwargs: ReplaySplit()

        def fake_load_or_build_samples(config, files, excluded_tokens, **_kwargs):
            load_calls.append({
                "files": tuple(files),
                "excluded_tokens": set(excluded_tokens),
                "include_flow_features": config.get("include_flow_features"),
            })
            return [{"features": {}, "meta": {"token_address": files[0], "sample_time": 1}}]

        fake_model_replay.load_or_build_samples = fake_load_or_build_samples
        fake_model_replay.load_model_artifacts = lambda _model_dir: Artifacts()

        fake_candidate_ranker = types.ModuleType("src.pipeline.candidate_ranker_probe")
        fake_candidate_ranker.runtime_params_with_buy_threshold = lambda config, _artifact: dict(config)

        fake_train_hybrid = types.ModuleType("src.pipeline.train_hybrid")
        fake_train_hybrid._build_eval_episodes = lambda samples: [samples]

        with patch.dict(
            sys.modules,
            {
                "src.pipeline.model_replay": fake_model_replay,
                "src.pipeline.candidate_ranker_probe": fake_candidate_ranker,
                "src.pipeline.train_hybrid": fake_train_hybrid,
            },
        ):
            loaded = cli._load_shadow_context(args, base_overrides)

        self.assertEqual([call["files"] for call in load_calls], [("train.json",), ("validation.json",), ("final.json",)])
        self.assertEqual([call["include_flow_features"] for call in load_calls], [True, True, True])
        self.assertEqual(load_calls[1]["excluded_tokens"], {"0xtrain"})
        self.assertEqual(load_calls[2]["excluded_tokens"], {"0xtrain", "0xvalidation"})
        self.assertTrue(loaded["runtime_params"]["include_flow_features"])

    def test_refuses_output_path_inside_model_dir_protected_artifact_name(self):
        cli = _load_cli()

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            output_path = model_dir / "hybrid_manifest.json"

            with self.assertRaises(SystemExit):
                cli.main(["--model-dir", str(model_dir), "--output", str(output_path)])


if __name__ == "__main__":
    unittest.main()
