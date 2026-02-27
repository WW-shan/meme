import unittest
from pathlib import Path
import importlib.util


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestSimpleBacktestExitLogic(unittest.TestCase):
    def test_execute_trade_uses_configurable_exit_params_when_tp_hit(self):
        module = _load_module(
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "simple_backtest.py",
            "simple_backtest",
        )
        SimpleBacktester = module.SimpleBacktester

        tester = SimpleBacktester.__new__(SimpleBacktester)
        tester.balance = 1.0
        tester.initial_balance = 1.0
        tester.position_size = 0.1
        tester.stop_loss = -0.5
        tester.take_profit = 999.0
        tester.prob_threshold = 0.8
        tester.first_take_profit = 1.0
        tester.first_exit_ratio = 0.6
        tester.drawdown_stop = 0.25
        tester.trades = []

        sample = {
            "label": {
                "is_moon_200": 0,
                "min_return_pct": -10.0,
                "max_return_pct": 120.0,
                "final_return_pct": 20.0,
            },
            "meta": {"symbol": "AAA", "sample_time": 0},
        }

        tester._execute_trade(sample, 0.95)
        self.assertEqual(len(tester.trades), 1)
        self.assertGreater(tester.trades[0]["actual_return"], 50.0)


if __name__ == "__main__":
    unittest.main()
