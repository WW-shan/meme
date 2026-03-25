import json
import tempfile
import unittest
from pathlib import Path

from src.data.collector import DataCollector


def _create_event(token: str, timestamp: int, symbol: str = "TKN") -> dict:
    return {
        "timestamp": timestamp,
        "blockNumber": 1,
        "logIndex": 0,
        "transactionHash": b"\x01" * 32,
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
        "logIndex": 1,
        "transactionHash": b"\x02" * 32,
        "args": {
            "token": token,
            "account": account,
            "amount": int(100 * 1e18),
            "cost": int(1 * 1e18),
        },
    }


def _write_lifecycle(path: Path, token: str, symbol: str = "TKN", accounts=None):
    accounts = accounts or ["0x1"]
    buys = []
    price_history = []
    for index, account in enumerate(accounts, start=1):
        timestamp = 1000 + index * 10
        buys.append(
            {
                "timestamp": timestamp,
                "account": account,
                "token_amount": 100.0,
                "bnb_amount": 1.0,
                "price": 0.01,
            }
        )
        price_history.append(
            {
                "timestamp": timestamp,
                "price": 0.01,
                "type": "buy",
            }
        )

    lifecycle = {
        "token_address": token,
        "creator": "0xcreator",
        "name": "Token",
        "symbol": symbol,
        "total_supply": float(int(1_000_000 * 1e18)),
        "launch_fee": float(int(0.01 * 1e18)),
        "launch_time": 1000,
        "create_timestamp": 1000,
        "create_block": 1,
        "buys": buys,
        "sells": [],
        "price_history": price_history,
        "total_buy_volume_bnb": float(len(buys)),
        "total_sell_volume_bnb": 0.0,
        "total_buy_count": len(buys),
        "total_sell_count": 0,
        "unique_buyers": accounts,
        "unique_sellers": [],
        "volume_1min": float(len(buys)),
        "volume_5min": float(len(buys)),
        "volume_15min": float(len(buys)),
        "volume_30min": float(len(buys)),
        "volume_1h": float(len(buys)),
        "price_max": 0.01,
        "price_min": 0.01,
        "price_current": 0.01,
        "price_first": 0.01,
        "graduated": False,
        "graduate_time": None,
        "last_update": buys[-1]["timestamp"] if buys else 1000,
    }

    with path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(lifecycle, ensure_ascii=False) + "\n")


class TestDataCollectorRuntimeState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_bootstrap_metadata_from_lifecycle_files_supports_restart_reactivation(self):
        token = "0xAAA"
        _write_lifecycle(
            self.output_dir / "lifecycle_incremental_20260325_010000.jsonl",
            token=token,
            symbol="AAA",
            accounts=["0x1", "0x2"],
        )

        collector = DataCollector(output_dir=str(self.output_dir), incremental_run_id="20260325_020000")

        loaded = collector.load_token_metadata_from_lifecycle_files()

        self.assertEqual(loaded, 1)
        self.assertIn(token, collector.token_metadata)
        self.assertNotIn(token, collector.token_lifecycle)

        collector.on_token_purchase(_buy_event(token, 2000, account="0x3"))

        self.assertIn(token, collector.token_lifecycle)
        lifecycle = collector.token_lifecycle[token]
        self.assertEqual(lifecycle["symbol"], "AAA")
        self.assertEqual(len(lifecycle["buys"]), 1)
        self.assertEqual(lifecycle["buys"][0]["account"], "0x3")

    def test_save_and_restore_runtime_state_round_trips_active_tokens_and_checkpoint(self):
        token = "0xBBB"
        state_file = self.output_dir / "collector_runtime_state.json"

        collector = DataCollector(output_dir=str(self.output_dir), incremental_run_id="20260325_030000")
        collector.on_token_create(_create_event(token, 1000, symbol="BBB"))
        collector.on_token_purchase(_buy_event(token, 1010, account="0x1"))

        self.assertEqual(
            {"block_number": 2, "log_index": 1, "tx_hash": "02" * 32},
            collector.get_applied_cursor(),
        )

        saved_path = collector.save_runtime_state(state_file)

        self.assertEqual(saved_path, state_file)
        self.assertTrue(state_file.exists())

        restored = DataCollector(output_dir=str(self.output_dir), incremental_run_id="20260325_040000")
        applied_cursor = restored.restore_runtime_state(state_file)

        self.assertEqual({"block_number": 2, "log_index": 1, "tx_hash": "02" * 32}, applied_cursor)
        self.assertIn(token, restored.token_lifecycle)
        self.assertIn(token, restored.token_metadata)
        self.assertEqual(restored.token_lifecycle[token]["symbol"], "BBB")
        self.assertIsInstance(restored.token_lifecycle[token]["unique_buyers"], set)
        self.assertIn("0x1", restored.token_lifecycle[token]["unique_buyers"])


if __name__ == "__main__":
    unittest.main()
