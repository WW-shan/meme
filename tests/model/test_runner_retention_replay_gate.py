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

from src.pipeline import reentry_probe
from src.pipeline import runner_retention_replay_gate as gate


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_runner_retention_candidate_gate_replay.py"
    spec = importlib.util.spec_from_file_location("run_runner_retention_candidate_gate_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _sample(token, *, sample_time, flow_sell_pressure_30s=0.1, flow_signed_imbalance_30s=0.5):
    return {
        "features": {
            "current_price": 1.0,
            "volume_30s": 0.75,
            "price_volatility": 0.08,
            "flow_sell_pressure_30s": flow_sell_pressure_30s,
            "flow_signed_imbalance_30s": flow_signed_imbalance_30s,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - 30,
        },
    }


def _path(anchor, *, kind):
    if kind == "slow_runner":
        return [
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor - 1), 1.0, "anchor"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 240), 1.26, "buy"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 390), 1.65, "buy"),
        ]
    return [
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor), 1.0, "anchor"),
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 180), 1.02, "buy"),
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 500), 0.98, "sell"),
    ]


class TestRunnerRetentionReplayGate(unittest.TestCase):
    def test_scores_runner_retention_near_candidates_and_keeps_episode_metadata(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xeval", sample_time=3000, flow_sell_pressure_30s=0.1),
            _sample("0xeval", sample_time=3010, flow_sell_pressure_30s=0.9),
        ]]
        runtime_params = {
            "buy_threshold": 0.99,
            "buy_near_threshold_min_prob": 0.85,
            "min_entry_score": 35.0,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }

        def fake_score_samples(samples, buy_artifact):
            return [0.90 for _sample in samples], [36.0 for _sample in samples]

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertEqual(metadata["intended_use"], "runner_retention_path_state_candidate_gate_score_map")
        self.assertEqual(metadata["train_label_counts"], {"total": 2, "positive": 1, "negative": 1})
        self.assertIn("flow_sell_pressure_30s", metadata["feature_names"])
        self.assertEqual(
            score_maps[0]["__episode_meta__"],
            {
                "token": "0xeval",
                "sample_count": 2,
                "start_time": 3000,
                "end_time": 3010,
            },
        )
        self.assertEqual(sorted(key for key in score_maps[0] if isinstance(key, int)), [0])
        self.assertGreaterEqual(score_maps[0][0], 0.5)

    def test_support_failure_returns_metadata_only_score_maps(self):
        train_samples = [_sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9)]
        eval_episodes = [[_sample("0xeval", sample_time=3000)]]

        with patch.object(gate.ranker_probe, "_score_samples", return_value=([0.90], [36.0])):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={"0xflat": _path(2000, kind="flat")},
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params={"buy_threshold": 0.99, "buy_near_threshold_min_prob": 0.85},
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertFalse(metadata["trained"])
        self.assertIn("train_labels_missing_positive_or_negative", metadata["support_reasons"])
        self.assertEqual(
            score_maps,
            [{
                "__episode_meta__": {
                    "token": "0xeval",
                    "sample_count": 1,
                    "start_time": 3000,
                    "end_time": 3000,
                }
            }],
        )

    def test_preserve_base_runtime_candidates_scores_only_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, flow_sell_pressure_30s=0.9),
            _sample("0xrescue", sample_time=3010, flow_sell_pressure_30s=0.1),
            _sample("0xlast", sample_time=3020, flow_sell_pressure_30s=0.1),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                if token == "0xbase":
                    buy_probs.append(0.99)
                else:
                    buy_probs.append(0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_flow_compatibility_filter_only_applies_to_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.2),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, flow_sell_pressure_30s=0.9),
            _sample("0xrescue", sample_time=3010, flow_sell_pressure_30s=0.1),
            _sample("0xtoxic", sample_time=3020, flow_sell_pressure_30s=0.9),
            _sample("0xlast", sample_time=3030, flow_sell_pressure_30s=0.1),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_runner_retention_rescue_max_flow_sell_pressure_30s": 0.35,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                buy_probs.append(0.99 if token == "0xbase" else 0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["rescue_flow_filter_active"])
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertNotIn(2, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_training_balancer_keeps_all_positives_and_caps_negatives(self):
        rows = [
            {"token": "0xpos1", "sample_time": 1, "label_positive": True},
            {"token": "0xpos2", "sample_time": 2, "label_positive": True},
        ] + [
            {
                "token": f"0xneg{index}",
                "sample_time": 100 + index,
                "label_positive": False,
                "retention_label": "flat_timeout" if index % 2 else "stop_first_collapse",
            }
            for index in range(20)
        ]

        balanced = gate._balanced_training_rows(rows, max_negative_count=5)

        self.assertEqual(sum(1 for row in balanced if row["label_positive"]), 2)
        self.assertEqual(sum(1 for row in balanced if not row["label_positive"]), 5)
        self.assertEqual(len(balanced), 7)

    def test_cli_writes_strict_runner_retention_candidate_gate_report(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_path_state_meta_gate_min_score": 0.55,
        }])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
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
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runner_retention_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                return_value=([{"0": 0.75}], {"trained": True}),
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertNotIn("buy_near_threshold_min_prob", calls[0]["overrides"])
        self.assertEqual(calls[1]["overrides"]["buy_near_threshold_min_prob"], 0.85)
        self.assertIn("path_state_scores_by_episode", calls[1]["overrides"])
        self.assertNotIn(
            "path_state_scores_by_episode",
            saved["candidates"][0]["replay_metadata"]["replay_config"],
        )
        self.assertEqual(
            saved["candidates"][0]["replay_metadata"]["replay_config"]["path_state_scores_by_episode_summary"],
            {
                "episode_count": 1,
                "non_empty_episode_count": 1,
                "scored_sample_count": 1,
                "max_episode_score_count": 1,
            },
        )

    def test_cli_passes_preserve_base_candidates_to_score_builder(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_path_state_meta_gate_min_score": 0.85,
        }])
        score_calls = []

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
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
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        def fake_score_maps(*args, **kwargs):
            score_calls.append(kwargs)
            return ([{"0": 1.0, "1": 0.9}], {"trained": True})

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runner_retention_preserve_base_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                side_effect=fake_score_maps,
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path), "--preserve-base-candidates"])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["preserve_base_candidates"] for call in score_calls], [True, True])
        self.assertTrue(saved["precision_guard"]["preserve_base_candidates"])

    def test_cli_can_load_candidate_grid_from_json(self):
        cli = _load_cli()
        calls = []
        score_calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
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
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        def fake_score_maps(*args, **kwargs):
            score_calls.append(kwargs)
            return ([{"0": 0.8}], {"trained": True})

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            grid_path = tmpdir_path / "grid.json"
            grid_path.write_text(json.dumps([{
                "buy_near_threshold_min_prob": 0.875,
                "buy_near_min_pred_return": 35.0,
                "buy_near_min_entry_volume_30s": 1.0,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
                "buy_path_state_meta_gate_min_score": 0.6,
                "buy_runner_retention_rescue_max_flow_sell_pressure_30s": 0.35,
            }]), encoding="utf-8")
            output_path = tmpdir_path / "runner_retention_json_grid_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                side_effect=fake_score_maps,
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path), "--candidate-grid-json", str(grid_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(len(saved["candidates"]), 1)
        self.assertEqual(
            saved["candidates"][0]["params"]["buy_runner_retention_rescue_max_flow_sell_pressure_30s"],
            0.35,
        )
        self.assertEqual(
            score_calls[0]["candidate_params"]["buy_runner_retention_rescue_max_flow_sell_pressure_30s"],
            0.35,
        )
        self.assertTrue(saved["candidate_grid"]["requires_flow_features"])
        self.assertTrue(calls[0]["overrides"]["include_flow_features"])
        self.assertEqual(calls[1]["overrides"]["buy_near_min_entry_volume_30s"], 1.0)


if __name__ == "__main__":
    unittest.main()
