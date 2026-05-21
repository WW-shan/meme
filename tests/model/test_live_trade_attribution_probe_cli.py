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
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_live_trade_attribution.py"
    spec = importlib.util.spec_from_file_location("probe_live_trade_attribution", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestLiveTradeAttributionProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.paper_trades, "data/paper_trades.jsonl")
        self.assertEqual(args.collector_state, "data/training/collector_runtime_state.json")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.recent_lifecycle_files, 1)
        self.assertEqual(args.output_json, "docs/research/20260522-live-trade-attribution-refresh/live_attribution.json")
        self.assertEqual(args.output_md, "docs/research/20260522-live-trade-attribution-refresh/summary.md")
        self.assertEqual(args.near_min_prob, 0.94)
        self.assertEqual(args.primary_min_prob, 0.98)

    def test_parse_args_rejects_negative_trade_sample_limit(self):
        cli = _load_cli()

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            cli.parse_args(["--max-trade-sample", "-1"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--max-trade-sample must be non-negative", stderr.getvalue())

    def test_validate_output_path_rejects_protected_paths(self):
        cli = _load_cli()

        with self.assertRaises(ValueError):
            cli._validate_output_path(".env")
        with self.assertRaises(ValueError):
            cli._validate_output_path("docs/goals/live-model-optimization-goal.md")

    def test_main_calls_probe_and_writes_json_and_markdown(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.live_trade_attribution_probe")
        fake_reentry = types.SimpleNamespace(
            latest_lifecycle_files=lambda lifecycle_dir, limit: [],
            extract_lifecycles_from_runtime_state=lambda state: {"0xa": {"token_address": "0xa"}},
            extract_lifecycles_from_rows=lambda rows: {"0xb": {"token_address": "0xb", "rows": list(rows)}},
            merge_lifecycle_maps=lambda *maps: {k: v for item in maps for k, v in item.items()},
            to_json_text=lambda report: json.dumps(report, default=str) + "\n",
        )
        fake_module.reentry_probe = fake_reentry
        fake_module.to_json_text = lambda report: json.dumps(report, default=str) + "\n"
        fake_module.to_markdown_text = lambda report: "# report\n"
        fake_module.build_attribution_report = lambda **kwargs: {"trade_count": len(kwargs["trade_rows"])}

        with patch.dict(sys.modules, {"src.pipeline.live_trade_attribution_probe": fake_module}):
            with patch.object(
                fake_module,
                "build_attribution_report",
                return_value={"trade_count": 1, "go_no_go": {"status": "NO_GO_FOR_LIVE_SWITCH"}},
            ) as mock_run:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    trade_path = tmpdir_path / "paper_trades.jsonl"
                    collector_path = tmpdir_path / "collector.json"
                    lifecycle_path = tmpdir_path / "lifecycle.jsonl"
                    output_json = tmpdir_path / "live_attribution.json"
                    output_md = tmpdir_path / "summary.md"
                    trade_path.write_text('{"action": "OPEN", "is_real_trade": true}\n', encoding="utf-8")
                    collector_path.write_text('{"active_lifecycles": [{"token_address": "0xA"}]}', encoding="utf-8")
                    lifecycle_path.write_text('{"token_address": "0xB", "price_history": []}\n', encoding="utf-8")
                    stdout = io.StringIO()
                    with patch.object(cli, "_allowed_output_root", return_value=tmpdir_path), contextlib.redirect_stdout(stdout):
                        result = cli.main(
                            [
                                "--paper-trades",
                                str(trade_path),
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
                                "--force",
                            ]
                        )

                    json_text = output_json.read_text(encoding="utf-8")
                    md_text = output_md.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["trade_rows"], [{"action": "OPEN", "is_real_trade": True}])
        self.assertEqual(sorted(kwargs["lifecycles"]), ["0xa", "0xb"])
        self.assertIn("NO_GO_FOR_LIVE_SWITCH", json_text)
        self.assertIn("# report", md_text)
        self.assertIn("NO_GO_FOR_LIVE_SWITCH", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
