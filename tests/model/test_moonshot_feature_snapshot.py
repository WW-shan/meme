import unittest

from src.pipeline import moonshot_feature_snapshot as snapshots
from src.pipeline import moonshot_label_truth as labels


class TestMoonshotFeatureSnapshot(unittest.TestCase):
    def _lifecycle(self):
        return {
            "chain": "bsc",
            "token_address": "0xRun",
            "symbol": "RUN",
            "create_timestamp": 1000,
            "buys": [
                {"timestamp": 1001, "price": 1.0, "bnb_amount": 1.0, "account": "a", "token_amount": 10},
                {"timestamp": 1030, "price": 1.5, "bnb_amount": 2.0, "account": "b", "token_amount": 20},
                {"timestamp": 1050, "price": 2.0, "bnb_amount": 3.0, "account": "a", "token_amount": 30},
                {"timestamp": 1070, "price": 10.0, "bnb_amount": 5.0, "account": "future", "token_amount": 50},
            ],
            "sells": [
                {"timestamp": 1040, "price": 1.4, "bnb_amount": 1.0, "account": "a", "token_amount": 4},
                {"timestamp": 1060, "price": 1.8, "bnb_amount": 0.5, "account": "b", "token_amount": 5},
                {"timestamp": 1080, "price": 12.0, "bnb_amount": 6.0, "account": "future", "token_amount": 60},
            ],
        }

    def test_build_local_snapshot_uses_only_visible_events(self):
        features = snapshots.build_local_snapshot(self._lifecycle(), snapshot_time=1060)

        self.assertEqual(features["token_age_seconds"], 60)
        self.assertEqual(features["buy_count_60s"], 3)
        self.assertEqual(features["sell_count_60s"], 2)
        self.assertEqual(features["buy_volume_60s"], 6.0)
        self.assertEqual(features["unique_buyers_60s"], 2)
        self.assertEqual(features["sell_pressure_60s"], 0.2)
        self.assertAlmostEqual(features["price_change_60s_pct"], 80.0)
        self.assertEqual(features["buy_volume_300s"], 6.0)
        self.assertEqual(features["unique_buyers_300s"], 2)
        self.assertAlmostEqual(features["price_change_300s_pct"], 80.0)
        self.assertNotIn("max_observed_price", features)
        self.assertNotIn("max_multiple", features)
        self.assertNotIn("hit_10x", features)
        self.assertNotIn("time_to_10x", features)

    def test_external_attention_defaults_are_explicit(self):
        defaults = snapshots.empty_external_attention_features()

        self.assertEqual(
            defaults,
            {
                "dexscreener_has_profile": False,
                "dexscreener_active_boosts": 0,
                "dexscreener_has_cto": False,
                "x_mentions_15m": 0,
                "x_unique_accounts_15m": 0,
                "x_high_signal_mentions_15m": 0,
                "gmgn_smart_money_buy_count": None,
                "gmgn_kol_buy_count": None,
                "coingecko_gt_suspicious_report": None,
            },
        )

    def test_build_snapshot_row_keeps_label_separate_from_features(self):
        label, reject = labels.extract_local_lifecycle_label(
            self._lifecycle(),
            source_fetched_at="2026-06-09T00:00:00Z",
        )

        row = snapshots.build_snapshot_row(self._lifecycle(), label, snapshot_time=1060)

        self.assertIsNone(reject)
        self.assertEqual(row["token_address"], "0xrun")
        self.assertEqual(row["snapshot_time"], 1060)
        self.assertIn("label", row)
        self.assertTrue(row["label"]["hit_10x"])
        self.assertNotIn("hit_10x", row["features"])
        self.assertEqual([], snapshots.validate_snapshot_no_future_fields(row))

        row["features"]["max_multiple"] = 10.0
        self.assertEqual(["features.max_multiple"], snapshots.validate_snapshot_no_future_fields(row))


if __name__ == "__main__":
    unittest.main()
