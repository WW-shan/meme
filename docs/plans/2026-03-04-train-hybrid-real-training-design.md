# Train Hybrid Real-Training Wiring Design

Date: 2026-03-04
Status: Approved

## 1. Context

Current hybrid orchestration (`src/pipeline/train_hybrid.py`) is still a scaffold that returns placeholder artifacts and zeroed evaluation fields. Core building blocks already exist in the codebase:

- dataset/sample generation: `src/data/dataset_builder.py`
- buy model wrapper: `src/model/buy_catboost.py`
- execution model + RL env + BC/PPO wrappers:
  - `src/backtest/impact_model.py`
  - `src/rl/trading_env.py`
  - `src/rl/warmstart_bc.py`
  - `src/rl/train_ppo.py`

Goal is to wire these components into a real end-to-end training pipeline while preserving the current CLI contract.

## 2. Goal and Scope

### Goal

Turn `run_hybrid_training(config)` into a real training entrypoint that performs:

1. data build/load
2. buy-side CatBoost training + thresholding
3. sell episode construction
4. BC warm start
5. PPO finetuning
6. evaluation aggregation
7. artifact persistence

### Out of Scope

- full architecture rewrite of legacy `MemeModelTrainer`
- online serving changes
- production-grade distributed RL training

## 3. Chosen Approach

Chosen approach: **staged real-training orchestration** inside `src/pipeline/train_hybrid.py`.

Reasons:

- matches existing staged function boundaries (`train_buy_model`, `build_sell_env`, `run_bc_warmstart`, `run_ppo_finetune`, `run_ab_evaluation`)
- minimizes risk by reusing existing tested modules
- supports clear failure isolation by stage

## 4. Architecture

`run_hybrid_training(config)` will become the single orchestrator and call concrete stage functions in sequence:

1. `train_buy_model(config)`
2. `build_sell_env(config, buy_artifact)`
3. `run_bc_warmstart(config, env_bundle)`
4. `run_ppo_finetune(config, env_bundle, bc_artifact)`
5. `run_ab_evaluation(config, buy_artifact, ppo_artifact, stage_stats)`

Each stage returns structured outputs used by downstream stages and final manifest.

## 5. Config Contract

Minimal config keys for real run:

```python
{
  "lifecycle_dir": "data/training",
  "sample_mode": "trade_event",
  "max_sample_age_seconds": 180,
  "future_windows": [240],
  "output_dir": "data/models",
  "run_id": "optional",
  "target_label_column": "max_return_pct",
  "target_threshold_value": 80.0,
  "cat_feature_names": ["creator_id"],
  "buy_min_precision": 0.10,
  "bc_hidden_dim": 64,
  "bc_epochs": 20,
  "bc_lr": 1e-3,
  "total_timesteps": 20000,
  "ppo_seed": 42,
  "ppo_policy_net_arch": [128, 128],
  "save_intermediate": True,
}
```

CLI keeps existing arguments (`--output-dir`, `--total-timesteps`) and provides defaults for the rest in pipeline code.

## 6. Data Flow

1. Build samples with `DatasetBuilder` from lifecycle files.
2. Flatten samples into buy training frame:
   - `X`: `sample["features"]`
   - `y_buy`: binarized from `sample["label"][target_label_column] >= target_threshold_value`
   - keep meta keys (`token_address`, `sample_time`) for episode mapping.
3. Train `BuyCatBoostModel` and compute threshold with `select_threshold`.
4. Construct sell episodes with event dictionaries compatible with `TradingEnv` observations:
   - `mid_price`, `lp_depth`, `sell_pressure`, `buy_sell_ratio`, `holders`.
5. Build BC tensors (`obs`, `action`) from episodes and train `train_bc`.
6. Train PPO with `train_ppo(..., bc_state_dict=...)`.
7. Persist artifacts and generate evaluation payload.

## 7. Failure Handling

Fail fast with explicit stage names:

- empty dataset / invalid labels (all-0 or all-1)
- CatBoost fit failure
- missing BC data
- PPO training or save failure

Errors should include `stage`, `output_dir`, and key counters for debug.

## 8. Evaluation Output

`evaluation` must be non-placeholder and include at least:

- `buy_positive_rate`
- `buy_threshold`
- `sell_episode_count`
- `bc_samples`
- `ppo_total_timesteps`
- `pipeline_status`

## 9. Artifact Contract

Under `output_dir`:

- `buy_model.cbm`
- `buy_threshold.json`
- `bc.pt`
- `sell_policy.zip`
- optional: `hybrid_manifest.json`

Returned result format remains:

```json
{
  "artifacts": {
    "buy_model": {...},
    "sell_policy": {...},
    "bc_warmstart": {...}
  },
  "evaluation": {...}
}
```

## 10. Test Strategy

Mandatory tests:

1. `tests/model/test_train_hybrid_pipeline.py`
   - happy path returns real-looking artifacts + evaluation keys
   - empty sample path raises `ValueError`
   - single-class buy target raises `ValueError`
2. `tests/model/test_train_ppo.py`
   - preserves learn call
   - verifies optional BC state load path
3. `tests/model/test_run_hybrid_training_cli.py`
   - parse defaults
   - main dispatch
   - subprocess direct-run smoke

## 11. Definition of Done

Done when:

1. `src/pipeline/train_hybrid.py` performs real staged training, no placeholder artifact stubs.
2. CLI run succeeds and outputs non-placeholder evaluation.
3. Required artifacts are created under `output_dir`.
4. pipeline/ppo/cli tests pass.
5. failure modes are explicit and deterministic.