import contextlib
import hashlib
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
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_post_target_exit_state.py"
    spec = importlib.util.spec_from_file_location("probe_post_target_exit_state", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestPostTargetExitStateProbeCli(unittest.TestCase):
    def test_parse_args_defaults_keep_risk_contract_strict(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.output, "data/replay_reports/post_target_exit_state_probe_20260521_v95.json")
        self.assertEqual(args.target_pct, 0.25)
        self.assertEqual(args.continuation_pct, 0.60)
        self.assertEqual(args.collapse_pct, -0.18)
        self.assertEqual(args.position_fraction, 0.10)
        self.assertEqual(args.max_open_positions, 8)
        self.assertEqual(args.split, "validation")
        self.assertFalse(args.force)

    def test_parser_rejects_position_fraction_above_or_below_ten_percent(self):
        cli = _load_cli()

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.parse_args(["--position-fraction", "0.11"])
            with self.assertRaises(SystemExit):
                cli.parse_args(["--position-fraction", "0.09"])

    def test_parser_rejects_max_open_positions_other_than_eight(self):
        cli = _load_cli()

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.parse_args(["--max-open-positions", "7"])
            with self.assertRaises(SystemExit):
                cli.parse_args(["--max-open-positions", "9"])

    def test_read_path_snapshot_hashes_the_same_bytes_used_for_parsing(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_bytes(b'{"token_address": "0xA"}\n')

            fingerprint, data = cli._read_path_snapshot(path)

        self.assertEqual(data, b'{"token_address": "0xA"}\n')
        self.assertEqual(fingerprint["path"], str(path))
        self.assertEqual(fingerprint["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(fingerprint["snapshot_read_mode"], "single_read_bytes")

    def test_output_writable_refuses_overwrite_without_force(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            output_path = project_root / "data" / "replay_reports" / "report.json"
            output_path.parent.mkdir(parents=True)
            output_path.write_text("old", encoding="utf-8")

            with patch.object(cli, "PROJECT_ROOT", project_root):
                with self.assertRaises(SystemExit):
                    cli._assert_output_writable(output_path, force=False)
                cli._assert_output_writable(output_path, force=True)

    def test_main_runs_replay_loads_lifecycles_and_writes_contract_and_fingerprints(self):
        cli = _load_cli()
        fake_probe = types.ModuleType("src.pipeline.post_target_exit_state_probe")
        fake_reentry = types.SimpleNamespace(
            latest_lifecycle_files=lambda lifecycle_dir, limit: [],
            extract_lifecycles_from_rows=lambda rows: {
                row["token_address"].lower(): {"token_address": row["token_address"], "price_history": []}
                for row in rows
            },
            merge_lifecycle_maps=lambda *maps: {k: v for item in maps for k, v in item.items()},
            to_json_text=lambda report: json.dumps(report, default=str, sort_keys=True) + "\n",
        )
        fake_probe.reentry_probe = fake_reentry
        fake_probe.build_probe_report = lambda **kwargs: {
            "probe_contract": {
                "read_only": True,
                "live_switch_evidence": False,
                "requires_replay_before_live_change": True,
            },
            "candidate_counts": {"trade_log_rows": len(kwargs["trades"]), "scored_candidates": len(kwargs["trades"])},
            "class_counts": {},
            "policy_counts": {},
            "candidate_sample": [],
        }
        fake_probe.to_json_text = lambda report: json.dumps(report, default=str, sort_keys=True) + "\n"
        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.PROTECTED_REPORT_OUTPUT_FILES = frozenset(
            ("hybrid_manifest.json", "bc.pt", "trade_log.jsonl", "buy_model.cbm")
        )
        fake_model_replay.run_model_replay = lambda **kwargs: {
            "evaluation": {
                "trade_log": [
                    {
                        "token": "0xA",
                        "symbol": "AAA",
                        "entry_time": "2026-05-21 02:10:00",
                        "entry_price": 1.0,
                    }
                ]
            },
            "lifecycle_paths": [],
            "sample_count": 1,
        }

        with patch.dict(
            sys.modules,
            {
                "src.pipeline.post_target_exit_state_probe": fake_probe,
                "src.pipeline.model_replay": fake_model_replay,
            },
        ):
            with patch.object(fake_model_replay, "run_model_replay", wraps=fake_model_replay.run_model_replay) as replay:
                with patch.object(fake_probe, "build_probe_report", wraps=fake_probe.build_probe_report) as build:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        project_root = Path(tmpdir)
                        lifecycle_path = Path(tmpdir) / "lifecycle.jsonl"
                        lifecycle_path.write_text('{"token_address": "0xA", "price_history": []}\n', encoding="utf-8")
                        output_path = project_root / "data" / "replay_reports" / "out.json"
                        output_path.parent.mkdir(parents=True)
                        stdout = io.StringIO()
                        with patch.object(cli, "PROJECT_ROOT", project_root), contextlib.redirect_stdout(stdout):
                            result = cli.main(
                                [
                                    "--split",
                                    "final",
                                    "--lifecycle-file",
                                    str(lifecycle_path),
                                    "--recent-lifecycle-files",
                                    "0",
                                    "--output",
                                    str(output_path),
                                ]
                            )
                        written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        replay.assert_called_once()
        self.assertEqual(replay.call_args.kwargs["split"], "final")
        self.assertTrue(replay.call_args.kwargs["include_trade_log"])
        self.assertFalse(replay.call_args.kwargs["write_report"])
        self.assertFalse(replay.call_args.kwargs["use_cache"])
        self.assertIsNone(replay.call_args.kwargs["cache_dir"])
        self.assertEqual(replay.call_args.kwargs["overrides"]["position_fraction"], 0.10)
        self.assertEqual(replay.call_args.kwargs["overrides"]["max_position_fraction"], 0.10)
        self.assertIsNone(replay.call_args.kwargs["overrides"]["fixed_stake_bnb"])
        self.assertTrue(replay.call_args.kwargs["overrides"]["skip_all_in_replay"])
        self.assertEqual(replay.call_args.kwargs["max_open_positions"], 8)
        build.assert_called_once()
        self.assertEqual(build.call_args.kwargs["target_pct"], 0.25)
        self.assertEqual(build.call_args.kwargs["trades"][0]["token"], "0xA")
        self.assertTrue(written["probe_contract"]["read_only"])
        self.assertFalse(written["probe_contract"]["live_switch_evidence"])
        self.assertIn("input_fingerprints", written)
        self.assertIn("lifecycle_files", written["input_fingerprints"])
        self.assertIn("input_fingerprint_policy", written)
        self.assertIn("wrote", stdout.getvalue())

    def test_load_lifecycles_uses_flow_aware_extractor_and_merge_when_available(self):
        cli = _load_cli()
        def merge_with_flow(*maps):
            merged = {}
            for item in maps:
                for token, lifecycle in item.items():
                    existing = merged.setdefault(
                        token,
                        {"token_address": token, "price_history": [], "buys": [], "sells": []},
                    )
                    existing["price_history"].extend(lifecycle.get("price_history") or [])
                    existing["buys"].extend(lifecycle.get("buys") or [])
                    existing["sells"].extend(lifecycle.get("sells") or [])
            return merged

        fake_probe = types.SimpleNamespace(
            reentry_probe=types.SimpleNamespace(
                merge_lifecycle_maps=lambda *maps: {k: v for item in maps for k, v in item.items()},
            ),
            flow_activation_probe=types.SimpleNamespace(
                extract_lifecycles_from_rows_for_flow=lambda rows: {
                    row["token_address"].lower(): {
                        "token_address": row["token_address"],
                        "price_history": row.get("price_history", []),
                        "buys": row.get("buys", []),
                        "sells": row.get("sells", []),
                    }
                    for row in rows
                },
                merge_lifecycle_maps_for_flow=merge_with_flow,
            ),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            first_path = Path(tmpdir) / "lifecycle1.jsonl"
            second_path = Path(tmpdir) / "lifecycle2.jsonl"
            first_path.write_text(
                json.dumps({
                    "token_address": "0xFLOW",
                    "price_history": [],
                    "buys": [{"timestamp": 1, "bnb_amount": 2}],
                }) + "\n",
                encoding="utf-8",
            )
            second_path.write_text(
                json.dumps({
                    "token_address": "0xFLOW",
                    "price_history": [],
                    "sells": [{"timestamp": 2, "bnb_amount": 1}],
                }) + "\n",
                encoding="utf-8",
            )

            lifecycles, fingerprints = cli._load_lifecycles(probe=fake_probe, lifecycle_paths=[first_path, second_path])

        self.assertEqual(len(fingerprints), 2)
        self.assertEqual(lifecycles["0xflow"]["buys"][0]["bnb_amount"], 2)
        self.assertEqual(lifecycles["0xflow"]["sells"][0]["bnb_amount"], 1)

    def test_main_refuses_protected_model_artifact_output_path(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            protected = Path(tmpdir) / "buy_model.cbm"
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    cli.parse_args(["--output", str(protected)])

    def test_output_writable_allows_reports_directory_with_force(self):
        cli = _load_cli()

        cli._assert_output_writable("data/replay_reports/post_target_exit_state_probe_tmp.json", force=True)

    def test_output_writable_refuses_non_report_paths_even_with_force(self):
        cli = _load_cli()
        protected_paths = [
            ".env",
            ".env.example",
            "config/trading_config.py",
            "scripts/probe_post_target_exit_state.py",
            "src/pipeline/post_target_exit_state_probe.py",
            "src/trader/bot.py",
            "docs/model_scoreboard.md",
            "docs/goals/live-model-optimization-goal.md",
        ]

        for protected in protected_paths:
            with self.subTest(protected=protected):
                with self.assertRaises(SystemExit):
                    cli._assert_output_writable(protected, force=True)

    def test_output_writable_refuses_absolute_paths_outside_project(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            outside_path = Path(tmpdir) / "data" / "replay_reports" / "out.json"

            with self.assertRaises(SystemExit):
                cli._assert_output_writable(outside_path, force=True)


if __name__ == "__main__":
    unittest.main()
