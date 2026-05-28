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

from src.pipeline import reentry_probe
from src.pipeline import runner_retention_replay_gate as gate


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_runner_retention_candidate_gate_replay.py"
    spec = importlib.util.spec_from_file_location("run_runner_retention_candidate_gate_replay", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _sample(
    token,
    *,
    sample_time,
    flow_sell_pressure_30s=0.1,
    flow_signed_imbalance_30s=0.5,
    volume_30s=0.75,
    price_volatility=0.08,
    price_momentum=5.0,
):
    return {
        "features": {
            "current_price": 1.0,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "price_momentum": price_momentum,
            "flow_sell_pressure_30s": flow_sell_pressure_30s,
            "flow_signed_imbalance_30s": flow_signed_imbalance_30s,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - 30,
        },
    }


def _dataset_flow_sample(token, *, sample_time):
    return {
        "features": {
            "current_price": 1.0,
            "volume_10s": 0.7,
            "volume_30s": 1.0,
            "price_volatility": 0.08,
            "sell_volume_30s": 0.25,
            "total_flow_volume_30s": 1.25,
            "sell_pressure_30s": 0.20,
            "signed_imbalance_30s": 0.60,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": sample_time - 30,
            "flow_event_count_30s": 3,
        },
    }


def _path(anchor, *, kind):
    if kind == "slow_runner":
        return [
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor - 1), 1.0, "anchor"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 240), 1.26, "buy"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 390), 1.65, "buy"),
        ]
    if kind == "drawdown_runner":
        return [
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor - 1), 1.0, "anchor"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 240), 1.26, "buy"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 390), 1.65, "buy"),
            reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 500), 0.70, "sell"),
        ]
    return [
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor), 1.0, "anchor"),
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 180), 1.02, "buy"),
        reentry_probe.PricePoint(reentry_probe.parse_time(anchor + 500), 0.98, "sell"),
    ]


class TestRunnerRetentionReplayGate(unittest.TestCase):
    def test_scores_runner_retention_near_candidates_and_keeps_episode_metadata(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xeval", sample_time=3000, flow_sell_pressure_30s=0.1),
            _sample("0xeval", sample_time=3010, flow_sell_pressure_30s=0.9),
        ]]
        runtime_params = {
            "buy_threshold": 0.99,
            "buy_near_threshold_min_prob": 0.85,
            "min_entry_score": 35.0,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }

        def fake_score_samples(samples, buy_artifact):
            return [0.90 for _sample in samples], [36.0 for _sample in samples]

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertEqual(metadata["intended_use"], "runner_retention_path_state_candidate_gate_score_map")
        self.assertEqual(metadata["train_label_counts"], {"total": 2, "positive": 1, "negative": 1})
        self.assertIn("flow_sell_pressure_30s", metadata["feature_names"])
        self.assertEqual(
            score_maps[0]["__episode_meta__"],
            {
                "token": "0xeval",
                "sample_count": 2,
                "start_time": 3000,
                "end_time": 3010,
            },
        )
        self.assertEqual(sorted(key for key in score_maps[0] if isinstance(key, int)), [0])
        self.assertGreaterEqual(score_maps[0][0], 0.5)

    def test_support_failure_returns_metadata_only_score_maps(self):
        train_samples = [_sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9)]
        eval_episodes = [[_sample("0xeval", sample_time=3000)]]

        with patch.object(gate.ranker_probe, "_score_samples", return_value=([0.90], [36.0])):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={"0xflat": _path(2000, kind="flat")},
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params={"buy_threshold": 0.99, "buy_near_threshold_min_prob": 0.85},
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertFalse(metadata["trained"])
        self.assertIn("train_labels_missing_positive_or_negative", metadata["support_reasons"])
        self.assertEqual(
            score_maps,
            [{
                "__episode_meta__": {
                    "token": "0xeval",
                    "sample_count": 1,
                    "start_time": 3000,
                    "end_time": 3000,
                }
            }],
        )

    def test_preserve_base_runtime_candidates_scores_only_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, flow_sell_pressure_30s=0.9),
            _sample("0xrescue", sample_time=3010, flow_sell_pressure_30s=0.1),
            _sample("0xlast", sample_time=3020, flow_sell_pressure_30s=0.1),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                if token == "0xbase":
                    buy_probs.append(0.99)
                else:
                    buy_probs.append(0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_rescue_rank_limit_keeps_top_scored_expanded_rescues_only(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, flow_sell_pressure_30s=0.9),
            _sample("0xlow", sample_time=3010, flow_sell_pressure_30s=0.1),
            _sample("0xbest", sample_time=3020, flow_sell_pressure_30s=0.1),
            _sample("0xsecond", sample_time=3030, flow_sell_pressure_30s=0.1),
            _sample("0xlast", sample_time=3040, flow_sell_pressure_30s=0.1),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_runner_retention_rescue_max_rank_per_episode": 2,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                buy_probs.append(0.99 if token == "0xbase" else 0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        def fake_score_rows(model, medians, feature_names, rows):
            scores_by_index = {0: 0.10, 1: 0.60, 2: 0.95, 3: 0.80}
            return [scores_by_index[int(row["original_index"])] for row in rows]

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples), patch.object(
            gate,
            "_score_rows",
            side_effect=fake_score_rows,
        ):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["rescue_rank_filter_active"])
        self.assertEqual(metadata["rescue_max_rank_per_episode"], 2)
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertNotIn(1, score_maps[0])
        self.assertEqual(score_maps[0][2], 0.95)
        self.assertEqual(score_maps[0][3], 0.80)
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["rank_eligible_rescue_candidate_count"], 3)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 2)
        self.assertEqual(metadata["rank_rejected_rescue_candidate_count"], 1)

    def test_early_replacement_labels_only_near_future_base_entries(self):
        train_samples = [
            _sample("0xsoon", sample_time=1000),
            _sample("0xsoon", sample_time=1008),
            _sample("0xpure", sample_time=2000),
        ]
        expanded_runtime_params = {
            "buy_threshold": 0.99,
            "buy_near_threshold_min_prob": 0.85,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        base_runtime_params = {
            **expanded_runtime_params,
            "buy_near_threshold_min_prob": 0.94,
            "buy_near_min_entry_volume_30s": 0.7,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                sample_time = sample.get("meta", {}).get("sample_time")
                if token == "0xsoon" and sample_time == 1008:
                    buy_probs.append(0.95)
                else:
                    buy_probs.append(0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            rows = gate._train_rows_with_labels(
                train_samples,
                {
                    "0xsoon": _path(1000, kind="slow_runner"),
                    "0xpure": _path(2000, kind="slow_runner"),
                },
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                early_replacement_max_lead_seconds=15,
            )

        by_time = {row["decision_sample_time"]: row for row in rows}
        self.assertTrue(by_time[1000]["runner_retention_positive"])
        self.assertEqual(by_time[1000]["baseline_entry_lead_seconds"], 8)
        self.assertTrue(by_time[1000]["label_positive"])
        self.assertEqual(by_time[1008]["baseline_entry_lead_seconds"], 0)
        self.assertFalse(by_time[1008]["label_positive"])
        self.assertIsNone(by_time[2000]["baseline_entry_lead_seconds"])
        self.assertFalse(by_time[2000]["label_positive"])

    def test_label_min_mae_relabels_deep_drawdown_runner_negative(self):
        train_samples = [
            _sample("0xclean", sample_time=1000),
            _sample("0xdeep", sample_time=2000),
            _sample("0xflat", sample_time=3000),
        ]
        eval_episodes = [[
            _sample("0xeval", sample_time=4000),
            _sample("0xeval", sample_time=4010),
        ]]
        runtime_params = {
            "buy_threshold": 0.99,
            "buy_near_threshold_min_prob": 0.85,
            "min_entry_score": 35.0,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_runner_retention_label_min_mae_pct": -18.0,
        }

        def fake_score_samples(samples, buy_artifact):
            return [0.90 for _sample in samples], [36.0 for _sample in samples]

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            train_rows = gate._train_rows_with_labels(
                train_samples,
                {
                    "0xclean": _path(1000, kind="slow_runner"),
                    "0xdeep": _path(2000, kind="drawdown_runner"),
                    "0xflat": _path(3000, kind="flat"),
                },
                buy_artifact={},
                runtime_params=runtime_params,
            )
            _score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xclean": _path(1000, kind="slow_runner"),
                    "0xdeep": _path(2000, kind="drawdown_runner"),
                    "0xflat": _path(3000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        by_token = {row["token"]: row for row in train_rows}
        self.assertTrue(by_token["0xdeep"]["runner_retention_positive"])
        self.assertLess(by_token["0xdeep"]["mae_pct"], -18.0)
        self.assertFalse(by_token["0xdeep"]["runner_retention_risk_adjusted_positive"])
        self.assertTrue(by_token["0xdeep"]["runner_retention_risk_rejected"])
        self.assertFalse(by_token["0xdeep"]["label_positive"])
        self.assertTrue(by_token["0xclean"]["label_positive"])
        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["label_risk_filter_active"])
        self.assertEqual(metadata["label_min_mae_pct"], -18.0)
        self.assertEqual(metadata["raw_train_label_counts"], {"total": 3, "positive": 1, "negative": 2})
        self.assertEqual(metadata["raw_train_risk_rejected_positive_count"], 1)

    def test_flow_compatibility_filter_only_applies_to_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.2),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, flow_sell_pressure_30s=0.9),
            _sample("0xrescue", sample_time=3010, flow_sell_pressure_30s=0.1),
            _sample("0xtoxic", sample_time=3020, flow_sell_pressure_30s=0.9),
            _sample("0xlast", sample_time=3030, flow_sell_pressure_30s=0.1),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_runner_retention_rescue_max_flow_sell_pressure_30s": 0.35,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                buy_probs.append(0.99 if token == "0xbase" else 0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["rescue_flow_filter_active"])
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertNotIn(2, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_hot_extension_ceiling_filter_only_applies_to_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, price_volatility=0.08),
            _sample("0xflat", sample_time=2000, price_volatility=0.07),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, price_volatility=0.18),
            _sample("0xrescue", sample_time=3010, price_volatility=0.08),
            _sample("0xhot", sample_time=3020, price_volatility=0.16),
            _sample("0xlast", sample_time=3030, price_volatility=0.08),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_runner_retention_rescue_max_entry_price_volatility": 0.10,
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                buy_probs.append(0.99 if token == "0xbase" else 0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["rescue_flow_filter_active"])
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertNotIn(2, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_generic_feature_bound_filter_only_applies_to_expanded_rescues(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, price_momentum=5.0),
            _sample("0xflat", sample_time=2000, price_momentum=4.0),
        ]
        eval_episodes = [[
            _sample("0xbase", sample_time=3000, price_momentum=18.0),
            _sample("0xrescue", sample_time=3010, price_momentum=5.0),
            _sample("0xhot", sample_time=3020, price_momentum=14.0),
            _sample("0xlast", sample_time=3030, price_momentum=5.0),
        ]]
        base_runtime_params = {
            "buy_threshold": 0.98,
            "buy_near_threshold_min_prob": 0.94,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 0.7,
            "min_entry_price_volatility": 0.05,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.7,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
        }
        expanded_runtime_params = {
            **base_runtime_params,
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_runner_retention_rescue_max_feature_values": '{"price_momentum": 10.0}',
        }

        def fake_score_samples(samples, buy_artifact):
            buy_probs = []
            entry_scores = []
            for sample in samples:
                token = sample.get("meta", {}).get("token_address")
                buy_probs.append(0.99 if token == "0xbase" else 0.90)
                entry_scores.append(36.0)
            return buy_probs, entry_scores

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=expanded_runtime_params,
                base_runtime_params=base_runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["rescue_flow_filter_active"])
        self.assertTrue(metadata["rescue_feature_bound_filter_active"])
        self.assertEqual(metadata["rescue_max_feature_values"], {"price_momentum": 10.0})
        self.assertEqual(score_maps[0][0], 1.0)
        self.assertIn(1, score_maps[0])
        self.assertNotIn(2, score_maps[0])
        self.assertEqual(metadata["preserved_base_candidate_count"], 1)
        self.assertEqual(metadata["scored_rescue_candidate_count"], 1)

    def test_generic_feature_bound_filter_rejects_label_like_features(self):
        sample = _sample("0xleak", sample_time=4000)
        runtime_params = {
            "buy_runner_retention_rescue_max_feature_values": {"future_return_pct": 10.0},
        }

        with self.assertRaises(ValueError):
            gate._passes_rescue_flow_compatibility(sample, runtime_params)

    def test_flow_compatibility_filter_accepts_dataset_builder_flow_names(self):
        sample = _dataset_flow_sample("0xdataset", sample_time=4000)
        runtime_params = {
            "buy_runner_retention_rescue_min_flow_total_volume_30s": 1.0,
            "buy_runner_retention_rescue_min_flow_buy_volume_30s": 0.9,
            "buy_runner_retention_rescue_min_flow_event_count_30s": 2,
            "buy_runner_retention_rescue_min_flow_signed_imbalance_30s": 0.5,
            "buy_runner_retention_rescue_min_flow_buy_sell_ratio_30s": 3.0,
            "buy_runner_retention_rescue_max_flow_sell_pressure_30s": 0.35,
        }

        self.assertTrue(gate._passes_rescue_flow_compatibility(sample, runtime_params))

    def test_cli_detects_flow_features_inside_generic_feature_bounds(self):
        cli = _load_cli()

        self.assertTrue(cli.candidate_grid_requires_flow_features([{
            "buy_runner_retention_rescue_max_feature_values": {"flow_sell_pressure_30s": 0.35},
        }]))
        self.assertTrue(cli.candidate_grid_requires_flow_features([{
            "buy_runner_retention_rescue_max_feature_values": '{"flow_sell_pressure_30s": 0.35}',
        }]))
        self.assertFalse(cli.candidate_grid_requires_flow_features([{
            "buy_runner_retention_rescue_max_feature_values": {"price_momentum": 10.0},
        }]))

    def test_added_trade_boundary_rule_matches_feature_rows(self):
        row = {
            "features": {
                "retail_entry_rate_ratio_30s": 1.0,
                "time_since_launch": 180.0,
            }
        }
        rule = {
            "conditions": [
                {"feature": "retail_entry_rate_ratio_30s", "operator": "<=", "threshold": 1.1911726598514814},
                {"feature": "time_since_launch", "operator": "<=", "threshold": 226.0},
            ]
        }

        self.assertTrue(gate._passes_added_trade_boundary_rule(row, rule))
        self.assertFalse(
            gate._passes_added_trade_boundary_rule(
                row,
                {
                    "conditions": [
                        {"feature": "retail_entry_rate_ratio_30s", "operator": "<=", "threshold": 0.5},
                        {"feature": "time_since_launch", "operator": "<=", "threshold": 226.0},
                    ]
                },
            )
        )

    def test_train_boundary_feature_is_soft_signal_not_hard_filter(self):
        train_samples = [
            _sample("0xslow", sample_time=1000, flow_sell_pressure_30s=0.1),
            _sample("0xflat", sample_time=2000, flow_sell_pressure_30s=0.9),
        ]
        eval_episodes = [[
            _sample("0xmatch", sample_time=3000, flow_sell_pressure_30s=0.1),
            _sample("0xmiss", sample_time=3010, flow_sell_pressure_30s=0.9),
            _sample("0xlast", sample_time=3020, flow_sell_pressure_30s=0.1),
        ]]
        runtime_params = {
            "buy_threshold": 0.99,
            "buy_near_threshold_min_prob": 0.85,
            "min_entry_score": 35.0,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_runner_retention_train_boundary_feature_enabled": True,
            "buy_runner_retention_train_boundary_min_keep_count": 1,
            "buy_runner_retention_train_boundary_min_reject_count": 1,
            "buy_runner_retention_train_boundary_max_conditions": 1,
            "buy_runner_retention_train_boundary_beam_width": 10,
        }

        def fake_score_samples(samples, buy_artifact):
            return [0.90 for _sample in samples], [36.0 for _sample in samples]

        with patch.object(gate.ranker_probe, "_score_samples", side_effect=fake_score_samples):
            score_maps, metadata = gate.fit_runner_retention_candidate_gate_and_score_episodes(
                train_samples=train_samples,
                train_price_paths_by_token={
                    "0xslow": _path(1000, kind="slow_runner"),
                    "0xflat": _path(2000, kind="flat"),
                },
                eval_episodes=eval_episodes,
                buy_artifact={},
                runtime_params=runtime_params,
                max_depth=1,
                min_samples_leaf=1,
                min_common_features=1,
            )

        self.assertTrue(metadata["trained"])
        self.assertTrue(metadata["train_boundary_feature_enabled"])
        self.assertTrue(metadata["train_boundary_feature_active"])
        self.assertIn("runner_retention_train_boundary_match", metadata["feature_names"])
        self.assertIn("runner_retention_train_boundary_condition_fraction", metadata["feature_names"])
        self.assertEqual(sorted(key for key in score_maps[0] if isinstance(key, int)), [0, 1])
        self.assertEqual(metadata["scored_rescue_candidate_count"], 2)
        self.assertEqual(metadata["boundary_rejected_rescue_candidate_count"], 0)

    def test_train_boundary_feature_report_uses_optional_search_row_cap(self):
        rows = [
            {
                "features": {"flow_sell_pressure_30s": index / 10},
                "label_positive": index % 2 == 0,
                "sample_time": index,
                "token": f"0x{index}",
            }
            for index in range(6)
        ]
        runtime_params = {
            "buy_runner_retention_train_boundary_feature_enabled": True,
            "buy_runner_retention_train_boundary_max_rows": 2,
        }

        with patch.object(
            gate.boundary_probe,
            "build_added_trade_boundary_policy_report",
            return_value={"selected_rule": None},
        ) as build_report:
            report = gate._train_boundary_feature_report(rows, runtime_params)

        self.assertEqual(report["source_row_count"], 6)
        self.assertEqual(report["search_row_count"], 2)
        self.assertEqual(report["max_rows"], 2)
        self.assertEqual(len(build_report.call_args.kwargs["validation_rows"]), 2)

    def test_training_balancer_keeps_all_positives_and_caps_negatives(self):
        rows = [
            {"token": "0xpos1", "sample_time": 1, "label_positive": True},
            {"token": "0xpos2", "sample_time": 2, "label_positive": True},
        ] + [
            {
                "token": f"0xneg{index}",
                "sample_time": 100 + index,
                "label_positive": False,
                "retention_label": "flat_timeout" if index % 2 else "stop_first_collapse",
            }
            for index in range(20)
        ]

        balanced = gate._balanced_training_rows(rows, max_negative_count=5)

        self.assertEqual(sum(1 for row in balanced if row["label_positive"]), 2)
        self.assertEqual(sum(1 for row in balanced if not row["label_positive"]), 5)
        self.assertEqual(len(balanced), 7)

    def test_cli_writes_strict_runner_retention_candidate_gate_report(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_path_state_meta_gate_min_score": 0.55,
        }])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runner_retention_gate_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                return_value=([{"0": 0.75}], {"trained": True}),
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(saved["decision"], "accept")
        self.assertFalse(saved["live_switch_evidence"])
        self.assertEqual([call["split"] for call in calls], ["validation", "validation", "final", "final"])
        self.assertNotIn("buy_near_threshold_min_prob", calls[0]["overrides"])
        self.assertEqual(calls[1]["overrides"]["buy_near_threshold_min_prob"], 0.85)
        self.assertIn("path_state_scores_by_episode", calls[1]["overrides"])
        self.assertNotIn(
            "path_state_scores_by_episode",
            saved["candidates"][0]["replay_metadata"]["replay_config"],
        )
        self.assertEqual(
            saved["candidates"][0]["replay_metadata"]["replay_config"]["path_state_scores_by_episode_summary"],
            {
                "episode_count": 1,
                "non_empty_episode_count": 1,
                "scored_sample_count": 1,
                "max_episode_score_count": 1,
            },
        )

    def test_cli_passes_preserve_base_candidates_to_score_builder(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_path_state_meta_gate_min_score": 0.85,
        }])
        score_calls = []

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        def fake_score_maps(*args, **kwargs):
            score_calls.append(kwargs)
            return ([{"0": 1.0, "1": 0.9}], {"trained": True})

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runner_retention_preserve_base_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                side_effect=fake_score_maps,
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main([
                        "--output",
                        str(output_path),
                        "--preserve-base-candidates",
                        "--early-replacement-max-lead-seconds",
                        "15",
                    ])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual([call["preserve_base_candidates"] for call in score_calls], [True, True])
        self.assertEqual([call["early_replacement_max_lead_seconds"] for call in score_calls], [15, 15])
        self.assertTrue(saved["precision_guard"]["preserve_base_candidates"])
        self.assertEqual(saved["precision_guard"]["early_replacement_max_lead_seconds"], 15)

    def test_cli_can_load_candidate_grid_from_json(self):
        cli = _load_cli()
        calls = []
        score_calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": {
                    "net_profit_bnb": 0.002 if is_candidate else 0.001,
                    "total_trades": 10,
                    "max_drawdown_pct": -8.0,
                    "win_rate": 0.7,
                    "walk_forward_worst_net_return_pct": 4.0,
                    "walk_forward_worst_max_drawdown_pct": -10.0,
                    "stress_replay": [{
                        "name": "harsh_friction",
                        "net_return_pct": 3.0,
                        "net_profit_bnb": 0.0005,
                        "max_drawdown_pct": -11.0,
                    }],
                    "path_state_meta_gate_entry_count": int(is_candidate),
                    "path_state_meta_gate_signal_count": int(is_candidate),
                },
            }

        def fake_score_maps(*args, **kwargs):
            score_calls.append(kwargs)
            return ([{"0": 0.8}], {"trained": True})

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            grid_path = tmpdir_path / "grid.json"
            grid_path.write_text(json.dumps([{
                "buy_near_threshold_min_prob": 0.875,
                "buy_near_min_pred_return": 35.0,
                "buy_near_min_entry_volume_30s": 1.0,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
                "buy_path_state_meta_gate_min_score": 0.6,
                "buy_runner_retention_rescue_max_flow_sell_pressure_30s": 0.35,
            }]), encoding="utf-8")
            output_path = tmpdir_path / "runner_retention_json_grid_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [{"meta": {"token_address": f"0x{split}", "sample_time": 1}}],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                side_effect=fake_score_maps,
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path), "--candidate-grid-json", str(grid_path)])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(len(saved["candidates"]), 1)
        self.assertEqual(
            saved["candidates"][0]["params"]["buy_runner_retention_rescue_max_flow_sell_pressure_30s"],
            0.35,
        )
        self.assertEqual(
            score_calls[0]["candidate_params"]["buy_runner_retention_rescue_max_flow_sell_pressure_30s"],
            0.35,
        )
        self.assertTrue(saved["candidate_grid"]["requires_flow_features"])
        self.assertTrue(calls[0]["overrides"]["include_flow_features"])
        self.assertEqual(calls[1]["overrides"]["buy_near_min_entry_volume_30s"], 1.0)

    def test_cli_can_apply_added_trade_boundary_report(self):
        cli = _load_cli()
        score_calls = []

        boundary_report = {
            "decision": "shadow_promote_to_replay",
            "contract": {"uses_decision_time_features_only": True},
            "config": {"rule_family": "multi_feature_conjunction_keep_rule"},
            "selected_rule": {
                "conditions": [
                    {"feature": "retail_entry_rate_ratio_30s", "operator": "<=", "threshold": 1.1911726598514814},
                    {"feature": "time_since_launch", "operator": "<=", "threshold": 226.0},
                ]
            },
        }

        def fake_run_model_replay(**kwargs):
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            trade_log = [{"token": "0xaaa", "entry_signal_time": 100, "entry_time": 101, "return_pct": 10.0}]
            if is_candidate:
                trade_log.append({"token": "0xbbb", "entry_signal_time": 200, "entry_time": 201, "return_pct": -20.0})
            evaluation = {
                "net_profit_bnb": 0.002 if is_candidate else 0.001,
                "total_trades": len(trade_log),
                "max_drawdown_pct": -8.0,
                "win_rate": 0.5 if is_candidate else 1.0,
                "walk_forward_worst_net_return_pct": 4.0,
                "walk_forward_worst_max_drawdown_pct": -10.0,
                "stress_replay": [{
                    "name": "harsh_friction",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0005,
                    "max_drawdown_pct": -11.0,
                }],
                "path_state_meta_gate_entry_count": int(is_candidate),
                "path_state_meta_gate_signal_count": int(is_candidate),
            }
            if kwargs.get("include_trade_log"):
                evaluation["trade_log"] = trade_log
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": evaluation,
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            boundary_path = tmpdir_path / "boundary.json"
            boundary_path.write_text(json.dumps(boundary_report), encoding="utf-8")
            output_path = tmpdir_path / "runner_retention_boundary_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [
                        {
                            "meta": {"token_address": "0xaaa", "sample_time": 100},
                            "features": {
                                "retail_entry_rate_ratio_30s": 1.0,
                                "time_since_launch": 180.0,
                            },
                        },
                        {
                            "meta": {"token_address": "0xbbb", "sample_time": 200},
                            "features": {
                                "retail_entry_rate_ratio_30s": 2.0,
                                "time_since_launch": 240.0,
                            },
                        },
                    ],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                side_effect=lambda *args, **kwargs: (
                    score_calls.append(kwargs) or ([{"0": 0.75, "1": 0.75}], {"trained": True})
                ),
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main([
                        "--output",
                        str(output_path),
                        "--added-trade-boundary-report",
                        str(boundary_path),
                    ])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertGreater(len(score_calls), 0)
        self.assertTrue(
            all(call["added_trade_boundary_rule"] == boundary_report["selected_rule"] for call in score_calls)
        )
        self.assertEqual(saved["precision_guard"]["added_trade_boundary"]["source"], str(boundary_path))

    def test_cli_can_write_selected_trade_delta_attribution(self):
        cli = _load_cli()
        cli.candidate_grid = lambda: iter([{
            "buy_near_threshold_min_prob": 0.85,
            "buy_near_min_pred_return": 32.0,
            "buy_near_min_entry_volume_30s": 0.6,
            "buy_near_min_entry_price_volatility": 0.05,
            "buy_near_min_age_seconds": 0.0,
            "buy_path_state_meta_gate_min_score": 0.55,
        }])
        calls = []

        def fake_run_model_replay(**kwargs):
            calls.append(kwargs)
            overrides = dict(kwargs.get("overrides") or {})
            is_candidate = "buy_path_state_meta_gate_min_score" in overrides
            trade_log = [{
                "token": "0xaaa",
                "entry_signal_time": 100,
                "entry_time": 101,
                "return_pct": 10.0,
                "exit_reason": "TRAILING_STOP",
            }]
            if is_candidate:
                trade_log.append({
                    "token": "0xbbb",
                    "entry_signal_time": 200,
                    "entry_time": 201,
                    "return_pct": -20.0,
                    "exit_reason": "STOP_LOSS",
                })
            evaluation = {
                "net_profit_bnb": 0.002 if is_candidate else 0.001,
                "total_trades": len(trade_log),
                "max_drawdown_pct": -8.0,
                "win_rate": 0.5 if is_candidate else 1.0,
                "walk_forward_worst_net_return_pct": 4.0,
                "walk_forward_worst_max_drawdown_pct": -10.0,
                "stress_replay": [{
                    "name": "harsh_friction",
                    "net_return_pct": 3.0,
                    "net_profit_bnb": 0.0005,
                    "max_drawdown_pct": -11.0,
                }],
                "path_state_meta_gate_entry_count": int(is_candidate),
                "path_state_meta_gate_signal_count": int(is_candidate),
            }
            if kwargs.get("include_trade_log"):
                evaluation["trade_log"] = trade_log
            return {
                "generated_at": "2026-05-26T00:00:00+00:00",
                "split": kwargs["split"],
                "selection_role": "report_only",
                "git": {"commit": "abc123"},
                "model_checksums": {"buy_model.cbm": "sha256"},
                "replay_config": dict(overrides),
                "sample_count": 2,
                "lifecycle_paths": ["data/training/a.json"],
                "evaluation": evaluation,
            }

        fake_module = types.ModuleType("src.pipeline.model_replay")
        fake_module.run_model_replay = fake_run_model_replay

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "runner_retention_delta_report.json"
            with patch.dict(sys.modules, {"src.pipeline.model_replay": fake_module}), patch.object(
                cli,
                "_load_common_context",
                return_value={
                    "split_samples": lambda split: [
                        {"meta": {"token_address": "0xaaa", "sample_time": 100}, "features": {"depth": 10.0}},
                        {"meta": {"token_address": "0xbbb", "sample_time": 200}, "features": {"depth": 2.0}},
                    ],
                },
            ), patch.object(
                cli,
                "_runner_retention_score_maps_for_split",
                return_value=([{"0": 0.75, "1": 0.75}], {"trained": True}),
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    cli.main(["--output", str(output_path), "--write-selected-trade-delta"])
            saved = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertIn("selected_trade_delta_attribution", saved)
        self.assertEqual(
            saved["selected_trade_delta_attribution"]["validation"]["delta_summary"]["added_candidate_trades"]["trade_count"],
            1,
        )
        self.assertTrue(any(call["include_trade_log"] for call in calls))


if __name__ == "__main__":
    unittest.main()
