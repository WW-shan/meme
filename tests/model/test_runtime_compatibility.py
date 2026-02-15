import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestRuntimeCompatibility(unittest.TestCase):
    def test_bot_load_models_from_explicit_model_dir(self):
        bot_module = _load_module(
            "worktree_bot",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            (model_dir / "classifier_xgb.pkl").write_bytes(b"fake")
            (model_dir / "model_metadata.json").write_text("{}", encoding="utf-8")

            bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
            bot.clf = None
            bot.meta = None

            with patch.object(bot_module.joblib, "load", return_value=object()) as mock_load:
                bot._load_models(str(model_dir))

            self.assertIsNotNone(bot.clf)
            self.assertEqual(bot.meta, {})
            mock_load.assert_called_once_with(model_dir / "classifier_xgb.pkl")

    def test_backtester_loads_latest_model_subdir(self):
        backtest_module = _load_module(
            "worktree_backtester",
            Path(__file__).resolve().parents[2] / "src" / "backtest" / "simple_backtest.py",
        )

        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            old = base / "models_20260215_103804"
            new = base / "models_20260215_120000"
            old.mkdir()
            new.mkdir()
            for p in (old, new):
                (p / "classifier_xgb.pkl").write_bytes(b"fake")
                (p / "model_metadata.json").write_text(json.dumps({"features": ["f1"]}), encoding="utf-8")

            class _FakeModel:
                pass

            with patch.object(backtest_module.joblib, "load", return_value=_FakeModel()) as mock_load:
                backtester = backtest_module.SimpleBacktester(model_dir=str(base))

            self.assertIsNotNone(backtester.clf)
            self.assertEqual(backtester.meta, {"features": ["f1"]})
            self.assertEqual(mock_load.call_args.args[0], new / "classifier_xgb.pkl")


if __name__ == "__main__":
    unittest.main()
