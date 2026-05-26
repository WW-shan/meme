import unittest

from src.pipeline import replay_trade_delta_attribution as delta


def _trade(token, signal_time, return_pct, reason="TRAILING_STOP"):
    return {
        "token": token,
        "entry_signal_time": signal_time,
        "entry_time": signal_time + 1,
        "return_pct": return_pct,
        "exit_reason": reason,
    }


def _sample(token, sample_time, buyer_depth, sell_pressure):
    return {
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
        },
        "features": {
            "buyer_depth": buyer_depth,
            "sell_pressure_30s": sell_pressure,
            "future_return_pct": 999.0,
        },
    }


class TestReplayTradeDeltaAttribution(unittest.TestCase):
    def test_build_report_identifies_added_removed_and_worsened_trades(self):
        baseline_trades = [
            _trade("0xaaa", 100, 20.0),
            _trade("0xbbb", 200, -10.0, "STOP_LOSS"),
        ]
        candidate_trades = [
            _trade("0xaaa", 100, 5.0),
            _trade("0xccc", 300, -30.0, "STOP_LOSS"),
        ]
        sample_rows = [
            _sample("0xaaa", 100, 10.0, 0.1),
            _sample("0xbbb", 200, 3.0, 0.8),
            _sample("0xccc", 300, 2.0, 0.9),
        ]

        report = delta.build_trade_delta_attribution_report(
            baseline_trade_rows=baseline_trades,
            candidate_trade_rows=candidate_trades,
            sample_rows=sample_rows,
            top_n=5,
        )

        self.assertEqual(report["contract"]["live_switch_evidence"], False)
        self.assertEqual(report["delta_summary"]["added_candidate_trades"]["trade_count"], 1)
        self.assertEqual(report["delta_summary"]["removed_baseline_trades"]["trade_count"], 1)
        self.assertEqual(report["delta_summary"]["common_trades"]["worsened_count"], 1)
        self.assertEqual(report["added_candidate_trades"][0]["token"], "0xccc")
        self.assertEqual(report["removed_baseline_trades"][0]["token"], "0xbbb")
        self.assertEqual(report["common_trade_deltas"][0]["return_delta_pct"], -15.0)
        added_contrast = report["feature_contrast"]["added_candidate_trades"]
        self.assertEqual(added_contrast["match_summary"]["matched_trade_count"], 1)
        self.assertEqual(added_contrast["feature_summary"]["scanned_features"], ["buyer_depth", "sell_pressure_30s"])


if __name__ == "__main__":
    unittest.main()
