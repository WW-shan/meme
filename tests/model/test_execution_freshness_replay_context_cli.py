import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "probe_execution_freshness_replay_context.py"
    spec = importlib.util.spec_from_file_location("probe_execution_freshness_replay_context", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _sample(token, sample_time, features):
    return {
        "meta": {"token_address": token, "sample_time": sample_time},
        "features": dict(features),
    }


class TestExecutionFreshnessReplayContextCli(unittest.TestCase):
    def test_main_writes_strict_replay_context_audit(self):
        cli = _load_cli()
        calls = []

        def frozen_samples(_args, split, _base_overrides, _context):
            if split == "validation":
                return [
                    _sample("0xaaa", 100, {"lifecycle_status_staleness_seconds": 0.02}),
                    _sample("0xbbb", 200, {"price_volatility": 0.10}),
                ]
            return [
                _sample("0xccc", 300, {"lifecycle_status_staleness_seconds": 0.03}),
            ]

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            trade_log = [{
                "token": "0xaaa" if kwargs["split"] == "validation" else "0xccc",
                "entry_signal_time": 100 if kwargs["split"] == "validation" else 300,
                "entry_time": 101,
                "return_pct": -12.0,
                "exit_reason": "TIME_EXIT",
                "lifecycle_status_staleness_seconds": 0.02,
            }]
            return {
                "generated_at": "2026-06-08T00:00:00+00:00",
                "split": kwargs["split"],
                "evaluation": {
                    "net_profit_bnb": 0.001,
                    "net_return_pct": 10.0,
                    "total_trades": 1,
                    "max_drawdown_pct": -2.0,
                    "win_rate": 0.0,
                    "walk_forward_worst_net_return_pct": 3.0,
                    "walk_forward_worst_max_drawdown_pct": -4.0,
                    "trade_log": trade_log if kwargs.get("include_trade_log") else [],
                },
            }

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir=Path("data/replay_reports")) as tmpdir:
            output_json = Path(tmpdir) / "freshness_context.json"
            output_md = Path(tmpdir) / "freshness_context.md"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_model_replay}), \
                 patch.object(cli, "_split_samples_for_replay", side_effect=frozen_samples):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    rc = cli.main([
                        "--output-json",
                        str(output_json),
                        "--output-md",
                        str(output_md),
                        "--rule-field",
                        "lifecycle_status_staleness_seconds",
                        "--rule-threshold",
                        "0.015399",
                    ])
            report = json.loads(output_json.read_text(encoding="utf-8"))
            markdown = output_md.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertEqual(report["decision"], "strict_replay_context_available")
        self.assertFalse(report["probe_contract"]["live_switch_evidence"])
        self.assertEqual(report["required_rule_inputs"], ["lifecycle_status_staleness_seconds"])
        self.assertEqual(set(report["splits"]), {"validation", "final"})
        validation = report["splits"]["validation"]
        self.assertTrue(validation["selected_proxy_rule_replayable_from_samples"])
        self.assertTrue(validation["selected_proxy_rule_replayable_from_trade_context"])
        sample_by_field = {row["field"]: row for row in validation["sample_policy_feature_coverage"]}
        self.assertEqual(sample_by_field["lifecycle_status_staleness_seconds"]["status"], "available")
        trade_by_field = {
            row["field"]: row
            for row in validation["baseline_trade_policy_feature_coverage"]["fields"]
        }
        self.assertEqual(trade_by_field["lifecycle_status_staleness_seconds"]["status"], "available")
        self.assertIn("Execution Freshness Replay Context Audit", markdown)
        self.assertEqual([call["split"] for call in calls], ["validation", "final"])
        self.assertTrue(all(call["include_trade_log"] for call in calls))
        self.assertEqual({call["max_open_positions"] for call in calls}, {8})
        self.assertTrue(all(call["overrides"]["position_fraction"] == 0.1 for call in calls))
        self.assertTrue(all(call["overrides"]["max_position_fraction"] == 0.1 for call in calls))

    def test_main_rejects_available_but_degenerate_numeric_rule(self):
        cli = _load_cli()

        def frozen_samples(_args, _split, _base_overrides, _context):
            return [
                _sample("0xaaa", 100, {"lifecycle_status_chain_lag_seconds": 0.0}),
                _sample("0xbbb", 200, {"lifecycle_status_chain_lag_seconds": 0.0}),
            ]

        def fake_run_model_replay(**kwargs):
            return {
                "generated_at": "2026-06-08T00:00:00+00:00",
                "split": kwargs["split"],
                "evaluation": {
                    "net_profit_bnb": 0.001,
                    "net_return_pct": 10.0,
                    "total_trades": 1,
                    "max_drawdown_pct": -2.0,
                    "win_rate": 0.0,
                    "walk_forward_worst_net_return_pct": 3.0,
                    "walk_forward_worst_max_drawdown_pct": -4.0,
                    "trade_log": [{
                        "token": "0xaaa",
                        "entry_signal_time": 100,
                        "entry_time": 101,
                        "return_pct": -12.0,
                        "exit_reason": "TIME_EXIT",
                        "lifecycle_status_chain_lag_seconds": 0.0,
                    }],
                },
            }

        fake_model_replay = types.ModuleType("src.pipeline.model_replay")
        fake_model_replay.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory(dir=Path("data/replay_reports")) as tmpdir:
            output_json = Path(tmpdir) / "freshness_context_degenerate.json"
            output_md = Path(tmpdir) / "freshness_context_degenerate.md"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_model_replay}), \
                 patch.object(cli, "_split_samples_for_replay", side_effect=frozen_samples):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    rc = cli.main([
                        "--output-json",
                        str(output_json),
                        "--output-md",
                        str(output_md),
                        "--rule-field",
                        "lifecycle_status_chain_lag_seconds",
                        "--rule-threshold",
                        "6.109405994415283",
                    ])
            report = json.loads(output_json.read_text(encoding="utf-8"))
            markdown = output_md.read_text(encoding="utf-8")

        self.assertEqual(rc, 0)
        self.assertEqual(report["decision"], "rejected_strict_replay_context_degenerate")
        self.assertEqual(report["outcome_tier"], "Rejected")
        validation = report["splits"]["validation"]
        self.assertEqual(validation["selected_proxy_rule_sample_match_count"], 0)
        self.assertEqual(validation["selected_proxy_rule_trade_context_match_count"], 0)
        self.assertEqual(
            validation["selected_proxy_rule_sample_value_summary"]["max"],
            0.0,
        )
        self.assertIn("present, but degenerate", markdown)
        self.assertIn("Selected rule sample match count: `0`", markdown)

    def test_cli_refuses_output_outside_replay_reports(self):
        cli = _load_cli()
        rc = cli.main([
            "--output-json",
            "docs/research/bad.json",
            "--rule-field",
            "lifecycle_status_staleness_seconds",
            "--rule-threshold",
            "0.015399",
        ])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
