# Train Hybrid Real-Training Wiring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert `src/pipeline/train_hybrid.py` from placeholder orchestration into a real staged training pipeline using `DatasetBuilder`, `BuyCatBoostModel`, BC warm-start, PPO finetuning, and real evaluation/artifact outputs.

**Architecture:** Keep staged orchestration (`train_buy_model -> build_sell_env -> run_bc_warmstart -> run_ppo_finetune -> run_ab_evaluation`) but replace each stage with real data/model operations. Add small internal helpers for config normalization, sample-to-frame conversion, episode construction, and serialization so behavior is testable and fail-fast.

**Tech Stack:** Python 3, unittest, pandas/numpy, CatBoost, Gymnasium TradingEnv, PyTorch BC, Stable-Baselines3 PPO, existing DatasetBuilder.

---

Execution discipline for every task: follow @superpowers:test-driven-development (failing test -> fail run -> minimal implementation -> pass run -> commit).

### Task 1: Add train_hybrid data-contract guard tests and helper contract

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

**Step 1: Write the failing tests**

Add to `tests/model/test_train_hybrid_pipeline.py`:

```python
    def test_prepare_training_rows_rejects_empty_samples(self):
        m = _load_module()
        with self.assertRaises(ValueError):
            m._prepare_training_rows([], "max_return_pct", 80.0)

    def test_prepare_training_rows_rejects_single_class_target(self):
        m = _load_module()
        samples = [
            {
                "features": {"current_price": 1.0, "buy_pressure": 0.6},
                "label": {"max_return_pct": 10.0},
                "meta": {"token_address": "A", "sample_time": 100},
            },
            {
                "features": {"current_price": 1.1, "buy_pressure": 0.7},
                "label": {"max_return_pct": 12.0},
                "meta": {"token_address": "B", "sample_time": 110},
            },
        ]
        with self.assertRaises(ValueError):
            m._prepare_training_rows(samples, "max_return_pct", 80.0)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_prepare_training_rows_rejects_empty_samples tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_prepare_training_rows_rejects_single_class_target -v`

Expected: FAIL with `AttributeError` (helper missing).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`, add helper:

```python
def _prepare_training_rows(samples, target_label_column, target_threshold_value):
    if not samples:
        raise ValueError("no samples generated from DatasetBuilder")

    feature_rows, labels, metas = [], [], []
    for sample in samples:
        label_value = float(sample.get("label", {}).get(target_label_column, 0.0))
        feature_rows.append(dict(sample.get("features", {})))
        labels.append(1 if label_value >= float(target_threshold_value) else 0)
        metas.append(dict(sample.get("meta", {})))

    if len(set(labels)) < 2:
        raise ValueError("buy target has single class; cannot train classifier")

    return feature_rows, labels, metas
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_train_hybrid_pipeline.py src/pipeline/train_hybrid.py
git commit -m "test: add train_hybrid sample contract guards"
```

---

### Task 2: Implement real buy-stage training and artifact persistence

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add test:

```python
    def test_train_buy_model_saves_model_and_threshold(self):
        import tempfile
        m = _load_module()
        samples = [
            {"features": {"current_price": 1.0, "buy_pressure": 0.4}, "label": {"max_return_pct": 20.0}, "meta": {"token_address": "A", "sample_time": 100}},
            {"features": {"current_price": 1.1, "buy_pressure": 0.8}, "label": {"max_return_pct": 120.0}, "meta": {"token_address": "B", "sample_time": 110}},
            {"features": {"current_price": 1.2, "buy_pressure": 0.3}, "label": {"max_return_pct": 10.0}, "meta": {"token_address": "C", "sample_time": 120}},
            {"features": {"current_price": 1.3, "buy_pressure": 0.9}, "label": {"max_return_pct": 200.0}, "meta": {"token_address": "D", "sample_time": 130}},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_load_samples", return_value=samples), \
                 patch.object(m, "BuyCatBoostModel") as MockModel:
                fake = MagicMock()
                fake.predict_proba.return_value = [[0.3, 0.7]] * len(samples)
                fake.select_threshold.return_value = 0.42
                fake.model = MagicMock()
                MockModel.return_value = fake

                out = m.train_buy_model({"output_dir": tmpdir, "target_label_column": "max_return_pct", "target_threshold_value": 80.0})

            self.assertTrue(Path(out["model_path"]).exists())
            self.assertTrue(Path(out["threshold_path"]).exists())
            self.assertIn("labels", out)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_train_buy_model_saves_model_and_threshold -v`

Expected: FAIL (placeholder `train_buy_model` has no persistence/labels contract).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`:

```python
def _load_samples(config):
    builder = DatasetBuilder(
        lifecycle_dir=config.get("lifecycle_dir", "data/training"),
        sample_mode=config.get("sample_mode", "trade_event"),
        max_sample_age_seconds=int(config.get("max_sample_age_seconds", 180)),
        future_windows=config.get("future_windows", [240]),
    )
    builder.load_lifecycle_files()
    return builder.samples


def train_buy_model(config):
    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = _load_samples(config)
    rows, labels, metas = _prepare_training_rows(
        samples,
        config.get("target_label_column", "max_return_pct"),
        float(config.get("target_threshold_value", 80.0)),
    )

    X = pd.DataFrame(rows)
    y = np.asarray(labels, dtype=int)

    model = BuyCatBoostModel(cat_feature_names=config.get("cat_feature_names", []))
    model.fit(X, y)
    proba = model.predict_proba(X)
    threshold = model.select_threshold(y, proba, min_precision=float(config.get("buy_min_precision", 0.10)))

    model_path = output_dir / "buy_model.cbm"
    model.model.save_model(str(model_path))

    threshold_path = output_dir / "buy_threshold.json"
    threshold_path.write_text(json.dumps({"threshold": float(threshold)}, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "model_path": str(model_path),
        "threshold": float(threshold),
        "threshold_path": str(threshold_path),
        "samples": samples,
        "labels": labels,
        "meta": metas,
    }
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: wire real buy-stage training in hybrid pipeline"
```

---

### Task 3: Implement sell episode construction and TradingEnv build stage

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add test:

```python
    def test_build_sell_env_creates_trading_env_bundle(self):
        m = _load_module()
        buy_artifact = {
            "samples": [
                {
                    "features": {
                        "current_price": 1.0,
                        "launch_fee": 0.5,
                        "buy_pressure": 0.7,
                        "holder_count": 40,
                        "total_buy_volume": 3.0,
                        "total_sell_volume": 1.0,
                    },
                    "meta": {"token_address": "A", "sample_time": 100},
                },
                {
                    "features": {
                        "current_price": 1.1,
                        "launch_fee": 0.5,
                        "buy_pressure": 0.6,
                        "holder_count": 42,
                        "total_buy_volume": 4.0,
                        "total_sell_volume": 2.0,
                    },
                    "meta": {"token_address": "A", "sample_time": 110},
                },
            ]
        }

        bundle = m.build_sell_env({"liquidity_floor": 0.05, "stall_steps": 2}, buy_artifact)

        self.assertIn("env", bundle)
        self.assertGreater(bundle["episode_count"], 0)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_build_sell_env_creates_trading_env_bundle -v`

Expected: FAIL (`build_sell_env` returns placeholder dict).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`:

```python
def _sample_to_event(sample):
    f = sample.get("features", {})
    buy_vol = float(f.get("total_buy_volume", 0.0))
    sell_vol = float(f.get("total_sell_volume", 0.0))
    buy_sell_ratio = buy_vol / max(sell_vol, 1e-9)
    sell_pressure = sell_vol / max(buy_vol + sell_vol, 1e-9)
    return {
        "mid_price": float(f.get("current_price", 0.0)),
        "lp_depth": float(f.get("launch_fee", 0.0)),
        "sell_pressure": float(sell_pressure),
        "buy_sell_ratio": float(buy_sell_ratio),
        "holders": float(f.get("holder_count", 0.0)),
        "ts": int(sample.get("meta", {}).get("sample_time", 0) or 0),
    }


def build_sell_env(config, buy_artifact):
    grouped = {}
    for sample in buy_artifact.get("samples", []):
        token = str(sample.get("meta", {}).get("token_address", ""))
        grouped.setdefault(token, []).append(sample)

    episodes = []
    for token_samples in grouped.values():
        ordered = sorted(token_samples, key=lambda s: int(s.get("meta", {}).get("sample_time", 0) or 0))
        episode = [_sample_to_event(s) for s in ordered]
        if len(episode) >= 2:
            episodes.append(episode)

    if not episodes:
        raise ValueError("no sell episodes could be built from samples")

    env = TradingEnv(
        episodes[0],
        liquidity_floor=float(config.get("liquidity_floor", 0.05)),
        stall_steps=int(config.get("stall_steps", 3)),
    )
    return {"env": env, "episodes": episodes, "episode_count": len(episodes)}
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: build sell-side episodes and trading env bundle"
```

---

### Task 4: Implement BC warm-start stage with saved weights

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add test:

```python
    def test_run_bc_warmstart_saves_weights(self):
        import tempfile
        m = _load_module()
        env_bundle = {
            "episodes": [
                [
                    {"mid_price": 1.0, "lp_depth": 1.0, "sell_pressure": 0.2, "buy_sell_ratio": 2.0, "holders": 40},
                    {"mid_price": 0.9, "lp_depth": 1.0, "sell_pressure": 1.4, "buy_sell_ratio": 0.7, "holders": 38},
                ]
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "train_bc", return_value={"net.0.weight": [1.0]}), \
                 patch.object(m, "_torch_save") as mock_save:
                out = m.run_bc_warmstart({"output_dir": tmpdir, "bc_epochs": 3}, env_bundle)

        self.assertTrue(out["weights"].endswith("bc.pt"))
        mock_save.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_bc_warmstart_saves_weights -v`

Expected: FAIL (placeholder return, no train/save path).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`:

```python
def _torch_save(obj, path):
    import torch
    torch.save(obj, path)


def _build_bc_arrays(episodes):
    obs_rows, action_rows = [], []
    for ep in episodes:
        for event in ep:
            obs_rows.append([
                float(event.get("mid_price", 0.0)),
                float(event.get("lp_depth", 0.0)),
                float(event.get("sell_pressure", 0.0)),
                float(event.get("buy_sell_ratio", 0.0)),
                float(event.get("holders", 0.0)),
            ])
            sp = float(event.get("sell_pressure", 0.0))
            if sp >= 1.2:
                action_rows.append(3)
            elif sp >= 0.8:
                action_rows.append(2)
            elif sp >= 0.5:
                action_rows.append(1)
            else:
                action_rows.append(0)
    return np.asarray(obs_rows, dtype=np.float32), np.asarray(action_rows, dtype=np.int64)


def run_bc_warmstart(config, env_bundle):
    import torch

    episodes = env_bundle.get("episodes", [])
    obs_arr, act_arr = _build_bc_arrays(episodes)
    if obs_arr.size == 0:
        raise ValueError("no BC samples generated from episodes")

    obs = torch.tensor(obs_arr, dtype=torch.float32)
    actions = torch.tensor(act_arr, dtype=torch.long)

    state = train_bc(
        obs,
        actions,
        hidden_dim=int(config.get("bc_hidden_dim", 64)),
        epochs=int(config.get("bc_epochs", 20)),
        lr=float(config.get("bc_lr", 1e-3)),
    )

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    weight_path = output_dir / "bc.pt"
    _torch_save(state, str(weight_path))

    return {"weights": str(weight_path), "bc_samples": int(obs_arr.shape[0])}
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: add BC warm-start stage to hybrid pipeline"
```

---

### Task 5: Implement PPO finetune stage with BC state loading and policy save

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add test:

```python
    def test_run_ppo_finetune_saves_policy_with_bc_init(self):
        import tempfile
        m = _load_module()
        fake_model = MagicMock()
        env_bundle = {"env": object()}
        bc_artifact = {"weights": "dummy-bc.pt"}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(m, "_torch_load", return_value={"k": 1.0}), \
                 patch.object(m, "train_ppo", return_value=fake_model) as mock_train:
                out = m.run_ppo_finetune({"output_dir": tmpdir, "total_timesteps": 64, "ppo_seed": 9}, env_bundle, bc_artifact)

        mock_train.assert_called_once()
        fake_model.save.assert_called_once()
        self.assertTrue(out["policy_path"].endswith("sell_policy.zip"))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_ppo_finetune_saves_policy_with_bc_init -v`

Expected: FAIL (placeholder path return).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`:

```python
def _torch_load(path):
    import torch
    return torch.load(path, map_location="cpu")


def run_ppo_finetune(config, env_bundle, bc_artifact):
    env = env_bundle.get("env")
    if env is None:
        raise ValueError("env bundle missing env")

    bc_path = bc_artifact.get("weights")
    bc_state = _torch_load(bc_path) if bc_path else None

    model = train_ppo(
        env,
        total_timesteps=int(config.get("total_timesteps", 20000)),
        seed=int(config.get("ppo_seed", 42)),
        policy_kwargs={"net_arch": list(config.get("ppo_policy_net_arch", [128, 128]))},
        bc_state_dict=bc_state,
    )

    output_dir = Path(config.get("output_dir", "data/models"))
    output_dir.mkdir(parents=True, exist_ok=True)
    policy_path = output_dir / "sell_policy.zip"
    model.save(str(policy_path))

    return {"policy_path": str(policy_path), "total_timesteps": int(config.get("total_timesteps", 20000))}
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: add PPO finetune stage with BC initialization"
```

---

### Task 6: Replace placeholder evaluation + finalize real orchestrator result

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

**Step 1: Write the failing test**

Add test:

```python
    def test_run_hybrid_training_returns_non_placeholder_evaluation(self):
        m = _load_module()
        with patch.object(m, "train_buy_model", return_value={"model_path": "buy_model.cbm", "threshold": 0.45, "labels": [0, 1, 1], "samples": [{}]}), \
             patch.object(m, "build_sell_env", return_value={"env": object(), "episodes": [[{}]], "episode_count": 1}), \
             patch.object(m, "run_bc_warmstart", return_value={"weights": "bc.pt", "bc_samples": 10}), \
             patch.object(m, "run_ppo_finetune", return_value={"policy_path": "sell_policy.zip", "total_timesteps": 128}):
            result = m.run_hybrid_training({"output_dir": "data/models"})

        self.assertIn("pipeline_status", result["evaluation"])
        self.assertEqual(result["evaluation"]["pipeline_status"], "ok")
        self.assertIn("buy_positive_rate", result["evaluation"])
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_train_hybrid_pipeline.TestTrainHybridPipeline.test_run_hybrid_training_returns_non_placeholder_evaluation -v`

Expected: FAIL (`evaluation` still placeholder or missing keys).

**Step 3: Write minimal implementation**

In `src/pipeline/train_hybrid.py`:

```python
def run_ab_evaluation(config, buy_artifact, ppo_artifact, env_bundle, bc_artifact):
    labels = np.asarray(buy_artifact.get("labels", []), dtype=float)
    positive_rate = float(labels.mean()) if labels.size > 0 else 0.0
    return {
        "buy_positive_rate": positive_rate,
        "buy_threshold": float(buy_artifact.get("threshold", 1.0)),
        "sell_episode_count": int(env_bundle.get("episode_count", 0)),
        "bc_samples": int(bc_artifact.get("bc_samples", 0)),
        "ppo_total_timesteps": int(ppo_artifact.get("total_timesteps", 0)),
        "pipeline_status": "ok",
    }


def run_hybrid_training(config):
    buy_artifact = train_buy_model(config)
    env_bundle = build_sell_env(config, buy_artifact)
    bc_artifact = run_bc_warmstart(config, env_bundle)
    ppo_artifact = run_ppo_finetune(config, env_bundle, bc_artifact)
    evaluation = run_ab_evaluation(config, buy_artifact, ppo_artifact, env_bundle, bc_artifact)

    result = {
        "artifacts": {
            "buy_model": {
                "model_path": buy_artifact.get("model_path"),
                "threshold": buy_artifact.get("threshold"),
                "threshold_path": buy_artifact.get("threshold_path"),
            },
            "sell_policy": ppo_artifact,
            "bc_warmstart": bc_artifact,
        },
        "evaluation": evaluation,
    }

    manifest_path = Path(config.get("output_dir", "data/models")) / "hybrid_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
```

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "feat: finalize real hybrid orchestration and evaluation summary"
```

---

### Task 7: Extend CLI config passthrough for real-training keys

**Files:**
- Modify: `scripts/run_hybrid_training.py`
- Modify: `tests/model/test_run_hybrid_training_cli.py`

**Step 1: Write the failing tests**

Add to `tests/model/test_run_hybrid_training_cli.py`:

```python
    def test_parse_args_includes_dataset_and_target_controls(self):
        cli = _load_cli()
        args = cli.parse_args([])
        self.assertEqual(args.lifecycle_dir, "data/training")
        self.assertEqual(args.sample_mode, "trade_event")
        self.assertEqual(args.target_threshold_value, 80.0)

    def test_main_passes_extended_config(self):
        cli = _load_cli()
        with patch.object(cli, "run_hybrid_training", return_value={"artifacts": {}, "evaluation": {}}) as mock_run:
            cli.main(["--output-dir", "tmp/models", "--total-timesteps", "32", "--lifecycle-dir", "tmp/lifecycle"])
        cfg = mock_run.call_args.args[0]
        self.assertEqual(cfg["lifecycle_dir"], "tmp/lifecycle")
        self.assertEqual(cfg["total_timesteps"], 32)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_run_hybrid_training_cli.TestRunHybridTrainingCli.test_parse_args_includes_dataset_and_target_controls tests.model.test_run_hybrid_training_cli.TestRunHybridTrainingCli.test_main_passes_extended_config -v`

Expected: FAIL (args/config keys missing).

**Step 3: Write minimal implementation**

In `scripts/run_hybrid_training.py`, add args:

```python
parser.add_argument("--lifecycle-dir", default="data/training")
parser.add_argument("--sample-mode", default="trade_event")
parser.add_argument("--max-sample-age-seconds", type=int, default=180)
parser.add_argument("--target-label-column", default="max_return_pct")
parser.add_argument("--target-threshold-value", type=float, default=80.0)
parser.add_argument("--buy-min-precision", type=float, default=0.10)
```

and include these keys in `config` passed to `run_hybrid_training`.

**Step 4: Run test to verify it passes**

Run: same command as step 2.

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/run_hybrid_training.py tests/model/test_run_hybrid_training_cli.py
git commit -m "feat: extend hybrid CLI config passthrough for real training"
```

---

### Task 8: Final verification sweep

**Files:**
- Modify: none (verification task)

**Step 1: Run full hybrid verification suite**

Run:

```bash
python3 -m unittest tests.model.test_train_hybrid_pipeline -v && \
python3 -m unittest tests.model.test_train_ppo -v && \
python3 -m unittest tests.model.test_run_hybrid_training_cli -v
```

Expected: PASS.

**Step 2: Run CLI smoke test**

Run:

```bash
python3 scripts/run_hybrid_training.py --output-dir data/models --total-timesteps 512
```

Expected: exit 0 and JSON output containing `artifacts` + `evaluation` with non-placeholder keys.

**Step 3: Commit verification note (optional if no file changes)**

If no code changes from verification, skip commit.

If tiny fixes required, commit with:

```bash
git add <fixed-files>
git commit -m "fix: address verification findings in hybrid real-training pipeline"
```
