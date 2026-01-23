# FourMeme 数据收集和训练系统

23万+样本,56个特征的Meme币交易训练集

## 快速开始

### 1. Linux部署 (推荐)
```bash
chmod +x setup_linux.sh && ./setup_linux.sh
./tools/collector.sh start    # 启动收集
tail -f data/logs/*.log        # 查看日志
```

### 2. 构建训练集
```bash
# 从历史数据生成
python tools/process_history.py

# 构建训练集
python tools/collect_data.py build

# 查看摘要
python tools/dataset_summary.py
```

## 数据集信息

**规模**: 235,117个样本 (训练80% / 验证10% / 测试10%)
**特征**: 56个 (价格、成交量、地址分析、早期活动等)
**标签**: 7个 (收益率、分类、风险)
**文件**: `data/datasets/train_*.jsonl` (~300MB)

### 核心特征 (56个)
- 基础(6): 供应量、流动性等
- 交易(11): 买卖次数、成交量、时间窗口
- 价格(6): 当前价、动量等
- 持币地址(4): 集中度、最大持币者
- 创建者(5): 买卖行为、持币占比
- 大户(2): 数量、占比
- 早期活动(5): 前30秒活跃度
- 突发检测(3): 是否突发、强度
- 交易规律(4): 规律性、波动率
- 其他(10): 买压、频率等

### 标签分布
- 盈利: 12.5%
- 最高收益: 1358%
- 平均收益: 6.86%

## 工具

| 工具 | 用途 |
|------|------|
| `collector.sh` | Linux守护进程 |
| `process_history.py` | 处理历史数据 |
| `collect_data.py build` | 构建训练集 |
| `dataset_summary.py` | 数据摘要 |
| `analyze_dataset.py` | 详细分析 |

## 详细文档

完整特征说明和使用指南: [TRAINING_DATASET_FINAL.md](TRAINING_DATASET_FINAL.md)

## 下一步

1. 训练模型 (XGBoost/LightGBM/神经网络)
2. 集成到回测系统
3. 部署到实时交易
