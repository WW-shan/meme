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
