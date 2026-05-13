import re
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
REQ_FILE = ROOT / "requirements.txt"


class TestHybridRequirementsContract(unittest.TestCase):
    def _requirement_names(self):
        names = set()
        for raw in REQ_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()
            if name:
                names.add(name)
        return names

    def test_hybrid_dependencies_are_declared(self):
        names = self._requirement_names()
        expected = {"catboost", "gymnasium", "stable-baselines3", "torch"}
        missing = sorted(expected - names)
        self.assertFalse(missing, f"Missing dependencies: {missing}")


class TestPredReturnFilterStartupContract(unittest.TestCase):
    def _base_config(self, model_dir: str, **overrides):
        config = {
            "w3": MagicMock(),
            "model_dir": model_dir,
            "initial_balance": 1.0,
        }
        config.update(overrides)
        return config

    def _patch_bot_deps(self, collector=None):
        return patch.multiple(
            "src.trader.bot",
            TradeExecutor=MagicMock(return_value=MagicMock()),
            DataCollector=MagicMock(return_value=collector or MagicMock()),
            FourMemeListener=MagicMock(return_value=MagicMock()),
            WSConnectionManager=MagicMock(return_value=MagicMock()),
        )

    def _create_model_dir(self):
        tmp = tempfile.TemporaryDirectory()
        Path(tmp.name, "buy_model.cbm").write_text("x", encoding="utf-8")
        return tmp

    def test_use_pred_return_filter_true_fails_fast_when_artifacts_unsupported(self):
        from src.trader.bot import MemeBot

        class _UnsupportedHybrid:
            buy_threshold = 0.5
            sell_policy = None

        unsupported_hybrid = _UnsupportedHybrid()

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=unsupported_hybrid):
            with self.assertRaisesRegex(ValueError, r"use_pred_return_filter=true.*predicted-return support"):
                MemeBot(self._base_config(model_dir, use_pred_return_filter=True))

    def test_use_pred_return_filter_true_allows_supported_artifacts(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_return = MagicMock(return_value=1.0)

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, use_pred_return_filter=True))

        self.assertTrue(bot.use_pred_return_filter)

    def test_use_pred_return_filter_true_fails_when_model_load_errors(self):
        from src.trader.bot import MemeBot

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", side_effect=RuntimeError("boom")):
            with self.assertRaisesRegex(ValueError, r"use_pred_return_filter=true.*predicted-return support"):
                MemeBot(self._base_config(model_dir, use_pred_return_filter=True))

    def test_use_pred_return_filter_true_allows_inherited_predict_return(self):
        from src.trader.bot import MemeBot

        class _BaseHybrid:
            def predict_return(self, *args, **kwargs):
                return 1.0

        class _InheritedHybrid(_BaseHybrid):
            pass

        supported_hybrid = _InheritedHybrid()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, use_pred_return_filter=True))

        self.assertTrue(bot.use_pred_return_filter)

    def test_legacy_return_model_file_does_not_bypass_single_switch_contract(self):
        from src.trader.bot import MemeBot

        class _UnsupportedHybrid:
            buy_threshold = 0.5
            sell_policy = None

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=_UnsupportedHybrid()):
            Path(model_dir, "return_model.cbm").write_text("legacy", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"use_pred_return_filter=true.*predicted-return support"):
                MemeBot(self._base_config(model_dir, use_pred_return_filter=True))

    def test_pred_return_filter_blocks_buy_when_predicted_return_is_below_threshold(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)
        supported_hybrid.predict_return.return_value = 10.0

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, use_pred_return_filter=True, min_pred_return=80.0))
            bot._enqueue_buy_signal = AsyncMock()
            import asyncio
            asyncio.run(bot._process_token_logic("0xToken"))

        bot._enqueue_buy_signal.assert_not_called()

    def test_signal_audit_logs_model_reject_reason_and_feature_hash(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)
        supported_hybrid.predict_return.return_value = 10.0

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0, "buy_pressure": 0.8}
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            audit_path = Path(tmpdir) / "signals.jsonl"
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    use_pred_return_filter=True,
                    min_pred_return=80.0,
                    signal_audit_file=str(audit_path),
                )
            )
            asyncio.run(bot._process_token_logic("0xToken"))

            rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "SIGNAL_DECISION")
        self.assertEqual(rows[0]["token"], "0xToken")
        self.assertEqual(rows[0]["decision"], "rejected")
        self.assertEqual(rows[0]["reason"], "pred_return_below_min")
        self.assertEqual(rows[0]["prob"], 0.9)
        self.assertEqual(rows[0]["pred_return"], 10.0)
        self.assertRegex(rows[0]["features_hash"], r"^[0-9a-f]{64}$")
        self.assertEqual(rows[0]["feature_count"], 2)

    def test_pred_return_filter_allows_buy_when_predicted_return_meets_threshold(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)
        supported_hybrid.predict_return.return_value = 100.0

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, use_pred_return_filter=True, min_pred_return=80.0))
            bot._enqueue_buy_signal = AsyncMock()
            import asyncio
            asyncio.run(bot._process_token_logic("0xToken"))

        bot._enqueue_buy_signal.assert_awaited_once()

    def test_process_token_logic_uses_configured_entry_activity_gate(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b"},
                "buys": [1, 2],
                "sells": [],
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    min_entry_unique_buyers=2,
                    min_entry_buy_count=2,
                )
            )
            bot._enqueue_buy_signal = AsyncMock()
            import asyncio
            asyncio.run(bot._process_token_logic("0xToken"))

        bot._enqueue_buy_signal.assert_awaited_once()

    def test_buy_capacity_respects_fixed_stake_cash(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.05,
                    fixed_stake_bnb=0.1,
                    max_concurrent_positions=10,
                )
            )

        self.assertFalse(bot._has_buy_capacity())

    def test_open_position_uses_fixed_stake_bnb_in_paper_mode(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        lifecycle = {
            "symbol": "TK",
            "price_current": 1.0,
            "last_update": 120,
            "create_timestamp": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.5,
                    fixed_stake_bnb=0.1,
                    position_size=0.5,
                    max_concurrent_positions=10,
                )
            )
            bot.state_file = Path(tmpdir) / "state.json"
            asyncio.run(bot._open_position("0xToken", lifecycle, 0.9))

        self.assertAlmostEqual(bot.positions["0xToken"]["size_bnb"], 0.1)
        self.assertAlmostEqual(bot.balance, 0.4)

    def test_signal_audit_logs_open_position_execution_price(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        lifecycle = {
            "symbol": "TK",
            "price_current": 1.2,
            "last_update": 120,
            "create_timestamp": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            audit_path = Path(tmpdir) / "signals.jsonl"
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.5,
                    fixed_stake_bnb=0.1,
                    max_concurrent_positions=10,
                    signal_audit_file=str(audit_path),
                )
            )
            bot.state_file = Path(tmpdir) / "state.json"
            asyncio.run(bot._open_position("0xToken", lifecycle, 0.9, pred_return=42.0, signal_price=1.0))
            rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(rows[-1]["action"], "POSITION_OPENED")
        self.assertEqual(rows[-1]["token"], "0xToken")
        self.assertEqual(rows[-1]["signal_price"], 1.0)
        self.assertEqual(rows[-1]["entry_price"], 1.2)
        self.assertEqual(rows[-1]["pred_return"], 42.0)

    def test_open_position_skips_chasing_price_above_manifest_protection(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        lifecycle = {
            "symbol": "TK",
            "price_current": 1.30,
            "last_update": 120,
            "create_timestamp": 0,
        }
        manifest = {"evaluation": {"entry_price_protection_pct": 0.25}}

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            audit_path = Path(tmpdir) / "signals.jsonl"
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.5,
                    fixed_stake_bnb=0.1,
                    max_concurrent_positions=10,
                    signal_audit_file=str(audit_path),
                )
            )
            asyncio.run(bot._open_position("0xToken", lifecycle, 0.9, pred_return=42.0, signal_price=1.0))
            rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(bot.entry_price_protection_pct, 0.25)
        self.assertNotIn("0xToken", bot.positions)
        self.assertAlmostEqual(bot.balance, 0.5)
        self.assertEqual(rows[-1]["action"], "ENTRY_PRICE_PROTECTION_SKIP")
        self.assertEqual(rows[-1]["signal_price"], 1.0)
        self.assertEqual(rows[-1]["candidate_price"], 1.3)

    def test_real_entry_price_protection_normalizes_helper_price(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        lifecycle = {
            "symbol": "TK",
            "price_current": 7.719648494861625e-09,
            "last_update": 120,
            "create_timestamp": 0,
        }
        executor = MagicMock()
        executor.check_token_status = AsyncMock(
            return_value={
                "ready": True,
                "price": 8055655943,
                "reason": "OK",
            }
        )
        executor.buy_token = AsyncMock(return_value=None)

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, patch.multiple(
            "src.trader.bot",
            TradeExecutor=MagicMock(return_value=executor),
            DataCollector=MagicMock(return_value=MagicMock()),
            FourMemeListener=MagicMock(return_value=MagicMock()),
            WSConnectionManager=MagicMock(return_value=MagicMock()),
        ), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", True), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            audit_path = Path(tmpdir) / "signals.jsonl"
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.5,
                    fixed_stake_bnb=0.1,
                    max_concurrent_positions=10,
                    entry_price_protection_pct=0.25,
                    signal_audit_file=str(audit_path),
                )
            )
            asyncio.run(
                bot._open_position(
                    "0xToken",
                    lifecycle,
                    0.99,
                    pred_return=13.0,
                    signal_price=7.719648494861625e-09,
                )
            )
            rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]

        executor.buy_token.assert_awaited_once()
        self.assertEqual(rows[-1]["action"], "BUY_EXECUTION_FAILED")
        self.assertFalse(any(row["action"] == "ENTRY_PRICE_PROTECTION_SKIP" for row in rows))

    def test_negative_entry_price_protection_is_clamped_to_zero_like_replay(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        lifecycle = {
            "symbol": "TK",
            "price_current": 1.0,
            "last_update": 120,
            "create_timestamp": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.5,
                    fixed_stake_bnb=0.1,
                    max_concurrent_positions=10,
                    entry_price_protection_pct=-0.10,
                    signal_audit_file=str(Path(tmpdir) / "signals.jsonl"),
                )
            )
            bot.state_file = Path(tmpdir) / "state.json"
            asyncio.run(bot._open_position("0xToken", lifecycle, 0.9, signal_price=1.0))

        self.assertEqual(bot.entry_price_protection_pct, 0.0)
        self.assertIn("0xToken", bot.positions)

    def test_paper_full_close_uses_entry_price_not_signal_price_for_pnl(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        collector = MagicMock()
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.2,
                "last_update": 120,
                "create_timestamp": 0,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, initial_balance=0.4))
            bot.trade_file = Path(tmpdir) / "trades.jsonl"
            bot.signal_audit_file = Path(tmpdir) / "signals.jsonl"
            bot.state_file = Path(tmpdir) / "state.json"
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.2,
                    "signal_price": 1.0,
                    "tp_base_price": 1.2,
                    "peak_price": 1.2,
                    "entry_time": datetime.now() - timedelta(seconds=10),
                    "size_bnb": 0.1,
                    "initial_size_bnb": 0.1,
                }
            }
            asyncio.run(bot._close_position_inner("0xToken", "TEST_EXIT"))
            rows = [json.loads(line) for line in bot.signal_audit_file.read_text(encoding="utf-8").splitlines()]

        self.assertNotIn("0xToken", bot.positions)
        self.assertAlmostEqual(bot.balance, 0.5)
        self.assertAlmostEqual(rows[-1]["net_profit"], 0.0)
        self.assertEqual(rows[-1]["entry_price"], 1.2)
        self.assertEqual(rows[-1]["signal_price"], 1.0)

    def test_paper_partial_sell_uses_entry_price_not_signal_price_for_pnl(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        collector = MagicMock()
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.2,
                "last_update": 120,
                "create_timestamp": 0,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, initial_balance=0.4))
            bot.trade_file = Path(tmpdir) / "trades.jsonl"
            bot.signal_audit_file = Path(tmpdir) / "signals.jsonl"
            bot.state_file = Path(tmpdir) / "state.json"
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.2,
                    "signal_price": 1.0,
                    "tp_base_price": 1.2,
                    "peak_price": 1.2,
                    "entry_time": datetime.now() - timedelta(seconds=10),
                    "size_bnb": 0.1,
                    "initial_size_bnb": 0.1,
                }
            }
            asyncio.run(bot._partial_sell("0xToken", sell_ratio=0.5, reason="TEST_PARTIAL"))
            rows = [json.loads(line) for line in bot.trade_file.read_text(encoding="utf-8").splitlines()]
            audit_rows = [json.loads(line) for line in bot.signal_audit_file.read_text(encoding="utf-8").splitlines()]

        self.assertAlmostEqual(bot.positions["0xToken"]["size_bnb"], 0.05)
        self.assertAlmostEqual(bot.balance, 0.45)
        self.assertAlmostEqual(rows[-1]["net_profit"], 0.0)
        self.assertEqual(rows[-1]["entry_price"], 1.2)
        self.assertEqual(rows[-1]["exit_price"], 1.2)
        self.assertEqual(audit_rows[-1]["action"], "POSITION_PARTIAL_CLOSED")
        self.assertEqual(audit_rows[-1]["sell_ratio"], 0.5)
        self.assertAlmostEqual(audit_rows[-1]["net_profit"], 0.0)

    def test_emergency_liquidation_summary_uses_entry_price_not_signal_price(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        collector = MagicMock()
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.2,
                "last_update": 120,
                "create_timestamp": 0,
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", False), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, initial_balance=0.4))
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.2,
                    "signal_price": 1.0,
                    "tp_base_price": 1.2,
                    "peak_price": 1.2,
                    "entry_time": datetime.now() - timedelta(seconds=10),
                    "size_bnb": 0.1,
                    "initial_size_bnb": 0.1,
                }
            }
            bot._close_position = AsyncMock()
            with self.assertLogs("MemeBot", level="WARNING") as logs:
                asyncio.run(bot.sell_all_positions(timeout=12))

        position_logs = [line for line in logs.output if "0xToken" in line and "PnL:" in line]
        self.assertTrue(position_logs)
        self.assertIn("PnL: +0.0%", position_logs[-1])
        self.assertNotIn("PnL: +20.0%", position_logs[-1])

    def test_runtime_risk_params_load_from_model_manifest_when_not_manual(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.77
        supported_hybrid.sell_policy = None

        manifest = {
            "evaluation": {
                "stop_loss": -0.35,
                "max_hold_seconds": 300,
                "min_policy_hold_seconds": 5,
                "max_entry_age_seconds": 300,
                "position_fraction": 0.05,
                "trailing_start_pct": 0.25,
                "trailing_stop_pct": 0.20,
                "rug_sell_pressure": 0.92,
                "allow_partial_exits": False,
                "max_open_positions": 8,
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(self._base_config(model_dir))

        self.assertEqual(bot.stop_loss, -0.35)
        self.assertEqual(bot.hold_time_seconds, 300)
        self.assertEqual(bot.min_policy_hold_seconds, 5)
        self.assertEqual(bot.max_age_seconds, 300)
        self.assertEqual(bot.position_size, 0.05)
        self.assertEqual(bot.trailing_start_pct, 0.25)
        self.assertEqual(bot.trailing_stop_pct, 0.20)
        self.assertEqual(bot.rug_sell_pressure, 0.92)
        self.assertEqual(bot.max_concurrent_positions, 8)

    def test_manual_zero_max_open_positions_overrides_manifest_limit(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.77
        supported_hybrid.sell_policy = None

        manifest = {"evaluation": {"max_open_positions": 1000}}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(self._base_config(model_dir, max_concurrent_positions=0))

        self.assertEqual(bot.max_concurrent_positions, 0)
        self.assertEqual(bot.exit_param_sources["max_concurrent_positions"], "manual")

    def test_zero_max_concurrent_positions_means_unlimited_capacity(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xNew": {
                "symbol": "NEW",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, initial_balance=1.0, max_concurrent_positions=0))
            bot.positions = {
                "0xHeld": {
                    "symbol": "HELD",
                    "entry_price": 1.0,
                    "entry_time": datetime.now(),
                    "size_bnb": 0.1,
                }
            }
            asyncio.run(bot._process_token_logic("0xNew"))

        self.assertEqual(bot._buy_signal_queue.qsize(), 1)

    def test_fixed_stake_is_capped_by_max_entry_size(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=0.15,
                    fixed_stake_bnb=0.2,
                    max_entry_size_bnb=0.1,
                )
            )

        self.assertAlmostEqual(bot._entry_size_bnb(), 0.1)

    def test_runtime_fraction_sizing_can_disable_manifest_fixed_stake(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        manifest = {"evaluation": {"fixed_stake_bnb": 0.1, "position_fraction": 0.5}}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    initial_balance=2.0,
                    position_size=0.10,
                    fixed_stake_bnb=None,
                    max_entry_size_bnb=0.1,
                )
            )

        self.assertIsNone(bot.fixed_stake_bnb)
        self.assertEqual(bot.exit_param_sources["fixed_stake_bnb"], "manual")
        self.assertAlmostEqual(bot.position_size, 0.10)
        self.assertAlmostEqual(bot._entry_size_bnb(), 0.1)

    def test_pred_return_filter_runtime_params_load_from_model_manifest_when_not_manual(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.77
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_return = MagicMock(return_value=12.0)

        manifest = {
            "evaluation": {
                "min_entry_score": 10.0,
                "use_pred_return_filter": True,
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(self._base_config(model_dir))

        self.assertTrue(bot.use_pred_return_filter)
        self.assertEqual(bot.min_pred_return, 10.0)
        self.assertEqual(bot.strategy_param_sources["min_pred_return"], "model_manifest")

    def test_entry_value_ranking_requires_pred_return_support(self):
        from src.trader.bot import MemeBot

        class _UnsupportedHybrid:
            buy_threshold = 0.5
            sell_policy = None

        manifest = {"evaluation": {"entry_ranking_mode": "entry_value"}}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=_UnsupportedHybrid()):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, r"entry_ranking_mode=entry_value.*predicted-return support"):
                MemeBot(self._base_config(model_dir))

    def test_live_buy_queue_prioritizes_entry_value_manifest_ranking(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.side_effect = [(0.95, True), (0.90, True)]
        supported_hybrid.predict_return.side_effect = [11.0, 50.0]

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xLow": {
                "symbol": "LOW",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            },
            "0xHigh": {
                "symbol": "HIGH",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"d", "e", "f"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            },
        }
        manifest = {"evaluation": {"entry_ranking_mode": "entry_value"}}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(self._base_config(model_dir, max_concurrent_positions=10))

            opened = []

            async def record_open(token_address, lifecycle, prob, pred_return=None, signal_price=None):
                opened.append((token_address, pred_return))
                if len(opened) >= 2:
                    bot.active = False

            bot._open_position = record_open

            async def run_flow():
                await bot._process_token_logic("0xLow")
                await bot._process_token_logic("0xHigh")
                await bot._buy_worker_loop()

            asyncio.run(run_flow())

        self.assertEqual(bot.entry_ranking_mode, "entry_value")
        self.assertEqual(opened, [("0xHigh", 50.0), ("0xLow", 11.0)])

    def test_live_buy_queue_replaces_lower_entry_value_signal_when_capacity_reserved(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.side_effect = [(0.95, True), (0.90, True)]
        supported_hybrid.predict_return.side_effect = [11.0, 50.0]

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xLow": {
                "symbol": "LOW",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            },
            "0xHigh": {
                "symbol": "HIGH",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"d", "e", "f"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            },
        }
        manifest = {"evaluation": {"entry_ranking_mode": "entry_value"}}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(self._base_config(model_dir, max_concurrent_positions=1))

            opened = []

            async def record_open(token_address, lifecycle, prob, pred_return=None, signal_price=None):
                opened.append((token_address, pred_return))
                bot.active = False

            bot._open_position = record_open

            async def run_flow():
                await bot._process_token_logic("0xLow")
                await bot._process_token_logic("0xHigh")
                await bot._buy_worker_loop()

            asyncio.run(run_flow())

        self.assertEqual(opened, [("0xHigh", 50.0)])
        self.assertNotIn("0xLow", bot._pending_buy_signals)

    def test_process_token_logic_blocks_buy_when_max_concurrent_positions_is_full(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None
        supported_hybrid.predict_buy.return_value = (0.9, True)

        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0}
        collector.token_lifecycle = {
            "0xNew": {
                "symbol": "NEW",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [1, 2, 3, 4, 5],
                "sells": [],
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, max_concurrent_positions=1))
            bot.positions = {
                "0xHeld": {
                    "symbol": "HELD",
                    "entry_price": 1.0,
                    "entry_time": datetime.now(),
                    "size_bnb": 0.1,
                }
            }
            asyncio.run(bot._process_token_logic("0xNew"))

        self.assertEqual(bot._buy_signal_queue.qsize(), 0)

    def test_manual_runtime_config_overrides_model_manifest_and_threshold(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.77
        supported_hybrid.sell_policy = None

        manifest = {
            "evaluation": {
                "stop_loss": -0.35,
                "max_hold_seconds": 300,
                "min_policy_hold_seconds": 5,
                "max_entry_age_seconds": 300,
                "position_fraction": 0.05,
                "trailing_start_pct": 0.25,
                "trailing_stop_pct": 0.20,
                "rug_sell_pressure": 0.92,
                "max_open_positions": 99,
            }
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            Path(model_dir, "hybrid_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    prob_threshold=0.91,
                    stop_loss=-0.50,
                    hold_time_seconds=120,
                    min_policy_hold_seconds=1,
                    max_age_seconds=150,
                    position_size=0.20,
                    trailing_start_pct=0.40,
                    trailing_stop_pct=0.30,
                    rug_sell_pressure=0.95,
                    max_concurrent_positions=7,
                )
            )

        self.assertEqual(bot.hybrid.buy_threshold, 0.91)
        self.assertEqual(bot.stop_loss, -0.50)
        self.assertEqual(bot.hold_time_seconds, 120)
        self.assertEqual(bot.min_policy_hold_seconds, 1)
        self.assertEqual(bot.max_age_seconds, 150)
        self.assertEqual(bot.position_size, 0.20)
        self.assertEqual(bot.trailing_start_pct, 0.40)
        self.assertEqual(bot.trailing_stop_pct, 0.30)
        self.assertEqual(bot.rug_sell_pressure, 0.95)
        self.assertEqual(bot.max_concurrent_positions, 7)

    def test_position_logic_enforces_manifest_rug_exit_before_policy(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = object()

        collector = MagicMock()
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.0,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [],
                "sells": [],
            }
        }
        collector._extract_features.return_value = {
            "total_buy_volume": 1.0,
            "total_sell_volume": 9.0,
            "launch_fee": 0.5,
            "holder_count": 5,
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir, rug_sell_pressure=0.80, hold_time_seconds=300))
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.0,
                    "signal_price": 1.0,
                    "tp_base_price": 1.0,
                    "peak_price": 1.0,
                    "entry_time": datetime.now() - timedelta(seconds=10),
                    "size_bnb": 0.1,
                    "initial_size_bnb": 0.1,
                }
            }
            bot._close_position = AsyncMock()
            asyncio.run(bot._process_token_logic("0xToken"))

        bot._close_position.assert_awaited_once_with("0xToken", reason="RUG_EXIT")

    def test_position_logic_enforces_trailing_stop_before_policy(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = object()

        collector = MagicMock()
        collector.token_lifecycle = {
            "0xToken": {
                "symbol": "TK",
                "price_current": 1.5,
                "last_update": 120,
                "create_timestamp": 0,
                "unique_buyers": {"a", "b", "c"},
                "buys": [],
                "sells": [],
            }
        }
        collector._extract_features.return_value = {
            "total_buy_volume": 10.0,
            "total_sell_volume": 1.0,
            "launch_fee": 0.5,
            "holder_count": 5,
        }

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(
                self._base_config(
                    model_dir,
                    trailing_start_pct=0.25,
                    trailing_stop_pct=0.20,
                    hold_time_seconds=300,
                )
            )
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.0,
                    "signal_price": 1.0,
                    "tp_base_price": 1.0,
                    "peak_price": 2.0,
                    "entry_time": datetime.now() - timedelta(seconds=10),
                    "size_bnb": 0.1,
                    "initial_size_bnb": 0.1,
                }
            }
            bot._close_position = AsyncMock()
            asyncio.run(bot._process_token_logic("0xToken"))

        bot._close_position.assert_awaited_once_with("0xToken", reason="TRAILING_STOP")

    def test_restored_lifecycle_stub_contains_feature_required_fields(self):
        from src.trader.bot import MemeBot

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        collector = MagicMock()
        collector.token_lifecycle = {}

        with self._create_model_dir() as model_dir, self._patch_bot_deps(collector=collector), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir))
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.0,
                    "entry_time": datetime.now(),
                    "size_bnb": 0.1,
                }
            }
            bot._ensure_lifecycle("0xToken")

        lifecycle = collector.token_lifecycle["0xToken"]
        for required_key in ("creator", "name", "total_supply", "launch_fee"):
            self.assertIn(required_key, lifecycle)

    def test_sync_positions_removes_invalid_restored_token_address(self):
        from src.trader.bot import MemeBot
        import asyncio

        supported_hybrid = MagicMock()
        supported_hybrid.buy_threshold = 0.5
        supported_hybrid.sell_policy = None

        with tempfile.TemporaryDirectory() as tmpdir, self._create_model_dir() as model_dir, self._patch_bot_deps(), patch.object(MemeBot, "_load_state", return_value=None), patch.object(MemeBot, "_register_handlers", return_value=None), patch.object(MemeBot.__init__.__globals__["TradingConfig"], "ENABLE_TRADING", True), patch("src.model.hybrid_inference.HybridModel.load", return_value=supported_hybrid):
            bot = MemeBot(self._base_config(model_dir))
            bot.state_file = Path(tmpdir) / "state.json"
            bot.executor.wallet_address = "0x867883B3e77E4E12f2baB796F220f56586b38703"
            bot.executor.w3.is_address.return_value = False
            bot.positions = {
                "0xToken": {
                    "symbol": "TK",
                    "entry_price": 1.0,
                    "entry_time": datetime.now(),
                    "size_bnb": 0.1,
                }
            }
            asyncio.run(bot._sync_positions_with_chain())

        self.assertEqual(bot.positions, {})
        self.assertIn("0xToken", bot.closed_tokens)


if __name__ == "__main__":
    unittest.main()
