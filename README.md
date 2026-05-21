# FourMeme Hybrid Trading System

FourMeme/BSC token lifecycle collector, dataset builder, hybrid model trainer, and bot runtime.

主链路是 **collector -> dataset -> hybrid training -> bot**：

1. 收集 FourMeme token lifecycle 数据。
2. 构建训练样本与特征。
3. 训练 Hybrid 模型（CatBoost 买入 + BC/PPO 卖出）。
4. 运行 bot 进行 paper 或实盘流程。

## Safety First

This repository can submit real on-chain transactions when trading is enabled. Keep `ENABLE_TRADING=false` unless you are intentionally validating live trading with reviewed configuration and a funded wallet you are prepared to risk.

Never commit `.env`, private keys, wallet files, paid RPC credentials, or unreviewed live state.

## Requirements

- Python 3.11+
- A BSC websocket endpoint for listener head tracking
- One or more BSC HTTP endpoints for log polling
- A dedicated BSC HTTP RPC endpoint for trade submission

Install dependencies in a local virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Copy the environment template and fill in local values:

```bash
cp .env.example .env
```

Prefer the role-specific RPC variables from `.env.example`:

- `BSC_WSS_URL` for websocket listener connectivity
- `BSC_LOG_HTTP_ENDPOINTS` for listener `get_logs` polling
- `BSC_TRADE_HTTP_RPC` for transaction submission

`BSC_HTTP_RPC` exists only as legacy fallback compatibility. Trading remains disabled by default through `ENABLE_TRADING=false`.

## Workflow

### 1. Collect lifecycle data

```bash
python tools/collect_continuous.py
```

用途：持续监听 FourMeme 事件，并将 token lifecycle 数据写入训练数据目录。

### 2. Build datasets

```bash
python scripts/build_dataset_new.py --lifecycle-dir data/training --output-dir data/datasets
```

用途：从 lifecycle JSONL 文件构建训练样本。

### 3. Train the hybrid model

```bash
python scripts/run_hybrid_training.py --output-dir data/models --lifecycle-dir data/training
```

用途：训练买入模型与卖出策略，并把产物写入模型目录。

### 4. Run the bot

```bash
python -m src.trader.bot
```

用途：加载配置与模型，在实时事件流上执行 bot 流程。

## Tests

The repo uses `unittest`.

```bash
python -m unittest discover
python -m unittest tests.core.test_rpc_config
python -m unittest tests.model.test_run_hybrid_training_cli
python -m unittest tests.smoke.test_surviving_workflow_imports
```

GitHub Actions runs the full `python -m unittest discover` command on pushes to `main` and on pull requests.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `config/` | Env contract, RPC role separation, trading knobs, ABI loading |
| `tools/` | Collector entrypoint and local service wrapper |
| `scripts/` | Dataset, replay, probe, and training CLIs |
| `src/core/` | Listener, websocket, event, and trade transport code |
| `src/data/` | Lifecycle collection, dataset building, feature extraction |
| `src/model/` | Buy model and hybrid inference helpers |
| `src/pipeline/` | Hybrid training pipeline |
| `src/rl/` | Sell-side RL environment, rewards, BC warmstart, PPO training |
| `src/trader/` | Bot runtime and position behavior |
| `tests/` | `unittest` contract, model, workflow, and smoke coverage |
| `data/models/` | Curated model artifacts and selected reports |
| `data/replay_reports/` | Reviewable replay/probe evidence |
| `systemd/` | Linux service unit examples |

Before editing a subtree, read the nearest `AGENTS.md`. Root `AGENTS.md` contains repo-wide workflow rules; child files own local conventions.

## Artifact Policy

Most generated data stays local by default. The `.gitignore` intentionally hides large runtime and training outputs while keeping curated model reports and replay reports visible for review.

- Raw lifecycle data and datasets are local working artifacts.
- New model binaries are ignored unless intentionally force-added.
- Lightweight JSON/JSONL reports under `data/models/`, `data/replay_reports/`, and `data/reports/` remain visible so experiment evidence can be reviewed.
- Logs, pid files, local cache directories, virtualenvs, and secret files must remain untracked.

## Local Service Wrapper

`tools/memectl` is the supported Linux/macOS wrapper for long-running local services:

```bash
./tools/memectl collector start
./tools/memectl collector status
./tools/memectl collector logs -f

./tools/memectl bot start
./tools/memectl bot status
./tools/memectl bot logs -f
```

On Windows, prefer direct Python entrypoints unless you are specifically changing wrapper behavior.

## License

MIT. See `LICENSE`.

## Notes

- This is a plain Python application repo, not a packaged library.
- `src` is the import root; several entry scripts prepend the repo root to `sys.path`.
- Runtime config should flow through `.env.example`, `config/config.py`, and `config/trading_config.py`.
- Prefer paper validation before enabling any real trading path.
