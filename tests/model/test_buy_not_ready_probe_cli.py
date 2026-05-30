import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_buy_not_ready_outcomes.py"
    spec = importlib.util.spec_from_file_location("probe_buy_not_ready_outcomes", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBuyNotReadyProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 24)
        self.assertEqual(args.max_hold_seconds, 560.0)
        self.assertEqual(args.horizon_seconds, 10800.0)
        self.assertEqual(args.min_support, 3)
        self.assertEqual(args.reason_contains, "Unsupported quote asset")

    def test_validate_output_path_rejects_goal_docs(self):
        cli = _load_cli()

        with self.assertRaises(ValueError):
            cli._validate_output_path("docs/goals/live-model-optimization-goal.md")
        with self.assertRaises(ValueError):
            cli._validate_output_path(".env")

    def test_main_writes_json_and_markdown_with_fingerprints(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            signal_path = base / "signal_audit.jsonl"
            collector_path = base / "collector.json"
            lifecycle_path = base / "lifecycle.jsonl"
            output_json = base / "data" / "replay_reports" / "buy_not_ready.json"
            output_md = base / "data" / "replay_reports" / "buy_not_ready.md"
            signal_path.write_text(
                json.dumps(
                    {
                        "action": "BUY_NOT_READY",
                        "token": "0xA",
                        "symbol": "AAA",
                        "time": "2026-05-30 10:00:00",
                        "reason": "Unsupported quote asset: 0xQuote",
                        "token_quote": "0xQuote",
                        "signal_price": 1.0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            collector_path.write_text('{"active_lifecycles": []}', encoding="utf-8")
            lifecycle_path.write_text(
                json.dumps(
                    {
                        "token_address": "0xA",
                        "symbol": "AAA",
                        "price_history": [
                            {"timestamp": "2026-05-30 10:01:00", "price": 1.02, "type": "buy"},
                            {"timestamp": "2026-05-30 10:10:20", "price": 1.4, "type": "buy"},
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch_allowed_roots(cli, [base / "data" / "replay_reports"]), contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--signal-audit",
                        str(signal_path),
                        "--collector-state",
                        str(collector_path),
                        "--recent-lifecycle-files",
                        "0",
                        "--lifecycle-file",
                        str(lifecycle_path),
                        "--output-json",
                        str(output_json),
                        "--output-md",
                        str(output_md),
                        "--max-hold-seconds",
                        "560",
                        "--horizon-seconds",
                        "1200",
                    ]
                )
            report = json.loads(output_json.read_text(encoding="utf-8"))
            md_text = output_md.read_text(encoding="utf-8")
            lifecycle_sha256 = hashlib.sha256(lifecycle_path.read_bytes()).hexdigest()

        self.assertEqual(result, 0)
        self.assertEqual(report["summary"]["event_count"], 1)
        self.assertEqual(report["input_fingerprints"]["lifecycle_files"][0]["sha256"], lifecycle_sha256)
        self.assertIn("reject_unsupported_quote_no_within_hold_support", stdout.getvalue())
        self.assertIn("# BUY_NOT_READY Outcome Probe", md_text)


class patch_allowed_roots:
    def __init__(self, cli, roots):
        self.cli = cli
        self.roots = roots
        self.original = None

    def __enter__(self):
        self.original = self.cli._allowed_output_roots
        self.cli._allowed_output_roots = lambda: self.roots

    def __exit__(self, exc_type, exc, tb):
        self.cli._allowed_output_roots = self.original


if __name__ == "__main__":
    unittest.main()
