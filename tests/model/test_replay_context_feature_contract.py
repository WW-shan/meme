import unittest

from src.model.hybrid_inference import normalize_ignored_feature_names
from src.pipeline import candidate_ranker_probe
from src.pipeline import model_replay
from src.pipeline import train_hybrid


class TestReplayContextFeatureContract(unittest.TestCase):
    def test_replay_sample_cache_version_covers_context_feature_schema(self):
        self.assertGreaterEqual(model_replay.SAMPLE_CACHE_VERSION, 3)

    def test_training_sample_cache_version_covers_context_feature_schema(self):
        self.assertGreaterEqual(train_hybrid._SAMPLE_CACHE_VERSION, 3)

    def test_training_prunes_context_features_from_model_inputs(self):
        _rows, feature_names, dropped_features = train_hybrid._prune_training_feature_rows(
            [
                {
                    "current_price": 1.0,
                    "lifecycle_status_chain_lag_seconds": 0.5,
                },
                {
                    "current_price": 2.0,
                    "lifecycle_status_chain_lag_seconds": 1.5,
                },
            ],
            drop_constant=False,
        )

        self.assertEqual(feature_names, ["current_price"])
        self.assertIn(
            "lifecycle_status_chain_lag_seconds",
            dropped_features["invalid"],
        )

    def test_replay_contract_ignores_context_features_for_old_artifacts(self):
        _feature_names, ignored_feature_names = train_hybrid._feature_contract_for_replay(
            {
                "feature_names": ["current_price"],
                "dropped_features": [],
            },
            {"include_flow_features": False},
        )

        self.assertIn(
            "lifecycle_status_chain_lag_seconds",
            normalize_ignored_feature_names(ignored_feature_names),
        )

    def test_candidate_ranker_contract_ignores_context_features_for_old_artifacts(self):
        _feature_names, ignored_feature_names = candidate_ranker_probe._feature_contract(
            {
                "feature_names": ["current_price"],
                "dropped_features": [],
            },
            [
                {
                    "current_price": 1.0,
                    "lifecycle_status_chain_lag_seconds": 0.5,
                }
            ],
        )

        self.assertIn(
            "lifecycle_status_chain_lag_seconds",
            normalize_ignored_feature_names(ignored_feature_names),
        )


if __name__ == "__main__":
    unittest.main()
