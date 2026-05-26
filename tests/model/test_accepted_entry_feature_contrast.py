import contextlib
import importlib.util
import io
import json
import pickle
import tempfile
import unittest
from pathlib import Path

from src.pipeline import accepted_entry_feature_contrast as probe


def _trade(token, signal_time, return_pct, reason="TIME_EXIT"):
    return {
        "token": token,
        "entry_signal_time": signal_time,
        "entry_time": signal_time + 1,
        "return_pct": return_pct,
        "exit_reason": reason,
    }


def _sample(token, sample_time, depth, noise):
    return {
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
        },
        "features": {
            "organic_depth": depth,
            "noisy_numeric": noise,
            "future_window": 300,
            "symbolic": "skip-me",
        },
        "label": {
            "future_return_pct": 999.0,
        },
    }


class TestAcceptedEntryFeatureContrast(unittest.TestCase):
    def test_build_report_matches_trades_and_ranks_loss_features(self):
        trades = [
            _trade("0xaaa", 100, -10.0, "STOP_LOSS"),
            _trade("0xbbb", 200, -5.0, "TIME_EXIT"),
            _trade("0xccc", 300, 25.0, "TIME_EXIT"),
            _trade("0xddd", 400, 50.0, "TRAILING_STOP"),
        ]
        samples = [
            _sample("0xaaa", 100, 1.0, 0.1),
            _sample("0xbbb", 200, 2.0, 0.2),
            _sample("0xccc", 300, 10.0, 0.3),
            _sample("0xddd", 400, 12.0, 0.4),
        ]

        report = probe.build_contrast_report(
            trade_rows=trades,
            sample_rows=samples,
            trade_log_sources=["trades.jsonl"],
            sample_sources=["cache.pkl"],
            top_n=5,
        )

        self.assertEqual(report["match_summary"]["matched_trade_count"], 4)
        self.assertEqual(report["match_summary"]["unmatched_trade_count"], 0)
        self.assertNotIn("future_window", report["feature_summary"]["scanned_features"])
        self.assertNotIn("symbolic", report["feature_summary"]["scanned_features"])
        bad_loss = report["labels"]["bad_loss"]
        self.assertEqual(bad_loss["positive_count"], 2)
        organic_depth = next(row for row in bad_loss["top_features"] if row["feature"] == "organic_depth")
        self.assertLess(organic_depth["auc"], 0.5)
        self.assertLess(organic_depth["positive_mean"], organic_depth["negative_mean"])

    def test_build_report_records_unmatched_trades(self):
        report = probe.build_contrast_report(
            trade_rows=[_trade("0xmissing", 500, -1.0)],
            sample_rows=[],
            trade_log_sources=["trades.jsonl"],
            sample_sources=[],
            top_n=5,
        )

        self.assertEqual(report["match_summary"]["matched_trade_count"], 0)
        self.assertEqual(report["match_summary"]["unmatched_trade_count"], 1)
        self.assertEqual(report["unmatched_trades"][0]["token"], "0xmissing")

    def test_cli_writes_json_report_from_trade_log_and_pickle_cache(self):
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "probe_accepted_entry_feature_contrast.py"
        spec = importlib.util.spec_from_file_location("probe_accepted_entry_feature_contrast", script_path)
        cli = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cli)

        output_path = Path("data/replay_reports/test_accepted_entry_feature_contrast_cli.json")
        output_path.unlink(missing_ok=True)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                trade_log = tmp / "trades.jsonl"
                cache = tmp / "samples.pkl"
                trades = [
                    _trade("0xaaa", 100, -10.0, "STOP_LOSS"),
                    _trade("0xbbb", 200, -5.0, "TIME_EXIT"),
                    _trade("0xccc", 300, 25.0, "TIME_EXIT"),
                    _trade("0xddd", 400, 50.0, "TRAILING_STOP"),
                ]
                trade_log.write_text("\n".join(json.dumps(row) for row in trades) + "\n", encoding="utf-8")
                cache.write_bytes(pickle.dumps([
                    _sample("0xaaa", 100, 1.0, 0.1),
                    _sample("0xbbb", 200, 2.0, 0.2),
                    _sample("0xccc", 300, 10.0, 0.3),
                    _sample("0xddd", 400, 12.0, 0.4),
                ]))

                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = cli.main([
                        "--trade-log",
                        str(trade_log),
                        "--sample-cache",
                        str(cache),
                        "--output",
                        str(output_path),
                        "--force",
                    ])

            self.assertEqual(exit_code, 0)
            saved = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["match_summary"]["matched_trade_count"], 4)
            self.assertEqual(saved["labels"]["bad_loss"]["positive_count"], 2)
        finally:
            output_path.unlink(missing_ok=True)
