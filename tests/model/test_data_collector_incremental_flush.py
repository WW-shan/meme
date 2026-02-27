import json
import tempfile
import unittest
from pathlib import Path

from src.data.collector import DataCollector


def _create_event(token: str, timestamp: int) -> dict:
    return {
        "timestamp": timestamp,
        "blockNumber": 1,
        "args": {
            "token": token,
            "creator": "0xcreator",
            "name": "Token",
            "symbol": "TKN",
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


class TestDataCollectorIncrementalFlush(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_flush_eligible_tokens_appends_and_evicts(self):
        collector = DataCollector(
            output_dir=str(self.output_dir),
            incremental_run_id="20260227_000000",
        )

        collector.on_token_create(_create_event("0xA", 1000))
        collector.on_token_purchase(_buy_event("0xA", 1010, account="0x1"))

        collector.on_token_create(_create_event("0xB", 1500))
        collector.on_token_purchase(_buy_event("0xB", 1690, account="0x2"))

        flushed = collector.flush_eligible_tokens(
            current_time=1900,
            min_age_seconds=420,
            inactivity_seconds=300,
        )

        self.assertEqual(flushed, 1)
        self.assertNotIn("0xA", collector.token_lifecycle)
        self.assertIn("0xB", collector.token_lifecycle)

        self.assertIsNotNone(collector.incremental_output_file)
        self.assertTrue(collector.incremental_output_file.exists())

        with collector.incremental_output_file.open("r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["token_address"], "0xA")
        self.assertIn("0x1", rows[0]["unique_buyers"])

    def test_flush_eligible_tokens_respects_min_age(self):
        collector = DataCollector(
            output_dir=str(self.output_dir),
            incremental_run_id="20260227_000001",
        )

        collector.on_token_create(_create_event("0xC", 1000))
        collector.on_token_purchase(_buy_event("0xC", 1010, account="0x3"))

        flushed = collector.flush_eligible_tokens(
            current_time=1300,
            min_age_seconds=420,
            inactivity_seconds=60,
        )

        self.assertEqual(flushed, 0)
        self.assertIn("0xC", collector.token_lifecycle)


if __name__ == "__main__":
    unittest.main()
