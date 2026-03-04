# Hybrid Model Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire CatBoost+PPO hybrid model into bot inference and backtest engine, replacing old XGBoost+LightGBM; add real post-training backtest with Sortino/MaxDD metrics.

**Architecture:** New `HybridModel` adapter class provides unified `predict_buy`/`predict_sell` interface. Bot and BacktestEngine both consume this adapter. Post-training backtest runs automatically at end of `run_hybrid_training`.

**Tech Stack:** Python 3, unittest, CatBoost, Stable-Baselines3, Gymnasium, pandas/numpy.

---

Execution discipline for every task: follow @superpowers:test-driven-development (failing test -> fail run -> minimal implementation -> pass run -> commit).

### Task 1: Create HybridModel adapter with predict_buy

**Files:**
- Create: `src/model/hybrid_inference.py`
- Create: `tests/model/test_hybrid_inference.py`

**Step 1: Write the failing test**

Add to `tests/model/test_hybrid_inference.py`:

```python
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util
import json
import tempfile


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "model" / "hybrid_inference.py"
    spec = importlib.util.spec_from_file_location("hybrid_inference", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestHybridInference(unittest.TestCase):
    def test_predict_buy_returns_prob_and_decision(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.3, 0.7]]
        hybrid = m.HybridModel(buy_model=fake_model, buy_threshold=0.5, sell_policy=None)
        features = {"current_price": 1.0, "buy_pressure": 0.6}
        prob, should_buy = hybrid.predict_buy(features)
        self.assertAlmostEqual(prob, 0.7)
        self.assertTrue(should_buy)

    def test_predict_buy_rejects_below_threshold(self):
        m = _load_module()
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.8, 0.2]]
        hybrid = m.HybridModel(buy_model=fake_model, buy_threshold=0.5, sell_policy=None)
        prob, should_buy = hybrid.predict_buy({"current_price": 1.0})
        self.assertAlmostEqual(prob, 0.2)
        self.assertFalse(should_buy)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_hybrid_inference -v`

Expected: ERROR (module/class not found).

**Step 3: Write minimal implementation**

Create `src/model/hybrid_inference.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class HybridModel:
    def __init__(self, buy_model, buy_threshold: float, sell_policy=None):
        self.buy_model = buy_model
        self.buy_threshold = float(buy_threshold)
        self.sell_policy = sell_policy

    def predict_buy(self, features_dict: dict) -> tuple:
        X = pd.DataFrame([features_dict])
        proba = self.buy_model.predict_proba(X)
        if hasattr(proba, '__len__') and len(proba) > 0:
            row = proba[0]
            prob = float(row[1]) if len(row) > 1 else float(row[0])
        else:
            prob = float(proba)
        return prob, prob >= self.buy_threshold
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/hybrid_inference.py tests/model/test_hybrid_inference.py
git commit -m "feat: add HybridModel adapter with predict_buy"
```

---

### Task 2: Add predict_sell and load class method to HybridModel

**Files:**
- Modify: `src/model/hybrid_inference.py`
- Modify: `tests/model/test_hybrid_inference.py`

**Step 1: Write the failing tests**

Add to `tests/model/test_hybrid_inference.py`:

```python
    def test_predict_sell_returns_action_from_policy(self):
        m = _load_module()
        fake_policy = MagicMock()
        fake_policy.predict.return_value = (2, None)
        hybrid = m.HybridModel(buy_model=MagicMock(), buy_threshold=0.5, sell_policy=fake_policy)
        action = hybrid.predict_sell([1.0, 0.5, 0.3, 2.0, 40.0])
        self.assertEqual(action, 2)

    def test_predict_sell_returns_negative_one_when_no_policy(self):
        m = _load_module()
        hybrid = m.HybridModel(buy_model=MagicMock(), buy_threshold=0.5, sell_policy=None)
        action = hybrid.predict_sell([1.0, 0.5, 0.3, 2.0, 40.0])
        self.assertEqual(action, -1)

    def test_load_reads_artifacts_from_directory(self):
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake artifacts
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "buy_threshold.json").write_text(
                json.dumps({"threshold": 0.42}), encoding="utf-8"
            )
            # No sell_policy.zip -> sell_policy should be None

            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                hybrid = m.HybridModel.load(tmpdir)

            self.assertAlmostEqual(hybrid.buy_threshold, 0.42)
            self.assertIsNone(hybrid.sell_policy)
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_hybrid_inference -v`

Expected: FAIL/ERROR (predict_sell and load not implemented).

**Step 3: Write minimal implementation**

Add to `src/model/hybrid_inference.py`:

```python
    def predict_sell(self, obs) -> int:
        if self.sell_policy is None:
            return -1
        import numpy as np
        obs_arr = np.asarray(obs, dtype=np.float32).reshape(1, -1)
        action, _ = self.sell_policy.predict(obs_arr, deterministic=True)
        return int(action)

    @classmethod
    def load(cls, model_dir) -> "HybridModel":
        model_dir = Path(model_dir)

        buy_model = _load_catboost_model(str(model_dir / "buy_model.cbm"))

        threshold_path = model_dir / "buy_threshold.json"
        if threshold_path.exists():
            with open(threshold_path, "r", encoding="utf-8") as f:
                threshold = float(json.load(f).get("threshold", 0.5))
        else:
            threshold = 0.5

        sell_policy = None
        policy_path = model_dir / "sell_policy.zip"
        if policy_path.exists():
            sell_policy = _load_sb3_policy(str(policy_path))

        return cls(buy_model=buy_model, buy_threshold=threshold, sell_policy=sell_policy)


def _load_catboost_model(path):
    from catboost import CatBoostClassifier
    model = CatBoostClassifier()
    model.load_model(path)
    return model


def _load_sb3_policy(path):
    from stable_baselines3 import PPO
    return PPO.load(path)
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/hybrid_inference.py tests/model/test_hybrid_inference.py
git commit -m "feat: add predict_sell and load to HybridModel"
```

---

### Task 3: Replace bot model loading with HybridModel

**Files:**
- Modify: `src/trader/bot.py:130-133` (init attrs)
- Modify: `src/trader/bot.py:289-358` (_load_models)

**Step 1: Write the failing test**

Add to `tests/model/test_hybrid_inference.py`:

```python
    def test_bot_load_models_uses_hybrid(self):
        """Verify bot._load_models sets self.hybrid when buy_model.cbm exists."""
        m = _load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "buy_model.cbm").write_text("fake", encoding="utf-8")
            Path(tmpdir, "buy_threshold.json").write_text(
                json.dumps({"threshold": 0.55}), encoding="utf-8"
            )
            with patch.object(m, "_load_catboost_model", return_value=MagicMock()):
                hybrid = m.HybridModel.load(tmpdir)

        self.assertIsNotNone(hybrid.buy_model)
        self.assertAlmostEqual(hybrid.buy_threshold, 0.55)
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_hybrid_inference.TestHybridInference.test_bot_load_models_uses_hybrid -v`

Expected: PASS (this tests the adapter, not the bot directly — it validates the contract the bot will use).

**Step 3: Modify bot.py `_load_models`**

In `src/trader/bot.py`, replace lines 130-133:

```python
# Old:
self.clf = None
self.reg = None
self.prob_calibrator = None
self.meta = None

# New:
self.hybrid = None
```

Replace `_load_models` method (lines 289-358):

```python
def _load_models(self, model_dir: str):
    """Load trained hybrid ML models"""
    from src.model.hybrid_inference import HybridModel
    path = Path(model_dir)
    if not (path / "buy_model.cbm").exists():
        if path.exists() and path.is_dir():
            subdirs = sorted([d for d in path.iterdir() if d.is_dir() and (d / "buy_model.cbm").exists()])
            if subdirs:
                path = subdirs[-1]
            else:
                logger.warning(f"No hybrid models found in {path}! Bot will only collect data.")
                return
        else:
            logger.warning(f"Model path {path} does not exist! Bot will only collect data.")
            return

    logger.info(f"📂 Loading hybrid models from: {path}")
    try:
        self.hybrid = HybridModel.load(str(path))
        self.model_path = path

        self.prob_threshold = self.hybrid.buy_threshold
        self.stop_loss = float(self.config.get('stop_loss', -0.50))

        logger.info(
            f"✅ Hybrid models loaded | buy_threshold={self.hybrid.buy_threshold:.2f} | "
            f"sell_policy={'PPO' if self.hybrid.sell_policy is not None else 'rules'}"
        )
    except Exception as e:
        logger.error(f"Failed to load hybrid models: {e}")
```

**Step 4: Update `_run_model_inference`**

Replace `_run_model_inference` (lines 417-438):

```python
def _run_model_inference(self, lifecycle):
    if self.hybrid is None:
        return 0.0, False
    features_dict = self.collector._extract_features(
        lifecycle,
        lifecycle['buys'],
        lifecycle['sells'],
        lifecycle['last_update'],
        future_window=240
    )
    prob, should_buy = self.hybrid.predict_buy(features_dict)
    return prob, should_buy
```

**Step 5: Update sell logic guard**

In `_process_token_logic`, the buy guard (around line 543) currently checks `if not self.clf`. Change to:

```python
# Old: if not self.clf:
# New:
if self.hybrid is None:
```

**Step 6: Commit**

```bash
git add src/trader/bot.py
git commit -m "feat: replace XGBoost model loading with HybridModel in bot"
```

---

### Task 4: Replace bot sell logic with PPO decisions

**Files:**
- Modify: `src/trader/bot.py:475-531` (sell logic)

**Step 1: Modify sell logic**

Replace the sell logic block (lines 475-531) with PPO-driven sell:

```python
if token_address in self.positions:
    pos = self.positions[token_address]

    tp_base_price = pos.get('tp_base_price', pos['entry_price'])
    pnl_pct = (current_price - tp_base_price) / tp_base_price

    # Hard stop-loss floor: always enforced regardless of PPO
    if pnl_pct <= self.stop_loss:
        await self._close_position(token_address, reason="STOP_LOSS")
        return

    # PPO sell decision
    if self.hybrid is not None and self.hybrid.sell_policy is not None:
        features_dict = self.collector._extract_features(
            lifecycle, lifecycle['buys'], lifecycle['sells'],
            lifecycle['last_update'], future_window=240
        )
        obs = [
            current_price,
            float(features_dict.get("launch_fee", 0.0)),
            float(features_dict.get("sell_pressure", 0.0)),
            float(features_dict.get("buy_sell_ratio", 0.0)),
            float(features_dict.get("holder_count", 0.0)),
        ]
        action = self.hybrid.predict_sell(obs)
        if action == 1:
            await self._partial_sell(token_address, sell_ratio=0.25, reason="PPO_SELL25")
            return
        elif action == 2:
            await self._partial_sell(token_address, sell_ratio=0.50, reason="PPO_SELL50")
            return
        elif action == 3:
            await self._close_position(token_address, reason="PPO_SELL100")
            return
        # action == 0: hold, fall through to time exit
    else:
        # Fallback: rule-based sell (original logic)
        if pnl_pct >= self.first_take_profit and not pos.get('partial_sold', False):
            first_tp_label = int(round(self.first_take_profit * 100))
            await self._partial_sell(
                token_address, sell_ratio=self.first_exit_ratio,
                reason=f"FIRST_TP_{first_tp_label}"
            )
            pos['partial_sold'] = True
            pos['peak_price'] = current_price
            return

        if pos.get('partial_sold', False):
            if 'peak_price' not in pos:
                tp_base_price = pos.get('tp_base_price', pos.get('entry_price', 0))
                pos['peak_price'] = max(current_price, tp_base_price * (1.0 + self.first_take_profit))
            else:
                pos['peak_price'] = max(pos['peak_price'], current_price)
            drawdown_pct = (current_price - pos['peak_price']) / pos['peak_price']
            if drawdown_pct <= -self.drawdown_stop:
                await self._close_position(token_address, reason="POST_TP_DRAWDOWN_EXIT")
                return

    # Time exit (always applies)
    time_held = (datetime.now() - pos['entry_time']).total_seconds()
    if time_held >= self.hold_time_seconds:
        await self._close_position(token_address, reason="TIME_EXIT")
        return
    return
```

**Step 2: Clean up unused attributes**

Remove references to `self.clf`, `self.reg`, `self.prob_calibrator`, `self.meta` throughout bot.py. Search and replace any remaining guards like `if self.clf` with `if self.hybrid`.

**Step 3: Commit**

```bash
git add src/trader/bot.py
git commit -m "feat: replace rule-based sell with PPO-driven sell in bot"
```

---

### Task 5: Add hybrid model support to BacktestEngine

**Files:**
- Modify: `src/backtest/engine.py:21-50` (__init__)
- Modify: `src/backtest/engine.py:120-158` (_process_launch_event)
- Modify: `src/backtest/engine.py:209-227` (_check_initial_position)
- Create: `tests/model/test_backtest_hybrid.py`

**Step 1: Write the failing test**

Create `tests/model/test_backtest_hybrid.py`:

```python
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util


def _load_engine():
    path = Path(__file__).resolve().parents[2] / "src" / "backtest" / "engine.py"
    spec = importlib.util.spec_from_file_location("engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBacktestHybrid(unittest.TestCase):
    def test_engine_accepts_hybrid_model_param(self):
        m = _load_engine()
        fake_hybrid = MagicMock()
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)
        self.assertIs(engine.hybrid, fake_hybrid)

    def test_engine_without_hybrid_still_works(self):
        m = _load_engine()
        engine = m.BacktestEngine()
        self.assertIsNone(engine.hybrid)


if __name__ == "__main__":
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_backtest_hybrid -v`

Expected: ERROR (BacktestEngine.__init__ doesn't accept hybrid_model).

**Step 3: Modify BacktestEngine.__init__**

In `src/backtest/engine.py`, change `__init__` signature (line 21):

```python
# Old:
def __init__(self):

# New:
def __init__(self, hybrid_model=None):
    self.hybrid = hybrid_model
```

Add `self.hybrid = hybrid_model` as the first line inside `__init__`, before `self.filter = TradeFilter()`.

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/backtest/engine.py tests/model/test_backtest_hybrid.py
git commit -m "feat: add hybrid_model param to BacktestEngine"
```

---

### Task 6: Wire hybrid buy signal into BacktestEngine

**Files:**
- Modify: `src/backtest/engine.py:120-158` (_process_launch_event)
- Modify: `tests/model/test_backtest_hybrid.py`

**Step 1: Write the failing test**

Add to `tests/model/test_backtest_hybrid.py`:

```python
    def test_launch_event_uses_hybrid_buy_signal(self):
        import asyncio
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_buy.return_value = (0.8, True)
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        event = {
            "event_type": "launch",
            "token_address": "0xABC",
            "token_name": "TestToken",
            "token_symbol": "TT",
            "creator": "0x123",
            "total_supply": 1000000,
            "launch_fee": 0.5,
            "timestamp": 100,
        }
        asyncio.run(engine._process_launch_event(event))
        self.assertIn("0xABC", engine.positions)
        fake_hybrid.predict_buy.assert_called_once()

    def test_launch_event_rejects_when_hybrid_says_no(self):
        import asyncio
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_buy.return_value = (0.2, False)
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        event = {
            "event_type": "launch",
            "token_address": "0xDEF",
            "token_name": "BadToken",
            "token_symbol": "BT",
            "creator": "0x456",
            "total_supply": 1000000,
            "launch_fee": 0.5,
            "timestamp": 200,
        }
        asyncio.run(engine._process_launch_event(event))
        self.assertNotIn("0xDEF", engine.positions)
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_backtest_hybrid -v`

Expected: FAIL (hybrid_model.predict_buy not called, old filter used).

**Step 3: Modify _process_launch_event**

In `src/backtest/engine.py`, modify `_process_launch_event` (around lines 132-135):

```python
        # Filter check
        if self.hybrid is not None:
            from src.data.feature_extractor import extract_features
            features = extract_features(token_info, [], [], token_info.get('launch_time', 0))
            prob, should_buy = self.hybrid.predict_buy(features)
            if not should_buy:
                return
        else:
            should_buy, reason = self.filter.should_buy(token_info)
            if not should_buy:
                return
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/backtest/engine.py tests/model/test_backtest_hybrid.py
git commit -m "feat: wire hybrid buy signal into BacktestEngine"
```

---

### Task 7: Wire hybrid sell signal into BacktestEngine

**Files:**
- Modify: `src/backtest/engine.py:204-207` (sell dispatch)
- Modify: `src/backtest/engine.py:209-227` (_check_initial_position)
- Modify: `tests/model/test_backtest_hybrid.py`

**Step 1: Write the failing test**

Add to `tests/model/test_backtest_hybrid.py`:

```python
    def test_sell_uses_ppo_when_hybrid_available(self):
        import asyncio
        m = _load_engine()
        fake_hybrid = MagicMock()
        fake_hybrid.predict_sell.return_value = 3  # sell100
        engine = m.BacktestEngine(hybrid_model=fake_hybrid)

        engine.positions["0xABC"] = {
            "token_address": "0xABC",
            "token_symbol": "TT",
            "entry_price": 1.0,
            "entry_time": 100,
            "total_amount": 100,
            "remaining_amount": 100,
            "bnb_invested": 0.1,
            "status": "holding",
            "peak_price": 1.0,
        }
        engine.latest_prices["0xABC"] = 1.2

        asyncio.run(engine._check_initial_position("0xABC", 1.2, 200))
        fake_hybrid.predict_sell.assert_called_once()
        self.assertNotIn("0xABC", engine.positions)
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_backtest_hybrid.TestBacktestHybrid.test_sell_uses_ppo_when_hybrid_available -v`

Expected: FAIL (predict_sell not called, old rule-based logic used).

**Step 3: Modify _check_initial_position**

In `src/backtest/engine.py`, modify `_check_initial_position` (lines 209-227):

```python
    async def _check_initial_position(self, token_address: str, current_price: float, timestamp: int):
        position = self.positions[token_address]
        entry_price = position['entry_price']
        if entry_price <= 0:
            return

        pnl_pct = (current_price - entry_price) / entry_price * 100

        # Hard stop-loss always applies
        if pnl_pct <= self.stop_loss_pct:
            await self._sell_all(token_address, current_price, timestamp, 'stop_loss')
            return

        # PPO sell decision when hybrid model available
        if self.hybrid is not None and self.hybrid.sell_policy is not None:
            obs = [current_price, 0.0, 0.0, 0.0, 0.0]
            action = self.hybrid.predict_sell(obs)
            if action == 1:
                await self._sell_partial(token_address, 0.25, current_price, timestamp, 'ppo_sell25')
                return
            elif action == 2:
                await self._sell_partial(token_address, 0.50, current_price, timestamp, 'ppo_sell50')
                return
            elif action == 3:
                await self._sell_all(token_address, current_price, timestamp, 'ppo_sell100')
                return
            return  # action == 0: hold

        # Fallback: original rule-based logic
        if pnl_pct >= self.take_profit_pct:
            await self._sell_partial(token_address, self.take_profit_sell_pct / 100, current_price, timestamp, 'take_profit')
            return
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/backtest/engine.py tests/model/test_backtest_hybrid.py
git commit -m "feat: wire hybrid sell signal into BacktestEngine"
```

---

### Task 8: Add Sortino and MaxDD metrics to BacktestEngine

**Files:**
- Modify: `src/backtest/engine.py:337-385` (_generate_stats)
- Modify: `tests/model/test_backtest_hybrid.py`

**Step 1: Write the failing test**

Add to `tests/model/test_backtest_hybrid.py`:

```python
    def test_generate_stats_includes_sortino_and_maxdd(self):
        m = _load_engine()
        engine = m.BacktestEngine()
        engine.closed_positions = [
            {"pnl_bnb": 0.05, "pnl_pct": 50.0, "bnb_invested": 0.1, "exit_reason": "take_profit"},
            {"pnl_bnb": -0.02, "pnl_pct": -20.0, "bnb_invested": 0.1, "exit_reason": "stop_loss"},
            {"pnl_bnb": 0.03, "pnl_pct": 30.0, "bnb_invested": 0.1, "exit_reason": "take_profit"},
        ]
        stats = engine._generate_stats()
        self.assertIn("sortino_ratio", stats)
        self.assertIn("max_drawdown_pct", stats)
        self.assertIn("net_return_pct", stats)
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_backtest_hybrid.TestBacktestHybrid.test_generate_stats_includes_sortino_and_maxdd -v`

Expected: FAIL (keys missing from stats dict).

**Step 3: Add metrics to _generate_stats**

At the end of `_generate_stats` in `src/backtest/engine.py`, before the return dict, add:

```python
        import numpy as np

        returns = np.array([p['pnl_pct'] for p in valid_positions])
        net_return_pct = float(returns.sum()) if returns.size > 0 else 0.0

        # Sortino ratio (annualized, using downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = float(np.std(negative_returns)) if len(negative_returns) > 0 else 1e-9
        mean_return = float(np.mean(returns)) if returns.size > 0 else 0.0
        sortino_ratio = mean_return / max(downside_std, 1e-9)

        # Max drawdown from cumulative equity curve
        cumulative = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = cumulative - peak
        max_drawdown_pct = float(np.min(drawdown)) if drawdown.size > 0 else 0.0
```

Then add to the return dict:

```python
            'sortino_ratio': sortino_ratio,
            'max_drawdown_pct': max_drawdown_pct,
            'net_return_pct': net_return_pct,
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/backtest/engine.py tests/model/test_backtest_hybrid.py
git commit -m "feat: add sortino/maxdd/net_return metrics to backtest stats"
```

---

### Task 9: Wire post-training backtest into hybrid pipeline

**Files:**
- Modify: `src/pipeline/train_hybrid.py:212-249` (run_ab_evaluation + run_hybrid_training)
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add to `tests/model/test_train_hybrid_pipeline.py`:

```python
    def test_evaluation_includes_backtest_metrics(self):
        m = _load_module()
        fake_stats = {
            "total_trades": 10,
            "win_rate": 60.0,
            "sortino_ratio": 1.5,
            "max_drawdown_pct": -15.0,
            "net_return_pct": 42.0,
        }
        with patch.object(m, "train_buy_model", return_value={"model_path": "buy.cbm", "threshold": 0.45, "labels": [0, 1], "samples": [{}]}), \
             patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
             patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
             patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128}), \
             patch.object(m, "_run_backtest", return_value=fake_stats):
            result = m.run_hybrid_training({"output_dir": "data/models", "lifecycle_dir": "data/training"})

        self.assertEqual(result["evaluation"]["sortino_ratio"], 1.5)
        self.assertEqual(result["evaluation"]["max_drawdown_pct"], -15.0)
        self.assertIn("pipeline_status", result["evaluation"])
```

**Step 2: Run test to verify it fails**

Run: `cd /root/meme && python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_evaluation_includes_backtest_metrics -v`

Expected: FAIL (no backtest metrics in evaluation).

**Step 3: Implement _run_backtest and update run_ab_evaluation**

In `src/pipeline/train_hybrid.py`, add:

```python
def _run_backtest(config, model_dir):
    import asyncio
    import glob
    from src.backtest.engine import BacktestEngine
    from src.model.hybrid_inference import HybridModel

    lifecycle_dir = config.get("lifecycle_dir", "data/training")
    data_files = sorted(glob.glob(str(Path(lifecycle_dir) / "*.jsonl")))
    if not data_files:
        return {"total_trades": 0, "win_rate": 0, "sortino_ratio": 0, "max_drawdown_pct": 0, "net_return_pct": 0}

    try:
        hybrid = HybridModel.load(model_dir)
    except Exception:
        return {"total_trades": 0, "win_rate": 0, "sortino_ratio": 0, "max_drawdown_pct": 0, "net_return_pct": 0, "error": "failed to load model for backtest"}

    engine = BacktestEngine(hybrid_model=hybrid)
    all_stats = {}
    for f in data_files:
        stats = asyncio.run(engine.run_backtest(f))
        all_stats = stats  # last file stats (or merge logic)
    return all_stats
```

Update `run_ab_evaluation` to include backtest results:

```python
def run_ab_evaluation(config, buy_artifact, ppo_artifact, env_bundle, bc_artifact):
    labels = np.asarray(buy_artifact.get("labels", []), dtype=float)
    positive_rate = float(labels.mean()) if labels.size > 0 else 0.0

    output_dir = config.get("output_dir", "data/models")
    backtest_stats = _run_backtest(config, output_dir)

    return {
        "buy_positive_rate": positive_rate,
        "buy_threshold": float(buy_artifact.get("threshold", 1.0)),
        "sell_episode_count": int(env_bundle.get("episode_count", 0)),
        "bc_samples": int(bc_artifact.get("bc_samples", 0)),
        "ppo_total_timesteps": int(ppo_artifact.get("total_timesteps", 0)),
        "pipeline_status": "ok",
        **backtest_stats,
    }
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: wire post-training backtest into hybrid pipeline"
```

---

### Task 10: Final verification sweep

**Files:**
- None (verification only)

**Step 1: Run all test suites**

Run:

```bash
cd /root/meme && python3 -m unittest tests.model.test_hybrid_inference tests.model.test_backtest_hybrid tests.model.test_train_hybrid_pipeline tests.model.test_run_hybrid_training_cli tests.model.test_impact_model tests.model.test_trading_env tests.model.test_buy_catboost -v
```

Expected: all PASS.

**Step 2: Verify CLI smoke test**

Run:

```bash
cd /root/meme && python3 scripts/run_hybrid_training.py --help
```

Expected: shows all args including `--lifecycle-dir`, `--target-threshold-value`, etc.

**Step 3: Commit if fixes needed**

```bash
git add <fixed-files>
git commit -m "fix: address verification findings in hybrid integration"
```
