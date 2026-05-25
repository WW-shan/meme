import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_candidate_meta_stability.py"
    spec = importlib.util.spec_from_file_location("probe_candidate_meta_stability", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _write_report(path: Path, prefix: str) -> None:
    path.write_text(
        json.dumps(
            {
                "candidate_sample": [
                    {
                        "symbol": f"{prefix}_POS",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.991,
                        "entry_volume_30s": 1.8,
                        "entry_price_volatility": 0.12,
                        "flow_buy_sell_overlap_ratio_60s": 0.1,
                    },
                    {
                        "symbol": f"{prefix}_NEG",
                        "recommended_policy": "skip",
                        "prob": 0.991,
                        "entry_volume_30s": 1.7,
                        "entry_price_volatility": 0.11,
                        "flow_buy_sell_overlap_ratio_60s": 0.9,
                    },
                    {
                        "symbol": f"{prefix}_FILTERED",
                        "recommended_policy": "quick_take_profit",
                        "prob": 0.991,
                        "entry_volume_30s": 0.2,
                        "entry_price_volatility": 0.12,
                        "flow_buy_sell_overlap_ratio_60s": 0.1,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


class TestCandidateMetaStabilityProbeCli(unittest.TestCase):
    def test_main_writes_stability_report_with_candidate_filters(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            tmp_path = Path(tmpdir)
            paths = [tmp_path / f"r{index}.json" for index in range(3)]
            for index, path in enumerate(paths):
                _write_report(path, f"R{index}")
            output_path = tmp_path / "stability.json"

            result = cli.main(
                [
                    "--time-to-barrier-report",
                    str(paths[0]),
                    "--time-to-barrier-report",
                    str(paths[1]),
                    "--time-to-barrier-report",
                    str(paths[2]),
                    "--output",
                    str(output_path),
                    "--validation-report-count",
                    "1",
                    "--probability-threshold",
                    "0.5",
                    "--max-depth",
                    "1",
                    "--min-samples-leaf",
                    "1",
                    "--min-validation-selected",
                    "1",
                    "--min-train-selected",
                    "1",
                    "--min-stable-precision",
                    "0.75",
                    "--candidate-filter",
                    "entry_volume_30s>=1.25",
                ]
            )

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["top_stable_results"][0]["pooled_precision"], 1.0)
            self.assertEqual(report["parameters"]["candidate_filters"], [{"field": "entry_volume_30s", "op": ">=", "value": 1.25}])


if __name__ == "__main__":
    unittest.main()
