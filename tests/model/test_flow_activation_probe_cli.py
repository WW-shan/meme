import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_flow_activation.py"
    spec = importlib.util.spec_from_file_location("probe_flow_activation", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestFlowActivationProbeCli(unittest.TestCase):
    def test_parse_args_defaults_to_live_inputs(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 4)
        self.assertIsNone(args.lifecycle_file)
        self.assertIsNone(args.since)
        self.assertEqual(args.lookback_seconds, 30)
        self.assertEqual(args.flow_window_seconds, 30)
        self.assertEqual(args.horizon_seconds, 300)
        self.assertIn("data/replay_reports/flow_activation_probe_", cli._default_output_path())

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

    def test_main_writes_report_with_input_status(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            signal_path = base / "signals.jsonl"
            collector_path = base / "collector.json"
            lifecycle_path = base / "lifecycle.jsonl"
            output_path = base / "out.json"
            signal_rows = [
                {
                    "action": "SIGNAL_DECISION",
                    "time": "2026-05-19 12:00:10",
                    "token": "0xA",
                    "symbol": "TOK",
                    "decision": "rejected",
                    "prob": 0.97,
                    "pred_return": 22,
                    "volume_30s": 0.62,
                    "price_volatility": 0.10,
                },
                {
                    "action": "SIGNAL_DECISION",
                    "time": "2026-05-19 12:00:30",
                    "token": "0xA",
                    "symbol": "TOK",
                    "decision": "queued",
                    "prob": 0.9901,
                    "pred_return": 65.7,
                    "volume_30s": 1.79,
                    "price_volatility": 0.193,
                },
            ]
            lifecycle = {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [
                    {"timestamp": "2026-05-19 12:00:30", "price": 1.0, "type": "buy"},
                    {"timestamp": "2026-05-19 12:00:36", "price": 1.28, "type": "buy"},
                ],
                "buys": [],
                "sells": [],
            }
            lifecycle_followup = {
                "token_address": "0xA",
                "symbol": "TOK",
                "price_history": [],
                "buys": [{"timestamp": "2026-05-19 12:00:18", "bnb_amount": 0.5, "price": 0.95}],
                "sells": [{"timestamp": "2026-05-19 12:00:28", "bnb_amount": 0.1, "price": 0.98}],
            }
            signal_path.write_text("\n".join(json.dumps(row) for row in signal_rows) + "\n", encoding="utf-8")
            collector_path.write_text(
                json.dumps(
                    {
                        "active_lifecycles": [
                            {
                                "token_address": "0xA",
                                "symbol": "TOK",
                                "price_history": [],
                                "buys": [],
                                "sells": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            lifecycle_path.write_text(
                json.dumps(lifecycle) + "\n" + json.dumps(lifecycle_followup) + "\n",
                encoding="utf-8",
            )

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
                        "2026-05-19 12:00:00",
                    ]
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))
            lifecycle_sha256 = hashlib.sha256(lifecycle_path.read_bytes()).hexdigest()

        self.assertEqual(result, 0)
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertTrue(report["input_fingerprint_policy"]["mutable_live_inputs"])
        self.assertEqual(report["input_status"]["existing_lifecycle_path_count"], 1)
        self.assertEqual(report["input_status"]["lifecycle_paths"][0]["sha256"], lifecycle_sha256)
        self.assertEqual(len(report["candidates"]), 1)
        self.assertEqual(report["candidates"][0]["flow"]["flow_event_count"], 2)
        self.assertGreater(report["candidates"][0]["flow"]["pre_buy_pressure"], 0.8)
        self.assertIn("flow_activation_candidates=1", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
