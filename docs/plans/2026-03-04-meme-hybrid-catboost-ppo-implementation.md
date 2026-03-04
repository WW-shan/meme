# Meme Hybrid CatBoost+PPO Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a behavior-first hybrid pipeline that uses CatBoost for buy-side classification and PPO for sell-side execution in low-liquidity meme coin episodes.

**Architecture:** Keep existing dataset/trainer flows intact for backward compatibility, then add a parallel hybrid stack (`features -> buy model -> RL env -> BC warm start -> PPO fine-tune -> evaluation artifacts`). Implement low-liquidity execution realism via explicit slippage/impact modeling and dynamic episode termination. Favor small-data stability and reproducibility over model complexity.

**Tech Stack:** Python 3, pandas/numpy, CatBoost, Gymnasium, Stable-Baselines3 (PPO), PyTorch, unittest, existing project scripts and data format.

---

Execution discipline for every task: follow @superpowers:test-driven-development (failing test -> fail run -> minimal implementation -> pass run -> commit).

### Task 1: Add hybrid dependency contract

**Files:**
- Modify: `requirements.txt`
- Create: `tests/core/test_hybrid_requirements_contract.py`

**Step 1: Write the failing test**

```python
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQ_FILE = ROOT / "requirements.txt"


class TestHybridRequirementsContract(unittest.TestCase):
    def _requirement_names(self):
        names = set()
        for raw in REQ_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            name = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip().lower()
            if name:
                names.add(name)
        return names

    def test_hybrid_dependencies_are_declared(self):
        names = self._requirement_names()
        expected = {"catboost", "gymnasium", "stable-baselines3", "torch"}
        missing = sorted(expected - names)
        self.assertFalse(missing, f"Missing dependencies: {missing}")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_hybrid_requirements_contract.TestHybridRequirementsContract.test_hybrid_dependencies_are_declared -v`

Expected: FAIL with missing dependency names.

**Step 3: Write minimal implementation**

Add to `requirements.txt`:

```text
catboost>=1.2
gymnasium>=0.29
stable-baselines3>=2.3
torch>=2.2
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_hybrid_requirements_contract.TestHybridRequirementsContract.test_hybrid_dependencies_are_declared -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add requirements.txt tests/core/test_hybrid_requirements_contract.py
git commit -m "build: add hybrid CatBoost+RL dependency contract"
```

---

### Task 2: Implement feature validity analyzer for <5m lifecycle

**Files:**
- Create: `src/features/__init__.py`
- Create: `src/features/feature_validity.py`
- Create: `tests/model/test_feature_validity.py`

**Step 1: Write the failing test**

```python
import unittest
from pathlib import Path
import importlib.util


def _load_feature_validity_module():
    path = Path(__file__).resolve().parents[2] / "src" / "features" / "feature_validity.py"
    spec = importlib.util.spec_from_file_location("feature_validity", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestFeatureValidity(unittest.TestCase):
    def test_analyze_feature_columns_assigns_tiers(self):
        module = _load_feature_validity_module()
        cols = [
            "price_change_pct",
            "volume_5min",
            "creator_id",
            "future_max_return",
            "token_name_pattern",
        ]

        result = module.analyze_feature_columns(cols)

        self.assertEqual(result["price_change_pct"]["tier"], "effective")
        self.assertEqual(result["creator_id"]["tier"], "effective")
        self.assertEqual(result["volume_5min"]["tier"], "weak")
        self.assertEqual(result["future_max_return"]["tier"], "invalid")
        self.assertIn("reason", result["future_max_return"])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_feature_validity.TestFeatureValidity.test_analyze_feature_columns_assigns_tiers -v`

Expected: FAIL (module/file missing).

**Step 3: Write minimal implementation**

In `src/features/feature_validity.py`, add:

```python
from typing import Dict, List

INVALID_PATTERNS = ("future_", "label_", "target_")
WEAK_PATTERNS = ("_5min", "_10min", "hour", "daily")
EFFECTIVE_PATTERNS = (
    "creator",
    "token_name",
    "holder",
    "concentration",
    "lp_",
    "buy_sell",
    "retail",
    "price_change",
)


def classify_feature(name: str) -> Dict[str, str]:
    n = str(name)
    low = n.lower()

    if any(p in low for p in INVALID_PATTERNS):
        return {"tier": "invalid", "reason": "contains future/target leakage pattern"}
    if any(p in low for p in EFFECTIVE_PATTERNS):
        return {"tier": "effective", "reason": "aligned with sub-5m behavior microstructure"}
    if any(p in low for p in WEAK_PATTERNS):
        return {"tier": "weak", "reason": "likely too slow for sub-5m token lifecycle"}
    return {"tier": "weak", "reason": "no strong short-horizon behavior signal"}


def analyze_feature_columns(columns: List[str]) -> Dict[str, Dict[str, str]]:
    return {str(col): classify_feature(str(col)) for col in columns}
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_feature_validity -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/features/__init__.py src/features/feature_validity.py tests/model/test_feature_validity.py
git commit -m "feat: add short-lifecycle feature validity analyzer"
```

---

### Task 3: Add behavior dynamics features to extractor

**Files:**
- Modify: `src/data/feature_extractor.py`
- Create: `tests/model/test_feature_extractor_behavior_dynamics.py`

**Step 1: Write the failing test**

```python
import unittest
from src.data.feature_extractor import extract_features


class TestFeatureExtractorBehaviorDynamics(unittest.TestCase):
    def test_extract_features_includes_behavior_dynamics_keys(self):
        lifecycle = {
            "create_timestamp": 100,
            "total_supply": int(1_000_000 * 1e18),
            "launch_fee": int(0.2 * 1e18),
            "name": "MemeA",
            "symbol": "MA",
            "creator": "C1",
        }
        past_buys = [
            {"timestamp": 105, "account": "A", "bnb_amount": 0.1, "token_amount": 100, "price": 0.001},
            {"timestamp": 115, "account": "B", "bnb_amount": 0.2, "token_amount": 160, "price": 0.00125},
            {"timestamp": 125, "account": "C", "bnb_amount": 0.25, "token_amount": 180, "price": 0.00138},
        ]
        past_sells = [
            {"timestamp": 128, "account": "B", "bnb_amount": 0.05, "token_amount": 30, "price": 0.00166},
        ]

        features = extract_features(lifecycle, past_buys, past_sells, sample_time=130)

        for key in [
            "top10_holder_share_10s",
            "top10_holder_share_30s",
            "concentration_decay_10_30",
            "retail_entry_rate_ratio_30s",
            "lp_resistance_ratio_10s",
        ]:
            self.assertIn(key, features)
            self.assertTrue(isinstance(features[key], float))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_feature_extractor_behavior_dynamics.TestFeatureExtractorBehaviorDynamics.test_extract_features_includes_behavior_dynamics_keys -v`

Expected: FAIL (new keys missing).

**Step 3: Write minimal implementation**

In `src/data/feature_extractor.py`, add helper calculations and include keys:

```python
# new keys added to features dict
"top10_holder_share_10s": ...,
"top10_holder_share_30s": ...,
"concentration_decay_10_30": ...,
"retail_entry_rate_ratio_30s": ...,
"lp_resistance_ratio_10s": ...,
```

Implementation guidance:
- `top10_holder_share_*`: recompute balances inside rolling cutoffs and take top-10 / total held.
- `concentration_decay_10_30 = (top10_10s - top10_30s) / 20.0`.
- `retail_entry_rate_ratio_30s = slope(unique_buyers_30s) / max(slope(volume_30s), eps)`.
- `lp_resistance_ratio_10s = liquidity_proxy / max(recent_sell_pressure, eps)`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_feature_extractor_behavior_dynamics -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/data/feature_extractor.py tests/model/test_feature_extractor_behavior_dynamics.py
git commit -m "feat: add behavior dynamics features for short-lifecycle tokens"
```

---

### Task 4: Add CatBoost buy-side classifier module

**Files:**
- Create: `src/model/buy_catboost.py`
- Create: `tests/model/test_buy_catboost.py`

**Step 1: Write the failing test**

```python
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util
import pandas as pd


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "model" / "buy_catboost.py"
    spec = importlib.util.spec_from_file_location("buy_catboost", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestBuyCatBoost(unittest.TestCase):
    def test_build_focal_like_weights_increases_positive_weight(self):
        module = _load_module()
        y = [0, 0, 0, 1]
        w = module.build_focal_like_weights(y, gamma=2.0, alpha_pos=3.0)
        self.assertEqual(len(w), 4)
        self.assertGreater(w[-1], w[0])

    def test_fit_passes_cat_feature_indices(self):
        module = _load_module()
        df = pd.DataFrame({
            "creator_id": ["a", "b", "c", "a"],
            "price_change_pct": [1.0, 2.0, 3.0, 4.0],
            "target": [0, 0, 1, 1],
        })
        fake_model = MagicMock()
        fake_model.predict_proba.return_value = [[0.4, 0.6]] * len(df)

        with patch.object(module, "CatBoostClassifier", return_value=fake_model):
            model = module.BuyCatBoostModel(cat_feature_names=["creator_id"])
            model.fit(df.drop(columns=["target"]), df["target"])

        self.assertTrue(fake_model.fit.called)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_buy_catboost -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/model/buy_catboost.py`, implement:

```python
def build_focal_like_weights(y, gamma=2.0, alpha_pos=2.0): ...

class BuyCatBoostModel:
    def __init__(self, cat_feature_names=None, random_state=42): ...
    def fit(self, X, y): ...
    def predict_proba(self, X): ...
    def select_threshold(self, y_true, prob, min_precision=0.10): ...
```

Use CatBoost with:
- `loss_function="Logloss"`
- `eval_metric="AUC"`
- class imbalance via sample weights from `build_focal_like_weights`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_buy_catboost -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/model/buy_catboost.py tests/model/test_buy_catboost.py
git commit -m "feat: add CatBoost buy-side classifier wrapper"
```

---

### Task 5: Implement low-liquidity impact/slippage model

**Files:**
- Create: `src/backtest/impact_model.py`
- Create: `tests/model/test_impact_model.py`

**Step 1: Write the failing test**

```python
import unittest
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "backtest" / "impact_model.py"
    spec = importlib.util.spec_from_file_location("impact_model", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestImpactModel(unittest.TestCase):
    def test_cost_increases_with_order_size(self):
        m = _load_module()
        c_small = m.estimate_execution_cost(order_size=0.1, lp_depth=10.0, imbalance=0.1)
        c_large = m.estimate_execution_cost(order_size=1.0, lp_depth=10.0, imbalance=0.1)
        self.assertGreater(c_large, c_small)

    def test_partial_fill_when_depth_too_low(self):
        m = _load_module()
        result = m.simulate_sell_fill(order_size=10.0, lp_depth=1.0, max_fill_ratio=0.8)
        self.assertLess(result["filled_size"], 10.0)
        self.assertAlmostEqual(result["fill_ratio"], 0.8)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_impact_model -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/backtest/impact_model.py`, implement:

```python
def estimate_execution_cost(order_size, lp_depth, imbalance, k_temp=0.02, k_perm=0.01): ...

def simulate_sell_fill(order_size, lp_depth, max_fill_ratio=0.8): ...
```

Keep formulas simple and monotonic; use finite clamps.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_impact_model -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/backtest/impact_model.py tests/model/test_impact_model.py
git commit -m "feat: add low-liquidity impact and partial-fill model"
```

---

### Task 6: Build Gymnasium TradingEnv and reward module

**Files:**
- Create: `src/rl/__init__.py`
- Create: `src/rl/reward.py`
- Create: `src/rl/trading_env.py`
- Create: `tests/model/test_trading_env.py`

**Step 1: Write the failing test**

```python
import unittest
from pathlib import Path
import importlib.util


def _load_env_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "trading_env.py"
    spec = importlib.util.spec_from_file_location("trading_env", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTradingEnv(unittest.TestCase):
    def _episode(self):
        return [
            {"mid_price": 1.0, "lp_depth": 8.0, "sell_pressure": 0.3, "buy_sell_ratio": 1.2, "holders": 40, "ts": 1},
            {"mid_price": 1.1, "lp_depth": 7.0, "sell_pressure": 0.4, "buy_sell_ratio": 1.0, "holders": 42, "ts": 2},
            {"mid_price": 0.9, "lp_depth": 0.1, "sell_pressure": 1.8, "buy_sell_ratio": 0.4, "holders": 35, "ts": 3},
        ]

    def test_step_sell25_reduces_position(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode())
        obs, _ = env.reset()
        _, _, _, _, info = env.step(1)
        self.assertLess(info["position_remaining"], 1.0)

    def test_dynamic_termination_on_liquidity_exhaustion(self):
        m = _load_env_module()
        env = m.TradingEnv(self._episode(), liquidity_floor=0.2, stall_steps=1)
        env.reset()
        _, _, terminated, _, info = env.step(0)
        _, _, terminated, _, info = env.step(0)
        self.assertTrue(terminated)
        self.assertEqual(info.get("done_reason"), "liquidity_exhausted")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_trading_env -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/rl/reward.py` add:

```python
def differential_sharpe_increment(...): ...
def compute_step_reward(...): ...
```

In `src/rl/trading_env.py` add `TradingEnv(gym.Env)` with:
- action mapping: hold/sell25/sell50/sell100
- event-driven step
- execution cost from `src.backtest.impact_model`
- dynamic done reasons

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_trading_env -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/rl/__init__.py src/rl/reward.py src/rl/trading_env.py tests/model/test_trading_env.py
git commit -m "feat: add low-liquidity Gym trading environment"
```

---

### Task 7: Add behavior-cloning warm start module

**Files:**
- Create: `src/rl/warmstart_bc.py`
- Create: `tests/model/test_warmstart_bc.py`

**Step 1: Write the failing test**

```python
import unittest
import torch
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "warmstart_bc.py"
    spec = importlib.util.spec_from_file_location("warmstart_bc", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestWarmstartBC(unittest.TestCase):
    def test_train_bc_returns_state_dict(self):
        m = _load_module()
        obs = torch.tensor([[0.1, 0.2], [0.2, 0.1], [0.9, 0.8]], dtype=torch.float32)
        actions = torch.tensor([0, 0, 3], dtype=torch.long)

        state = m.train_bc(obs, actions, hidden_dim=8, epochs=5, lr=1e-2)

        self.assertIsInstance(state, dict)
        self.assertTrue(any(k.endswith("weight") for k in state.keys()))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_warmstart_bc -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/rl/warmstart_bc.py`, add:

```python
class BCSmallPolicy(torch.nn.Module): ...
def train_bc(obs_tensor, action_tensor, hidden_dim=64, epochs=20, lr=1e-3): ...
```

Train via cross-entropy and return `state_dict`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_warmstart_bc -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/rl/warmstart_bc.py tests/model/test_warmstart_bc.py
git commit -m "feat: add behavior cloning warm-start trainer"
```

---

### Task 8: Add PPO training wrapper with optional BC initialization

**Files:**
- Create: `src/rl/train_ppo.py`
- Create: `tests/model/test_train_ppo.py`

**Step 1: Write the failing test**

```python
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "rl" / "train_ppo.py"
    spec = importlib.util.spec_from_file_location("train_ppo", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTrainPPO(unittest.TestCase):
    def test_train_ppo_calls_learn_with_timesteps(self):
        m = _load_module()
        fake_env = object()
        fake_model = MagicMock()

        with patch.object(m, "PPO", return_value=fake_model):
            result = m.train_ppo(fake_env, total_timesteps=128, seed=7)

        self.assertIs(result, fake_model)
        fake_model.learn.assert_called_once_with(total_timesteps=128, progress_bar=False)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_ppo -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/rl/train_ppo.py`, add:

```python
from stable_baselines3 import PPO

def train_ppo(env, total_timesteps=20000, seed=42, policy_kwargs=None):
    model = PPO("MlpPolicy", env, seed=seed, policy_kwargs=policy_kwargs or dict(net_arch=[128, 128]), verbose=0)
    model.learn(total_timesteps=total_timesteps, progress_bar=False)
    return model
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_train_ppo -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/rl/train_ppo.py tests/model/test_train_ppo.py
git commit -m "feat: add PPO training wrapper for sell policy"
```

---

### Task 9: Add hybrid training pipeline orchestrator

**Files:**
- Create: `src/pipeline/__init__.py`
- Create: `src/pipeline/train_hybrid.py`
- Create: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

```python
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestTrainHybridPipeline(unittest.TestCase):
    def test_run_hybrid_training_returns_artifact_manifest(self):
        m = _load_module()

        with patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.42}), \
             patch.object(m, "build_sell_env", return_value=MagicMock()), \
             patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt"}), \
             patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip"}), \
             patch.object(m, "run_ab_evaluation", return_value={"maxdd_delta": -0.25, "sortino_delta": 0.2}):
            result = m.run_hybrid_training({"output_dir": "data/models"})

        self.assertIn("buy_model", result["artifacts"])
        self.assertIn("sell_policy", result["artifacts"])
        self.assertIn("evaluation", result)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline -v`

Expected: FAIL (module missing).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`, add orchestrator with explicit stages:

```python
def train_buy_model(config): ...
def build_sell_env(config, buy_artifact): ...
def run_bc_warmstart(config, env): ...
def run_ppo_finetune(config, env, bc_artifact): ...
def run_ab_evaluation(config, buy_artifact, ppo_artifact): ...

def run_hybrid_training(config):
    ...
    return {
        "artifacts": {"buy_model": ..., "sell_policy": ...},
        "evaluation": ...,
    }
```

Keep this task as orchestration skeleton + artifact manifest only.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/__init__.py src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: add hybrid CatBoost+PPO training orchestrator"
```

---

### Task 10: Add CLI entrypoint for hybrid pipeline

**Files:**
- Create: `scripts/run_hybrid_training.py`
- Create: `tests/model/test_run_hybrid_training_cli.py`

**Step 1: Write the failing test**

```python
import unittest
from unittest.mock import patch
from pathlib import Path
import importlib.util


def _load_cli():
    path = Path(__file__).resolve().parents[2] / "scripts" / "run_hybrid_training.py"
    spec = importlib.util.spec_from_file_location("run_hybrid_training", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestRunHybridTrainingCli(unittest.TestCase):
    def test_parse_args_defaults(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.output_dir, "data/models")
        self.assertEqual(args.total_timesteps, 20000)

    def test_main_calls_pipeline(self):
        cli = _load_cli()
        with patch.object(cli, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
            cli.main(["--output-dir", "tmp/models", "--total-timesteps", "512"])
        mock_run.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_run_hybrid_training_cli -v`

Expected: FAIL (script missing).

**Step 3: Write minimal implementation**

Create `scripts/run_hybrid_training.py`:

```python
import argparse
from src.pipeline.train_hybrid import run_hybrid_training


def parse_args(argv=None): ...

def main(argv=None):
    args = parse_args(argv)
    config = {
        "output_dir": args.output_dir,
        "total_timesteps": args.total_timesteps,
    }
    return run_hybrid_training(config)

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_run_hybrid_training_cli -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/run_hybrid_training.py tests/model/test_run_hybrid_training_cli.py
git commit -m "feat: add hybrid training CLI entrypoint"
```

---

### Task 11: Verification sweep and artifact sanity

**Files:**
- Verify only (no required file edits unless test failures demand fixes)

**Step 1: Run focused unit tests**

Run:
```bash
python3 -m unittest tests.core.test_hybrid_requirements_contract -v
python3 -m unittest tests.model.test_feature_validity -v
python3 -m unittest tests.model.test_feature_extractor_behavior_dynamics -v
python3 -m unittest tests.model.test_buy_catboost -v
python3 -m unittest tests.model.test_impact_model -v
python3 -m unittest tests.model.test_trading_env -v
python3 -m unittest tests.model.test_warmstart_bc -v
python3 -m unittest tests.model.test_train_ppo -v
python3 -m unittest tests.model.test_train_hybrid_pipeline -v
python3 -m unittest tests.model.test_run_hybrid_training_cli -v
```

Expected: PASS.

**Step 2: Run CLI smoke test**

Run:
`python3 scripts/run_hybrid_training.py --output-dir data/models --total-timesteps 512`

Expected:
- command exits successfully
- prints/saves artifact manifest containing buy model + sell policy + evaluation summary

**Step 3: Validate output manifest fields**

Check latest output JSON/report includes:
- buy side: model path + threshold
- sell side: PPO policy path
- evaluation: `maxdd_delta`, `sortino_delta`, `net_return_delta`

**Step 4: Commit final integration fixes (if any)**

```bash
git add src/features src/model src/rl src/pipeline src/backtest scripts tests requirements.txt
git commit -m "feat: deliver hybrid CatBoost buy and PPO sell training pipeline"
```

---

Use @superpowers:verification-before-completion before claiming final success.
