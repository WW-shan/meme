import tempfile
import unittest
from pathlib import Path
import importlib.util
from unittest.mock import patch


def _load_cli_module():
    module_path = Path(__file__).resolve().parents[2] / "tools" / "calibrate_profit_first.py"
    spec = importlib.util.spec_from_file_location("calibrate_profit_first", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCalibrateProfitFirstCli(unittest.TestCase):
    def test_parse_args_reads_threshold_lists(self):
        module = _load_cli_module()
        args = module.parse_args(
            [
                "--prob-thresholds",
                "0.2,0.3",
                "--reg-min-returns",
                "50,70",
                "--max-age-seconds",
                "120,180",
                "--min-trades",
                "25",
                "--max-drawdown",
                "30",
                "--top-k",
                "5",
            ]
        )

        self.assertEqual(args.prob_thresholds, [0.2, 0.3])
        self.assertEqual(args.reg_min_returns, [50.0, 70.0])
        self.assertEqual(args.max_age_seconds, [120, 180])
        self.assertEqual(args.min_trades, 25)
        self.assertEqual(args.max_drawdown, 30.0)
        self.assertEqual(args.top_k, 5)

    def test_main_writes_calibration_report(self):
        module = _load_cli_module()
        fake_result = {
            "dataset_timestamp": "20260215_160001",
            "model_timestamp": "20260215_153845",
            "top_candidates": [],
            "recommended": {
                "prob_threshold": 0.3,
                "reg_min_return": 60.0,
                "max_age_seconds": 180,
                "return_pct": 40.0,
                "max_drawdown_pct": 20.0,
                "trades": 50,
            },
        }

        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            with patch.object(module, "run_profit_first_calibration", return_value=fake_result):
                output_path = module.main(
                    [
                        "--output-dir",
                        str(out_dir),
                        "--dataset-path",
                        str(out_dir),
                        "--model-dir",
                        str(out_dir),
                    ]
                )

            self.assertTrue(output_path.exists())
            self.assertTrue(output_path.name.startswith("calibration_"))
            latest_link = out_dir / "calibration_latest.json"
            self.assertTrue(latest_link.exists())


if __name__ == "__main__":
    unittest.main()
