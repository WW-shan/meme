# Joint Exit Optimization Design (Moon Branch)

Date: 2026-02-27
Status: Approved

## 1. Context

当前训练/回测流程中，moon 分支卖出逻辑是固定参数：
- 第一止盈位固定为 `200%`
- 首次卖出比例固定为 `60%`
- 剩余仓位回撤止损固定为 `25%`

这在高控盘币场景下可能不稳定：部分标的在 80%~150% 区间更容易兑现，固定 200% 可能错过更稳健收益。

用户目标是：
- 保留原有策略框架（不推翻）
- 将固定 200% 止盈改为可比较方案
- 并进一步进行**联合优化**，回测筛选“更合适”的组合

## 2. Goals / Non-Goals

### Goals
1. 在训练回测选优阶段，联合优化以下维度：
   - 入场参数：`prob_threshold` / `reg_min_return` / `max_age_seconds`
   - 卖出参数（moon 分支）：`first_take_profit` / `first_exit_ratio` / `drawdown_stop`
2. 支持候选止盈位：`80% / 100% / 150% / 200%`
3. 保持现有 gate 与评分框架兼容，输出可追踪的最优参数与指标。

### Non-Goals
1. 不改非 moon 分支的收益计算规则。
2. 不改“每 token 最多买一次”的入场事件规则。
3. 不引入新服务/新数据库，仅在当前训练与回测流水线上扩展。

## 3. Current Baseline

当前关键逻辑位置：
- 训练入口参数：`scripts/run_full_training.py`
- 回测门控主流程：`src/model/trainer.py`
- moon 分支固定 200% 逻辑：
  - `src/model/trainer.py`
  - `src/backtest/simple_backtest.py`
  - `src/backtest/profit_first_calibrator.py`

现状问题：
- 卖出参数硬编码，无法在同一训练批次中横向对比。
- 入场参数可自动调优，卖出参数不可调优，导致“优化不完整”。

## 4. Chosen Approach (C: Joint Optimization)

采用“分层联合优化”而不是全量一次性笛卡尔搜索：

1. 阶段 A（入场筛选）
   - 先按现有入场网格（prob/reg/age）评估
   - 选出 Top-N 入场组合（默认 N=10，可配置）

2. 阶段 B（卖出联合搜索）
   - 仅对 Top-N 入场组合继续搜索卖出参数：
     - `first_take_profit_candidates = [0.8, 1.0, 1.5, 2.0]`
     - `first_exit_ratio_candidates = [0.5, 0.6, 0.7]`
     - `drawdown_stop_candidates = [0.20, 0.25, 0.30]`

3. 统一评分与约束
   - 保留现有 selection/validation/full 的优先级策略
   - 保留回撤与收益 gate 约束
   - 最终输出“完整最优组合（入场+卖出）”

该方案在维持现有流程稳定性的同时，显著减少计算爆炸风险。

## 5. Detailed Design

### 5.1 Config Extension

在 `DEFAULT_GATE_THRESHOLDS["backtest"]` 中新增：

- 默认值（非 auto-tune/兜底使用）：
  - `first_take_profit: 2.0`
  - `first_exit_ratio: 0.6`
  - `drawdown_stop: 0.25`

- 候选网格：
  - `first_take_profit_candidates: [0.8, 1.0, 1.5, 2.0]`
  - `first_exit_ratio_candidates: [0.5, 0.6, 0.7]`
  - `drawdown_stop_candidates: [0.20, 0.25, 0.30]`

- 分层联合搜索控制项：
  - `joint_optimize_top_entry_n: 10`

### 5.2 Moon Exit Logic Parameterization

将 moon 分支硬编码参数替换为可注入参数：
- `first_take_profit`（首次止盈点）
- `first_exit_ratio`（首次卖出比例）
- `drawdown_stop`（剩余仓位回撤止损比例）

计算逻辑保持原框架：
1. 到达 `first_take_profit` 时卖出 `first_exit_ratio`
2. 剩余仓位从峰值按 `drawdown_stop` 回撤止损
3. 对两段收益进行加权

### 5.3 Backtest Joint Search Flow

在 `_select_backtest_thresholds` 扩展为联合策略选择器：

1. 继续预计算 `probs/pred_returns`
2. 枚举入场组合并评分，取 Top-N
3. 对 Top-N 入场组合枚举卖出参数
4. 对每个组合都计算：selection / validation / full
5. 按现有 priority + score 规则选最优

### 5.4 Scoring / Gate

- 沿用 `_selection_score` 的主结构
- 沿用 gate 判定（return/drawdown）
- 维持既有排序倾向，避免行为突变

这样可保证“新增卖出维度”不会破坏现有筛选语义。

### 5.5 Result Persistence

在 `selection_summary.json` 与 `model_metadata.json` 中增加卖出参数字段：
- `first_take_profit`
- `first_exit_ratio`
- `drawdown_stop`

并将其与入场参数、收益、回撤、成交数、综合分数一起落盘，便于复盘和策略回放。

## 6. Safety / Validation Rules

参数校验：
- `first_take_profit > 0`
- `0 < first_exit_ratio < 1`
- `0 < drawdown_stop < 1`

异常处理：
- 若候选列表为空，回退到默认单值
- 若无可行组合，按现有 fallback 路径返回并保留诊断信息

## 7. Testing Strategy

1. 单元测试：moon 分支收益计算
   - 覆盖 80/100/150/200 不同止盈位
   - 覆盖不同首卖比例/回撤止损组合

2. 选择器测试：联合网格
   - 验证 Top-N 入场再卖出优化流程
   - 验证最终 selected 参数包含卖出字段

3. 回归测试：兼容性
   - 关闭新候选或使用默认值时，行为与旧版本一致

## 8. Acceptance Criteria

1. `run_full_training.py` 触发的训练回测可同时比较 80/100/150/200 止盈方案。
2. 最终选出的最佳模型包含“入场+卖出”完整参数。
3. 结果文件可直接查看各方案收益/回撤/成交数并比较优劣。
4. 非 moon 分支与入场行为保持原有语义，不引入额外策略漂移。

## 9. Execution Notes

- 先完成参数化与联合搜索，再补充测试。
- 默认先维持候选范围较小（4×3×3）控制计算量。
- 若后续要进一步扩展候选空间，优先增加分层筛选规则，而不是全量暴力枚举。
