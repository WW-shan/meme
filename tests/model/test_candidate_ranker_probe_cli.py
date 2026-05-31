import contextlib
import importlib.util
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_candidate_ranker_probe.py"
    spec = importlib.util.spec_from_file_location("run_candidate_ranker_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCandidateRankerProbeCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args(["--model-dir", "data/models/example"])

        self.assertEqual(args.model_dir, "data/models/example")
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.output, "data/replay_reports/v96_candidate_ranker_probe_20260519.json")
        self.assertEqual(args.train_split_ratio, 0.60)
        self.assertEqual(args.validation_split_ratio, 0.20)
        self.assertEqual(args.max_samples_per_token, 120)
        self.assertEqual(args.sample_cache_dir, ".cache/model_replay")
        self.assertEqual(args.top_k_per_group, 1)
        self.assertEqual(args.relevance_mode, "tiered_runner")
        self.assertIsNone(args.max_lifecycle_files)
        self.assertIsNone(args.lifecycle_file)
        self.assertFalse(args.include_shadow_score_rejects)
        self.assertIsNone(args.shadow_min_prob)
        self.assertIsNone(args.shadow_max_entry_score)
        self.assertIsNone(args.shadow_min_entry_volume_30s)
        self.assertIsNone(args.shadow_min_entry_price_volatility)
        self.assertIsNone(args.shadow_max_age_seconds)

    def test_main_calls_probe_and_prints_json(self):
        cli = _load_cli()
        fake_module = types.ModuleType("src.pipeline.candidate_ranker_probe")
        fake_module.run_candidate_ranker_probe = lambda **kwargs: {"decision": "reject"}

        with patch.dict(sys.modules, {"src.pipeline.candidate_ranker_probe": fake_module}):
            with patch.object(fake_module, "run_candidate_ranker_probe", return_value={"decision": "reject"}) as mock_run:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    result = cli.main(
                        [
                            "--model-dir",
                            "data/models/example",
                            "--output",
                            "data/replay_reports/out.json",
                            "--no-cache",
                            "--top-k-per-group",
                            "2",
                            "--relevance-mode",
                            "risk_adjusted_return",
                            "--include-shadow-score-rejects",
                            "--shadow-min-prob",
                            "0.985",
                            "--shadow-max-entry-score",
                            "10",
                            "--shadow-min-entry-volume-30s",
                            "3.0",
                            "--shadow-min-entry-price-volatility",
                            "0.20",
                            "--shadow-max-age-seconds",
                            "30",
                            "--lifecycle-file",
                            "data/training/a.jsonl",
                            "--lifecycle-file",
                            "data/training/b.jsonl",
                        ]
                    )

        mock_run.assert_called_once_with(
            model_dir="data/models/example",
            lifecycle_dir="data/training",
            output_path="data/replay_reports/out.json",
            train_split_ratio=0.60,
            validation_split_ratio=0.20,
            min_validation_files=1,
            min_eval_files=1,
            max_samples_per_token=120,
            sample_cache_dir=None,
            top_k_per_group=2,
            group_bucket_seconds=30,
            max_lifecycle_files=None,
            lifecycle_files=["data/training/a.jsonl", "data/training/b.jsonl"],
            include_shadow_score_rejects=True,
            shadow_min_prob=0.985,
            shadow_max_entry_score=10.0,
            shadow_min_entry_volume_30s=3.0,
            shadow_min_entry_price_volatility=0.20,
            shadow_max_age_seconds=30.0,
            relevance_mode="risk_adjusted_return",
        )
        self.assertEqual(result, {"decision": "reject"})
        self.assertEqual(stdout.getvalue(), '{"decision": "reject"}\n')


if __name__ == "__main__":
    unittest.main()
