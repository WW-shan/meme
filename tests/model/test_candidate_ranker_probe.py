import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "candidate_ranker_probe.py"
    spec = importlib.util.spec_from_file_location("candidate_ranker_probe", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCandidateRankerProbe(unittest.TestCase):
    def test_relevance_prefers_clean_runner_over_medium_and_collapse(self):
        module = _load_module()

        self.assertEqual(
            module.candidate_relevance(
                {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 75.0}
            ),
            3.0,
        )
        self.assertEqual(
            module.candidate_relevance(
                {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 32.0}
            ),
            2.0,
        )
        self.assertEqual(
            module.candidate_relevance(
                {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 1.2}
            ),
            1.0,
        )
        self.assertEqual(
            module.candidate_relevance(
                {"live_target_hit_before_stop": 0, "live_risk_adjusted_return_pct": -20.0}
            ),
            0.0,
        )

    def test_candidate_rows_keep_v95_primary_and_near_gate_only(self):
        module = _load_module()

        def sample(token, volume_30s, price_volatility):
            return {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": volume_30s,
                    "price_volatility": price_volatility,
                },
                "label": {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 70.0},
                "meta": {"token_address": token, "sample_time": 120, "create_timestamp": 100},
            }

        rows = module.build_candidate_rows(
            [
                sample("0xprimary", 1.5, 0.10),
                sample("0xnear", 1.25, 0.08),
                sample("0xnear_low_score", 1.25, 0.08),
                sample("0xlow_prob", 5.0, 0.50),
            ],
            buy_probabilities=[0.99, 0.95, 0.95, 0.93],
            entry_scores=[40.0, 33.0, 20.0, 80.0],
            runtime_params={
                "buy_threshold": 0.98,
                "min_entry_score": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "max_entry_age_seconds": 300,
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
            },
        )

        self.assertEqual([row["token"] for row in rows], ["0xprimary", "0xnear"])
        self.assertEqual(rows[0]["candidate_source"], "primary")
        self.assertEqual(rows[1]["candidate_source"], "near")
        self.assertEqual(rows[1]["entry_volume_30s"], 1.25)

    def test_score_samples_ignores_optional_flow_features_for_non_flow_model(self):
        module = _load_module()

        class BuyModel:
            def __init__(self):
                self.frames = []

            def predict_proba(self, X):
                self.frames.append(X.copy())
                return [[0.2, 0.8] for _ in range(len(X))]

        class EntryModel:
            def __init__(self):
                self.frames = []

            def predict(self, X):
                self.frames.append(X.copy())
                return [42.0 for _ in range(len(X))]

        buy_model = BuyModel()
        entry_model = EntryModel()
        probabilities, entry_scores = module._score_samples(
            [
                {
                    "features": {
                        "current_price": 1.0,
                        "sell_volume_30s": 0.25,
                        "total_flow_volume_30s": 1.25,
                        "sell_pressure_30s": 0.2,
                        "signed_imbalance_30s": 0.6,
                    },
                    "meta": {"token_address": "0xflow", "sample_time": 120, "create_timestamp": 100},
                }
            ],
            {
                "model": buy_model,
                "entry_value_model": {"model": entry_model},
                "feature_names": ["current_price"],
                "dropped_features": [],
            },
        )

        self.assertEqual(probabilities, [0.8])
        self.assertEqual(entry_scores, [42.0])
        self.assertEqual(list(buy_model.frames[0].columns), ["current_price"])
        self.assertEqual(list(entry_model.frames[0].columns), ["current_price"])

    def test_shadow_score_rejects_are_default_off(self):
        module = _load_module()

        sample = {
            "features": {
                "current_price": 1.0,
                "volume_30s": 3.2,
                "price_volatility": 0.27,
            },
            "label": {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 70.0},
            "meta": {"token_address": "0xshadow", "sample_time": 109, "create_timestamp": 100},
        }

        rows = module.build_candidate_rows(
            [sample],
            buy_probabilities=[0.989],
            entry_scores=[-4.5],
            runtime_params={
                "buy_threshold": 0.98,
                "min_entry_score": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "max_entry_age_seconds": 300,
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
            },
        )

        self.assertEqual(rows, [])

    def test_shadow_score_rejects_include_high_prob_quality_score_rejects(self):
        module = _load_module()

        def sample(token, age, volume_30s=3.2, price_volatility=0.27):
            return {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": volume_30s,
                    "price_volatility": price_volatility,
                    "token_age_seconds": age,
                },
                "label": {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 70.0},
                "meta": {"token_address": token, "sample_time": 100 + age, "create_timestamp": 100},
            }

        rows = module.build_candidate_rows(
            [
                sample("0xaccepted", 5),
                sample("0xshadow", 9),
            ],
            buy_probabilities=[0.989, 0.989],
            entry_scores=[40.0, -4.5],
            runtime_params={
                "buy_threshold": 0.98,
                "min_entry_score": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "max_entry_age_seconds": 300,
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
                "include_shadow_score_rejects": True,
                "shadow_min_prob": 0.988,
                "shadow_max_entry_score": 10.0,
                "shadow_min_entry_volume_30s": 2.0,
                "shadow_min_entry_price_volatility": 0.20,
                "shadow_max_age_seconds": 60,
            },
        )

        self.assertEqual([row["token"] for row in rows], ["0xaccepted", "0xshadow"])
        self.assertEqual(rows[0]["candidate_source"], "primary")
        self.assertEqual(rows[1]["candidate_source"], "shadow_score_reject")
        self.assertEqual(rows[1]["entry_score"], -4.5)

    def test_shadow_score_rejects_apply_prob_quality_score_and_age_guards(self):
        module = _load_module()

        def sample(token, age, volume_30s=3.2, price_volatility=0.27):
            return {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": volume_30s,
                    "price_volatility": price_volatility,
                    "token_age_seconds": age,
                },
                "label": {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 70.0},
                "meta": {"token_address": token, "sample_time": 100 + age, "create_timestamp": 100},
            }

        rows = module.build_candidate_rows(
            [
                sample("0xlowprob", 9),
                sample("0xscore_too_high", 9),
                sample("0xlow_volume", 9, volume_30s=1.99),
                sample("0xlow_volatility", 9, price_volatility=0.19),
                sample("0xold", 61),
                sample("0xvalid", 9),
            ],
            buy_probabilities=[0.987, 0.989, 0.989, 0.989, 0.989, 0.989],
            entry_scores=[-4.5, 15.0, -4.5, -4.5, -4.5, -4.5],
            runtime_params={
                "buy_threshold": 0.98,
                "min_entry_score": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "max_entry_age_seconds": 300,
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
                "include_shadow_score_rejects": True,
                "shadow_min_prob": 0.988,
                "shadow_max_entry_score": 10.0,
                "shadow_min_entry_volume_30s": 2.0,
                "shadow_min_entry_price_volatility": 0.20,
                "shadow_max_age_seconds": 60,
            },
        )

        self.assertEqual([row["token"] for row in rows], ["0xvalid"])

    def test_shadow_score_rejects_keep_probability_guard_when_threshold_missing(self):
        module = _load_module()

        sample = {
            "features": {
                "current_price": 1.0,
                "volume_30s": 3.2,
                "price_volatility": 0.27,
                "token_age_seconds": 9,
            },
            "label": {"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 70.0},
            "meta": {"token_address": "0xlowprob", "sample_time": 109, "create_timestamp": 100},
        }

        rows = module.build_candidate_rows(
            [sample],
            buy_probabilities=[0.5],
            entry_scores=[-4.5],
            runtime_params={
                "min_entry_score": 35.0,
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "max_entry_age_seconds": 300,
                "include_shadow_score_rejects": True,
                "shadow_max_entry_score": 10.0,
                "shadow_min_entry_volume_30s": 2.0,
                "shadow_min_entry_price_volatility": 0.20,
                "shadow_max_age_seconds": 60,
            },
        )

        self.assertEqual(rows, [])

    def test_shadow_ranker_score_maps_preserve_episode_indices_for_shadow_candidates(self):
        module = _load_module()

        def sample(token, relevance=70.0):
            return {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": 3.2,
                    "price_volatility": 0.27,
                    "token_age_seconds": 9,
                },
                "label": {
                    "live_target_hit_before_stop": 1,
                    "live_risk_adjusted_return_pct": relevance,
                },
                "meta": {"token_address": token, "sample_time": 109, "create_timestamp": 100},
            }

        def fake_score_samples(samples, _buy_artifact):
            probabilities = []
            entry_scores = []
            for row in samples:
                token = row["meta"]["token_address"]
                if token.endswith("primary"):
                    probabilities.append(0.989)
                    entry_scores.append(40.0)
                elif token.endswith("lowprob"):
                    probabilities.append(0.5)
                    entry_scores.append(-4.5)
                else:
                    probabilities.append(0.989)
                    entry_scores.append(-4.5)
            return probabilities, entry_scores

        def fake_predict(_model, rows, _buy_artifact):
            scores = []
            for row in rows:
                scores.append(0.75 if row["candidate_source"] == "shadow_score_reject" else 0.10)
            return scores

        train_samples = [sample("0xtrainshadow", 70.0), sample("0xtraincollapse", 0.0)]
        eval_episodes = [[
            sample("0xevalprimary"),
            sample("0xevalshadow"),
            sample("0xevallowprob"),
        ]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.10,
            "max_entry_age_seconds": 300,
            "shadow_min_prob": 0.988,
            "shadow_max_entry_score": 10.0,
            "shadow_min_entry_volume_30s": 2.0,
            "shadow_min_entry_price_volatility": 0.20,
            "shadow_max_age_seconds": 60,
        }

        with patch.object(module, "_score_samples", side_effect=fake_score_samples), patch.object(
            module, "_train_ranker", return_value=object()
        ), patch.object(module, "_predict_ranker", side_effect=fake_predict):
            score_maps = module.fit_shadow_ranker_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertEqual(score_maps, [{1: 0.75}])

    def test_shadow_ranker_score_maps_return_empty_maps_when_training_has_no_relevance_variety(self):
        module = _load_module()

        sample = {
            "features": {
                "current_price": 1.0,
                "volume_30s": 3.2,
                "price_volatility": 0.27,
                "token_age_seconds": 9,
            },
            "label": {"live_target_hit_before_stop": 0, "live_risk_adjusted_return_pct": -20.0},
            "meta": {"token_address": "0xshadow", "sample_time": 109, "create_timestamp": 100},
        }

        with patch.object(module, "_score_samples", return_value=([0.989], [-4.5])), patch.object(
            module, "_train_ranker"
        ) as train_ranker:
            score_maps = module.fit_shadow_ranker_and_score_episodes(
                [sample],
                [[sample]],
                buy_artifact={"model": object()},
                runtime_params={
                    "buy_threshold": 0.98,
                    "min_entry_score": 35.0,
                    "min_entry_volume_30s": 1.5,
                    "min_entry_price_volatility": 0.10,
                    "shadow_min_prob": 0.988,
                    "shadow_max_entry_score": 10.0,
                    "shadow_min_entry_volume_30s": 2.0,
                    "shadow_min_entry_price_volatility": 0.20,
                    "shadow_max_age_seconds": 60,
                },
            )

        self.assertEqual(score_maps, [{}])
        train_ranker.assert_not_called()

    def test_prefilter_respects_explicit_zero_shadow_quality_floors(self):
        module = _load_module()

        def sample(token, volume_30s, price_volatility):
            return {
                "features": {
                    "current_price": 1.0,
                    "volume_30s": volume_30s,
                    "price_volatility": price_volatility,
                    "token_age_seconds": 9,
                },
                "meta": {"token_address": token, "sample_time": 109, "create_timestamp": 100},
            }

        out = module.prefilter_candidate_samples(
            [
                sample("0xshadow_zero_quality", 0.1, 0.01),
                sample("0xno_price", 3.2, 0.27),
            ],
            {
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "max_entry_age_seconds": 300,
                "include_shadow_score_rejects": True,
                "shadow_min_entry_volume_30s": 0.0,
                "shadow_min_entry_price_volatility": 0.0,
                "shadow_max_age_seconds": 60,
            },
        )

        self.assertEqual([row["meta"]["token_address"] for row in out], ["0xshadow_zero_quality", "0xno_price"])

    def test_group_ids_bucket_by_sample_time(self):
        module = _load_module()
        rows = [
            {"sample_time": 100, "token": "0xa"},
            {"sample_time": 119, "token": "0xb"},
            {"sample_time": 141, "token": "0xc"},
        ]

        self.assertEqual(module.assign_group_ids(rows, bucket_seconds=30), ["100", "100", "130"])

    def test_file_fingerprints_record_exact_inputs(self):
        module = _load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "lifecycle.jsonl"
            path.write_text('{"token":"0x1"}\n', encoding="utf-8")
            out = module._file_fingerprints([path])

        self.assertEqual(out[0]["name"], "lifecycle.jsonl")
        self.assertTrue(out[0]["exists"])
        self.assertEqual(out[0]["size_bytes"], 16)
        self.assertEqual(len(out[0]["sha256"]), 64)

    def test_prefilter_candidate_samples_uses_union_of_primary_and_near_quality_gates(self):
        module = _load_module()

        def sample(token, volume_30s, price_volatility, price=1.0):
            return {
                "features": {
                    "current_price": price,
                    "volume_30s": volume_30s,
                    "price_volatility": price_volatility,
                },
                "meta": {"token_address": token, "sample_time": 120, "create_timestamp": 100},
            }

        out = module.prefilter_candidate_samples(
            [
                sample("0xnear_quality", 1.25, 0.08),
                sample("0xlow_volume", 1.24, 0.20),
                sample("0xlow_volatility", 2.0, 0.079),
                sample("0xno_price", 5.0, 0.50, price=0.0),
            ],
            {
                "min_entry_volume_30s": 1.5,
                "min_entry_price_volatility": 0.10,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "max_entry_age_seconds": 300,
            },
        )

        self.assertEqual([row["meta"]["token_address"] for row in out], ["0xnear_quality"])

    def test_runtime_params_use_buy_artifact_threshold_when_manifest_omits_buy_threshold(self):
        module = _load_module()

        params = module.runtime_params_with_buy_threshold(
            {"buy_threshold": None, "min_entry_score": 35.0, "buy_near_min_age_seconds": 0.0},
            {"threshold": 0.98},
        )

        self.assertEqual(params["buy_threshold"], 0.98)
        self.assertEqual(params["min_entry_score"], 35.0)
        self.assertEqual(params["buy_near_min_age_seconds"], 0.0)

    def test_runtime_params_for_report_includes_complete_near_gate(self):
        module = _load_module()

        out = module.runtime_params_for_report(
            {
                "buy_threshold": 0.98,
                "buy_near_threshold_min_prob": 0.94,
                "buy_near_min_pred_return": 32.0,
                "buy_near_min_entry_volume_30s": 1.25,
                "buy_near_min_entry_price_volatility": 0.08,
                "buy_near_min_age_seconds": 0.0,
                "include_shadow_score_rejects": True,
                "shadow_min_prob": 0.988,
                "shadow_max_entry_score": 10.0,
                "shadow_min_entry_volume_30s": 2.0,
                "shadow_min_entry_price_volatility": 0.20,
                "shadow_max_age_seconds": 60,
            }
        )

        self.assertEqual(out["buy_near_min_age_seconds"], 0.0)
        self.assertTrue(out["include_shadow_score_rejects"])
        self.assertEqual(out["shadow_min_prob"], 0.988)
        self.assertEqual(out["shadow_max_age_seconds"], 60)

    def test_runtime_params_for_report_includes_shadow_gate(self):
        module = _load_module()

        out = module.runtime_params_for_report(
            {
                "include_shadow_score_rejects": True,
                "shadow_min_prob": 0.985,
                "shadow_max_entry_score": 10.0,
                "shadow_min_entry_volume_30s": 3.0,
                "shadow_min_entry_price_volatility": 0.20,
                "shadow_max_age_seconds": 30.0,
            }
        )

        self.assertIs(out["include_shadow_score_rejects"], True)
        self.assertEqual(out["shadow_min_prob"], 0.985)
        self.assertEqual(out["shadow_max_entry_score"], 10.0)
        self.assertEqual(out["shadow_min_entry_volume_30s"], 3.0)
        self.assertEqual(out["shadow_min_entry_price_volatility"], 0.20)
        self.assertEqual(out["shadow_max_age_seconds"], 30.0)


    def test_evaluate_ranker_predictions_compares_ranker_to_entry_value_baseline(self):
        module = _load_module()
        rows = [
            {"token": "0xa", "group_id": "g1", "entry_score": 90.0, "relevance": 0.0},
            {"token": "0xb", "group_id": "g1", "entry_score": 10.0, "relevance": 3.0},
            {"token": "0xc", "group_id": "g2", "entry_score": 50.0, "relevance": 1.0},
            {"token": "0xd", "group_id": "g2", "entry_score": 40.0, "relevance": 0.0},
        ]

        out = module.evaluate_ranker_predictions(rows, predictions=[0.1, 0.9, 0.8, 0.2], top_k_per_group=1)

        self.assertEqual(out["group_count"], 2)
        self.assertEqual(out["ranker_top_relevance_sum"], 4.0)
        self.assertEqual(out["entry_value_top_relevance_sum"], 1.0)
        self.assertEqual(out["ranker_clean_runner_top_count"], 1)

    def test_predict_ranker_preserves_duplicate_token_time_rows(self):
        module = _load_module()

        class FakeRanker:
            def predict(self, X):
                return [0.1, 0.9]

        rows = [
            {"token": "0xdup", "group_id": "g1", "sample_time": 100, "features": {"current_price": 1.0}},
            {"token": "0xdup", "group_id": "g1", "sample_time": 100, "features": {"current_price": 1.1}},
        ]

        with patch.object(module, "_rows_to_frame", return_value=[object(), object()]):
            out = module._predict_ranker(FakeRanker(), rows, {})

        self.assertEqual(out, [0.1, 0.9])

    def test_load_split_samples_allows_raw_overlap_and_excludes_prior_tokens(self):
        module = _load_module()
        load_calls = []
        split_result = {
            "train_files": [Path("train.jsonl")],
            "validation_files": [Path("validation.jsonl")],
            "eval_files": [Path("final.jsonl")],
            "raw_train_validation_overlap_count": 1,
            "raw_train_eval_overlap_count": 1,
            "raw_validation_eval_overlap_count": 1,
            "raw_final_overlap_token_count": 1,
            "train_raw_tokens": {"0xtrain"},
            "validation_raw_tokens": {"0xvalidation"},
            "eval_raw_tokens": {"0xfinal"},
        }

        def fake_load_or_build_samples(config, lifecycle_paths, exclude_tokens, *, cache_dir, use_cache):
            load_calls.append(
                {
                    "config": dict(config),
                    "lifecycle_paths": list(lifecycle_paths),
                    "exclude_tokens": set(exclude_tokens),
                    "cache_dir": cache_dir,
                    "use_cache": use_cache,
                }
            )
            token = f"0xsample{len(load_calls)}"
            return [{"meta": {"token_address": token}}]

        with patch("src.pipeline.train_hybrid._discover_lifecycle_files", return_value=[Path("a"), Path("b"), Path("c"), Path("d")]), \
             patch("src.pipeline.train_hybrid._split_lifecycle_files_three_way", return_value=split_result) as mock_split, \
             patch("src.pipeline.model_replay.load_or_build_samples", side_effect=fake_load_or_build_samples):
            _, split_meta = module._load_split_samples(
                lifecycle_dir="data/training",
                runtime_params={"sample_mode": "trade_event"},
                train_split_ratio=0.6,
                validation_split_ratio=0.2,
                min_validation_files=1,
                min_eval_files=1,
                max_samples_per_token=80,
                sample_cache_dir=".cache/probe-test",
                max_lifecycle_files=3,
            )

        self.assertFalse(mock_split.call_args.kwargs["enforce_no_overlap"])
        self.assertEqual(mock_split.call_args.args[0], [Path("b"), Path("c"), Path("d")])
        self.assertEqual(load_calls[0]["exclude_tokens"], set())
        self.assertEqual(load_calls[1]["exclude_tokens"], {"0xtrain"})
        self.assertEqual(load_calls[2]["exclude_tokens"], {"0xtrain", "0xvalidation"})
        self.assertEqual(load_calls[0]["cache_dir"], ".cache/probe-test")
        self.assertTrue(load_calls[0]["use_cache"])
        self.assertEqual(split_meta["sample_train_validation_overlap_count"], 0)
        self.assertEqual(split_meta["sample_train_final_overlap_count"], 0)
        self.assertEqual(split_meta["sample_validation_final_overlap_count"], 0)
        self.assertEqual(split_meta["train_files"], ["train.jsonl"])
        self.assertEqual(split_meta["validation_files"], ["validation.jsonl"])
        self.assertEqual(split_meta["final_files"], ["final.jsonl"])
        self.assertIn("train_file_fingerprints", split_meta)

    def test_load_split_samples_accepts_explicit_lifecycle_files(self):
        module = _load_module()
        split_result = {
            "train_files": [Path("explicit_a.jsonl")],
            "validation_files": [Path("explicit_b.jsonl")],
            "eval_files": [Path("explicit_c.jsonl")],
            "raw_train_validation_overlap_count": 0,
            "raw_train_eval_overlap_count": 0,
            "raw_validation_eval_overlap_count": 0,
            "raw_final_overlap_token_count": 0,
            "train_raw_tokens": set(),
            "validation_raw_tokens": set(),
            "eval_raw_tokens": set(),
        }

        with patch("src.pipeline.train_hybrid._discover_lifecycle_files") as mock_discover, \
             patch("src.pipeline.train_hybrid._split_lifecycle_files_three_way", return_value=split_result) as mock_split, \
             patch("src.pipeline.model_replay.load_or_build_samples", return_value=[]):
            _, split_meta = module._load_split_samples(
                lifecycle_dir="data/training",
                runtime_params={"sample_mode": "trade_event"},
                train_split_ratio=0.34,
                validation_split_ratio=0.25,
                min_validation_files=1,
                min_eval_files=1,
                max_samples_per_token=80,
                sample_cache_dir=".cache/probe-test",
                lifecycle_files=["explicit_a.jsonl", "explicit_b.jsonl", "explicit_c.jsonl"],
            )

        mock_discover.assert_not_called()
        self.assertEqual(
            mock_split.call_args.args[0],
            [Path("explicit_a.jsonl"), Path("explicit_b.jsonl"), Path("explicit_c.jsonl")],
        )
        self.assertEqual(split_meta["train_files"], ["explicit_a.jsonl"])

    def test_load_split_samples_rejects_post_load_sample_overlap(self):
        module = _load_module()
        split_result = {
            "train_files": [Path("train.jsonl")],
            "validation_files": [Path("validation.jsonl")],
            "eval_files": [Path("final.jsonl")],
            "raw_train_validation_overlap_count": 1,
            "raw_train_eval_overlap_count": 0,
            "raw_validation_eval_overlap_count": 0,
            "raw_final_overlap_token_count": 0,
            "train_raw_tokens": {"0xtrain"},
            "validation_raw_tokens": set(),
            "eval_raw_tokens": set(),
        }

        def fake_load_or_build_samples(config, lifecycle_paths, exclude_tokens, *, cache_dir, use_cache):
            return [{"meta": {"token_address": "0xleak"}}]

        with patch("src.pipeline.train_hybrid._discover_lifecycle_files", return_value=[Path("a"), Path("b"), Path("c")]), \
             patch("src.pipeline.train_hybrid._split_lifecycle_files_three_way", return_value=split_result), \
             patch("src.pipeline.model_replay.load_or_build_samples", side_effect=fake_load_or_build_samples):
            with self.assertRaisesRegex(ValueError, "sample leakage detected"):
                module._load_split_samples(
                    lifecycle_dir="data/training",
                    runtime_params={"sample_mode": "trade_event"},
                    train_split_ratio=0.6,
                    validation_split_ratio=0.2,
                    min_validation_files=1,
                    min_eval_files=1,
                    max_samples_per_token=80,
                    sample_cache_dir=".cache/probe-test",
                    max_lifecycle_files=3,
                )


if __name__ == "__main__":
    unittest.main()
