# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Environment setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in RPC settings before running collector or bot flows.

### Main workflows
```bash
python tools/collect_continuous.py
python scripts/build_dataset_new.py --lifecycle-dir data/training --output-dir data/datasets
python scripts/run_hybrid_training.py --output-dir data/models --lifecycle-dir data/training
python -m src.trader.bot
```

### Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest tests.core.test_rpc_config
python -m unittest tests.model.test_run_hybrid_training_cli
```

### Linux/macOS process wrapper
`tools/memectl` is the repo-supported wrapper for long-running services, but it depends on the shell helpers in `tools/lib` and enforces Linux/Darwin.

```bash
./tools/memectl collector start
./tools/memectl collector status
./tools/memectl collector logs -f

./tools/memectl bot start
./tools/memectl bot status
./tools/memectl bot logs -f
```

## Architecture

The current repo is organized around a single main workflow:

1. collect token lifecycle data from FourMeme/BSC
2. build datasets and features from lifecycle JSONL files
3. train a hybrid model
   - buy side: CatBoost classifier
   - sell side: BC warmstart + PPO policy
4. run the bot on live events for paper or real trading

The most important entrypoints are:
- `tools/collect_continuous.py` — realtime lifecycle collection
- `scripts/build_dataset_new.py` — dataset build CLI
- `scripts/run_hybrid_training.py` — hybrid training CLI
- `src/trader/bot.py` — bot runtime entrypoint

## Subsystem map

### Config
- `config/config.py` handles RPC-role separation, listener mode, contract config, and provider validation.
- `config/trading_config.py` holds trading toggles and risk parameters.

### Listener and connectivity
- `src/core/ws_manager.py` manages websocket connectivity.
- `src/core/listener.py` is the main FourMeme event listener. It uses websocket head tracking plus HTTP `get_logs` polling/fallback for robustness.

### Data collection
- `tools/collect_continuous.py` orchestrates listener + queue workers + periodic save/flush.
- `src/data/collector.py` maintains in-memory lifecycle state, incremental flushes, and final snapshots.

### Dataset and features
- `src/data/dataset_builder.py` loads lifecycle files and produces training samples.
- `src/data/feature_extractor.py` contains feature extraction logic used by dataset building and bot inference.

### Training and inference
- `src/pipeline/train_hybrid.py` orchestrates buy-model training, BC warmstart, PPO finetuning, and manifest output.
- `src/model/buy_catboost.py` contains the buy classifier.
- `src/model/hybrid_inference.py` loads `buy_model.cbm`, `buy_threshold.json`, and optional `sell_policy.zip`.
- `src/rl/*` contains the sell-side RL environment, reward, PPO training, and BC warmstart.

### Bot and execution
- `src/trader/bot.py` wires listener, collector, model loading, inference, and position management together.
- `src/core/trader.py` is the transaction executor. It uses dedicated HTTP RPC for trade submission rather than the websocket listener connection.

## Data and model artifacts

Expected repo-local artifacts:
- lifecycle data: `data/training/lifecycle_*.jsonl` and `data/training/lifecycle_incremental_*.jsonl`
- datasets: `data/datasets/*.jsonl`
- trained models: `data/models/`
  - `buy_model.cbm`
  - `buy_threshold.json`
  - `bc.pt`
  - `sell_policy.zip`
  - `hybrid_manifest.json`

The bot can run without model artifacts, but it falls back to data collection behavior if no trained hybrid model is found.

## Repo-specific guidance

### RPC roles are intentionally separated
Prefer the role-specific env vars from `.env.example`:
- `BSC_WSS_URL` for websocket listener connectivity
- `BSC_LOG_HTTP_ENDPOINTS` for listener `get_logs` polling pool
- `BSC_TRADE_HTTP_RPC` for sending transactions

`BSC_HTTP_RPC` is treated as legacy fallback compatibility, not the preferred path.

### Treat trading as opt-in
This repository can send real on-chain transactions when trading is enabled. Keep `ENABLE_TRADING=false` unless the user explicitly asks for real trading changes or validation. Treat `PRIVATE_KEY` and RPC credentials as sensitive runtime configuration.

### Test style
Tests are primarily `unittest`-driven even though filenames follow pytest-style naming. Prefer `python -m unittest ...` commands when validating targeted changes.

### Platform-specific ops
- `tools/memectl` is intended for Linux/macOS shells.
- `systemd/README.md` documents service installation for the collector.
- When working on Windows, prefer direct Python entrypoints over `memectl` unless the user specifically wants service-wrapper changes.

### Less-central files
The current core workflow is the collector/dataset/hybrid-bot path described above. Files such as `src/core/processor.py` and `four_meme_buyer.py` appear less central than the main path and should be treated cautiously before modifying or relying on them.
