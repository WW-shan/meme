import unittest

from src.pipeline import moonshot_token_level_eval as token_eval


class TestMoonshotTokenLevelEval(unittest.TestCase):
    def _label(self, token, multiple, event_count, launch_time=1000):
        return {
            "chain": "bsc",
            "token_address": token.lower(),
            "launch_time": launch_time,
            "first_observed_price": 1.0,
            "max_observed_price": float(multiple),
            "max_multiple": float(multiple),
            "hit_10x": float(multiple) >= 10.0,
            "source": "local_lifecycle",
            "_event_count": int(event_count),
        }

    def test_dedupe_policy_max_events_chooses_most_complete_lifecycle(self):
        rows = [self._label("0xA", 8.0, 2), self._label("0xA", 12.0, 5)]
        selected, summary = token_eval.dedupe_label_rows(rows, policy="max_events")
        self.assertEqual(selected[0]["token_address"], "0xa")
        self.assertEqual(selected[0]["max_multiple"], 12.0)
        self.assertEqual(summary["duplicate_token_count"], 1)
        self.assertEqual(summary["policy"], "max_events")

    def test_dedupe_sensitivity_reports_optimistic_and_conservative_counts(self):
        rows = [self._label("0xA", 8.0, 2), self._label("0xA", 12.0, 5), self._label("0xB", 11.0, 1)]
        summary = token_eval.dedupe_sensitivity(rows)
        self.assertEqual(summary["max_multiple"][">=10x"], 2)
        self.assertEqual(summary["min_multiple"][">=10x"], 1)
        self.assertEqual(summary["max_events"][">=10x"], 2)

    def _snapshot(self, token, score, hit, launch_time, snapshot_time):
        return {
            "chain": "bsc",
            "token_address": token.lower(),
            "snapshot_time": snapshot_time,
            "features": {"buy_volume_300s": score, "unique_buyers_300s": score},
            "label": {"hit_10x": bool(hit), "launch_time": launch_time},
            "_score": float(score),
        }

    def test_collapse_snapshots_keeps_one_candidate_per_token(self):
        rows = [self._snapshot("0xA", 1, False, 1000, 1030), self._snapshot("0xA", 5, False, 1000, 1300)]
        collapsed = token_eval.collapse_snapshots_to_tokens(rows, score_key="_score")
        self.assertEqual(len(collapsed), 1)
        self.assertEqual(collapsed[0]["token_address"], "0xa")
        self.assertEqual(collapsed[0]["chosen_snapshot_time"], 1300)

    def test_group_time_split_has_zero_token_overlap(self):
        rows = [self._snapshot(f"0x{i}", i, i == 4, 1000 + i, 1100 + i) for i in range(5)]
        train, validation, split = token_eval.group_time_split(rows, validation_ratio=0.4)
        self.assertEqual(split["token_overlap"], 0)
        self.assertEqual(len(train), 3)
        self.assertEqual(len(validation), 2)

    def test_evaluate_token_level_reports_validation_metrics(self):
        rows = [self._snapshot(f"0x{i}", 10 - i, i in (0, 1), 1000 + i, 1100 + i) for i in range(10)]
        report = token_eval.evaluate_token_level(rows, top_k_values=(3,))
        self.assertEqual(report["decision"], "research_baseline_only")
        self.assertEqual(report["token_count"], 10)
        self.assertEqual(report["positive_count"], 2)
        self.assertEqual(report["split"]["token_overlap"], 0)
        self.assertIn("precision_at_3", report["metrics"])


if __name__ == "__main__":
    unittest.main()
