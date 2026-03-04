import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util
import asyncio


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

    def test_launch_event_uses_hybrid_buy_signal(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_buy.return_value = (0.8, True)
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        event = {
            "event_type": "launch",
            "token_address": "0xABC",
            "token_name": "TestToken",
            "token_symbol": "TT",
            "creator": "0x123",
            "total_supply": 1000000,
            "launch_fee": 0.5,
            "timestamp": 100,
        }
        asyncio.run(engine._process_launch_event(event))
        self.assertIn("0xABC", engine.positions)
        fake_hybrid.predict_buy.assert_called_once()

    def test_launch_event_rejects_when_hybrid_says_no(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_buy.return_value = (0.2, False)
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        event = {
            "event_type": "launch",
            "token_address": "0xDEF",
            "token_name": "BadToken",
            "token_symbol": "BT",
            "creator": "0x456",
            "total_supply": 1000000,
            "launch_fee": 0.5,
            "timestamp": 200,
        }
        asyncio.run(engine._process_launch_event(event))
        self.assertNotIn("0xDEF", engine.positions)

    def test_sell_uses_ppo_when_hybrid_available(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_sell.return_value = 3  # sell100
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        engine.positions["0xABC"] = {
            "token_address": "0xABC",
            "token_symbol": "TT",
            "entry_price": 1.0,
            "entry_time": 100,
            "total_amount": 100,
            "remaining_amount": 100,
            "bnb_invested": 0.1,
            "status": "holding",
            "peak_price": 1.0,
        }
        engine.latest_prices["0xABC"] = 1.2

        asyncio.run(engine._check_initial_position("0xABC", 1.2, 200))
        fake_hybrid.predict_sell.assert_called_once()
        self.assertNotIn("0xABC", engine.positions)

    def test_sell_holds_when_ppo_says_hold(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_sell.return_value = 0  # hold
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        engine.positions["0xABC"] = {
            "token_address": "0xABC",
            "token_symbol": "TT",
            "entry_price": 1.0,
            "entry_time": 100,
            "total_amount": 100,
            "remaining_amount": 100,
            "bnb_invested": 0.1,
            "status": "holding",
            "peak_price": 1.0,
        }

        asyncio.run(engine._check_initial_position("0xABC", 1.2, 200))
        self.assertIn("0xABC", engine.positions)

    def test_generate_stats_includes_sortino_and_maxdd(self):
        m = _load_engine()
        engine = m.BacktestEngine()
        engine.closed_positions = [
            {"pnl_bnb": 0.05, "pnl_pct": 50.0, "bnb_invested": 0.1, "exit_reason": "take_profit"},
            {"pnl_bnb": -0.02, "pnl_pct": -20.0, "bnb_invested": 0.1, "exit_reason": "stop_loss"},
            {"pnl_bnb": 0.03, "pnl_pct": 30.0, "bnb_invested": 0.1, "exit_reason": "take_profit"},
        ]
        stats = engine._generate_stats()
        self.assertIn("sortino_ratio", stats)
        self.assertIn("max_drawdown_pct", stats)
        self.assertIn("net_return_pct", stats)


if __name__ == "__main__":
    unittest.main()
