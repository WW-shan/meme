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
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_low_volume_breakout.py"
    spec = importlib.util.spec_from_file_location("probe_low_volume_breakout", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestLowVolumeBreakoutProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 1)
        self.assertIsNone(args.lifecycle_file)
        self.assertIsNone(args.since)
        self.assertEqual(args.min_prob, 0.98)
        self.assertEqual(args.min_volume_30s, 0.75)
        self.assertEqual(args.max_volume_30s, 1.5)
        self.assertEqual(args.min_price_volatility, 0.05)
        self.assertEqual(args.max_token_age_seconds, 60)
        self.assertEqual(args.horizon_seconds, 600)
        self.assertEqual(args.quick_profit_seconds, 120)

    def test_read_path_snapshot_hashes_the_same_bytes_used_for_parsing(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_bytes(b'{"a": 1}\n')

            fingerprint, data = cli._read_path_snapshot(path)

        self.assertEqual(data, b'{"a": 1}\n')
        self.assertEqual(fingerprint["size_bytes"], len(data))
        self.assertEqual(fingerprint["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(fingerprint["snapshot_read_mode"], "single_read_bytes")
        self.assertFalse(fingerprint["changed_during_read"])

    def test_read_path_snapshot_marks_changed_when_file_disappears_after_read(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_bytes(b'{"a": 1}\n')
            original_read_bytes = Path.read_bytes

            def removing_read_bytes(target):
                data = original_read_bytes(target)
                if target == path:
                    target.unlink()
                return data

            with patch.object(Path, "read_bytes", removing_read_bytes):
                fingerprint, data = cli._read_path_snapshot(path)

        self.assertEqual(data, b'{"a": 1}\n')
        self.assertTrue(fingerprint["changed_during_read"])
        self.assertTrue(fingerprint["exists"])
        self.assertFalse(fingerprint["exists_after_read"])
        self.assertEqual(fingerprint["sha256"], hashlib.sha256(data).hexdigest())

    def test_input_fingerprint_policy_records_single_read_bytes(self):
        cli = _load_cli()

        policy = cli._input_fingerprint_policy()

        self.assertTrue(policy["mutable_live_inputs"])
        self.assertTrue(policy["fingerprints_are_run_snapshot"])
        self.assertEqual(policy["snapshot_read_mode"], "single_read_bytes")
        self.assertIn("same bytes", policy["input_fingerprint_policy"])

    def test_main_calls_probe_with_rows_lifecycles_and_filter_parameters(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.low_volume_breakout_probe")
        fake_reentry = types.SimpleNamespace(
            latest_lifecycle_files=lambda lifecycle_dir, limit: [],
            extract_lifecycles_from_runtime_state=lambda state: {"0xa": {"token_address": "0xa"}},
            extract_lifecycles_from_rows=lambda rows: {"0xb": {"token_address": "0xb", "rows": list(rows)}},
            merge_lifecycle_maps=lambda *maps: {key: value for item in maps for key, value in item.items()},
            build_input_status=lambda **kwargs: {"existing_lifecycle_path_count": 1},
        )
        fake_module.reentry_probe = fake_reentry
        fake_module.to_json_text = lambda report: json.dumps(report, default=str) + "\n"
        fake_module.build_probe_report = lambda **kwargs: {"candidate_counts": {"per_token_candidates": 2}}

        with patch.dict(sys.modules, {"src.pipeline.low_volume_breakout_probe": fake_module}):
            with patch.object(
                fake_module,
                "build_probe_report",
                return_value={"candidate_counts": {"per_token_candidates": 2}},
            ) as mock_run:
                with tempfile.TemporaryDirectory() as tmpdir:
                    signal_path = Path(tmpdir) / "signals.jsonl"
                    collector_path = Path(tmpdir) / "collector.json"
                    lifecycle_path = Path(tmpdir) / "lifecycle.jsonl"
                    output_path = Path(tmpdir) / "out.json"
                    signal_path.write_text('{"action": "SIGNAL_DECISION"}\n', encoding="utf-8")
                    collector_path.write_text('{"active_lifecycles": [{"token_address": "0xA"}]}', encoding="utf-8")
                    lifecycle_path.write_text('{"token_address": "0xB", "price_history": []}\n', encoding="utf-8")
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        result = cli.main(
                            [
                                "--signal-audit",
                                str(signal_path),
                                "--collector-state",
                                str(collector_path),
                                "--recent-lifecycle-files",
                                "0",
                                "--output",
                                str(output_path),
                                "--lifecycle-file",
                                str(lifecycle_path),
                                "--since",
                                "2026-05-19 04:02:23",
                                "--min-prob",
                                "0.99",
                                "--min-volume-30s",
                                "0.8",
                                "--max-volume-30s",
                                "1.4",
                                "--min-price-volatility",
                                "0.07",
                                "--max-token-age-seconds",
                                "45",
                            ]
                        )

                    written = output_path.read_text(encoding="utf-8")

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["signal_rows"], [{"action": "SIGNAL_DECISION"}])
        self.assertEqual(sorted(kwargs["lifecycles"]), ["0xa", "0xb"])
        self.assertEqual(kwargs["since"], "2026-05-19 04:02:23")
        self.assertEqual(kwargs["min_prob"], 0.99)
        self.assertEqual(kwargs["min_volume_30s"], 0.8)
        self.assertEqual(kwargs["max_volume_30s"], 1.4)
        self.assertEqual(kwargs["min_price_volatility"], 0.07)
        self.assertEqual(kwargs["max_token_age_seconds"], 45)
        self.assertEqual(kwargs["horizon_seconds"], 600)
        self.assertEqual(kwargs["quick_profit_seconds"], 120)
        self.assertEqual(result, 0)
        self.assertIn("input_fingerprint_policy", written)
        self.assertIn("single_read_bytes", written)
        self.assertIn("sha256", written)
        self.assertIn("per_token_candidates=2", stdout.getvalue())

    def test_main_deduplicates_explicit_and_latest_lifecycle_paths(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.low_volume_breakout_probe")

        with tempfile.TemporaryDirectory() as tmpdir:
            signal_path = Path(tmpdir) / "signals.jsonl"
            collector_path = Path(tmpdir) / "collector.json"
            lifecycle_path = Path(tmpdir) / "lifecycle.jsonl"
            output_path = Path(tmpdir) / "out.json"
            signal_path.write_text("", encoding="utf-8")
            collector_path.write_text("{}", encoding="utf-8")
            lifecycle_path.write_text('{"token_address": "0xB", "price_history": []}\n', encoding="utf-8")
            fake_reentry = types.SimpleNamespace(
                latest_lifecycle_files=lambda lifecycle_dir, limit: [lifecycle_path],
                extract_lifecycles_from_runtime_state=lambda state: {},
                extract_lifecycles_from_rows=lambda rows: {"0xb": {"rows": list(rows)}},
                merge_lifecycle_maps=lambda *maps: {key: value for item in maps for key, value in item.items()},
                build_input_status=lambda **kwargs: {"lifecycle_paths": [str(p) for p in kwargs["lifecycle_paths"]]},
            )
            fake_module.reentry_probe = fake_reentry
            fake_module.to_json_text = lambda report: json.dumps(report, default=str) + "\n"
            fake_module.build_probe_report = lambda **kwargs: {"candidate_counts": {"per_token_candidates": 1}}

            with patch.dict(sys.modules, {"src.pipeline.low_volume_breakout_probe": fake_module}):
                cli.main(
                    [
                        "--signal-audit",
                        str(signal_path),
                        "--collector-state",
                        str(collector_path),
                        "--lifecycle-dir",
                        tmpdir,
                        "--recent-lifecycle-files",
                        "1",
                        "--lifecycle-file",
                        str(lifecycle_path),
                        "--output",
                        str(output_path),
                    ]
                )
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(written["inputs"]["lifecycle_files"], [str(lifecycle_path)])
        self.assertEqual(len(written["input_fingerprints"]["lifecycle_files"]), 1)


if __name__ == "__main__":
    unittest.main()
