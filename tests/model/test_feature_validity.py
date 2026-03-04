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

    def test_analyze_feature_columns_flags_pattern_based_invalid_features(self):
        features = [
            "target_buy_signal",
            "label_confidence",
            "future_price_hint",
            "max_return_pct",
            "final_return_pct",
            "min_return_pct",
            "mystery_indicator",
        ]

        result = analyze_feature_columns(features)

        for feature in features[:-1]:
            self.assertEqual(result[feature]["tier"], "invalid")

        self.assertEqual(result["mystery_indicator"]["tier"], "weak")

    def test_analyze_feature_columns_normalizes_case_and_whitespace(self):
        features = [
            " Price_Change_Pct ",
            "CREATOR_ID",
            " Volume_5Min ",
            " Future_Max_Return ",
        ]

        result = analyze_feature_columns(features)

        self.assertEqual(result[" Price_Change_Pct "]["tier"], "effective")
        self.assertEqual(result["CREATOR_ID"]["tier"], "effective")
        self.assertEqual(result[" Volume_5Min "]["tier"], "weak")
        self.assertEqual(result[" Future_Max_Return "]["tier"], "invalid")


if __name__ == "__main__":
    unittest.main()
