import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util


def _load_engine():
    path = Path(__file__).resolve().parents[2] / "src" / "backtest" / "engine.py"
    spec = importlib.util.spec_from_file_location("engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBacktestHybrid(unittest.TestCase):
    def test_engine_accepts_hybrid_model_param(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)
        self.assertIs(engine.hybrid, fake_hybrid)

    def test_engine_without_hybrid_still_works(self):
        m = _load_engine()
        engine = m.BacktestEngine()
        self.assertIsNone(engine.hybrid)


if __name__ == "__main__":
    unittest.main()
