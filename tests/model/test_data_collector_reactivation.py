import tempfile
import unittest

from src.data.collector import DataCollector


def _create_event(token: str, timestamp: int, symbol: str = "TKN") -> dict:
    return {
        "timestamp": timestamp,
        "blockNumber": 1,
        "args": {
            "token": token,
            "creator": "0xcreator",
            "name": "Token",
            "symbol": symbol,
            "totalSupply": int(1_000_000 * 1e18),
            "launchFee": int(0.01 * 1e18),
            "launchTime": timestamp,
        },
    }


def _buy_event(token: str, timestamp: int, account: str = "0xbuyer") -> dict:
    return {
        "timestamp": timestamp,
        "blockNumber": 2,
        "args": {
            "token": token,
            "account": account,
            "amount": int(100 * 1e18),
            "cost": int(1 * 1e18),
        },
    }


class TestDataCollectorReactivation(unittest.TestCase):
    def test_token_reactivates_after_flush(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = DataCollector(output_dir=tmpdir, incremental_run_id="20260227_010000")

            token = "0xAAA"
            collector.on_token_create(_create_event(token, 1000, symbol="AAA"))
            collector.on_token_purchase(_buy_event(token, 1010, account="0x1"))

            flushed = collector.flush_eligible_tokens(
                current_time=1900,
                min_age_seconds=300,
                inactivity_seconds=300,
            )
            self.assertEqual(flushed, 1)
            self.assertNotIn(token, collector.token_lifecycle)

            # Same token becomes active again later: should rehydrate from metadata
            collector.on_token_purchase(_buy_event(token, 2000, account="0x2"))

            self.assertIn(token, collector.token_lifecycle)
            lifecycle = collector.token_lifecycle[token]
            self.assertEqual(lifecycle["symbol"], "AAA")
            self.assertEqual(len(lifecycle["buys"]), 1)
            self.assertEqual(lifecycle["buys"][0]["account"], "0x2")


if __name__ == "__main__":
    unittest.main()
