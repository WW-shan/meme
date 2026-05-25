import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_action_policy_meta_label.py"
    spec = importlib.util.spec_from_file_location("probe_action_policy_meta_label", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestActionPolicyMetaLabelProbeCli(unittest.TestCase):
    def test_main_writes_read_only_report_with_grouped_accepted_and_rejected_inputs(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory(dir="data/replay_reports") as tmpdir:
            tmp_path = Path(tmpdir)
            rejected_train = tmp_path / "rejected_train.json"
            rejected_validation = tmp_path / "rejected_validation.json"
            accepted_train = tmp_path / "accepted_train.json"
            accepted_validation = tmp_path / "accepted_validation.json"
            output_path = tmp_path / "out.json"
            rejected_train.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "REJ_TRAIN_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.10,
                            },
                            {
                                "symbol": "REJ_TRAIN_NEG",
                                "recommended_policy": "skip",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.90,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            rejected_validation.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "REJ_VALID_POS",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.20,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            accepted_train.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "ACC_TRAIN_POS",
                                "recommended_policy": "continue_hold",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.15,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            accepted_validation.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "ACC_VALID_POS",
                                "recommended_policy": "lock_profit",
                                "prob": 0.991,
                                "flow_buy_sell_overlap_ratio_60s": 0.18,
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
                        "--rejected-report",
                        str(rejected_train),
                        "--rejected-report",
                        str(rejected_validation),
                        "--accepted-report",
                        str(accepted_train),
                        "--accepted-report",
                        str(accepted_validation),
                        "--rejected-source-name",
                        "train",
                        "--rejected-source-name",
                        "validation",
                        "--accepted-source-name",
                        "train",
                        "--accepted-source-name",
                        "validation",
                        "--output",
                        str(output_path),
                        "--validation-source-count",
                        "1",
                        "--min-validation-selected",
                        "1",
                        "--min-family-candidates",
                        "1",
                        "--min-common-features",
                        "1",
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
            self.assertEqual(report["inputs"]["rejected_reports"], [str(rejected_train), str(rejected_validation)])
            self.assertEqual(report["inputs"]["accepted_reports"], [str(accepted_train), str(accepted_validation)])
            self.assertIn("decision=", stdout.getvalue())

    def test_main_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                result = cli.main(
                    [
                        "--rejected-report",
                        str(input_path),
                        "--accepted-report",
                        str(input_path),
                        "--output",
                        str(Path(tmpdir) / "out.json"),
                    ]
                )

            self.assertEqual(result, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
