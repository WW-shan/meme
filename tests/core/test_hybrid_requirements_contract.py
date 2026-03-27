import re
import tempfile
import unittest
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
