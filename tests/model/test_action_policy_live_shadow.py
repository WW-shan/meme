import unittest

import importlib

from scripts import probe_action_policy_activation_shadow as activation_cli
from scripts import probe_action_policy_live_shadow as live_cli
from src.pipeline import action_policy_live_shadow as shadow


class FakeRuntime:
    enabled = True
    min_confidence = 0.4
    min_live_features = 2
    route_names = ["continue_hold", "skip"]
    feature_names = ["prob", "pred_return", "volume_30s"]
    metadata = {"trained": True}

    def predict(self, *, lifecycle, features, prob, pred_return, token_address=None, sample_time=None, create_timestamp=None):
        used = float(prob) >= 0.98 and float(pred_return or 0.0) >= 35.0
        return {
            "used": used,
            "route": "continue_hold" if used else "skip",
            "confidence": 0.75 if used else 0.25,
            "reason": "continue_hold" if used else "non_continue_hold_route",
            "live_feature_count": len(features),
            "route_probabilities": {"continue_hold": 0.75 if used else 0.25, "skip": 0.25 if used else 0.75},
        }


class ActionPolicyLiveShadowTest(unittest.TestCase):
    def test_recorded_shadow_audit_report_uses_persisted_runtime_fields(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-06-08 15:10:00",
                "token": "0xabc",
                "symbol": "ABC",
                "reason": "queued",
                "prob": 0.99,
                "pred_return": 42.0,
                "action_policy_shadow_enabled": True,
                "action_policy_shadow_used": True,
                "action_policy_shadow_route": "continue_hold",
                "action_policy_shadow_confidence": 0.78,
                "action_policy_shadow_reason": "continue_hold",
                "action_policy_shadow_live_feature_count": 25,
                "action_policy_shadow_min_confidence": 0.55,
                "action_policy_shadow_min_live_features": 2,
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "time": "2026-06-08 15:11:00",
                "token": "0xdef",
                "symbol": "DEF",
                "reason": "near_threshold_pred_return_below_min",
                "prob": 0.96,
                "pred_return": -12.0,
                "action_policy_shadow_enabled": True,
                "action_policy_shadow_used": False,
                "action_policy_shadow_route": "quick_take_profit",
                "action_policy_shadow_confidence": 0.48,
                "action_policy_shadow_reason": "non_continue_hold_route",
                "action_policy_shadow_live_feature_count": 25,
                "action_policy_shadow_min_confidence": 0.55,
                "action_policy_shadow_min_live_features": 2,
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "time": "2026-06-08 15:12:00",
                "token": "0xnoaudit",
                "symbol": "NOAUDIT",
                "reason": "buy_model_reject",
                "prob": 0.8,
                "pred_return": -4.0,
            },
        ]
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xabc",
                "symbol": "ABC",
                "entry_signal_time": "2026-06-08 15:10:01",
                "time": "2026-06-08 15:10:03",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xabc",
                "symbol": "ABC",
                "time": "2026-06-08 15:13:00",
                "reason": "TRAILING_STOP",
                "net_profit": 0.0015,
                "is_real_trade": True,
            },
        ]

        report = shadow.build_recorded_shadow_audit_report(
            signal_rows=signal_rows,
            trade_rows=trade_rows,
            since="2026-06-08 15:00:00",
            active_model="model",
        )

        self.assertEqual(report["summary"]["signal_count"], 3)
        self.assertEqual(report["summary"]["recorded_shadow_count"], 2)
        self.assertEqual(report["summary"]["missing_recorded_shadow_count"], 1)
        self.assertEqual(report["summary"]["recorded_shadow_used_count"], 1)
        self.assertEqual(report["summary"]["queued_recorded_shadow_used_count"], 1)
        self.assertEqual(report["summary"]["queued_recorded_shadow_used_matched_count"], 1)
        self.assertEqual(report["summary"]["queued_recorded_shadow_used_matched_net_profit_bnb"], 0.0015)
        self.assertEqual(report["summary"]["recorded_shadow_route_counts"], {"continue_hold": 1, "quick_take_profit": 1})
        self.assertEqual(report["go_no_go"]["status"], "has_matched_recorded_shadow_route")
        self.assertIn("Recorded Shadow Audit", shadow.recorded_shadow_to_markdown_text(report))

    def test_recorded_shadow_path_attribution_summarizes_route_outcomes(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "time": "2026-06-08 15:10:00",
                "token": "0xfast",
                "symbol": "FAST",
                "reason": "near_threshold_pred_return_below_min",
                "prob": 0.96,
                "pred_return": 18.0,
                "action_policy_shadow_enabled": True,
                "action_policy_shadow_used": False,
                "action_policy_shadow_route": "quick_take_profit",
                "action_policy_shadow_confidence": 0.48,
                "action_policy_shadow_reason": "non_continue_hold_route",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "time": "2026-06-08 15:11:00",
                "token": "0xflat",
                "symbol": "FLAT",
                "reason": "buy_model_reject",
                "prob": 0.94,
                "pred_return": 2.0,
                "action_policy_shadow_enabled": True,
                "action_policy_shadow_used": False,
                "action_policy_shadow_route": "quick_take_profit",
                "action_policy_shadow_confidence": 0.42,
                "action_policy_shadow_reason": "non_continue_hold_route",
            },
            {
                "action": "SIGNAL_DECISION",
                "decision": "rejected",
                "time": "2026-06-08 15:12:00",
                "token": "0xstop",
                "symbol": "STOP",
                "reason": "buy_model_reject",
                "prob": 0.93,
                "pred_return": -4.0,
                "action_policy_shadow_enabled": True,
                "action_policy_shadow_used": False,
                "action_policy_shadow_route": "skip",
                "action_policy_shadow_confidence": 0.88,
                "action_policy_shadow_reason": "non_continue_hold_route",
            },
        ]
        lifecycles = {
            "0xfast": {
                "price_history": [
                    {"timestamp": "2026-06-08 15:09:55", "price": 1.0},
                    {"timestamp": "2026-06-08 15:10:00", "price": 1.0},
                    {"timestamp": "2026-06-08 15:11:00", "price": 1.30},
                    {"timestamp": "2026-06-08 15:12:00", "price": 0.70},
                ]
            },
            "0xflat": {
                "price_history": [
                    {"timestamp": "2026-06-08 15:10:55", "price": 1.0},
                    {"timestamp": "2026-06-08 15:11:20", "price": 1.05},
                ]
            },
            "0xstop": {
                "price_history": [
                    {"timestamp": "2026-06-08 15:11:55", "price": 1.0},
                    {"timestamp": "2026-06-08 15:12:30", "price": 0.70},
                ]
            },
        }

        report = shadow.build_recorded_shadow_path_attribution_report(
            signal_rows=signal_rows,
            lifecycles=lifecycles,
            since="2026-06-08 15:00:00",
            active_model="model",
            min_route_path_support=2,
            min_quick_profit_precision=0.5,
            max_sample_rows=0,
        )

        self.assertEqual(report["summary"]["signal_count"], 3)
        self.assertEqual(report["summary"]["recorded_shadow_count"], 3)
        self.assertEqual(report["summary"]["path_evaluable_count"], 3)
        self.assertEqual(report["summary"]["recorded_shadow_route_counts"], {"quick_take_profit": 2, "skip": 1})
        quick_take_profit = report["route_path_summary"]["quick_take_profit"]
        self.assertEqual(quick_take_profit["path_evaluable_count"], 2)
        self.assertEqual(
            quick_take_profit["barrier_class_counts"],
            {"fast_profit_then_collapse": 1, "flat_timeout": 1},
        )
        self.assertEqual(quick_take_profit["quick_take_profit_candidate_count"], 1)
        self.assertEqual(quick_take_profit["quick_take_profit_precision"], 0.5)
        self.assertEqual(report["go_no_go"]["status"], "recorded_quick_take_profit_path_support")
        self.assertIn("Recorded Shadow Path Attribution", shadow.recorded_shadow_path_to_markdown_text(report))

    def test_matches_queued_signal_to_live_trade_and_summarizes_shadow_route(self):
        signal_rows = [
            {
                "action": "SIGNAL_DECISION",
                "decision": "queued",
                "time": "2026-05-29 00:00:00",
                "token": "0xabc",
                "symbol": "ABC",
                "prob": 0.99,
                "pred_return": 40.0,
                "volume_30s": 2.0,
                "price_volatility": 0.2,
                "token_age_seconds": 30.0,
                "min_pred_return": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.1,
            }
        ]
        trade_rows = [
            {
                "action": "OPEN",
                "token": "0xabc",
                "symbol": "ABC",
                "entry_signal_time": "2026-05-29 00:00:01",
                "time": "2026-05-29 00:00:03",
                "is_real_trade": True,
            },
            {
                "action": "CLOSE",
                "token": "0xabc",
                "symbol": "ABC",
                "time": "2026-05-29 00:01:00",
                "reason": "PPO_SELL100",
                "net_profit": 0.001,
                "is_real_trade": True,
            },
        ]

        report = shadow.build_live_shadow_report(
            signal_rows=signal_rows,
            trade_rows=trade_rows,
            runtime=FakeRuntime(),
            since="2026-05-29 00:00:00",
            active_model="model",
        )

        self.assertEqual(report["summary"]["signal_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_matched_count"], 1)
        self.assertEqual(report["summary"]["queued_shadow_used_matched_net_profit_bnb"], 0.001)
        self.assertEqual(report["go_no_go"]["status"], "has_matched_shadow_route")

    def test_runtime_params_are_derived_from_live_signal_rows(self):
        params = shadow.runtime_params_from_signal_rows(
            [
                {
                    "min_pred_return": 36.0,
                    "min_entry_volume_30s": 1.7,
                    "min_entry_price_volatility": 0.12,
                    "buy_near_threshold_min_prob": 0.93,
                }
            ],
            primary_min_prob=0.981,
        )

        self.assertEqual(params["buy_threshold"], 0.981)
        self.assertEqual(params["min_entry_score"], 36.0)
        self.assertEqual(params["min_entry_volume_30s"], 1.7)
        self.assertEqual(params["min_entry_price_volatility"], 0.12)
        self.assertEqual(params["buy_near_threshold_min_prob"], 0.93)

    def test_report_records_router_runtime_params_used_for_shadow(self):
        runtime = FakeRuntime()
        runtime.runtime_params = {
            "buy_threshold": 0.98,
            "buy_action_policy_router_min_prob": 0.988,
            "buy_action_policy_router_max_pred_return": 45.0,
        }

        report = shadow.build_live_shadow_report(
            signal_rows=[],
            trade_rows=[],
            runtime=runtime,
            since="2026-05-29 00:00:00",
        )

        params = report["router_runtime"]["runtime_params"]
        self.assertEqual(params["buy_action_policy_router_min_prob"], 0.988)
        self.assertEqual(params["buy_action_policy_router_max_pred_return"], 45.0)
        shadow_params = report["parameters"]["runtime_params_for_shadow"]
        self.assertEqual(shadow_params["buy_action_policy_router_min_prob"], 0.988)
        self.assertEqual(shadow_params["buy_action_policy_router_max_pred_return"], 45.0)
        self.assertIn("buy_action_policy_router_min_prob", shadow.to_markdown_text(report))

    def test_runtime_params_include_router_hazard_guard_overrides(self):
        params = shadow.runtime_params_from_signal_rows(
            [],
            primary_min_prob=0.98,
            router_min_prob=0.988,
            router_max_pred_return=45.0,
        )

        self.assertEqual(params["buy_action_policy_router_min_prob"], 0.988)
        self.assertEqual(params["buy_action_policy_router_max_pred_return"], 45.0)

    def test_live_shadow_cli_accepts_router_hazard_guard_args(self):
        args = live_cli.parse_args(["--router-min-prob", "0.988", "--router-max-pred-return", "45.0"])

        self.assertEqual(args.router_min_prob, 0.988)
        self.assertEqual(args.router_max_pred_return, 45.0)

    def test_activation_shadow_cli_accepts_router_hazard_guard_args(self):
        args = activation_cli.parse_args(["--router-min-prob", "0.988", "--router-max-pred-return", "45.0"])

        self.assertEqual(args.router_min_prob, 0.988)
        self.assertEqual(args.router_max_pred_return, 45.0)

    def test_recorded_shadow_audit_cli_accepts_report_args(self):
        recorded_cli = importlib.import_module("scripts.probe_action_policy_recorded_shadow_audit")

        args = recorded_cli.parse_args(
            [
                "--since",
                "2026-06-08 15:00:00",
                "--active-model",
                "model",
                "--output-json",
                "data/replay_reports/recorded_shadow.json",
                "--output-md",
                "data/replay_reports/recorded_shadow.md",
                "--max-sample-rows",
                "0",
            ]
        )

        self.assertEqual(args.since, "2026-06-08 15:00:00")
        self.assertEqual(args.active_model, "model")
        self.assertEqual(args.max_sample_rows, 0)

    def test_recorded_shadow_path_attribution_cli_accepts_report_args(self):
        path_cli = importlib.import_module("scripts.probe_action_policy_recorded_shadow_path_attribution")

        args = path_cli.parse_args(
            [
                "--since",
                "2026-06-08 15:00:00",
                "--active-model",
                "model",
                "--output-json",
                "data/replay_reports/recorded_shadow_path.json",
                "--output-md",
                "data/replay_reports/recorded_shadow_path.md",
                "--horizon-seconds",
                "300",
                "--quick-profit-seconds",
                "90",
                "--min-route-path-support",
                "2",
                "--min-quick-profit-precision",
                "0.5",
                "--max-sample-rows",
                "0",
            ]
        )

        self.assertEqual(args.since, "2026-06-08 15:00:00")
        self.assertEqual(args.active_model, "model")
        self.assertEqual(args.horizon_seconds, 300.0)
        self.assertEqual(args.quick_profit_seconds, 90.0)
        self.assertEqual(args.min_route_path_support, 2)
        self.assertEqual(args.min_quick_profit_precision, 0.5)
        self.assertEqual(args.max_sample_rows, 0)


if __name__ == "__main__":
    unittest.main()
