import tempfile
import unittest


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


if __name__ == "__main__":
    unittest.main()
