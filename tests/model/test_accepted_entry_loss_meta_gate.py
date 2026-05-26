import unittest
import importlib.util
from pathlib import Path

from src.pipeline import accepted_entry_loss_meta_gate as gate


def _trade(token, signal_time, return_pct):
    return {
        "token": token,
        "entry_signal_time": signal_time,
        "entry_time": signal_time + 1,
        "return_pct": return_pct,
        "exit_reason": "STOP_LOSS" if return_pct < 0 else "TRAILING_STOP",
    }


def _sample(token, sample_time, depth, noise=0.0):
    return {
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
        },
        "features": {
            "organic_depth": depth,
            "noise": noise,
            "future_window": 300,
        },
    }


class TestAcceptedEntryLossMetaGate(unittest.TestCase):
    def test_fit_scorer_scores_eval_episode_with_path_state_metadata(self):
        train_trades = [
            _trade("0xaaa", 100, -15.0),
            _trade("0xbbb", 200, -8.0),
            _trade("0xccc", 300, 25.0),
            _trade("0xddd", 400, 45.0),
        ]
        train_samples = [
            _sample("0xaaa", 100, 1.0),
            _sample("0xbbb", 200, 2.0),
            _sample("0xccc", 300, 10.0),
            _sample("0xddd", 400, 12.0),
        ]
        eval_episodes = [[
            _sample("0xeee", 500, 1.5),
            _sample("0xeee", 501, 11.0),
        ]]

        score_maps, metadata = gate.fit_keep_scorer_and_score_episodes(
            trade_rows=train_trades,
            train_samples=train_samples,
            eval_episodes=eval_episodes,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
        )

        self.assertEqual(metadata["train_match_summary"]["matched_trade_count"], 4)
        self.assertIn("organic_depth", metadata["model"]["feature_names"])
        self.assertNotIn("future_window", metadata["model"]["feature_names"])
        self.assertEqual(score_maps[0][gate.PATH_STATE_EPISODE_META_KEY]["token"], "0xeee")
        self.assertGreater(score_maps[0][1], score_maps[0][0])

    def test_fit_scorer_requires_both_keep_and_skip_examples(self):
        with self.assertRaisesRegex(ValueError, "both keep and skip"):
            gate.fit_keep_scorer_and_score_episodes(
                trade_rows=[_trade("0xaaa", 100, 10.0)],
                train_samples=[_sample("0xaaa", 100, 10.0)],
                eval_episodes=[],
                min_samples_leaf=1,
            )

    def test_fit_lcb_scorer_uses_stable_lower_quantile_across_windows(self):
        train_trades = [
            _trade("0xaaa", 100, -15.0),
            _trade("0xbbb", 120, 18.0),
            _trade("0xccc", 140, -12.0),
            _trade("0xddd", 160, 20.0),
            _trade("0xeee", 180, -10.0),
            _trade("0xfff", 200, 22.0),
        ]
        train_samples = [
            _sample("0xaaa", 100, 1.0),
            _sample("0xbbb", 120, 10.0),
            _sample("0xccc", 140, 1.5),
            _sample("0xddd", 160, 11.0),
            _sample("0xeee", 180, 2.0),
            _sample("0xfff", 200, 12.0),
        ]
        eval_episodes = [[
            _sample("0xggg", 300, 1.25),
            _sample("0xggg", 301, 11.5),
        ]]

        score_maps, metadata = gate.fit_keep_lcb_scorer_and_score_episodes(
            trade_rows=train_trades,
            train_samples=train_samples,
            eval_episodes=eval_episodes,
            max_depth=1,
            min_samples_leaf=1,
            min_common_features=1,
            window_count=3,
            lcb_quantile=0.25,
        )

        self.assertEqual(metadata["model"]["score_aggregation"], "lower_quantile")
        self.assertGreaterEqual(metadata["model"]["ensemble_model_count"], 3)
        self.assertEqual(score_maps[0][gate.PATH_STATE_EPISODE_META_KEY]["token"], "0xggg")
        self.assertGreater(score_maps[0][1], score_maps[0][0])

    def test_replay_cli_uses_bounded_path_state_keep_score_grid(self):
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "run_accepted_entry_loss_meta_gate_replay.py"
        spec = importlib.util.spec_from_file_location("run_accepted_entry_loss_meta_gate_replay", script_path)
        cli = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cli)

        grid = list(cli.candidate_grid())

        self.assertEqual(len(grid), 9)
        self.assertEqual(grid[0], {"buy_path_state_meta_gate_min_score": 0.05})
        self.assertIn({"buy_path_state_meta_gate_min_score": 0.55}, grid)
        self.assertTrue(all(set(candidate) == {"buy_path_state_meta_gate_min_score"} for candidate in grid))

    def test_replay_cli_supports_stable_lcb_score_mode(self):
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "run_accepted_entry_loss_meta_gate_replay.py"
        spec = importlib.util.spec_from_file_location("run_accepted_entry_loss_meta_gate_replay", script_path)
        cli = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(cli)

        args = cli.parse_args(["--score-mode", "stable-lcb", "--score-lcb-quantile", "0.2"])

        self.assertEqual(args.score_mode, "stable-lcb")
        self.assertEqual(args.score_lcb_quantile, 0.2)


if __name__ == "__main__":
    unittest.main()
