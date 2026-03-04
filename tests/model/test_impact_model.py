import unittest
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "backtest" / "impact_model.py"
    spec = importlib.util.spec_from_file_location("impact_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestImpactModel(unittest.TestCase):
    def test_cost_increases_with_order_size(self):
        m = _load_module()
        c_small = m.estimate_execution_cost(order_size=0.1, lp_depth=10.0, imbalance=0.1)
        c_large = m.estimate_execution_cost(order_size=1.0, lp_depth=10.0, imbalance=0.1)
        self.assertGreater(c_large, c_small)

    def test_partial_fill_when_depth_too_low(self):
        m = _load_module()
        result = m.simulate_sell_fill(order_size=10.0, lp_depth=1.0, max_fill_ratio=0.8)
        self.assertLess(result["filled_size"], 10.0)
        self.assertAlmostEqual(result["fill_ratio"], 0.8)


if __name__ == "__main__":
    unittest.main()
