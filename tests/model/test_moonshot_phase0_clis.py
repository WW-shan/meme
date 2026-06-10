import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli(script_name):
    path = Path(__file__).resolve().parents[2] / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestMoonshotPhase0Clis(unittest.TestCase):
    def _write_lifecycle_fixture(self, lifecycle_dir):
        rows = [
            {
                "chain": "bsc",
                "token_address": "0xRun",
                "symbol": "RUN",
                "create_timestamp": 1000,
                "buys": [
                    {"timestamp": 1001, "price": 1.0, "bnb_amount": 1.0, "account": "a", "token_amount": 10},
                    {"timestamp": 1030, "price": 2.0, "bnb_amount": 2.0, "account": "b", "token_amount": 20},
                    {"timestamp": 1060, "price": 12.0, "bnb_amount": 3.0, "account": "c", "token_amount": 30},
                ],
                "sells": [
                    {"timestamp": 1045, "price": 1.8, "bnb_amount": 0.25, "account": "a", "token_amount": 2}
                ],
            },
            {
                "chain": "bsc",
                "token_address": "0xEmpty",
                "symbol": "EMPTY",
                "create_timestamp": 2000,
                "buys": [],
                "sells": [],
            },
        ]
        path = Path(lifecycle_dir) / "lifecycle_incremental_20260609_000000.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return path

    def _write_external_fixture(self, base_dir):
        path = Path(base_dir) / "bitquery_export.jsonl"
        row = {
            "chain": "bsc",
            "tokenAddress": "0xExternal",
            "pairAddress": "0xPair",
            "launchTimestamp": "2026-01-01T00:00:00Z",
            "initialPriceUsd": "0.01",
            "athPriceUsd": "0.25",
            "sourceUrl": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
            "exportedAt": "2026-06-09T00:00:00Z",
        }
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        return path

    def test_label_truth_cli_writes_report_and_rejects_unsafe_output(self):
        cli = _load_cli("probe_moonshot_label_truth.py")

        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory(dir="data/replay_reports") as outdir:
            lifecycle_dir = Path(tmpdir) / "lifecycles"
            lifecycle_dir.mkdir()
            self._write_lifecycle_fixture(lifecycle_dir)
            external_path = self._write_external_fixture(tmpdir)
            output_path = Path(outdir) / "label_truth.json"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--lifecycle-dir",
                        str(lifecycle_dir),
                        "--external-labels",
                        str(external_path),
                        "--output",
                        str(output_path),
                        "--force",
                    ]
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))

            with self.assertRaises(SystemExit):
                cli.main(["--lifecycle-dir", str(lifecycle_dir), "--output", "data/models/unsafe.json"])

        self.assertEqual(result, 0)
        self.assertIn("summary", report)
        self.assertIn("threshold_counts", report)
        self.assertIn("rejects", report)
        self.assertIn("warnings", report)
        self.assertIn("provenance_sources", report)
        self.assertEqual(report["source_counts"]["bitquery_export"], 1)
        self.assertEqual(report["reject_reason_counts"]["missing_first_price"], 1)
        self.assertEqual(report["summary"]["accepted_count"], 2)
        self.assertEqual(report["summary"]["reject_count"], 1)
        self.assertIn("wrote", stdout.getvalue())

    def test_local_runner_baseline_cli_writes_expected_report_shape(self):
        label_cli = _load_cli("probe_moonshot_label_truth.py")
        baseline_cli = _load_cli("probe_moonshot_local_runner_baseline.py")

        with tempfile.TemporaryDirectory() as tmpdir, tempfile.TemporaryDirectory(dir="data/replay_reports") as outdir:
            lifecycle_dir = Path(tmpdir) / "lifecycles"
            lifecycle_dir.mkdir()
            self._write_lifecycle_fixture(lifecycle_dir)
            label_report = Path(outdir) / "label_truth.json"
            baseline_report = Path(outdir) / "baseline.json"
            with contextlib.redirect_stdout(io.StringIO()):
                label_cli.main(
                    [
                        "--lifecycle-dir",
                        str(lifecycle_dir),
                        "--output",
                        str(label_report),
                        "--force",
                    ]
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = baseline_cli.main(
                    [
                        "--lifecycle-dir",
                        str(lifecycle_dir),
                        "--label-report",
                        str(label_report),
                        "--snapshot-seconds",
                        "30,60",
                        "--output",
                        str(baseline_report),
                        "--force",
                    ]
                )

            report = json.loads(baseline_report.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertIn(report["decision"], {"research_baseline_only", "insufficient_positive_support", "invalid_input"})
        self.assertIn("sample_count", report)
        self.assertIn("positive_count", report)
        self.assertIn("base_rate", report)
        self.assertIn("top_k_metrics", report)
        self.assertIn("validation_metrics", report)
        self.assertIn("feature_component_summary", report)
        self.assertGreater(report["sample_count"], 0)
        self.assertIn("wrote", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
