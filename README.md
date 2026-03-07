# FourMeme Hybrid Trading System

一个围绕 **collector → dataset → hybrid training → bot** 的精简工作流仓库。

## Workflow

1. 收集 FourMeme 生命周期数据
2. 训练 Hybrid 模型（CatBoost 买入 + PPO 卖出）
3. 运行 bot 进行实盘或 paper 流程

## Requirements

- Python 3.8+
- `pip install -r requirements.txt`
- 可用的 BSC RPC / WebSocket 节点
- 按需配置 `.env`、`config/config.py`、`config/trading_config.py`

## Main Entrypoints

### 1. Collect lifecycle data

```bash
python tools/collect_continuous.py
```

用途：持续监听 FourMeme 事件，并将 token lifecycle 数据写入训练数据目录。

### 2. Train the hybrid model

```bash
python scripts/run_hybrid_training.py
```

用途：从 lifecycle 数据构建样本，训练买入模型与卖出策略，并把产物写入模型目录。

### 3. Run the bot

```bash
python -m src.trader.bot
```

用途：加载配置与模型，在实时事件流上执行 bot 流程。

## Key Paths

- `tools/collect_continuous.py` — 数据收集入口
- `scripts/run_hybrid_training.py` — 训练入口
- `src/trader/bot.py` — bot 运行入口
- `src/data/collector.py` — 生命周期收集与样本写出
- `src/data/dataset_builder.py` — 数据集构建
- `src/pipeline/train_hybrid.py` — hybrid 训练管线
- `config/config.py` / `config/trading_config.py` — 运行配置

## Notes

- 仓库当前只保留这条主链路相关内容。
- 运行前请先确认模型输出目录、数据目录、RPC 配置和交易配置可用。
- 本项目涉及真实交易风险，请先使用小资金或 paper 环境验证。
