import unittest
import contextlib
import io
from unittest.mock import patch

from src.pipeline import path_state_meta_probe as p


class TestPathStateMetaProbe(unittest.TestCase):
    def _sample(self, token, sample_time, price, **overrides):
        sample = {
            "features": {
                "current_price": price,
                "volume_30s": 2.0,
                "price_volatility": 0.10,
                "buy_count_30s": 3,
            },
            "label": {"live_target_hit_before_stop": 1},
            "meta": {
                "token_address": token,
                "sample_time": sample_time,
                "create_timestamp": 0,
            },
        }
        for section, values in overrides.items():
            if section == "label":
                sample[section] = dict(values)
            else:
                sample.setdefault(section, {}).update(values)
        return sample

    def test_path_state_features_use_only_prior_price_history(self):
        current = self._sample("0xA", 30, 1.20)
        prior_and_future = [
            self._sample("0xA", 0, 1.00),
            self._sample("0xA", 10, 2.00),
            self._sample("0xA", 20, 1.50),
            self._sample("0xA", 40, 4.00),
        ]

        features = p.build_path_state_features(
            current,
            prior_and_future,
            buy_prob=0.98,
            entry_score=35.0,
        )

        self.assertEqual(features["pre_entry_peak_price"], 2.0)
        self.assertAlmostEqual(features["pre_entry_peak_drawdown_pct"], -40.0)
        self.assertAlmostEqual(features["recent_price_return_pct"], -20.0)
        self.assertEqual(features["prior_sample_count"], 3)

    def test_path_state_feature_builder_rejects_label_like_columns(self):
        sample = self._sample(
            "0xA",
            30,
            1.0,
            features={
                "future_return_pct": 75.0,
                "live_target_hit_before_stop": 1,
                "target_label": 1,
                "label_profit": 99.0,
            },
            label={"live_target_hit_before_stop": 1},
        )

        features = p.build_path_state_features(
            sample,
            [],
            buy_prob=0.99,
            entry_score=40.0,
        )

        self.assertNotIn("future_return_pct", features)
        self.assertNotIn("live_target_hit_before_stop", features)
        self.assertNotIn("target_label", features)
        self.assertNotIn("label_profit", features)

    def test_path_state_features_copy_decision_time_flow_fields(self):
        sample = self._sample(
            "0xA",
            30,
            1.0,
            features={
                "total_buy_volume": 10.0,
                "total_sell_volume": 2.5,
                "volume_10s": 1.5,
                "volume_30s": 2.0,
                "buy_pressure": 0.80,
                "buy_sell_overlap_ratio_60s": 0.25,
                "recent_seller_reentry_ratio_30s": 0.10,
                "buyer_set_churn_10s_vs_prev50s": 0.40,
                "lp_resistance_ratio_10s": 3.0,
            },
        )

        features = p.build_path_state_features(
            sample,
            [],
            buy_prob=0.99,
            entry_score=40.0,
        )

        self.assertEqual(features["total_buy_volume"], 10.0)
        self.assertEqual(features["total_sell_volume"], 2.5)
        self.assertEqual(features["volume_10s"], 1.5)
        self.assertEqual(features["buy_pressure"], 0.80)
        self.assertAlmostEqual(features["sell_pressure"], 0.20)
        self.assertAlmostEqual(features["buy_sell_volume_ratio"], 4.0)
        self.assertEqual(features["buy_sell_overlap_ratio_60s"], 0.25)
        self.assertEqual(features["recent_seller_reentry_ratio_30s"], 0.10)
        self.assertEqual(features["buyer_set_churn_10s_vs_prev50s"], 0.40)
        self.assertEqual(features["lp_resistance_ratio_10s"], 3.0)

    def test_path_state_buy_sell_volume_ratio_distinguishes_buy_only_flow(self):
        sample = self._sample(
            "0xA",
            30,
            1.0,
            features={
                "total_buy_volume": 10.0,
                "total_sell_volume": 0.0,
            },
        )

        features = p.build_path_state_features(
            sample,
            [],
            buy_prob=0.99,
            entry_score=40.0,
        )

        self.assertAlmostEqual(features["buy_sell_volume_ratio"], 10.0 / 1e-9)

    def test_score_maps_preserve_episode_indices(self):
        train_samples = [
            self._sample(
                "0xtrain_pos",
                10,
                1.0,
                features={"volume_30s": 0.0, "price_volatility": 0.0},
                label={"live_target_hit_before_stop": 1},
            ),
            self._sample("0xtrain_pos", 15, 1.1, label={"live_target_hit_before_stop": 1}),
            self._sample(
                "0xtrain_neg",
                20,
                1.0,
                features={"volume_30s": 0.0, "price_volatility": 0.0},
                label={"live_stop_hit_before_target": 1},
            ),
            self._sample("0xtrain_neg", 25, 0.9, label={"live_stop_hit_before_target": 1}),
        ]
        eval_episodes = [[
            self._sample("0xeval_low_prob", 10, 1.0),
            self._sample(
                "0xeval_candidate",
                20,
                1.0,
                features={"volume_30s": 2.0, "price_volatility": 0.12},
            ),
            self._sample("0xeval_terminal", 30, 1.2),
        ]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }

        def fake_score_samples(samples, _buy_artifact):
            probabilities = []
            entry_scores = []
            for sample in samples:
                token = sample["meta"]["token_address"]
                probabilities.append(0.50 if token.endswith("low_prob") else 0.99)
                entry_scores.append(40.0)
            return probabilities, entry_scores

        with patch.object(p, "_score_samples", side_effect=fake_score_samples), patch.object(
            p, "_train_path_state_model", return_value=object()
        ), patch.object(p, "_predict_path_state_scores", return_value=[0.42]):
            score_maps = p.fit_path_state_model_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertEqual(score_maps[0][1], 0.42)
        self.assertNotIn(0, score_maps[0])

    def test_fit_uses_broader_training_pool_but_scores_runtime_candidates(self):
        train_samples = [
            self._sample("0xtrain_pos", 10, 1.0, label={"live_target_hit_before_stop": 1}),
            self._sample("0xtrain_pos", 15, 1.1, label={"live_target_hit_before_stop": 1}),
            self._sample("0xtrain_neg", 20, 1.0, label={"live_stop_hit_before_target": 1}),
            self._sample("0xtrain_neg", 25, 0.9, label={"live_stop_hit_before_target": 1}),
        ]
        eval_episodes = [[
            self._sample("0xeval_low_prob", 10, 1.0),
            self._sample(
                "0xeval_candidate",
                20,
                1.0,
                features={"volume_30s": 2.0, "price_volatility": 0.12},
            ),
            self._sample("0xeval_terminal", 30, 1.2),
        ]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }

        def fake_score_samples(samples, _buy_artifact):
            probabilities = []
            entry_scores = []
            for sample in samples:
                token = sample["meta"]["token_address"]
                probabilities.append(0.50 if token.endswith("low_prob") else 0.91 if token.startswith("0xtrain") else 0.99)
                entry_scores.append(40.0)
            return probabilities, entry_scores

        with patch.object(p, "_score_samples", side_effect=fake_score_samples), patch.object(
            p, "_train_path_state_model", return_value=object()
        ), patch.object(p, "_predict_path_state_scores", return_value=[0.73]):
            score_maps = p.fit_path_state_model_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertEqual(score_maps[0][1], 0.73)
        self.assertNotIn(0, score_maps[0])

    def test_eval_scoring_uses_runtime_filters_not_broadened_training_pool(self):
        train_samples = [
            self._sample("0xtrain_pos", 10, 1.0, label={"live_target_hit_before_stop": 1}),
            self._sample("0xtrain_pos", 15, 1.1, label={"live_target_hit_before_stop": 1}),
            self._sample("0xtrain_neg", 20, 1.0, label={"live_stop_hit_before_target": 1}),
            self._sample("0xtrain_neg", 25, 0.9, label={"live_stop_hit_before_target": 1}),
        ]
        eval_episodes = [[
            self._sample(
                "0xeval_low_quality",
                10,
                1.0,
                features={"volume_30s": 0.1, "price_volatility": 0.01},
            ),
            self._sample(
                "0xeval_runtime_candidate",
                20,
                1.1,
                features={"volume_30s": 2.0, "price_volatility": 0.12},
            ),
            self._sample("0xeval_terminal", 30, 1.2),
        ]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }

        def fake_score_samples(samples, _buy_artifact):
            probabilities = []
            entry_scores = []
            for sample in samples:
                token = sample["meta"]["token_address"]
                probabilities.append(0.91 if token.startswith("0xtrain") else 0.99)
                entry_scores.append(40.0)
            return probabilities, entry_scores

        with patch.object(p, "_score_samples", side_effect=fake_score_samples), patch.object(
            p, "_train_path_state_model", return_value=object()
        ), patch.object(p, "_predict_path_state_scores", return_value=[0.73]):
            score_maps = p.fit_path_state_model_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertNotIn(0, score_maps[0])
        self.assertEqual(score_maps[0][1], 0.73)

    def test_runtime_candidate_age_uses_sample_interval_when_create_timestamp_missing(self):
        sample = self._sample("0xA", 1_000_000, 1.0)
        sample["meta"].pop("create_timestamp")
        sample["meta"]["sample_interval"] = 25
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }

        self.assertTrue(p._is_candidate(sample, 0.99, 40.0, runtime_params))

    def test_fit_excludes_terminal_samples_from_training_and_scoring(self):
        train_samples = [
            self._sample("0xA", 10, 1.0, label={"live_stop_hit_before_target": 1}),
            self._sample("0xA", 20, 1.1, label={"live_target_hit_before_stop": 1}),
            self._sample("0xA", 30, 1.2, label={"live_target_hit_before_stop": 1}),
            self._sample("0xB", 15, 1.0, label={"live_stop_hit_before_target": 1}),
            self._sample("0xB", 25, 1.1, label={"live_target_hit_before_stop": 1}),
        ]
        eval_episodes = [[
            self._sample("0xeval", 10, 1.0),
            self._sample("0xeval", 20, 1.1),
        ]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }
        trained_sample_times = []

        def fake_score_samples(samples, _buy_artifact):
            return [0.99 for _sample in samples], [40.0 for _sample in samples]

        def fake_train(rows):
            trained_sample_times.extend(row["sample_time"] for row in rows)
            return object()

        with patch.object(p, "_score_samples", side_effect=fake_score_samples), patch.object(
            p, "_train_path_state_model", side_effect=fake_train
        ), patch.object(p, "_predict_path_state_scores", return_value=[0.73]):
            score_maps = p.fit_path_state_model_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertEqual(trained_sample_times, [10, 20, 15])
        self.assertEqual(score_maps[0][0], 0.73)
        self.assertNotIn(1, score_maps[0])

    def test_candidate_rows_pass_only_same_token_prior_samples_to_feature_builder(self):
        samples = [
            self._sample("0xA", 10, 1.0),
            self._sample("0xB", 20, 1.0),
            self._sample("0xA", 30, 1.1),
            self._sample("0xA", 40, 1.2),
        ]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }
        prior_lengths = []
        prior_tokens = []

        def fake_features(_sample, prior_samples, *, buy_prob, entry_score, **_kwargs):
            prior_lengths.append(len(prior_samples))
            prior_tokens.append([row["meta"]["token_address"] for row in prior_samples])
            return {"buy_prob": buy_prob, "entry_score": entry_score}

        with patch.object(p, "build_path_state_features", side_effect=fake_features):
            p.build_path_state_rows_with_indices(
                samples,
                [0.99, 0.99, 0.99, 0.99],
                [40.0, 40.0, 40.0, 40.0],
                runtime_params,
            )

        self.assertEqual(prior_lengths, [0, 0, 1, 2])
        self.assertEqual(prior_tokens, [[], [], ["0xA"], ["0xA", "0xA"]])

    def test_candidate_rows_include_prior_model_score_deltas(self):
        samples = [
            self._sample("0xA", 10, 1.0),
            self._sample("0xA", 20, 1.1),
        ]
        rows = p.build_path_state_rows_with_indices(
            samples,
            [0.80, 0.95],
            [20.0, 35.0],
            {"buy_threshold": 0.75},
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["features"]["buy_prob_delta"], 0.0)
        self.assertEqual(rows[0]["features"]["entry_score_delta"], 0.0)
        self.assertAlmostEqual(rows[1]["features"]["buy_prob_delta"], 0.15)
        self.assertAlmostEqual(rows[1]["features"]["entry_score_delta"], 15.0)

    def test_meta_labels_use_triple_barrier_fields(self):
        self.assertEqual(p.path_state_meta_label({"live_target_hit_before_stop": 1}), 1)
        self.assertEqual(p.path_state_meta_label({"live_stop_hit_before_target": 1}), 0)
        self.assertEqual(
            p.path_state_meta_label({
                "live_target_hit_before_stop": 1,
                "live_risk_adjusted_return_pct": -10.0,
            }),
            1,
        )
        self.assertEqual(
            p.path_state_meta_label({
                "live_stop_hit_before_target": 1,
                "live_risk_adjusted_return_pct": 100.0,
            }),
            0,
        )
        self.assertEqual(p.path_state_meta_label({"live_risk_adjusted_return_pct": 35.0}), 1)
        self.assertEqual(
            p.path_state_meta_label(
                {
                    "live_target_hit_before_stop": 0,
                    "live_stop_hit_before_target": 0,
                    "future_return_pct": 100.0,
                }
            ),
            0,
        )

    def test_score_samples_unwraps_entry_value_model_artifact_dict(self):
        sample = self._sample("0xA", 10, 1.0)

        class BuyModel:
            def predict_proba(self, X):
                return [[0.2, 0.8] for _ in range(len(X))]

        class EntryModel:
            def predict(self, X):
                return [42.0 for _ in range(len(X))]

        probabilities, entry_scores = p._score_samples(
            [sample],
            {
                "model": BuyModel(),
                "entry_value_model": {"model": EntryModel()},
                "feature_names": None,
                "ignored_feature_names": [],
            },
        )

        self.assertEqual(probabilities, [0.8])
        self.assertEqual(entry_scores, [42.0])

    def test_fit_logs_empty_score_reason_when_training_labels_are_single_class(self):
        train_samples = [
            self._sample("0xtrain_a", 10, 1.0, label={"live_stop_hit_before_target": 1}),
            self._sample("0xtrain_b", 20, 1.0, label={"live_stop_hit_before_target": 1}),
        ]
        eval_episodes = [[self._sample("0xeval", 10, 1.0)]]
        runtime_params = {
            "buy_threshold": 0.98,
            "min_entry_score": 35.0,
            "min_entry_volume_30s": 1.5,
            "min_entry_price_volatility": 0.08,
            "max_entry_age_seconds": 300,
        }

        def fake_score_samples(samples, _buy_artifact):
            return [0.99 for _sample in samples], [40.0 for _sample in samples]

        stderr = io.StringIO()
        with patch.object(p, "_score_samples", side_effect=fake_score_samples), contextlib.redirect_stderr(stderr):
            score_maps = p.fit_path_state_model_and_score_episodes(
                train_samples,
                eval_episodes,
                buy_artifact={"model": object()},
                runtime_params=runtime_params,
            )

        self.assertIn(p.PATH_STATE_EPISODE_META_KEY, score_maps[0])
        self.assertNotIn(0, score_maps[0])
        self.assertIn("stage=path_state_probe train_rows", stderr.getvalue())
        self.assertIn("label_positive=0", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
