import unittest

from scripts import probe_moonshot_token_level_eval as cli


class TestMoonshotTokenLevelEvalCli(unittest.TestCase):
    def test_output_guard_rejects_tmp_path(self):
        with self.assertRaises(SystemExit):
            cli._assert_output("/tmp/moonshot_token_eval.json", force=True)

    def test_report_shape_for_empty_inputs(self):
        report = cli.build_report([], [], snapshot_seconds=(30, 60, 300), dedupe_policy="max_events")
        self.assertFalse(report["external_api_calls"])
        self.assertEqual(report["decision"], "invalid_input")
        self.assertIn("dedupe", report)
        self.assertIn("token_level_evaluation", report)

    def _lifecycle(self, token, prices):
        return {
            "chain": "bsc",
            "token_address": token.lower(),
            "symbol": "RUN",
            "create_timestamp": 1000,
            "buys": [
                {
                    "timestamp": 1001 + index,
                    "price": price,
                    "bnb_amount": 1.0 + index,
                    "account": f"buyer{index}",
                    "token_amount": 10.0,
                }
                for index, price in enumerate(prices)
            ],
            "sells": [],
        }

    def test_streaming_report_selects_max_events_duplicate_without_materializing_all_lifecycles(self):
        lifecycles = (
            lifecycle
            for lifecycle in [
                self._lifecycle("0xA", [1.0, 8.0]),
                self._lifecycle("0xA", [1.0, 6.0, 12.0]),
            ]
        )

        report = cli.build_report_from_lifecycles(lifecycles, snapshot_seconds=(30, 60, 300), dedupe_policy="max_events")

        self.assertFalse(report["external_api_calls"])
        self.assertEqual(report["dedupe"]["input_row_count"], 2)
        self.assertEqual(report["dedupe"]["output_token_count"], 1)
        self.assertEqual(report["token_level_evaluation"]["token_count"], 1)
        self.assertEqual(report["token_level_evaluation"]["positive_count"], 1)
        self.assertEqual(report["token_level_evaluation"]["split"]["token_overlap"], 0)


if __name__ == "__main__":
    unittest.main()
