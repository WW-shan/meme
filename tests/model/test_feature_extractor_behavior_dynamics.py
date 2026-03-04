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

    def test_extract_features_behavior_dynamics_formula_contract(self):
        lifecycle = {
            "create_timestamp": 0,
            "total_supply": 1_000_000 * 10**18,
            "launch_fee": int(8.0 * 10**18),
            "name": "TokenY",
            "symbol": "TKY",
            "creator": "creator",
        }

        recent_buys = [
            {
                "timestamp": 95,
                "price": 1.0,
                "account": f"r{i}",
                "bnb_amount": 1.0,
                "token_amount": 10.0,
            }
            for i in range(12)
        ]
        older_buys = [
            {
                "timestamp": 80,
                "price": 1.0,
                "account": f"o{i}",
                "bnb_amount": 1.0,
                "token_amount": 10.0,
            }
            for i in range(18)
        ]
        past_buys = recent_buys + older_buys
        past_sells = [
            {"timestamp": 96, "price": 1.0, "account": "s1", "bnb_amount": 2.0, "token_amount": 1.0},
            {"timestamp": 97, "price": 1.0, "account": "s2", "bnb_amount": 2.0, "token_amount": 1.0},
        ]

        features = extract_features(
            lifecycle=lifecycle,
            past_buys=past_buys,
            past_sells=past_sells,
            sample_time=100,
        )

        expected_top10_10s = 100.0 / 120.0
        expected_top10_30s = 100.0 / 300.0
        expected_concentration_decay = (expected_top10_10s - expected_top10_30s) / 20.0

        expected_unique_buyer_slope = (30.0 - 12.0) / 20.0
        expected_volume_slope = (30.0 - 12.0) / 20.0
        expected_retail_entry_rate_ratio = expected_unique_buyer_slope / max(expected_volume_slope, 1e-9)

        expected_lp_depth_proxy = 8.0 + 12.0
        expected_recent_sell_pressure = 4.0
        expected_lp_resistance_ratio = expected_lp_depth_proxy / max(expected_recent_sell_pressure, 1e-9)

        self.assertAlmostEqual(features["top10_holder_share_10s"], expected_top10_10s, places=12)
        self.assertAlmostEqual(features["top10_holder_share_30s"], expected_top10_30s, places=12)
        self.assertAlmostEqual(features["concentration_decay_10_30"], expected_concentration_decay, places=12)
        self.assertAlmostEqual(features["retail_entry_rate_ratio_30s"], expected_retail_entry_rate_ratio, places=12)
        self.assertAlmostEqual(features["lp_resistance_ratio_10s"], expected_lp_resistance_ratio, places=12)


if __name__ == "__main__":
    unittest.main()
