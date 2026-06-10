import unittest
from pathlib import Path

from src.pipeline import moonshot_label_truth as labels


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "moonshot_external_labels"


class TestMoonshotExternalLabelFixtures(unittest.TestCase):
    def test_loads_mixed_external_export_fixtures_with_source_profiles(self):
        rows, rejects = labels.load_external_label_exports(
            [
                FIXTURE_DIR / "bitquery_fourmeme.jsonl",
                FIXTURE_DIR / "codex_launchpad.json",
                FIXTURE_DIR / "coingecko_fourmeme.json",
                FIXTURE_DIR / "cmc_rejects.csv",
            ]
        )
        report = labels.label_report(rows, rejects)

        self.assertEqual(report["summary"]["accepted_count"], 3)
        self.assertEqual(report["summary"]["reject_count"], 1)
        self.assertEqual(report["source_counts"], {
            "bitquery_export": 1,
            "codex_export": 1,
            "coingecko_export": 1,
        })
        self.assertEqual(report["reject_reason_counts"], {"missing_evidence_url": 1})
        self.assertEqual(report["threshold_counts"][">=50x"], 2)
        self.assertEqual(report["threshold_counts"][">=100x"], 1)

        by_source = {row.source: row.to_dict() for row in rows}
        self.assertEqual(by_source["bitquery_export"]["source_profile"], "bitquery_fourmeme")
        self.assertEqual(by_source["codex_export"]["source_profile"], "codex_launchpad")
        self.assertEqual(by_source["coingecko_export"]["source_profile"], "coingecko_fourmeme")
        self.assertEqual(by_source["coingecko_export"]["token_address"], "0x0000000000000000000000000000000000009e00")
        self.assertEqual(by_source["coingecko_export"]["pair_address"], "0x0000000000000000000000000000000000009ec1")
        self.assertEqual(by_source["coingecko_export"]["max_multiple"], 60.0)

    def test_source_profile_describes_required_fields_and_aliases(self):
        bitquery = labels.external_source_profile("bitquery_fourmeme")
        codex = labels.external_source_profile("codex_launchpad")
        coingecko = labels.external_source_profile("coingecko_fourmeme")

        self.assertEqual(bitquery["source"], "bitquery_export")
        self.assertIn("tokenAddress", bitquery["aliases"]["token_address"])
        self.assertIn("token.address", codex["aliases"]["token_address"])
        self.assertIn("data.attributes.address", coingecko["aliases"]["token_address"])
        self.assertIn("data.attributes.ath_price_usd", coingecko["aliases"]["max_observed_price"])
        self.assertIn("evidence_url", coingecko["required"])

    def test_unknown_source_profile_falls_back_to_external_export(self):
        profile = labels.external_source_profile("custom_vendor")

        self.assertEqual(profile["source"], "external_export")
        self.assertEqual(profile["source_profile"], "custom_vendor")
        self.assertIn("token_address", profile["aliases"])


if __name__ == "__main__":
    unittest.main()
