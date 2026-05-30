import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_post_skip_followup_hazard.py"
    spec = importlib.util.spec_from_file_location("probe_post_skip_followup_hazard", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _trade_rows():
    rows = []
    for index, net, prior_skip in [
        (1, 0.0010, False),
        (2, -0.0040, True),
        (3, -0.0030, True),
        (4, -0.0025, True),
        (5, 0.0010, False),
        (6, -0.0015, True),
        (7, -0.0020, True),
        (8, 0.0010, False),
        (9, -0.0020, True),
        (10, 0.0008, False),
    ]:
        token = f"0x{index:040x}"
        minute = f"{index:02d}"
        rows.extend([
            {
                "action": "OPEN",
                "token": token,
                "symbol": f"T{index}",
                "entry_signal_time": f"2026-05-30 10:{minute}:00",
                "time": f"2026-05-30 10:{minute}:08",
                "is_real_trade": True,
                "prob": 0.98,
                "pred_return": 40.0,
                "price": 1.0,
            },
            {
                "action": "CLOSE",
                "token": token,
                "symbol": f"T{index}",
                "time": f"2026-05-30 10:{minute}:50",
                "reason": "TIME_EXIT" if net <= 0 else "TRAILING_STOP",
                "net_profit_bnb": net,
                "is_real_trade": True,
            },
        ])
    return rows


def _signal_rows():
    rows = []
    for index in (2, 3, 4, 6, 7, 9):
        token = f"0x{index:040x}"
        minute = f"{index - 1:02d}"
        rows.append({
            "action": "ENTRY_PRICE_PROTECTION_SKIP",
            "token": token,
            "symbol": f"T{index}",
            "time": f"2026-05-30 10:{minute}:30",
            "prob": 0.99,
            "pred_return": 45.0,
            "signal_price": 1.0,
            "candidate_price": 1.4,
            "entry_slippage_pct": 0.4,
        })
    return rows


class TestPostSkipFollowupHazardCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])

        self.assertEqual(args.paper_trades, "data/paper_trades.jsonl")
        self.assertEqual(args.signal_audit, "data/signal_audit.jsonl")
        self.assertEqual(args.lookback_seconds, 120.0)
        self.assertEqual(args.path_horizon_seconds, 560.0)
        self.assertEqual(args.min_train_selected, 2)

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
            paper_path = base / "paper_trades.jsonl"
            signal_path = base / "signal_audit.jsonl"
            collector_path = base / "collector.json"
            output_json = base / "data" / "replay_reports" / "post_skip.json"
            output_md = base / "data" / "replay_reports" / "post_skip.md"
            paper_path.write_text(
                "\n".join(json.dumps(row) for row in _trade_rows()) + "\n",
                encoding="utf-8",
            )
            signal_path.write_text(
                "\n".join(json.dumps(row) for row in _signal_rows()) + "\n",
                encoding="utf-8",
            )
            collector_path.write_text('{"active_lifecycles": []}', encoding="utf-8")
            stdout = io.StringIO()
            with patch_allowed_roots(cli, [base / "data" / "replay_reports"]), contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--paper-trades",
                        str(paper_path),
                        "--signal-audit",
                        str(signal_path),
                        "--collector-state",
                        str(collector_path),
                        "--recent-lifecycle-files",
                        "0",
                        "--output-json",
                        str(output_json),
                        "--output-md",
                        str(output_md),
                        "--min-train-loss-precision",
                        "1.0",
                        "--max-train-winner-count",
                        "0",
                        "--max-validation-winner-count",
                        "0",
                        "--max-final-winner-count",
                        "0",
                    ]
                )
            report = json.loads(output_json.read_text(encoding="utf-8"))
            md_text = output_md.read_text(encoding="utf-8")
            paper_sha256 = hashlib.sha256(paper_path.read_bytes()).hexdigest()

        self.assertEqual(result, 0)
        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertEqual(report["input_fingerprints"]["paper_trades"]["sha256"], paper_sha256)
        self.assertIn("research_alpha_post_skip_followup", stdout.getvalue())
        self.assertIn("# Post-Skip Follow-Up Hazard Probe", md_text)


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
