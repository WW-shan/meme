# Meme Coin Hybrid Strategy Design (CatBoost Buy + PPO Sell)

Date: 2026-03-04
Status: Approved

## 1. Context

当前策略以 `XGBoost/LightGBM` 为主，主要依赖价格窗口与基础指标。目标标的具有以下特征：

- 标的生命周期极短（通常 < 5 分钟）
- 持仓人数低（约 50 人）
- 流动性脆弱，卖出会显著影响价格
- 样本规模有限（< 100k）

在该场景下，简单监督学习往往在离线评估看起来可行，但实盘容易被滑点与冲击成本吞噬收益。核心瓶颈不只在“买对”，也在“如何退出”。

## 2. Goals / Non-Goals

### Goals

1. 将特征工程从“价格窗口主导”升级为“行为微结构主导”。
2. 买入端改用 `CatBoost` 做极短线胜率分类（成本后标签）。
3. 卖出端引入 `PPO`，学习低流动性场景下的动态减仓/清仓策略。
4. 在回测中引入滑点与冲击成本（Impact Cost），避免纸面收益偏差。
5. 以“收益稳健性优先”作为首要优化目标（回撤约束优先于收益峰值）。

### Non-Goals

1. 本阶段不改为单一端到端 RL（买卖一体）方案。
2. 本阶段不引入复杂在线学习或实时模型热更新。
3. 本阶段不使用高复杂度序列网络（先保证样本效率和稳定性）。

## 3. Key Constraints (Confirmed)

- 业务目标：收益稳健优先
- Environment step：逐成交事件（event-driven）
- Episode 终止：动态终止（流动性枯竭/成交停滞等）
- 推理延迟预算：<= 500ms
- 训练数据规模：< 100k（样本效率与防过拟合优先）

## 4. Approaches Considered

### A. 两阶段解耦混合架构（Chosen）

- 买入：监督学习（CatBoost）
- 卖出：强化学习（PPO）
- 两者通过统一交易上下文衔接

**优点**：与现有代码兼容性高、可分模块评估与替换、工程风险可控。
**缺点**：非端到端全局最优。

### B. 单一 RL（买卖一体）

**优点**：理论上可学到全局耦合最优策略。
**缺点**：样本效率差、训练不稳定，对 <100k 样本不友好。

### C. 规则卖出 + RL 残差

**优点**：风险最低、上线快。
**缺点**：上限受规则天花板限制。

**最终选择**：A（在当前约束下收益/风险/落地性最佳）。

## 5. High-Level Architecture

### 5.1 Component Layout

- `src/features/behavior_features.py`
  - 行为特征计算（筹码、散户、流动性、订单流）
- `src/model/buy_catboost.py`
  - 买入分类模型训练与推理
- `src/rl/trading_env.py`
  - 低流动性卖出决策环境（Gymnasium）
- `src/rl/reward.py`
  - Differential Sharpe + Drawdown + Impact 组合奖励
- `src/rl/warmstart_bc.py`
  - 规则策略行为克隆预热
- `src/rl/train_ppo.py`
  - PPO 微调训练
- `src/backtest/impact_model.py`
  - 滑点/冲击成本/部分成交模型
- `src/pipeline/train_hybrid.py`
  - 一体化训练流水线入口

### 5.2 Data Flow

`raw lifecycle events -> behavior feature extraction -> CatBoost training/inference -> entry episodes -> TradingEnv -> BC warm start -> PPO fine-tune -> A/B evaluation report`

## 6. Feature Engineering Redesign

### 6.1 Feature Validity Criteria

对每个特征列按以下规则标记：`有效 / 弱有效 / 无效`：

1. **可观测性**：入场时刻是否可得（无未来泄漏）
2. **短窗敏感性**：前 30~90 秒内是否有响应
3. **微结构相关性**：是否反映人群行为与流动性承压
4. **跨标的一致性**：是否能跨 token 稳定泛化

### 6.2 Core Behavior Features

1. **筹码分布动力学**
   - `top10_holder_share_t`
   - `concentration_decay = d(top10_share)/dt`

2. **散户入场速率质量**
   - `retail_entry_rate_ratio = slope(unique_addresses_30s) / slope(volume_30s)`
   - 防止“大户互倒”伪热度

3. **池子健康度 / 抗压能力**
   - `lp_resistance_ratio = lp_depth / instantaneous_sell_pressure`
   - 流动性衰减速度（liquidity drain rate）

4. **订单流与节奏特征**
   - 主动买卖比、成交 burstiness、事件间隔波动

5. **类别特征（CatBoost）**
   - `creator_id`, `token_name_pattern`, `launch_source`, `pair_type`

### 6.3 Typical Weak/Invalid Features in <5m Lifecycle

- 长窗口慢指标（对秒级冲击反应迟钝）
- 粗粒度时段因子（小时/日级）
- 过度平滑统计（丢失瞬时流动性变化）

## 7. Buy-Side Model (CatBoost)

### 7.1 Prediction Target

将买入目标定义为：

- `is_profitable_after_cost@N_seconds`
- 以手续费+滑点+冲击后净收益生成标签

### 7.2 Imbalance Handling

CatBoost 不直接提供 Focal Loss，本方案使用：

1. `class_weights`
2. focal-like sample reweighting（难例增强）
3. 以稳健目标进行阈值校准（非单看 AUC）

### 7.3 Thresholding Policy

优先选择满足风险约束下的阈值：

- `MaxDD` 受控前提下最大化 `Sortino`
- 辅助关注 `precision@top-k`

## 8. Sell-Side RL (Gymnasium TradingEnv)

### 8.1 Action Space

`Discrete(4)`:

- `0`: Hold
- `1`: Sell 25% (remaining position)
- `2`: Sell 50% (remaining position)
- `3`: Sell 100%

### 8.2 Observation (Fixed-Length Numeric Vector)

包含以下子集：

- 持仓与收益：`position_remaining`, `unrealized_pnl`, `realized_pnl`
- 时间：`time_since_entry`, `time_to_300s`, `event_gap`
- 人群行为：`holder_delta`, `top10_share`, `concentration_decay`
- 流动性压力：`lp_depth`, `sell_pressure`, `lp_resistance_ratio`
- 订单流：`order_flow_imbalance`, `buy_sell_ratio`
- 执行预估：`est_slippage_sell25/50/100`

为利用 <=500ms 延迟预算，可采用“当前状态 + 最近 K 步堆叠（例如 K=8）”。

### 8.3 Execution and Impact Model

卖出执行价格：

`exec_price = mid_price * (1 - fee - slippage - impact)`

其中 impact 拆分为：

- temporary impact（当前成交恶化）
- permanent impact（后续价格路径下移）

对极低深度场景启用 `partial_fill`，防止虚假成交假设。

### 8.4 Reward Function

`reward_t = dsr_t - λ_dd * dd_increase_t - λ_impact * impact_cost_t`

- `dsr_t`: Differential Sharpe 增量项
- `dd_increase_t`: 回撤扩大惩罚
- `impact_cost_t`: 冲击成本惩罚

### 8.5 Dynamic Termination

满足任一条件结束：

1. 仓位清空
2. 达到 300 秒
3. 流动性低于阈值 + 成交停滞持续
4. 可交易性丧失（极端枯竭）

## 9. Training Pipeline (Small-Data Optimized)

### Stage 1: CatBoost Training

- 时间滚动切分（walk-forward）
- 按 token 生命周期隔离，防泄漏

### Stage 2: Episode Construction

- 基于买入信号构建入场后事件轨迹
- 轨迹内绑定成本参数与终止原因

### Stage 3: Behavior Cloning Warm Start

- 用规则策略动作做监督预训练（降低探索成本）

### Stage 4: PPO Fine-Tuning

- 在 TradingEnv 上做策略提升
- 早停指标以 OOS 稳健性为准（非训练 reward）

### Stage 5: Evaluation and Selection

- 与 baseline 在相同成本假设下对比
- 输出分 fold 与汇总报告

## 10. Backtest & A/B Protocol

### 10.1 Comparison Arms

- Baseline：XGBoost/LightGBM + 旧卖出逻辑
- Candidate：CatBoost + PPO + impact-aware env

### 10.2 Ablation

- A: Baseline
- B: A + 行为特征
- C: CatBoost + 行为特征 + 旧卖出
- D: C + PPO 卖出（完整方案）

### 10.3 Success Criteria (Robustness First)

建议上线门槛：

1. OOS 汇总 `MaxDD` 下降 >= 20%
2. OOS 汇总 `Sortino` 提升 >= 15%
3. OOS `Net Return` >= baseline 的 95%
4. 尾部风险（P1/P5）改善
5. bootstrap 95% CI 下改进方向稳定

## 11. Testing Strategy

1. 单元测试
   - 行为特征计算正确性
   - impact/slippage/partial_fill 合理性
   - reward 计算与 done 逻辑

2. 集成测试
   - 小样本端到端跑通（CatBoost -> BC -> PPO -> eval）

3. 回归测试
   - 相同成本假设下，baseline 指标可复现

4. 预上线灰度
   - paper/shadow 运行，监控滑点偏差和成交可实现率

## 12. Risks and Mitigations

1. **分布漂移快**：使用滚动重训与时间切分评估。
2. **环境过乐观**：impact 模型做保守参数并校准至实盘统计。
3. **奖励错配**：以风险指标驱动 early-stop 与模型选择。
4. **样本不足**：采用 BC warm start 与轻量策略网络。

## 13. Deliverables

- 设计文档（本文件）
- 实现计划文档（下一步）
- 代码产物（后续实现阶段）：
  - `buy_model.cbm`
  - `sell_policy.pt`
  - `feature_schema.json`
  - `cost_model.yaml`
  - `eval_report.json`
