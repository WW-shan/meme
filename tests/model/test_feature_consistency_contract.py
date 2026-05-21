import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch


class TestFeatureConsistencyContract(unittest.TestCase):
    def test_dataset_collector_and_bot_extract_same_features_for_same_lifecycle(self):
        from src.data.collector import DataCollector
        from src.data.dataset_builder import DatasetBuilder
        from src.trader.bot import MemeBot

        sample_time = 120
        lifecycle = {
            "token_address": "0xToken",
            "name": "Test Token",
            "symbol": "TK",
            "creator": "0xCreator",
            "create_timestamp": 0,
            "last_update": sample_time,
            "total_supply": 1_000_000_000_000_000_000_000_000,
            "launch_fee": 1_000_000_000_000_000_000,
            "price_current": 1.2,
            "unique_buyers": {"0xA", "0xB", "0xCreator"},
            "unique_sellers": {"0xA"},
            "buys": [
                {"timestamp": 10, "account": "0xCreator", "bnb_amount": 0.4, "token_amount": 4000.0, "price": 1.0},
                {"timestamp": 40, "account": "0xA", "bnb_amount": 0.3, "token_amount": 2500.0, "price": 1.1},
                {"timestamp": 100, "account": "0xB", "bnb_amount": 0.2, "token_amount": 1500.0, "price": 1.2},
            ],
            "sells": [
                {"timestamp": 110, "account": "0xA", "bnb_amount": 0.1, "token_amount": 700.0, "price": 1.15},
            ],
        }

        past_buys = lifecycle["buys"]
        past_sells = lifecycle["sells"]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir)
            builder = DatasetBuilder(lifecycle_dir=tmpdir)

            bot = MemeBot.__new__(MemeBot)
            bot.collector = collector
            bot.inference_future_window_seconds = 300

            collector_features = collector._extract_features(lifecycle, past_buys, past_sells, sample_time)
            builder_features = builder._extract_features(lifecycle, past_buys, past_sells, sample_time)
            bot_features = bot._extract_lifecycle_features(lifecycle)

        self.assertEqual(builder_features, collector_features)
        self.assertEqual(bot_features, collector_features)

    def test_bot_requests_optional_flow_features_when_loaded_model_schema_requires_them(self):
        from src.trader.bot import MemeBot

        lifecycle = {
            "buys": [],
            "sells": [],
            "last_update": 120,
        }
        collector = MagicMock()
        collector._extract_features.return_value = {"current_price": 1.0, "sell_pressure_10s": 0.8}

        bot = MemeBot.__new__(MemeBot)
        bot.collector = collector
        bot.inference_future_window_seconds = 300
        bot.include_flow_features = True

        features = bot._extract_lifecycle_features(lifecycle)

        self.assertEqual(features["sell_pressure_10s"], 0.8)
        collector._extract_features.assert_called_once_with(
            lifecycle,
            lifecycle["buys"],
            lifecycle["sells"],
            lifecycle["last_update"],
            future_window=300,
            include_flow_features=True,
        )

    def test_bot_load_models_derives_optional_flow_feature_flag_from_schema(self):
        from src.trader.bot import MemeBot

        fake_hybrid = MagicMock()
        fake_hybrid.feature_names = ["current_price", "sell_pressure_10s"]
        fake_hybrid.buy_threshold = 0.98
        fake_hybrid.sell_policy = None

        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "model"
            model_dir.mkdir()
            (model_dir / "buy_model.cbm").write_text("", encoding="utf-8")

            bot = MemeBot.__new__(MemeBot)
            bot.config = {}
            bot.strategy_param_sources = {}

            with patch("src.model.hybrid_inference.HybridModel.load", return_value=fake_hybrid), \
                 patch.object(MemeBot, "_load_model_manifest", return_value={}), \
                 patch.object(MemeBot, "_apply_manifest_runtime_params", return_value=None), \
                 patch.object(MemeBot, "_validate_pred_return_filter_contract", return_value=None), \
                 patch.object(MemeBot, "_validate_entry_value_ranking_contract", return_value=None):
                bot._load_models(model_dir)

        self.assertTrue(bot.include_flow_features)


if __name__ == "__main__":
    unittest.main()
