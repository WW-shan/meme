import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_action_policy_router.py"
    spec = importlib.util.spec_from_file_location("probe_action_policy_router", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestActionPolicyRouterProbeCli(unittest.TestCase):
    def test_main_writes_router_report_under_replay_reports(self):
        cli = _load_cli_module()
        with tempfile.TemporaryDirectory(dir=Path.cwd() / ".test_tmp") as tmp:
            tmp_path = Path(tmp)
            train_rejected = tmp_path / "train_rejected.json"
            train_accepted = tmp_path / "train_accepted.json"
            validation_rejected = tmp_path / "validation_rejected.json"
            validation_accepted = tmp_path / "validation_accepted.json"
            output = Path("data/replay_reports") / f"{tmp_path.name}_router.json"
            train_rejected.write_text(
                json.dumps(
                    {
                        "candidate_sample": [
                            {
                                "symbol": "REJ_QTP",
                                "recommended_policy": "quick_take_profit",
                                "prob": 0.99,
                                "pred_return": 30,
                                "flow_buy_sell_overlap_ratio_60s": 0.1,
                                "time_to_plus_25_seconds": 5,
                            },
                            {
                                "symbol": "REJ_SKIP",
                                "recommended_policy": "skip",
                                "prob": 0.99,
                                "pred_return": 30,
                                "flow_buy_sell_overlap_ratio_60s": 0.9,
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
                                "symbol": "ACC_HOLD",
                                "classification": "post_target_continuation",
                                "recommended_policy": "continue_hold",
                                "prob": 0.99,
                                "pred_return": 50,
                                "flow_buy_sell_overlap_ratio_60s": 0.15,
                                "post_target_window_returns_pct": {"60": 40},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            validation_rejected.write_text(train_rejected.read_text(encoding="utf-8"), encoding="utf-8")
            validation_accepted.write_text(train_accepted.read_text(encoding="utf-8"), encoding="utf-8")
            try:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
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
                self.assertIn("decision=", stdout.getvalue())
            finally:
                output.unlink(missing_ok=True)

    def test_main_refuses_output_outside_replay_reports(self):
        cli = _load_cli_module()
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.json"
            input_path.write_text(json.dumps({"candidate_sample": []}), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = cli.main(
                    [
                        "--train-rejected-report",
                        str(input_path),
                        "--validation-rejected-report",
                        str(input_path),
                        "--output",
                        str(Path(tmp) / "router.json"),
                    ]
                )

            self.assertEqual(code, 2)
            self.assertIn("outside data/replay_reports", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
