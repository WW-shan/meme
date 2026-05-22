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


DEAD_FLOW_KEYS = {
    "buy_dead_flow_exit_min_hold_seconds",
    "buy_dead_flow_exit_max_mfe_pct",
}
ENTRY_SIDE_FLOW_KEYS = {
    "buy_flow_activation_min_prob",
    "buy_flow_activation_min_pred_return",
    "buy_flow_activation_max_age_seconds",
    "buy_flow_activation_lookback_seconds",
    "buy_flow_activation_min_volume_ramp_ratio",
    "buy_flow_activation_min_volume_ramp_delta",
    "buy_flow_activation_min_pred_return_delta",
    "buy_flow_activation_min_price_volatility_delta",
    "buy_flow_activation_min_current_volume_30s",
}


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_dead_flow_exit_replay.py"
    spec = importlib.util.spec_from_file_location("run_dead_flow_exit_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _trade(token, entry_time, *, exit_reason="TIME_EXIT", return_pct=-5.0):
    return {
        "token": token,
        "entry_time": entry_time,
        "entry_index": int(entry_time),
        "entry_price": 1.0,
        "exit_reason": exit_reason,
        "return_pct": return_pct,
    }


def _evaluation(*, net_profit_bnb, trade_log, dead_flow_exit_count=0, win_rate=0.5):
    return {
        "net_profit_bnb": net_profit_bnb,
        "total_trades": len(trade_log),
        "max_drawdown_pct": -5.0,
        "win_rate": win_rate,
        "walk_forward_worst_net_return_pct": 10.0,
        "walk_forward_worst_max_drawdown_pct": -5.0,
        "stress_replay": [
            {
                "name": "stress_a",
                "net_return_pct": 8.0,
                "net_profit_bnb": net_profit_bnb * 0.5,
                "max_drawdown_pct": -6.0,
            }
        ],
        "dead_flow_exit_count": dead_flow_exit_count,
        "trade_log": trade_log,
    }


class TestDeadFlowExitReplayCli(unittest.TestCase):
    def test_candidate_grid_is_dead_flow_exit_only_and_bounded(self):
        cli = _load_cli()

        candidates = list(cli.candidate_grid())

        self.assertEqual(len(candidates), 12)
        self.assertEqual({row["buy_dead_flow_exit_min_hold_seconds"] for row in candidates}, {90.0, 120.0, 180.0, 240.0})
        self.assertEqual({row["buy_dead_flow_exit_max_mfe_pct"] for row in candidates}, {0.03, 0.05, 0.08})
        for candidate in candidates:
            self.assertEqual(set(candidate), DEAD_FLOW_KEYS)
            self.assertFalse(ENTRY_SIDE_FLOW_KEYS.intersection(candidate))

    def test_rejects_candidate_when_entry_set_changes_even_if_profit_improves(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_dead_flow_exit_min_hold_seconds": 120.0, "buy_dead_flow_exit_max_mfe_pct": 0.05}])
        calls = []
        baseline_log = [_trade("0xa", 100), _trade("0xb", 200, exit_reason="TRAILING_STOP", return_pct=40.0)]
        changed_log = [_trade("0xa", 100, exit_reason="DEAD_FLOW_TIME_EXIT"), _trade("0xc", 300, return_pct=20.0)]

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            calls.append({"split": kwargs.get("split"), "overrides": overrides})
            is_candidate = bool(DEAD_FLOW_KEYS.intersection(overrides))
            return {"evaluation": _evaluation(
                net_profit_bnb=0.002 if is_candidate else 0.001,
                trade_log=changed_log if is_candidate else baseline_log,
                dead_flow_exit_count=1 if is_candidate else 0,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output)])
            written_decision = json.loads(output.read_text(encoding="utf-8"))["decision"]

        self.assertEqual(report["decision"], "reject")
        self.assertFalse(report["candidates"][0]["passes_acceptance_gate"])
        self.assertFalse(report["candidates"][0]["gate_details"]["frozen_entries"])
        self.assertEqual(written_decision, "reject")
        self.assertFalse(ENTRY_SIDE_FLOW_KEYS.intersection(calls[1]["overrides"]))

    def test_accepts_dead_flow_only_candidate_when_all_gates_pass(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{"buy_dead_flow_exit_min_hold_seconds": 120.0, "buy_dead_flow_exit_max_mfe_pct": 0.05}])
        baseline_log = [_trade("0xa", 100), _trade("0xb", 200, exit_reason="TRAILING_STOP", return_pct=40.0)]
        candidate_log = [_trade("0xa", 100, exit_reason="DEAD_FLOW_TIME_EXIT", return_pct=-1.0), baseline_log[1]]

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = bool(DEAD_FLOW_KEYS.intersection(overrides))
            return {"evaluation": _evaluation(
                net_profit_bnb=0.0017 if is_candidate else 0.001,
                trade_log=candidate_log if is_candidate else baseline_log,
                dead_flow_exit_count=1 if is_candidate else 0,
                win_rate=0.5,
            )}

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = cli.main(["--output", str(output)])

        self.assertEqual(report["decision"], "accept")
        self.assertTrue(report["selected_candidate"]["passes_acceptance_gate"])
        self.assertTrue(report["selected_candidate"]["gate_details"]["frozen_entries"])
        self.assertTrue(report["selected_candidate"]["gate_details"]["baseline_profitable_trades_not_worse"])
        self.assertTrue(report["final_confirmation"]["passes_acceptance_gate"])


if __name__ == "__main__":
    unittest.main()
