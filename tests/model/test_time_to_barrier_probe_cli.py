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
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_time_to_barrier.py"
    spec = importlib.util.spec_from_file_location("probe_time_to_barrier", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTimeToBarrierProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 1)
        self.assertIsNone(args.lifecycle_file)
        self.assertIsNone(args.since)
        self.assertEqual(args.horizon_seconds, 600)
        self.assertEqual(args.quick_profit_seconds, 120)
        self.assertEqual(args.max_candidate_sample, 100)
        self.assertIsNone(args.until)

    def test_parse_args_rejects_negative_candidate_sample_limit(self):
        cli = _load_cli()

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            cli.parse_args(["--max-candidate-sample", "-1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--max-candidate-sample must be non-negative", stderr.getvalue())

    def test_fingerprint_path_records_sha256_for_reproducibility(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_bytes(b"abc\n")

            fingerprint = cli._fingerprint_path(path)

        self.assertEqual(fingerprint["path"], str(path))
        self.assertTrue(fingerprint["exists"])
        self.assertEqual(fingerprint["size_bytes"], 4)
        self.assertIsInstance(fingerprint["mtime_ns"], int)
        self.assertEqual(fingerprint["sha256"], hashlib.sha256(b"abc\n").hexdigest())

    def test_input_fingerprint_policy_marks_live_paths_as_mutable(self):
        cli = _load_cli()

        policy = cli._input_fingerprint_policy()

        self.assertTrue(policy["mutable_live_inputs"])
        self.assertTrue(policy["fingerprints_are_run_snapshot"])
        self.assertEqual(policy["snapshot_read_mode"], "single_read_bytes")
        self.assertTrue(policy["current_paths_may_change_after_run"])

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

    def test_main_calls_probe_and_writes_report(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.time_to_barrier_probe")
        fake_reentry = types.SimpleNamespace(
            latest_lifecycle_files=lambda lifecycle_dir, limit: [],
            extract_lifecycles_from_runtime_state=lambda state: {"0xa": {"token_address": "0xa"}},
            extract_lifecycles_from_rows=lambda rows: {"0xb": {"token_address": "0xb", "rows": list(rows)}},
            merge_lifecycle_maps=lambda *maps: {k: v for item in maps for k, v in item.items()},
            build_input_status=lambda **kwargs: {"existing_lifecycle_path_count": 1},
            to_json_text=lambda report: json.dumps(report, default=str) + "\n",
        )
        fake_module.build_probe_report = lambda **kwargs: {"candidate_counts": {"per_token_candidates": 2}}
        fake_module.reentry_probe = fake_reentry

        with patch.dict(sys.modules, {"src.pipeline.time_to_barrier_probe": fake_module}):
            with patch.object(
                fake_module,
                "build_probe_report",
                return_value={"candidate_counts": {"per_token_candidates": 2}},
            ) as mock_run:
                with tempfile.TemporaryDirectory() as tmpdir:
                    signal_path = Path(tmpdir) / "signals.jsonl"
                    collector_path = Path(tmpdir) / "collector.json"
                    lifecycle_path = Path(tmpdir) / "lifecycle.jsonl"
                    signal_path.write_text("", encoding="utf-8")
                    collector_path.write_text('{"active_lifecycles": [{"token_address": "0xA"}]}', encoding="utf-8")
                    lifecycle_path.write_text('{"token_address": "0xB", "price_history": []}\n', encoding="utf-8")
                    stdout = io.StringIO()
                    with patch("pathlib.Path.write_text") as mock_write, contextlib.redirect_stdout(stdout):
                        result = cli.main(
                            [
                                "--signal-audit",
                                str(signal_path),
                                "--collector-state",
                                str(collector_path),
                                "--recent-lifecycle-files",
                                "0",
                                "--output",
                                str(Path(tmpdir) / "out.json"),
                                "--lifecycle-file",
                                str(lifecycle_path),
                                "--since",
                                "2026-05-19 04:02:23",
                                "--until",
                                "2026-05-25 13:25:41",
                                "--max-candidate-sample",
                                "0",
                            ]
                        )

        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["signal_rows"], [])
        self.assertEqual(sorted(kwargs["lifecycles"]), ["0xa", "0xb"])
        self.assertEqual(kwargs["since"], "2026-05-19 04:02:23")
        self.assertEqual(kwargs["until"], "2026-05-25 13:25:41")
        self.assertEqual(kwargs["horizon_seconds"], 600)
        self.assertEqual(kwargs["quick_profit_seconds"], 120)
        self.assertEqual(kwargs["max_candidate_sample"], 0)
        self.assertEqual(result, 0)
        written = mock_write.call_args.args[0]
        self.assertIn("input_fingerprint_policy", written)
        self.assertIn("single_read_bytes", written)
        self.assertIn("per_token_candidates=2", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
