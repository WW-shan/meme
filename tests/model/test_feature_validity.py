import unittest

from src.features.feature_validity import analyze_feature_columns


class TestFeatureValidity(unittest.TestCase):
    def test_analyze_feature_columns_assigns_tiers(self):
        features = [
            "price_change_pct",
            "creator_id",
            "volume_5min",
            "future_max_return",
        ]

        result = analyze_feature_columns(features)

        self.assertEqual(set(result.keys()), set(features))

        for feature in features:
            self.assertIn("tier", result[feature])
            self.assertIn("reason", result[feature])
            self.assertIsInstance(result[feature]["reason"], str)
            self.assertTrue(result[feature]["reason"].strip())

        self.assertEqual(result["price_change_pct"]["tier"], "effective")
        self.assertEqual(result["creator_id"]["tier"], "effective")
        self.assertEqual(result["volume_5min"]["tier"], "weak")
        self.assertEqual(result["future_max_return"]["tier"], "invalid")


if __name__ == "__main__":
    unittest.main()
