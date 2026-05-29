import json
import unittest

from src.pipeline import replay_uncertainty_gate_probe as p


def _trade(return_pct, token):
    return {
        "token": token,
        "entry_signal_time": token,
        "return_pct": return_pct,
        "exit_reason": "TIME_EXIT",
    }


def _common(delta, token):
    return {
        "token": token,
        "entry_signal_time": token,
        "baseline_return_pct": 0.0,
        "candidate_return_pct": delta,
        "return_delta_pct": delta,
        "baseline_exit_reason": "SELL100",
        "candidate_exit_reason": "TIME_EXIT",
    }


def _delta_block(deltas):
    return {
        "delta_summary": {
            "baseline": {"trade_count": len(deltas), "return_pct_sum": 0.0, "win_rate": 0.5},
            "candidate": {"trade_count": len(deltas), "return_pct_sum": sum(deltas), "win_rate": 0.5},
            "common_trades": {"trade_count": len(deltas), "return_delta_pct_sum": sum(deltas)},
            "added_candidate_trades": {"trade_count": 0, "return_pct_sum": 0.0},
            "removed_baseline_trades": {"trade_count": 0, "return_pct_sum": 0.0},
        },
        "common_trade_deltas": [_common(delta, f"c{index}") for index, delta in enumerate(deltas)],
        "added_candidate_trades": [],
        "removed_baseline_trades": [],
    }


def _replacement_delta(added, removed):
    return {
        "delta_summary": {
            "baseline": {"trade_count": len(removed), "return_pct_sum": sum(removed), "win_rate": 0.5},
            "candidate": {"trade_count": len(added), "return_pct_sum": sum(added), "win_rate": 0.5},
            "common_trades": {"trade_count": 0, "return_delta_pct_sum": 0.0},
            "added_candidate_trades": {"trade_count": len(added), "return_pct_sum": sum(added)},
            "removed_baseline_trades": {"trade_count": len(removed), "return_pct_sum": sum(removed)},
        },
        "common_trade_deltas": [],
        "added_candidate_trades": [_trade(value, f"a{index}") for index, value in enumerate(added)],
        "removed_baseline_trades": [_trade(value, f"r{index}") for index, value in enumerate(removed)],
    }


def _gate_report(validation_delta, final_delta, *, gate_passes=True):
    return {
        "decision": "test",
        "selected_candidate": {"candidate_index": 3},
        "selected_trade_delta_attribution": {
            "validation": validation_delta,
            "final": final_delta,
        },
        "best_validation_candidate": {
            "passes_acceptance_gate": gate_passes,
            "gate_details": {"net_profit_bnb": gate_passes, "max_drawdown_pct": gate_passes},
            "summary": {"net_profit_bnb": 1.0},
        },
        "final_confirmation": {
            "passes_acceptance_gate": gate_passes,
            "gate_details": {"net_profit_bnb": gate_passes, "max_drawdown_pct": gate_passes},
            "summary": {"net_profit_bnb": 1.0},
        },
    }


class TestReplayUncertaintyGateProbe(unittest.TestCase):
    def test_shadow_candidate_when_paired_delta_is_positive_and_not_top_winner_dependent(self):
        validation = _delta_block([5.0, 4.0, 3.0, 2.0, 1.0] + [0.0] * 15)
        final = _delta_block([6.0, 5.0, 4.0, 3.0, 2.0] + [0.0] * 15)

        report = p.build_replay_uncertainty_gate_report(
            replay_report=_gate_report(validation, final),
            bootstrap_samples=500,
            seed=11,
        )

        self.assertEqual(report["outcome_tier"], "Shadow Candidate")
        self.assertEqual(report["decision"], "paired_delta_uncertainty_shadow_candidate")
        self.assertGreater(report["validation"]["bootstrap_total_delta_pct"]["positive_probability"], 0.8)
        self.assertFalse(report["final"]["top_winner_dependency"]["top1_dependency"])

    def test_research_alpha_when_final_delta_depends_on_single_added_winner(self):
        validation = _replacement_delta([30.0, 20.0, -5.0], [5.0])
        final = _replacement_delta([120.0, -40.0, -20.0], [5.0])

        report = p.build_replay_uncertainty_gate_report(
            replay_report=_gate_report(validation, final),
            bootstrap_samples=500,
            min_split_contributions=0,
            seed=13,
        )

        self.assertEqual(report["outcome_tier"], "Research Alpha")
        self.assertIn("final_top1_winner_dependent", report["shadow_blockers"])
        self.assertLessEqual(report["final"]["top_winner_dependency"]["delta_after_removing_top1_pct"], 0.0)

    def test_rejects_when_validation_delta_is_not_positive(self):
        validation = _delta_block([0.0] * 20)
        final = _delta_block([8.0, 4.0, 2.0] + [0.0] * 17)

        report = p.build_replay_uncertainty_gate_report(
            replay_report=_gate_report(validation, final),
            bootstrap_samples=300,
            seed=17,
        )

        self.assertEqual(report["outcome_tier"], "Rejected")
        self.assertIn("validation_observed_delta_non_positive", report["rejection_reasons"])

    def test_json_text_sanitizes_nonfinite_values(self):
        text = p.to_json_text({"nan": float("nan"), "inf": float("inf")})

        parsed = json.loads(text)
        self.assertIsNone(parsed["nan"])
        self.assertIsNone(parsed["inf"])


if __name__ == "__main__":
    unittest.main()
