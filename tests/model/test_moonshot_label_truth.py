import unittest

from src.pipeline import moonshot_label_truth as labels


class TestMoonshotLabelTruth(unittest.TestCase):
    def _lifecycle(self, token_address, *, create_timestamp=1000, buys=None, sells=None):
        return {
            "token_address": token_address,
            "symbol": "RUN",
            "name": "Runner",
            "create_timestamp": create_timestamp,
            "buys": list(buys or []),
            "sells": list(sells or []),
        }

    def test_extracts_local_lifecycle_threshold_labels(self):
        lifecycle = self._lifecycle(
            "0xAaA",
            create_timestamp=1000,
            buys=[
                {"timestamp": 1001, "price": 1.0, "bnb_amount": 1.0, "account": "a"},
                {"timestamp": 1010, "price": 5.0, "bnb_amount": 2.0, "account": "b"},
                {"timestamp": 1020, "price": 10.0, "bnb_amount": 3.0, "account": "c"},
                {"timestamp": 1030, "price": 12.0, "bnb_amount": 4.0, "account": "d"},
            ],
        )

        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at="2026-06-09T00:00:00Z")
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["chain"], "bsc")
        self.assertEqual(data["token_address"], "0xaaa")
        self.assertEqual(data["launch_time"], 1000)
        self.assertEqual(data["first_observed_price"], 1.0)
        self.assertEqual(data["max_observed_price"], 12.0)
        self.assertEqual(data["max_multiple"], 12.0)
        self.assertTrue(data["hit_2x"])
        self.assertTrue(data["hit_5x"])
        self.assertTrue(data["hit_10x"])
        self.assertFalse(data["hit_20x"])
        self.assertEqual(data["time_to_2x"], 1010)
        self.assertEqual(data["time_to_5x"], 1010)
        self.assertEqual(data["time_to_10x"], 1020)
        self.assertIsNone(data["time_to_20x"])
        self.assertEqual(data["source"], "local_lifecycle")
        self.assertEqual(data["source_fetched_at"], "2026-06-09T00:00:00Z")

    def test_extracts_local_lifecycle_non_runner(self):
        lifecycle = self._lifecycle(
            "0xBbB",
            create_timestamp=2000,
            buys=[
                {"timestamp": 2001, "price": 2.0, "bnb_amount": 1.0, "account": "a"},
                {"timestamp": 2010, "price": 3.0, "bnb_amount": 1.0, "account": "b"},
            ],
        )

        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at="2026-06-09T00:00:00Z")
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["max_multiple"], 1.5)
        self.assertFalse(data["hit_2x"])
        self.assertFalse(data["hit_10x"])
        self.assertIsNone(data["time_to_2x"])
        self.assertIsNone(data["time_to_10x"])

    def test_rejects_lifecycle_without_valid_first_price(self):
        lifecycle = self._lifecycle(
            "0xCcC",
            create_timestamp=3000,
            buys=[
                {"timestamp": 3001, "price": 0.0, "bnb_amount": 1.0, "account": "a"},
                {"timestamp": 3002, "price": -1.0, "bnb_amount": 1.0, "account": "b"},
            ],
        )

        row, reject = labels.extract_local_lifecycle_label(lifecycle, source_fetched_at="2026-06-09T00:00:00Z")

        self.assertIsNone(row)
        self.assertEqual(reject.reason, "missing_first_price")
        self.assertEqual(reject.token_address, "0xccc")

    def test_label_report_counts_thresholds_and_rejects(self):
        runner, _ = labels.extract_local_lifecycle_label(
            self._lifecycle(
                "0xAaA",
                buys=[
                    {"timestamp": 1001, "price": 1.0},
                    {"timestamp": 1002, "price": 12.0},
                ],
            )
        )
        weak, _ = labels.extract_local_lifecycle_label(
            self._lifecycle(
                "0xBbB",
                buys=[
                    {"timestamp": 1001, "price": 2.0},
                    {"timestamp": 1002, "price": 3.0},
                ],
            )
        )
        _, reject = labels.extract_local_lifecycle_label(self._lifecycle("0xCcC", buys=[]))

        report = labels.label_report([runner, weak], [reject])

        self.assertEqual(report["summary"]["accepted_count"], 2)
        self.assertEqual(report["summary"]["reject_count"], 1)
        self.assertEqual(report["threshold_counts"][">=2x"], 1)
        self.assertEqual(report["threshold_counts"][">=5x"], 1)
        self.assertEqual(report["threshold_counts"][">=10x"], 1)
        self.assertEqual(report["threshold_counts"][">=20x"], 0)
        self.assertEqual(report["rejects"][0]["reason"], "missing_first_price")

    def test_normalizes_external_label_export(self):
        row, reject = labels.normalize_external_label(
            {
                "chain": "bsc",
                "token_address": "0xAbC",
                "pair_address": "0xPair",
                "launch_time": "2026-01-01T00:00:00Z",
                "first_observed_price": "0.001",
                "max_observed_price": "0.055",
                "migration_time": "2026-01-01T00:12:00Z",
                "evidence_url": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
                "source": "bitquery_export",
                "source_fetched_at": "2026-06-09T00:00:00Z",
            }
        )
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["token_address"], "0xabc")
        self.assertEqual(data["pair_address"], "0xpair")
        self.assertEqual(data["max_multiple"], 55.0)
        self.assertTrue(data["hit_20x"])
        self.assertTrue(data["hit_50x"])
        self.assertFalse(data["hit_100x"])
        self.assertEqual(data["evidence_url"], "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/")
        self.assertEqual(data["source"], "bitquery_export")

    def test_normalizes_bitquery_style_external_export(self):
        row, reject = labels.normalize_external_label_export(
            {
                "network": "BSC",
                "tokenAddress": "0xBitQuery",
                "pairAddress": "0xPair",
                "launchTimestamp": "2026-01-01T00:00:00Z",
                "initialPriceUsd": "0.001",
                "athPriceUsd": "0.12",
                "migrationTimestamp": "2026-01-01T00:15:00Z",
                "sourceUrl": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
                "exportedAt": "2026-06-09T00:00:00Z",
            },
            source_hint="bitquery",
        )
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["chain"], "bsc")
        self.assertEqual(data["token_address"], "0xbitquery")
        self.assertEqual(data["pair_address"], "0xpair")
        self.assertEqual(data["max_multiple"], 120.0)
        self.assertTrue(data["hit_100x"])
        self.assertEqual(data["migration_time"], "2026-01-01T00:15:00Z")
        self.assertEqual(data["source"], "bitquery_export")
        self.assertEqual(data["provenance"][0]["source_format"], "bitquery")

    def test_normalizes_raw_source_name_to_canonical_export_source(self):
        row, reject = labels.normalize_external_label_export(
            {
                "source": "Bitquery",
                "tokenAddress": "0xBitQuery",
                "launchTimestamp": "2026-01-01T00:00:00Z",
                "initialPriceUsd": "0.001",
                "athPriceUsd": "0.12",
                "sourceUrl": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
                "exportedAt": "2026-06-09T00:00:00Z",
            },
            source_hint="external_labels",
        )
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["source"], "bitquery_export")

    def test_normalizes_codex_style_external_export_with_nested_token(self):
        row, reject = labels.normalize_external_label_export(
            {
                "chain": "bsc",
                "token": {"address": "0xCodex"},
                "pair": {"address": "0xPair"},
                "createdAt": "2026-01-01T00:00:00Z",
                "startPriceUsd": "0.01",
                "maxPriceUsd": "0.55",
                "url": "https://docs.codex.io/launchpads/four-meme",
                "fetchedAt": "2026-06-09T00:00:00Z",
            },
            source_hint="codex",
        )
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["token_address"], "0xcodex")
        self.assertEqual(data["pair_address"], "0xpair")
        self.assertEqual(data["max_multiple"], 55.0)
        self.assertEqual(data["source"], "codex_export")

    def test_normalizes_cmc_style_external_export(self):
        row, reject = labels.normalize_external_label_export(
            {
                "platform": "BNB Smart Chain",
                "contract_address": "0xCmc",
                "launch_date": "2026-01-01T00:00:00Z",
                "first_price_usd": "0.002",
                "all_time_high_price_usd": "0.08",
                "article_url": "https://coinmarketcap.com/cmc-ai/bianrensheng/what-is",
                "observed_at": "2026-06-09T00:00:00Z",
            },
            source_hint="cmc",
        )
        data = row.to_dict()

        self.assertIsNone(reject)
        self.assertEqual(data["chain"], "bsc")
        self.assertEqual(data["token_address"], "0xcmc")
        self.assertEqual(data["max_multiple"], 40.0)
        self.assertTrue(data["hit_20x"])
        self.assertEqual(data["source"], "cmc_export")

    def test_rejects_external_label_without_evidence_url(self):
        row, reject = labels.normalize_external_label(
            {
                "chain": "bsc",
                "token_address": "0xAbC",
                "launch_time": "2026-01-01T00:00:00Z",
                "first_observed_price": "0.001",
                "max_observed_price": "0.055",
                "source": "codex_export",
                "source_fetched_at": "2026-06-09T00:00:00Z",
            }
        )

        self.assertIsNone(row)
        self.assertEqual(reject.reason, "missing_evidence_url")
        self.assertEqual(reject.token_address, "0xabc")

    def test_rejects_external_label_with_invalid_source_timestamp(self):
        row, reject = labels.normalize_external_label(
            {
                "chain": "bsc",
                "token_address": "0xAbC",
                "launch_time": "2026-01-01T00:00:00Z",
                "first_observed_price": "0.001",
                "max_observed_price": "0.055",
                "evidence_url": "https://docs.codex.io/launchpads/four-meme",
                "source": "codex_export",
                "source_fetched_at": "2025-12-31T23:59:00Z",
            }
        )

        self.assertIsNone(row)
        self.assertEqual(reject.reason, "invalid_source_timestamp")

    def test_merges_label_rows_with_provenance_and_disagreement_warning(self):
        local, _ = labels.extract_local_lifecycle_label(
            self._lifecycle(
                "0xAbC",
                buys=[
                    {"timestamp": 1001, "price": 1.0},
                    {"timestamp": 1002, "price": 10.0},
                ],
            ),
            source_fetched_at="2026-06-09T00:00:00Z",
        )
        external, _ = labels.normalize_external_label(
            {
                "chain": "bsc",
                "token_address": "0xAbC",
                "launch_time": "2026-01-01T00:00:00Z",
                "first_observed_price": "1.0",
                "max_observed_price": "20.0",
                "evidence_url": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
                "source": "bitquery_export",
                "source_fetched_at": "2026-06-09T00:00:00Z",
            }
        )

        merged, warnings = labels.merge_label_rows([local], [external])
        data = merged[0].to_dict()

        self.assertEqual(len(merged), 1)
        self.assertEqual(data["max_multiple"], 20.0)
        self.assertEqual(len(data["provenance"]), 2)
        self.assertEqual(warnings[0]["reason"], "label_source_disagreement")

    def test_merges_duplicate_local_rows_by_highest_multiple(self):
        weak, _ = labels.extract_local_lifecycle_label(
            self._lifecycle(
                "0xDup",
                buys=[
                    {"timestamp": 1001, "price": 1.0},
                    {"timestamp": 1002, "price": 2.0},
                ],
            ),
            source_fetched_at="2026-06-09T00:00:00Z",
        )
        strong, _ = labels.extract_local_lifecycle_label(
            self._lifecycle(
                "0xDup",
                buys=[
                    {"timestamp": 1001, "price": 1.0},
                    {"timestamp": 1002, "price": 12.0},
                ],
            ),
            source_fetched_at="2026-06-09T00:00:01Z",
        )

        merged, warnings = labels.merge_label_rows([weak, strong], [])
        data = merged[0].to_dict()

        self.assertEqual(len(merged), 1)
        self.assertEqual(data["max_multiple"], 12.0)
        self.assertTrue(data["hit_10x"])
        self.assertEqual(len(data["provenance"]), 2)
        self.assertEqual(warnings[0]["reason"], "label_source_disagreement")

    def test_label_report_counts_sources_and_reject_reasons(self):
        bitquery, _ = labels.normalize_external_label_export(
            {
                "tokenAddress": "0xBitQuery",
                "launchTimestamp": "2026-01-01T00:00:00Z",
                "initialPriceUsd": "0.001",
                "athPriceUsd": "0.12",
                "sourceUrl": "https://docs.bitquery.io/docs/blockchain/BSC/four-meme-api/",
                "exportedAt": "2026-06-09T00:00:00Z",
            },
            source_hint="bitquery",
        )
        _, reject = labels.normalize_external_label_export(
            {
                "tokenAddress": "0xReject",
                "launchTimestamp": "2026-01-01T00:00:00Z",
                "initialPriceUsd": "0.001",
                "athPriceUsd": "0.12",
                "exportedAt": "2026-06-09T00:00:00Z",
            },
            source_hint="bitquery",
        )

        report = labels.label_report([bitquery], [reject])

        self.assertEqual(report["source_counts"]["bitquery_export"], 1)
        self.assertEqual(report["reject_reason_counts"]["missing_evidence_url"], 1)


if __name__ == "__main__":
    unittest.main()
