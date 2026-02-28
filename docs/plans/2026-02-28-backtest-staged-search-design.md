# Backtest Staged Search Design

Date: 2026-02-28
Status: Approved

## 1. Context

当前训练耗时瓶颈集中在回测参数搜索，不在模型训练本身。

现有实现中，`_select_backtest_thresholds` 对以下 6 个维度做全量笛卡尔积搜索：

- 入场参数：`prob_threshold`、`reg_min_return`、`max_age_seconds`
- 卖出参数：`first_take_profit`、`first_exit_ratio`、`drawdown_stop`

默认候选规模：

- `6 * 7 * 3 * 4 * 3 * 3 = 4536` 组/每个 trial

当训练流程需要评估多个 profile/target 组合时，回测阶段累计耗时显著增长。

## 2. Goals / Non-Goals

### Goals

1. 显著降低回测参数搜索时间。
2. 保留“回测参数需要被测试”的能力，不删除参数维度。
3. 保持现有评分与 gate 语义不变，避免策略漂移。
4. 在异常情况下保持流程可回退，不影响最终产出模型。

### Non-Goals

1. 不重写 `_run_backtest_gate_precomputed` 的收益计算语义。
2. 不改训练主流程（分类器/回归器）核心逻辑。
3. 不引入新服务或外部存储。

## 3. Chosen Approach: Staged Backtest Search

将“全量 6 维一次性搜索”改为“两阶段分层搜索”：

### Stage A（入场粗筛）

仅搜索入场参数三维：

- `prob_threshold`
- `reg_min_return`
- `max_age_seconds`

卖出参数固定为当前默认值：

- `first_take_profit`
- `first_exit_ratio`
- `drawdown_stop`

对每个候选继续计算：

- `selection_result` / `validation_result` / `full_result`
- 现有 `priority` 规则
- 现有 `score` 规则

输出 Stage A 排名后的 Top-N 入场候选。

### Stage B（卖出精筛）

仅对 Stage A 的 Top-N 入场候选，展开卖出参数三维：

- `first_take_profit`
- `first_exit_ratio`
- `drawdown_stop`

入场参数固定为该 Top-N 候选值。

对每个 Stage B 组合同样执行当前评分与优先级逻辑，最终选出全局 best。

## 4. Complexity Reduction

在默认候选下：

- 现状：`4536`
- 分层后：`126 + top_n * 36`

当 `top_n = 10`：

- 总评估量 `= 126 + 360 = 486`
- 相比 4536，减少约 `89%`

此方案保留全部参数维度测试能力，仅改变搜索顺序。

## 5. Detailed Design

## 5.1 Config Extension

在 `DEFAULT_GATE_THRESHOLDS["backtest"]` 增加：

- `auto_tune_strategy`: `"staged"`（默认）
- `entry_stage_top_n`: `10`

保留现有候选列表配置，不删除任何候选维度。

## 5.2 `_select_backtest_thresholds` Control Flow

1. 若 `auto_tune_entry=false`：保持当前直通逻辑。
2. 若 `auto_tune_entry=true` 且 `auto_tune_strategy="full"`：走现有全量 6 维搜索（兼容回退）。
3. 若 `auto_tune_entry=true` 且 `auto_tune_strategy="staged"`：
   - 执行 Stage A（3 维）
   - 取 Top-N
   - 执行 Stage B（仅卖出 3 维）
   - 复用现有 best 选择逻辑

## 5.3 Candidate Scoring Consistency

Stage A 与 Stage B 均沿用当前逻辑：

- `_selection_score(...)`
- viability 判定（return/drawdown）
- priority 规则（validation/full/fallback）
- best tie-break 顺序

确保结果排序语义与历史版本一致。

## 5.4 Fallback Rules

1. `entry_stage_top_n` 自动夹紧到 `[1, len(stageA_candidates)]`。
2. Stage A 全部“不达标”时，仍按 fallback 排序输出 Top-N（不中断）。
3. Stage B 若无候选或异常，回退 Stage A 最优组合。
4. 任一异常不应导致整个训练 trial 失败。

## 5.5 Observability

在日志与 `selection_summary.json` 增加字段：

- `auto_tune_strategy`
- `stageA_total`
- `stageA_top_n`
- `stageB_total`
- `evaluated_candidates_total`
- `estimated_reduction_ratio`

便于验证提速是否达到预期。

## 6. Safety / Compatibility

1. 提供 `auto_tune_strategy="full"` 作为兼容模式。
2. 当 `entry_stage_top_n` 取极大值时，行为趋近全量搜索。
3. 不修改回测收益计算与 gate 判定函数，降低策略漂移风险。

## 7. Testing Strategy

1. 单元测试：
   - staged 路径会先评估 Stage A，再仅对 Top-N 执行 Stage B
   - `entry_stage_top_n` 夹紧规则正确
   - Stage B 异常时回退 Stage A 最优
2. 回归测试：
   - `auto_tune_strategy="full"` 时行为与旧逻辑一致
3. 性能测试：
   - 默认配置下候选评估数从 4536 降到约 486（`top_n=10`）

## 8. Acceptance Criteria

1. 回测参数搜索默认走 staged 策略。
2. 仍能输出完整“入场+卖出”最优参数组合。
3. 在默认配置下，候选评估量显著降低（目标 ~89%）。
4. 发生异常时可回退，训练流程不中断。
5. `full` 模式可用，保证兼容性与对照验证能力。
