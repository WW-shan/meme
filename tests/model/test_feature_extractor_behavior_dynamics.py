import unittest

from src.data.feature_extractor import extract_features


class TestFeatureExtractorBehaviorDynamics(unittest.TestCase):
    def test_extract_features_includes_behavior_dynamics_keys(self):
        lifecycle = {
            "create_timestamp": 100,
            "total_supply": 1_000_000 * 10**18,
            "launch_fee": int(0.5 * 10**18),
            "name": "TokenX",
            "symbol": "TKX",
            "creator": "creator",
        }

        past_buys = [
            {"timestamp": 110, "price": 1.0, "account": "a", "bnb_amount": 1.0, "token_amount": 100.0},
            {"timestamp": 120, "price": 1.1, "account": "b", "bnb_amount": 0.2, "token_amount": 20.0},
            {"timestamp": 125, "price": 1.2, "account": "c", "bnb_amount": 0.1, "token_amount": 10.0},
            {"timestamp": 128, "price": 1.3, "account": "a", "bnb_amount": 0.3, "token_amount": 25.0},
        ]
        past_sells = [
            {"timestamp": 127, "price": 1.25, "account": "b", "bnb_amount": 0.05, "token_amount": 5.0},
        ]

        features = extract_features(
            lifecycle=lifecycle,
            past_buys=past_buys,
            past_sells=past_sells,
            sample_time=130,
        )

        required_keys = [
            "top10_holder_share_10s",
            "top10_holder_share_30s",
            "concentration_decay_10_30",
            "retail_entry_rate_ratio_30s",
            "lp_resistance_ratio_10s",
        ]

        for key in required_keys:
            self.assertIn(key, features)
            self.assertIsInstance(features[key], float)


if __name__ == "__main__":
    unittest.main()
