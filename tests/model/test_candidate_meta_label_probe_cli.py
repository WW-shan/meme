import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_candidate_meta_label.py"
    spec = importlib.util.spec_from_file_location("probe_candidate_meta_label", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCandidateMetaLabelProbeCli(unittest.TestCase):
    def test_main_writes_read_only_report_with_multiple_inputs(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            tmp_path = Path(tmpdir)
            train_path = tmp_path / "train.json"
            valid_path = tmp_path / "valid.json"
            output_path = tmp_path / "out.json"
            train_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "TRAIN_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.1,
                            },
                            {
                                "symbol": "TRAIN_NEG",
                                "recommended_policy": "skip",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.9,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            valid_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "VALID_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.992,
                                "flow_buy_sell_overlap_ratio_60s": 0.2,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(train_path),
                        "--time-to-barrier-report",
                        str(valid_path),
                        "--output",
                        str(output_path),
                        "--min-validation-selected",
                        "1",
                        "--probability-threshold",
                        "0.5",
                        "--max-depth",
                        "1",
                        "--min-samples-leaf",
                        "1",
                    ]
                )

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(report["probe_contract"]["read_only"])
            self.assertFalse(report["probe_contract"]["live_switch_evidence"])
            self.assertEqual(report["inputs"]["time_to_barrier_reports"], [str(train_path), str(valid_path)])
            self.assertIn("selected_count=", stdout.getvalue())

    def test_main_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--time-to-barrier-report",
                        str(input_path),
                        "--time-to-barrier-report",
                        str(input_path),
                        "--output",
                        str(Path(tmpdir) / "out.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())

    def test_main_accepts_candidate_filters(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            tmp_path = Path(tmpdir)
            train_path = tmp_path / "train.json"
            valid_path = tmp_path / "valid.json"
            output_path = tmp_path / "out.json"
            train_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "TRAIN_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "entry_volume_30s": 1.8,
                                "flow_buy_sell_overlap_ratio_60s": 0.1,
                            },
                            {
                                "symbol": "TRAIN_NEG",
                                "recommended_policy": "skip",
                                "prob": 0.991,
                                "entry_volume_30s": 1.8,
                                "flow_buy_sell_overlap_ratio_60s": 0.9,
                            },
                            {
                                "symbol": "TRAIN_EXCLUDED",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "entry_volume_30s": 0.2,
                                "flow_buy_sell_overlap_ratio_60s": 0.1,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            valid_path.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "VALID_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "entry_volume_30s": 1.8,
                                "flow_buy_sell_overlap_ratio_60s": 0.1,
                            },
                            {
                                "symbol": "VALID_EXCLUDED",
                                "recommended_policy": "skip",
                                "prob": 0.991,
                                "entry_volume_30s": 0.2,
                                "flow_buy_sell_overlap_ratio_60s": 0.9,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = cli.main(
                [
                    "--time-to-barrier-report",
                    str(train_path),
                    "--time-to-barrier-report",
                    str(valid_path),
                    "--output",
                    str(output_path),
                    "--candidate-filter",
                    "entry_volume_30s>=1.25",
                    "--min-validation-selected",
                    "1",
                    "--max-depth",
                    "1",
                    "--min-samples-leaf",
                    "1",
                    "--probability-threshold",
                    "0.5",
                ]
            )

            self.assertEqual(result, 0)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["candidate_counts"]["pre_filter_candidates"], 5)
            self.assertEqual(report["candidate_counts"]["input_candidates"], 3)
            self.assertEqual(report["candidate_counts"]["filtered_out_candidates"], 2)
            self.assertEqual(
                report["parameters"]["candidate_filters"],
                [{"field": "entry_volume_30s", "op": ">=", "value": 1.25}],
            )


if __name__ == "__main__":
    unittest.main()
