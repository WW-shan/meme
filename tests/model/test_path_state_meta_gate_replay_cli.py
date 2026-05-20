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
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_path_state_meta_gate_replay.py"
    spec = importlib.util.spec_from_file_location("run_path_state_meta_gate_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _robust_evaluation(*, net_profit_bnb, total_trades=10, entry_count=1, reject_count=1):
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
        "path_state_meta_gate_entry_count": entry_count,
        "path_state_meta_gate_reject_count": reject_count,
    }


def _assert_parse_exits(testcase, cli, argv):
    with contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit):
            cli.parse_args(argv)


class TestPathStateMetaGateReplayCli(unittest.TestCase):
    def test_parse_args_defaults_and_rejects_risk_expansion(self):
        cli = _load_cli()

        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.output, "data/replay_reports/path_state_meta_gate_replay_20260520_v95.json")
        self.assertEqual(args.position_fraction, 0.1)
        self.assertEqual(args.max_position_fraction, 0.1)
        self.assertEqual(args.max_open_positions, 8)
        self.assertTrue(args.use_cache)
        _assert_parse_exits(self, cli, ["--position-fraction", "0.2"])
        _assert_parse_exits(self, cli, ["--position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-position-fraction", "0.05"])
        _assert_parse_exits(self, cli, ["--max-open-positions", "9"])

    def test_candidate_grid_uses_only_path_state_meta_gate_params(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(candidates, [
            {"buy_path_state_meta_gate_min_score": 0.35},
            {"buy_path_state_meta_gate_min_score": 0.50},
            {"buy_path_state_meta_gate_min_score": 0.65},
            {"buy_path_state_meta_gate_min_score": 0.75},
            {"buy_path_state_meta_gate_min_score": 0.85},
            {"buy_path_state_meta_gate_min_score": 0.90},
            {"buy_path_state_meta_gate_min_score": 0.95},
            {"buy_path_state_meta_gate_min_score": 0.98},
            {"buy_path_state_meta_gate_min_score": 0.99},
        ])

    def test_replay_metadata_compacts_path_state_score_maps(self):
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
                "eval_samples": [{"features": {}, "meta": {"sample_time": 1}}],
                "path_state_scores_by_episode": [{0: 0.7, 3: 0.4}, {}, {1: 0.9}],
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
        self.assertNotIn("eval_samples", metadata["replay_config"])
        self.assertEqual(metadata["replay_config"]["eval_samples_summary"], {"sample_count": 1})
        self.assertNotIn("path_state_scores_by_episode", metadata["replay_config"])
        self.assertEqual(
            metadata["replay_config"]["path_state_scores_by_episode_summary"],
            {
                "episode_count": 3,
                "non_empty_episode_count": 2,
                "scored_sample_count": 3,
                "max_episode_score_count": 2,
            },
        )

    def test_main_writes_candidate_report_with_strict_replay_overrides(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_path_state_meta_gate_min_score": 0.5}])
        calls = []
        validation_samples = [{"meta": {"token_address": "0xvalidation", "sample_time": 1}}]
        final_samples = [{"meta": {"token_address": "0xfinal", "sample_time": 1}}]

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
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
            output_path = Path(tmpdir) / "path_state_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_path_state_score_maps_for_split", return_value=[{0: 0.75}]
            ), patch.object(
                cli,
                "_eval_samples_for_split",
                side_effect=lambda _args, *, split, **_kwargs: validation_samples if split == "validation" else final_samples,
            ):
                stderr = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                    report = cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("stage=validation_baseline start", stderr.getvalue())
        self.assertIn("stage=final_candidate done", stderr.getvalue())
        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertIs(calls[0]["overrides"]["eval_samples"], validation_samples)
        self.assertIs(calls[1]["overrides"]["eval_samples"], validation_samples)
        self.assertIs(calls[2]["overrides"]["eval_samples"], final_samples)
        self.assertIs(calls[3]["overrides"]["eval_samples"], final_samples)
        self.assertNotIn("buy_path_state_meta_gate_min_score", calls[0]["overrides"])
        self.assertIn("path_state_scores_by_episode", calls[1]["overrides"])
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
        self.assertIn("replay_metadata", saved["candidates"][0])
        self.assertEqual(saved["candidates"][0]["replay_metadata"]["git"], {"commit": "abc123"})
        self.assertNotIn(
            "path_state_scores_by_episode",
            saved["candidates"][0]["replay_metadata"]["replay_config"],
        )
        self.assertEqual(saved["replay_metadata"]["final_candidate"]["git"], {"commit": "abc123"})
        self.assertNotIn(
            "path_state_scores_by_episode",
            saved["replay_metadata"]["final_candidate"]["replay_config"],
        )
        self.assertEqual(saved["replay_metadata"]["final_candidate"]["replay_config"]["eval_samples_summary"], {"sample_count": 1})
        self.assertEqual(
            saved["replay_metadata"]["final_candidate"]["replay_config"]["path_state_scores_by_episode_summary"],
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
            {"buy_path_state_meta_gate_min_score": 0.35},
            {"buy_path_state_meta_gate_min_score": 0.50},
        ]
        cli.candidate_grid = lambda: iter(grid)
        calls = []

        def evaluation_for(split, overrides):
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            is_second = overrides.get("buy_path_state_meta_gate_min_score") == 0.50
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
            output_path = Path(tmpdir) / "path_state_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_path_state_score_maps_for_split", return_value=[{0: 0.75}]
            ), patch.object(cli, "_eval_samples_for_split", return_value=[{"meta": {"token_address": "0xsample"}}]):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
        self.assertEqual(report["best_validation_raw_candidate"]["candidate_index"], 0)
        self.assertEqual(report["best_validation_accepted_candidate"]["candidate_index"], 1)
        self.assertEqual(report["selected_candidate"]["candidate_index"], 1)
        self.assertEqual(report["final_confirmation"]["candidate"]["candidate_index"], 1)
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])
        self.assertEqual(report["decision"], "accept")

    def test_requires_path_state_meta_gate_entries(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_path_state_meta_gate_min_score": 0.5}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "path_state_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_path_state_score_maps_for_split", return_value=[{}]
            ), patch.object(cli, "_eval_samples_for_split", return_value=[{"meta": {"token_address": "0xsample"}}]):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["path_state_meta_gate_entry_count"])
        self.assertEqual(report["decision"], "reject")

    def test_requires_path_state_meta_gate_to_actually_reject_candidates(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_path_state_meta_gate_min_score": 0.5}])

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {"evaluation": _robust_evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                entry_count=int(is_candidate),
                reject_count=0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "path_state_meta_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli, "_path_state_score_maps_for_split", return_value=[{0: 0.75}]
            ), patch.object(cli, "_eval_samples_for_split", return_value=[{"meta": {"token_address": "0xsample"}}]):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output_path)])

        candidate = report["candidates"][0]
        self.assertFalse(candidate["passes_acceptance_gate"])
        self.assertFalse(candidate["gate_details"]["path_state_meta_gate_reject_count"])
        self.assertEqual(report["decision"], "reject")

    def test_path_state_context_loads_requested_eval_split_only(self):
        cli = _load_cli()
        args = cli.parse_args([])
        base_overrides = cli._base_overrides(args)
        load_calls = []

        class ReplaySplit:
            train_files = ["train.json"]
            validation_files = ["validation.json"]
            eval_files = ["final.json"]
            excluded_validation_tokens = set()
            excluded_final_tokens = set()

        class Artifacts:
            buy_artifact = {"model": object(), "entry_value_model": {"model": object()}}

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.load_manifest = lambda _model_dir: {"selected_runtime_params": {}}
        fake_model_replay.live_replay_config_from_manifest = lambda *args, **kwargs: {"buy_threshold": 0.98}
        fake_model_replay.resolve_replay_split = lambda *_args, **_kwargs: ReplaySplit()

        def fake_load_or_build_samples(_config, files, _excluded, **_kwargs):
            load_calls.append(tuple(files))
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
            common = cli._load_path_state_common_context(args, base_overrides)
            validation_episodes = cli._load_path_state_split_episodes(args, common, "validation")

        self.assertEqual(load_calls, [("train.json",), ("validation.json",)])
        self.assertEqual(validation_episodes, [[{"features": {}, "meta": {"token_address": "validation.json", "sample_time": 1}}]])

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
