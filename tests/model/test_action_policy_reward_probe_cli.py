import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_action_policy_reward.py"
    spec = importlib.util.spec_from_file_location("probe_action_policy_reward", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestActionPolicyRewardProbeCli(unittest.TestCase):
    def test_parse_args_requires_train_and_validation_reports(self):
        cli = _load_cli_module()

        args = cli.parse_args(
            [
                "--train-rejected-report",
                "data/replay_reports/train_rejected.json",
                "--train-accepted-report",
                "data/replay_reports/train_accepted.json",
                "--validation-rejected-report",
                "data/replay_reports/validation_rejected.json",
                "--validation-accepted-report",
                "data/replay_reports/validation_accepted.json",
            ]
        )

        self.assertEqual(args.train_rejected_report, ["data/replay_reports/train_rejected.json"])
        self.assertEqual(args.train_accepted_report, ["data/replay_reports/train_accepted.json"])
        self.assertTrue(args.output.startswith("data/replay_reports/action_policy_reward_probe_"))

    def test_main_writes_reward_report_under_replay_reports(self):
        cli = _load_cli_module()
        with tempfile.TemporaryDirectory(dir=Path.cwd() / ".test_tmp") as tmp:
            tmp_path = Path(tmp)
            train_rejected = tmp_path / "train_rejected.json"
            train_accepted = tmp_path / "train_accepted.json"
            validation_rejected = tmp_path / "validation_rejected.json"
            validation_accepted = tmp_path / "validation_accepted.json"
            output = Path("data/replay_reports") / f"{tmp_path.name}_reward.json"
            train_rejected.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "REJ_WIN",
                                "barrier_class": "fast_profit",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.99,
                                "pred_return": 10,
                                "time_to_plus_25_seconds": 5,
                            },
                            {
                                "symbol": "REJ_LOSS",
                                "barrier_class": "stop_first",
                                "recommended_policy": "skip",
                                "prob": 0.95,
                                "pred_return": 1,
                                "time_to_minus_18_seconds": 5,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            train_accepted.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "ACC_WIN",
                                "classification": "post_target_continuation",
                                "recommended_policy": "continue_hold",
                                "prob": 0.99,
                                "pred_return": 30,
                                "post_target_window_returns_pct": {"60": 20},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            validation_rejected.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "REJ_VALID",
                                "barrier_class": "fast_profit",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.99,
                                "pred_return": 10,
                                "time_to_plus_25_seconds": 5,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            validation_accepted.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "ACC_VALID",
                                "classification": "post_target_continuation",
                                "recommended_policy": "continue_hold",
                                "prob": 0.99,
                                "pred_return": 30,
                                "post_target_window_returns_pct": {"60": 30},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            try:
                code = cli.main(
                    [
                        "--train-rejected-report",
                        str(train_rejected),
                        "--train-accepted-report",
                        str(train_accepted),
                        "--validation-rejected-report",
                        str(validation_rejected),
                        "--validation-accepted-report",
                        str(validation_accepted),
                        "--output",
                        str(output),
                        "--force",
                        "--min-common-features",
                        "1",
                        "--min-selected-per-family",
                        "1",
                        "--min-samples-leaf",
                        "1",
                    ]
                )
                self.assertEqual(code, 0)
                saved = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(saved["inputs"]["validation_rejected_reports"], [str(validation_rejected)])
                self.assertEqual(saved["validation"]["selected_family_counts"], {"accepted": 1, "rejected": 1})
            finally:
                output.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
