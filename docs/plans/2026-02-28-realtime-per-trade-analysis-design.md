# Realtime Per-Trade Analysis Design

Date: 2026-02-28
Status: Approved

## 1. Context

用户反馈当前 bot 分析速度相比之前明显变慢，目标是“每收集到任何一笔交易就立马分析，第一时间能够交易”。

当前实现中，交易事件先进入 collector 队列，再由 `_collector_loop` 批量处理后将 token 写入 `_pending_analysis`（`set`）。分析循环按 token 去重消费，导致同一 token 的短时多笔成交会被合并为一次分析。

关键位置：
- 交易事件入 collector 队列：`src/trader/bot.py` `_on_trade`
- token 级分析触发去重：`src/trader/bot.py` `_pending_analysis`
- 分析消费：`src/trader/bot.py` `_analysis_loop`

## 2. Goals / Non-Goals

### Goals

1. 实现“每笔成交事件都触发一次分析机会”（事件级触发）。
2. 在不阻塞 listener 回调的前提下尽量降低分析触发延迟。
3. 保留买单去重与下单并发保护，避免重复下单风暴。
4. 保持现有持仓管理、卖出逻辑与 shutdown 稳定性。

### Non-Goals

1. 不修改模型特征与训练逻辑。
2. 不重写买卖策略阈值逻辑。
3. 不改变 listener 侧链上事件去重语义（`tx_hash + log_index`）。

## 3. Alternatives Considered

### A. 事件级分析队列（Chosen）

- 每条交易事件在 collector 更新后，立即入 analysis 事件队列。
- 分析循环逐条消费事件并调用 `_process_token_logic(token)`。

优点：完全满足“每笔都分析”；时延最低。
代价：高频场景 CPU/推理负载增大。

### B. Token 级实时合并

- 保留 token 去重，仅增强即时唤醒。

优点：改动小、负载稳。
缺点：不满足“每笔必分析”。

### C. 事件级 + 极端限流保护

- 常态每笔分析，极端爆量时做毫秒级短限流。

优点：性能韧性更强。
缺点：复杂度更高，极端时仍会合并。

## 4. Chosen Design

### 4.1 Trigger Model

将分析触发从 token 聚合改为事件驱动：

1. `_on_trade` 继续只做快速入队（collector 队列），避免阻塞 listener。
2. `_collector_loop` 对每条事件执行 `on_token_purchase/on_token_sale` 更新 lifecycle 后，立即将该事件对应 token 入 `analysis_event_queue`。
3. `_analysis_loop` 改为逐事件消费，不再从 `_pending_analysis(set)` 批量取 token。

结果：同一 token 连续 N 笔交易会触发 N 次分析调度。

### 4.2 Data Semantics

- lifecycle 仍是增量状态：每笔事件 append buys/sells 并更新 price/统计。
- 每次分析都基于当下 lifecycle 最新状态执行；不会丢交易数据。
- “每笔触发”保证时机不被 token 级去重吞并。

### 4.3 Safety Boundaries

保留以下稳定性机制：

1. listener 事件去重（`tx_hash + log_index`）保持不变。
2. 买单去重 `_pending_buy_signals` 保持不变（分析多次不等于重复下单）。
3. 卖出并发保护 `_selling_tokens` 与 `trader_lock` 保持不变。
4. 分析单条异常隔离：记录错误并继续消费后续事件。
5. analysis 队列设置 `maxsize`，避免内存无上限增长。

## 5. Expected Impact

1. 成交到分析日志的延迟显著下降。
2. 同 token 高频交易下可获得更细粒度的决策时机。
3. 整体 CPU 使用率可能上升（可通过后续参数调优观察）。

## 6. Verification Strategy

1. 单元测试：同 token 连续 2-3 笔交易，断言 `_process_token_logic` 调用次数与事件数一致。
2. 回归测试：买单去重依旧生效（不重复入 buy signal）。
3. 鲁棒性测试：分析单条异常不影响队列继续消费。
4. 运行验证：观察实盘日志中 `Analysis:` 触发频率与成交笔数一致，且触发时延明显缩短。

## 7. Acceptance Criteria

1. 每笔交易事件都会触发一次分析调度（不再 token 级合并）。
2. listener 回调路径不被重计算阻塞。
3. 买单/卖单并发保护机制不回归。
4. 运行时不出现异常增长的重复下单行为。
5. 分析速度主观与日志观测均明显快于当前版本。