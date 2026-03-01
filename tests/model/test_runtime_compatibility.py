import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

import numpy as np


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
            bot.reg = None
            bot.meta = None
            bot.config = {}
            bot.position_size = 0.1
            bot.model_path = None
            bot._strategy_defaults = {
                "prob_threshold": 0.85,
                "min_pred_return": 80.0,
                "max_age_seconds": 150,
            }
            bot.strategy_param_sources = {}
            bot.min_reg_r2_for_filter = 0.0
            bot.force_pred_return_filter = None
            bot.use_pred_return_filter = True
            bot.pred_return_filter_source = "default"

            with patch.object(bot_module.joblib, "load", return_value=object()) as mock_load:
                bot._load_models(str(model_dir))

            self.assertIsNotNone(bot.clf)
            self.assertIsNone(bot.reg)
            self.assertEqual(bot.meta, {})
            self.assertEqual(bot.model_path, model_dir)
            self.assertAlmostEqual(bot.prob_threshold, 0.85)
            self.assertAlmostEqual(bot.min_pred_return, 80.0)
            self.assertEqual(bot.max_age_seconds, 150)
            self.assertEqual(bot.strategy_param_sources["prob_threshold"], "default")
            self.assertEqual(bot.strategy_param_sources["min_pred_return"], "default")
            self.assertEqual(bot.strategy_param_sources["max_age_seconds"], "default")
            self.assertFalse(bot.use_pred_return_filter)
            self.assertEqual(bot.pred_return_filter_source, "auto_no_regressor")
            mock_load.assert_called_once_with(model_dir / "classifier_xgb.pkl")

    def test_resolve_strategy_params_priority_manual_over_calibration_over_default(self):
        bot_module = _load_module(
            "worktree_bot_priority",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot._strategy_defaults = {
            "prob_threshold": 0.85,
            "min_pred_return": 80.0,
            "max_age_seconds": 150,
        }

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            model_subdir = model_dir / "models_20260219_000001"
            model_subdir.mkdir(parents=True, exist_ok=True)

            (model_dir / "calibration_latest.json").write_text(
                json.dumps({
                    "recommended": {
                        "prob_threshold": 0.98,
                        "reg_min_return": 90.0,
                        "max_age_seconds": 90,
                    }
                }),
                encoding="utf-8",
            )

            resolved = bot._resolve_strategy_params(
                {
                    "prob_threshold": 0.97,
                    "min_pred_return": 95.0,
                },
                model_subdir,
            )

        self.assertAlmostEqual(resolved["values"]["prob_threshold"], 0.97)
        self.assertAlmostEqual(resolved["values"]["min_pred_return"], 95.0)
        self.assertEqual(resolved["values"]["max_age_seconds"], 90)
        self.assertEqual(resolved["sources"]["prob_threshold"], "manual")
        self.assertEqual(resolved["sources"]["min_pred_return"], "manual")
        self.assertEqual(resolved["sources"]["max_age_seconds"], "calibration")

    def test_resolve_strategy_params_fallback_when_calibration_missing_or_broken(self):
        bot_module = _load_module(
            "worktree_bot_fallback",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot._strategy_defaults = {
            "prob_threshold": 0.85,
            "min_pred_return": 80.0,
            "max_age_seconds": 150,
        }

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            model_subdir = model_dir / "models_20260219_000002"
            model_subdir.mkdir(parents=True, exist_ok=True)
            # 缺失 calibration 文件
            resolved_missing = bot._resolve_strategy_params({}, model_subdir)
            self.assertAlmostEqual(resolved_missing["values"]["prob_threshold"], 0.85)
            self.assertEqual(resolved_missing["sources"]["prob_threshold"], "default")

            # 损坏 calibration 文件
            (model_dir / "calibration_latest.json").write_text("{invalid", encoding="utf-8")
            resolved_broken = bot._resolve_strategy_params({}, model_subdir)
            self.assertAlmostEqual(resolved_broken["values"]["min_pred_return"], 80.0)
            self.assertEqual(resolved_broken["sources"]["min_pred_return"], "default")

    def test_resolve_exit_strategy_params_priority_manual_over_calibration_over_model_over_default(self):
        bot_module = _load_module(
            "worktree_bot_exit_priority",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot._exit_strategy_defaults = {
            "first_take_profit": 2.0,
            "first_exit_ratio": 0.6,
            "drawdown_stop": 0.25,
            "stop_loss": -0.5,
        }

        meta = {
            "trial_summary": {
                "selected_backtest_thresholds": {
                    "first_take_profit": 1.0,
                    "first_exit_ratio": 0.5,
                    "drawdown_stop": 0.2,
                    "stop_loss": -0.4,
                }
            },
            "gate_thresholds": {
                "backtest": {
                    "first_take_profit": 1.2,
                    "first_exit_ratio": 0.55,
                    "drawdown_stop": 0.22,
                    "stop_loss": -0.45,
                }
            },
        }

        with tempfile.TemporaryDirectory() as d:
            model_dir = Path(d)
            model_subdir = model_dir / "models_20260301_000001"
            model_subdir.mkdir(parents=True, exist_ok=True)

            (model_dir / "calibration_latest.json").write_text(
                json.dumps({
                    "recommended": {
                        "first_take_profit": 1.5,
                        "first_exit_ratio": 0.7,
                        "drawdown_stop": 0.2,
                        "stop_loss": -0.5,
                    }
                }),
                encoding="utf-8",
            )

            resolved = bot._resolve_exit_strategy_params(
                {
                    "first_take_profit": 1.8,
                },
                meta,
                model_subdir,
            )

        self.assertAlmostEqual(resolved["values"]["first_take_profit"], 1.8)
        self.assertAlmostEqual(resolved["values"]["first_exit_ratio"], 0.7)
        self.assertAlmostEqual(resolved["values"]["drawdown_stop"], 0.2)
        self.assertAlmostEqual(resolved["values"]["stop_loss"], -0.5)
        self.assertEqual(resolved["sources"]["first_take_profit"], "manual")
        self.assertEqual(resolved["sources"]["first_exit_ratio"], "calibration")
        self.assertEqual(resolved["sources"]["drawdown_stop"], "calibration")
        self.assertEqual(resolved["sources"]["stop_loss"], "calibration")

    def test_resolve_pred_return_filter_uses_r2_and_manual_override(self):
        bot_module = _load_module(
            "worktree_bot_filter",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot.reg = object()
        bot.meta = {"regressor": {"metrics": {"r2": -0.2}}}
        bot.min_reg_r2_for_filter = 0.0
        bot.force_pred_return_filter = None
        bot.use_pred_return_filter = True
        bot.pred_return_filter_source = "default"

        bot._resolve_pred_return_filter({})
        self.assertFalse(bot.use_pred_return_filter)
        self.assertEqual(bot.pred_return_filter_source, "auto_low_r2")

        bot._resolve_pred_return_filter({"force_pred_return_filter": True})
        self.assertTrue(bot.use_pred_return_filter)
        self.assertEqual(bot.pred_return_filter_source, "manual_on")

        bot._resolve_pred_return_filter({"force_pred_return_filter": False})
        self.assertFalse(bot.use_pred_return_filter)
        self.assertEqual(bot.pred_return_filter_source, "manual_off")

    def test_analysis_loop_does_not_skip_token_when_last_update_unchanged(self):
        bot_module = _load_module(
            "worktree_bot_analysis_repeat",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        class _Collector:
            def __init__(self):
                self.token_lifecycle = {
                    "token-1": {
                        "last_update": 30,
                        "create_timestamp": 0,
                        "price_current": 1.0,
                        "unique_buyers": {"a", "b", "c"},
                        "buys": [{"account": "a"}] * 5,
                        "sells": [],
                        "symbol": "TEST",
                    }
                }

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot.collector = _Collector()

        async def _run_once():
            bot.active = True
            bot._pending_analysis = {"token-1"}
            bot._analysis_wakeup = bot_module.asyncio.Event()

            processed = {"count": 0}

            async def _fake_process(_token):
                processed["count"] += 1
                bot.active = False

            bot._process_token_logic = _fake_process

            await bot._analysis_loop()
            return processed["count"]

        processed_count = asyncio.run(_run_once())
        self.assertEqual(processed_count, 1)

    def test_inference_uses_future_window_240(self):
        bot_module = _load_module(
            "worktree_bot_future_window",
            Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
        )

        class _DummyCollector:
            def __init__(self):
                self.token_lifecycle = {
                    "token-1": {
                        "create_timestamp": 0,
                        "last_update": 30,
                        "price_current": 1.0,
                        "unique_buyers": {"a", "b", "c"},
                        "buys": [{"account": "a"}] * 5,
                        "sells": [],
                        "symbol": "TEST",
                    }
                }
                self.future_window_used = None

            def _extract_features(self, lifecycle, buys, sells, last_update, future_window=300):
                self.future_window_used = future_window
                return {"f1": 1.0}

        class _DummyClf:
            def predict_proba(self, X):
                return np.array([[0.1, 0.95]])

        class _DummyReg:
            def predict(self, X):
                return np.array([100.0])

        bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
        bot.active = True
        bot.positions = {}
        bot.pending_buys = set()
        bot.failed_buys = {}
        bot.clf = _DummyClf()
        bot.reg = _DummyReg()
        bot.meta = {"features": ["f1"]}
        bot.collector = _DummyCollector()
        bot.max_age_seconds = 150
        bot.prob_threshold = 0.9
        bot.min_pred_return = 80.0
        bot.use_pred_return_filter = True
        bot.position_size = 0.1
        bot.buy_signal_queue_size = 10

        class _QueueStub:
            def __init__(self):
                self.items = []

            def put_nowait(self, item):
                self.items.append(item)

            def get_nowait(self):
                return self.items.pop(0)

            def qsize(self):
                return len(self.items)

        bot._buy_signal_queue = _QueueStub()
        bot._pending_buy_signals = set()

        class _OpenNotExpected(Exception):
            pass

        async def _unexpected_open(*_args, **_kwargs):
            raise _OpenNotExpected("analysis should enqueue buy signal, not execute buy inline")

        bot._open_position = _unexpected_open

        async def _run():
            await bot._process_token_logic("token-1")
            return bot._buy_signal_queue.get_nowait()

        queued_signal = asyncio.run(_run())

        self.assertEqual(bot.collector.future_window_used, 240)
        self.assertEqual(queued_signal["token"], "token-1")

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
