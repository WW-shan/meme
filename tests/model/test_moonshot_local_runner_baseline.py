import unittest

from src.pipeline import moonshot_local_runner_baseline as baseline


class TestMoonshotLocalRunnerBaseline(unittest.TestCase):
    def _row(self, token_address, features, *, hit_10x=False, snapshot_time=1000):
        return {
            "chain": "bsc",
            "token_address": token_address,
            "snapshot_time": snapshot_time,
            "features": dict(features),
            "label": {"hit_10x": bool(hit_10x)},
        }

    def test_score_snapshot_ranks_runner_shape_above_flat_and_collapse(self):
        high_runner = self._row(
            "0xhigh",
            {
                "buy_volume_60s": 8.0,
                "buy_volume_300s": 30.0,
                "unique_buyers_60s": 10,
                "unique_buyers_300s": 28,
                "price_change_300s_pct": 220.0,
                "sell_pressure_60s": 0.15,
                "sell_pressure_300s": 0.20,
                "top_holder_concentration": 0.25,
            },
        )
        flat = self._row(
            "0xflat",
            {
                "buy_volume_60s": 0.4,
                "buy_volume_300s": 2.0,
                "unique_buyers_60s": 1,
                "unique_buyers_300s": 2,
                "price_change_300s_pct": 0.0,
                "sell_pressure_60s": 0.05,
                "sell_pressure_300s": 0.10,
                "top_holder_concentration": 0.80,
            },
        )
        collapse = self._row(
            "0xcollapse",
            {
                "buy_volume_60s": 20.0,
                "buy_volume_300s": 45.0,
                "unique_buyers_60s": 2,
                "unique_buyers_300s": 3,
                "price_change_300s_pct": -50.0,
                "sell_pressure_60s": 0.90,
                "sell_pressure_300s": 0.85,
                "top_holder_concentration": 0.92,
            },
        )

        high_score = baseline.score_snapshot(high_runner)
        flat_score = baseline.score_snapshot(flat)
        collapse_score = baseline.score_snapshot(collapse)

        self.assertGreater(high_score["score"], flat_score["score"])
        self.assertGreater(high_score["score"], collapse_score["score"])
        self.assertEqual(high_score, baseline.score_snapshot(high_runner))
        self.assertIn("buy_volume_300s", high_score["components"])
        self.assertIn("sell_pressure_300s", high_score["components"])

    def test_rank_metrics_use_top_k_precision_and_base_rate_lift(self):
        rows = [
            self._row(f"0x{i}", {}, hit_10x=i in (0, 1), snapshot_time=1000 + i)
            for i in range(10)
        ]
        scores = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

        precision = baseline.precision_at_k(rows, scores, k=3)
        lift = baseline.lift_at_k(rows, scores, k=3)

        self.assertAlmostEqual(precision, 2 / 3)
        self.assertAlmostEqual(lift, (2 / 3) / 0.2)

    def test_evaluate_baseline_returns_insufficient_support_for_zero_positives(self):
        rows = [
            self._row(f"0x{i}", {"buy_volume_300s": float(i)}, hit_10x=False, snapshot_time=1000 + i)
            for i in range(8)
        ]

        report = baseline.evaluate_baseline(rows, top_k_values=(3,))

        self.assertEqual(report["decision"], "insufficient_positive_support")
        self.assertEqual(report["positive_count"], 0)
        self.assertEqual(report["base_positive_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
