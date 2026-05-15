import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "calibrate_execution_costs.py"
    spec = importlib.util.spec_from_file_location("calibrate_execution_costs", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCalibrateExecutionCostsCli(unittest.TestCase):
    def test_estimates_replay_overrides_from_signal_audit(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {"time": "2026-05-12T00:00:04", "action": "POSITION_OPENED", "token": "0xA", "signal_price": 1.0, "entry_price": 1.2},
            {"time": "2026-05-12T00:00:10", "action": "SIGNAL_DECISION", "token": "0xB", "decision": "queued"},
            {"time": "2026-05-12T00:00:11", "action": "BUY_EXECUTION_FAILED", "token": "0xB"},
            {"time": "2026-05-12T00:00:12", "action": "ENTRY_PRICE_PROTECTION_SKIP", "token": "0xC"},
            {"time": "2026-05-12T00:01:00", "action": "POSITION_CLOSED", "token": "0xA", "entry_price": 1.2, "exit_price": 1.5},
            {"time": "2026-05-12T00:01:01", "action": "SELL_EXECUTION_FAILED", "token": "0xD"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["signal_count"], 2)
        self.assertEqual(out["entry"]["open_count"], 1)
        self.assertEqual(out["entry"]["failure_count"], 1)
        self.assertEqual(out["entry"]["protection_skip_count"], 1)
        self.assertEqual(out["entry"]["avg_signal_to_open_seconds"], 4.0)
        self.assertAlmostEqual(out["entry"]["avg_entry_slippage_pct"], 0.20)
        self.assertGreaterEqual(out["replay_overrides"]["entry_price_protection_pct"], 0.20)
        self.assertEqual(out["replay_overrides"]["entry_delay_seconds"], 4)
        self.assertEqual(out["replay_overrides"]["entry_max_fill_wait_seconds"], 4)
        self.assertAlmostEqual(out["replay_overrides"]["entry_execution_failure_rate"], 0.5)
        self.assertAlmostEqual(out["replay_overrides"]["exit_execution_failure_rate"], 0.5)

    def test_since_filters_old_rows_before_estimating_live_execution(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T23:59:00", "action": "SIGNAL_DECISION", "token": "0xOld", "decision": "queued"},
            {"time": "2026-05-13T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {"time": "2026-05-13T00:00:05", "action": "POSITION_OPENED", "token": "0xA", "signal_price": 1.0, "entry_price": 1.1},
            {"time": "2026-05-13T00:00:08", "action": "POSITION_CLOSED", "token": "0xA", "entry_price": 1.1, "exit_price": 1.2},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(
                signal_audit_path=audit_path,
                since="2026-05-13T00:00:00",
            )

        self.assertEqual(out["entry"]["signal_count"], 1)
        self.assertEqual(out["entry"]["queued_signal_count"], 1)
        self.assertEqual(out["entry"]["open_count"], 1)
        self.assertEqual(out["entry"]["failure_count"], 0)
        self.assertEqual(out["entry"]["avg_signal_to_open_seconds"], 5.0)
        self.assertAlmostEqual(out["entry"]["avg_entry_slippage_pct"], 0.10)

    def test_since_with_timezone_treats_naive_runtime_rows_as_local_time(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-14 06:27:22", "action": "SIGNAL_DECISION", "token": "0xOld", "decision": "queued"},
            {"time": "2026-05-14 06:27:24", "action": "POSITION_OPENED", "token": "0xOld", "signal_price": 1.0, "entry_price": 1.0},
            {"time": "2026-05-14 13:38:35", "action": "SIGNAL_DECISION", "token": "0xNew", "decision": "queued"},
            {"time": "2026-05-14 13:38:38", "action": "POSITION_OPENED", "token": "0xNew", "signal_price": 1.0, "entry_price": 1.1},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(
                signal_audit_path=audit_path,
                since="2026-05-14T13:37:51+08:00",
            )

        self.assertEqual(out["entry"]["signal_count"], 1)
        self.assertEqual(out["entry"]["open_count"], 1)
        self.assertEqual(out["entry"]["avg_signal_to_open_seconds"], 3.0)
        self.assertAlmostEqual(out["entry"]["avg_entry_slippage_pct"], 0.10)

    def test_prefers_runtime_aligned_entry_and_exit_timing_fields(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-13T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {
                "time": "2026-05-13T00:00:09",
                "action": "POSITION_OPENED",
                "token": "0xA",
                "signal_price": 1.0,
                "entry_price": 1.1,
                "entry_wait_seconds": 9.0,
                "entry_fill_lag_seconds": 2.0,
                "buy_preflight_seconds": 0.7,
                "token_status_check_seconds": 0.4,
                "buy_tx_submit_rpc_seconds": 0.3,
                "buy_token_detect_seconds": 1.5,
                "buy_confirm_poll_interval_seconds": 0.25,
                "buy_post_detect_sync_seconds": 0.2,
            },
            {
                "time": "2026-05-13T00:01:00",
                "action": "POSITION_CLOSED",
                "token": "0xA",
                "entry_price": 1.1,
                "exit_price": 1.2,
                "sell_execution_seconds": 4.0,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["avg_signal_to_open_seconds"], 9.0)
        self.assertEqual(out["entry"]["avg_entry_delay_seconds"], 7.0)
        self.assertEqual(out["entry"]["avg_entry_fill_lag_seconds"], 2.0)
        self.assertEqual(out["entry"]["avg_buy_preflight_seconds"], 0.7)
        self.assertEqual(out["entry"]["avg_token_status_check_seconds"], 0.4)
        self.assertEqual(out["entry"]["avg_buy_tx_submit_rpc_seconds"], 0.3)
        self.assertEqual(out["entry"]["avg_buy_token_detect_seconds"], 1.5)
        self.assertEqual(out["entry"]["avg_buy_confirm_poll_interval_seconds"], 0.25)
        self.assertEqual(out["entry"]["avg_buy_post_detect_sync_seconds"], 0.2)
        self.assertEqual(out["replay_overrides"]["entry_delay_seconds"], 7)
        self.assertEqual(out["replay_overrides"]["entry_max_fill_wait_seconds"], 2)
        self.assertEqual(out["exit"]["avg_sell_execution_seconds"], 4.0)
        self.assertEqual(out["replay_overrides"]["exit_delay_seconds"], 4)
        self.assertEqual(out["replay_overrides"]["exit_max_fill_wait_seconds"], 4)

    def test_reports_lifecycle_fast_status_and_chain_lag_observations(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-13T00:00:00", "action": "SIGNAL_DECISION", "token": "0xFast", "decision": "queued"},
            {
                "time": "2026-05-13T00:00:02",
                "action": "POSITION_OPENED",
                "token": "0xFast",
                "signal_price": 1.0,
                "entry_price": 1.02,
                "buy_fast_status_used": True,
                "token_status_source": "lifecycle",
                "lifecycle_status_staleness_seconds": 0.4,
                "lifecycle_status_chain_lag_seconds": 1.2,
            },
            {"time": "2026-05-13T00:01:00", "action": "SIGNAL_DECISION", "token": "0xHelper", "decision": "queued"},
            {
                "time": "2026-05-13T00:01:04",
                "action": "POSITION_OPENED",
                "token": "0xHelper",
                "signal_price": 1.0,
                "entry_price": 1.05,
                "buy_fast_status_used": False,
                "token_status_source": "helper",
                "lifecycle_status_staleness_seconds": 0.2,
                "lifecycle_status_chain_lag_seconds": 9.2,
                "token_status_check_seconds": 0.7,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["fast_status_count"], 1)
        self.assertEqual(out["entry"]["helper_status_count"], 1)
        self.assertAlmostEqual(out["entry"]["fast_status_rate"], 0.5)
        self.assertAlmostEqual(out["entry"]["avg_lifecycle_status_staleness_seconds"], 0.3)
        self.assertAlmostEqual(out["entry"]["avg_lifecycle_status_chain_lag_seconds"], 5.2)
        self.assertAlmostEqual(out["entry"]["p95_lifecycle_status_chain_lag_seconds"], 8.8)

    def test_positive_subsecond_execution_times_round_up_for_replay(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-13T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {
                "time": "2026-05-13T00:00:01",
                "action": "POSITION_OPENED",
                "token": "0xA",
                "signal_price": 1.0,
                "entry_price": 1.0,
                "entry_submit_seconds": 0.25,
                "entry_fill_lag_seconds": 0.75,
            },
            {
                "time": "2026-05-13T00:00:03",
                "action": "POSITION_CLOSED",
                "token": "0xA",
                "entry_price": 1.0,
                "exit_price": 1.0,
                "sell_execution_seconds": 0.25,
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["replay_overrides"]["entry_delay_seconds"], 1)
        self.assertEqual(out["replay_overrides"]["entry_max_fill_wait_seconds"], 1)
        self.assertEqual(out["replay_overrides"]["exit_delay_seconds"], 1)
        self.assertEqual(out["replay_overrides"]["exit_max_fill_wait_seconds"], 1)

    def test_transient_buy_retry_events_do_not_inflate_entry_failure_rate(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {"time": "2026-05-12T00:00:01", "action": "BUY_NOT_READY", "token": "0xA"},
            {"time": "2026-05-12T00:00:02", "action": "BUY_ALREADY_SENT", "token": "0xA"},
            {"time": "2026-05-12T00:00:10", "action": "POSITION_OPENED", "token": "0xA", "signal_price": 1.0, "entry_price": 1.0},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["open_count"], 1)
        self.assertEqual(out["entry"]["failure_count"], 0)
        self.assertEqual(out["entry"]["transient_retry_count"], 2)
        self.assertAlmostEqual(out["replay_overrides"]["entry_execution_failure_rate"], 0.0)

    def test_post_fill_entry_protection_exit_counts_as_protection_skip(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "SIGNAL_DECISION", "token": "0xA", "decision": "queued"},
            {"time": "2026-05-12T00:00:03", "action": "POSITION_OPENED", "token": "0xA", "signal_price": 1.0, "entry_price": 2.0},
            {"time": "2026-05-12T00:00:04", "action": "ENTRY_PRICE_PROTECTION_POST_FILL_EXIT", "token": "0xA", "signal_price": 1.0, "entry_price": 2.0},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["open_count"], 1)
        self.assertEqual(out["entry"]["protection_skip_count"], 1)
        self.assertEqual(out["entry"]["post_fill_protection_exit_count"], 1)
        self.assertEqual(out["entry"]["unresolved_signal_count"], 0)
        self.assertEqual(out["entry"]["failure_count"], 0)

    def test_post_fill_entry_protection_exit_does_not_loosen_recommended_slippage_cap(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "SIGNAL_DECISION", "token": "0xGood", "decision": "queued"},
            {"time": "2026-05-12T00:00:03", "action": "POSITION_OPENED", "token": "0xGood", "signal_price": 1.0, "entry_price": 1.1},
            {"time": "2026-05-12T00:01:00", "action": "SIGNAL_DECISION", "token": "0xProtected", "decision": "queued"},
            {"time": "2026-05-12T00:01:03", "action": "POSITION_OPENED", "token": "0xProtected", "signal_price": 1.0, "entry_price": 2.0},
            {"time": "2026-05-12T00:01:04", "action": "ENTRY_PRICE_PROTECTION_POST_FILL_EXIT", "token": "0xProtected", "signal_price": 1.0, "entry_price": 2.0},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertAlmostEqual(out["entry"]["p95_positive_entry_slippage_pct"], 0.10)
        self.assertAlmostEqual(out["replay_overrides"]["entry_price_protection_pct"], 0.12)

    def test_replaced_queue_signal_does_not_count_as_execution_failure(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "SIGNAL_DECISION", "token": "0xLow", "decision": "queued"},
            {"time": "2026-05-12T00:00:01", "action": "QUEUE_REPLACE", "token": "0xHigh", "replaced_token": "0xLow"},
            {"time": "2026-05-12T00:00:01", "action": "SIGNAL_DECISION", "token": "0xHigh", "decision": "replaced"},
            {"time": "2026-05-12T00:00:05", "action": "POSITION_OPENED", "token": "0xHigh", "signal_price": 1.0, "entry_price": 1.1},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["entry"]["queued_signal_count"], 2)
        self.assertEqual(out["entry"]["replacement_drop_count"], 1)
        self.assertEqual(out["entry"]["unresolved_signal_count"], 0)
        self.assertEqual(out["entry"]["failure_count"], 0)
        self.assertAlmostEqual(out["replay_overrides"]["entry_execution_failure_rate"], 0.0)

    def test_partial_close_audit_counts_as_successful_exit_attempt(self):
        cli = _load_cli()

        rows = [
            {"time": "2026-05-12T00:00:00", "action": "POSITION_CLOSED", "token": "0xA", "entry_price": 1.0, "exit_price": 1.1},
            {"time": "2026-05-12T00:00:01", "action": "POSITION_PARTIAL_CLOSED", "token": "0xB", "entry_price": 1.0, "exit_price": 1.0},
            {"time": "2026-05-12T00:00:02", "action": "SELL_EXECUTION_FAILED", "token": "0xC"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "signals.jsonl"
            audit_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            out = cli.estimate_execution_costs(signal_audit_path=audit_path)

        self.assertEqual(out["exit"]["close_count"], 2)
        self.assertEqual(out["exit"]["failure_count"], 1)
        self.assertAlmostEqual(out["replay_overrides"]["exit_execution_failure_rate"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
