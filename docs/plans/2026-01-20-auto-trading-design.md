# FourMeme 自动交易系统设计文档

## 概述

在现有FourMeme实时监控系统基础上,添加自动交易功能,实现新币抢跑买入和智能止盈止损。

## 核心需求

- **买入策略**: 抢跑模式 + 条件过滤
- **卖出策略**: 动态止盈止损 + 分批卖出(留10%底仓)
- **交易方式**: 直接调用FourMeme TokenManager2合约
- **风险控制**: 固定金额 + 单日限额
- **回测支持**: 使用历史数据验证策略

## 系统架构

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                     FourMeme Monitor                     │
│                  (现有监控系统,保持不变)                   │
└────────────────────┬────────────────────────────────────┘
                     │ TokenCreate事件
                     ▼
          ┌──────────────────────┐
          │    TradeFilter       │ ← 条件过滤
          │  (交易过滤器)          │
          └──────────┬───────────┘
                     │ 通过过滤
                     ▼
          ┌──────────────────────┐
          │   TradeExecutor      │ ← 极速买入
          │  (交易执行器)          │
          └──────────┬───────────┘
                     │ 买入成功
                     ▼
          ┌──────────────────────┐
          │  PositionTracker     │ ← 持仓追踪
          │  (持仓追踪器)          │   价格监控
          └──────────┬───────────┘
                     │ 触发止盈/止损
                     ▼
          ┌──────────────────────┐
          │   TradeExecutor      │ ← 分批卖出
          │   (卖出)              │
          └──────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │    RiskManager       │ ← 风控检查
          │   (风控管理器)         │   (全程监控)
          └──────────────────────┘
```

### 回测系统

```
历史JSONL数据 → BacktestEngine → 模拟交易 → 统计报告
                      ↓
              复用Filter/Tracker逻辑
```

## 详细设计

### 1. TradeFilter (交易过滤器)

**功能**: 决定是否对新币执行买入

**过滤条件** (可配置):
- 关键词黑名单 (避免明显骗局)
- 最低初始流动性限制
- 创建者地址白名单 (可选)

**实现**:
```python
class TradeFilter:
    def should_buy(self, token_info: dict) -> bool:
        # 检查黑名单关键词
        if self._check_blacklist(token_info['name'], token_info['symbol']):
            return False

        # 检查初始流动性
        if token_info['launch_fee'] < self.min_liquidity:
            return False

        return True
```

### 2. TradeExecutor (交易执行器)

**功能**: 执行实际的买入/卖出交易

**极速优化策略**:
1. **预签名交易模板** - 启动时构建,检测到新币仅替换token地址
2. **高优先级Gas** - 动态获取pending交易Gas,加价50-100%抢跑
3. **异步并行处理** - 使用asyncio.create_task()不阻塞主监控
4. **交易重试机制** - 失败自动重试最多3次

**买入流程**:
```python
async def buy_token(self, token_address: str):
    # 1. 构建交易
    tx = self.contract.functions.buy(
        token_address,
        min_tokens_out  # 根据slippage计算
    ).build_transaction({
        'from': self.wallet_address,
        'value': Web3.to_wei(BUY_AMOUNT_BNB, 'ether'),
        'gas': 300000,
        'gasPrice': self._get_dynamic_gas_price(),  # 动态Gas
        'nonce': await self.w3.eth.get_transaction_count(self.wallet_address)
    })

    # 2. 签名
    signed_tx = self.account.sign_transaction(tx)

    # 3. 发送 (异步,不等待确认)
    tx_hash = await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # 4. 记录持仓
    await self.position_tracker.add_position(token_address, tx_hash)
```

**卖出流程**:
```python
async def sell_token(self, token_address: str, amount: int):
    # 调用FourMeme合约sell函数
    tx = self.contract.functions.sell(
        token_address,
        amount
    ).build_transaction({...})

    # 签名并发送
    # 更新持仓状态
```

### 3. PositionTracker (持仓追踪器)

**功能**: 追踪每笔交易,监控价格变化,触发止盈止损

**持仓数据结构**:
```python
{
    'token_address': '0x...',
    'entry_price': 0.001,          # 买入价格
    'total_amount': 50000,         # 总持仓
    'remaining_amount': 50000,     # 剩余持仓
    'bnb_invested': 0.05,          # 投入BNB
    'buy_time': timestamp,
    'buy_tx_hash': '0x...',
    'status': 'holding',           # holding/partial_sold/closed
    'first_sell_price': None,      # 第一次卖出价格
    'peak_price': 0.001,           # 峰值价格 (用于回撤止损)
}
```

**价格监控机制**:
- 监听TokenPurchase/TokenSale事件
- 每个事件推算隐含价格: `price = bnb_cost / token_amount`
- 异步检查所有持仓是否触发条件

**止盈止损逻辑**:

**第一阶段 - 初始持仓**:
```python
async def check_position(self, token_address: str, current_price: float):
    position = self.positions[token_address]
    pnl_percent = (current_price - position['entry_price']) / position['entry_price'] * 100

    # 止盈: +200%
    if pnl_percent >= TAKE_PROFIT_PERCENT:
        await self._sell_partial(token_address, 0.9)  # 卖出90%
        position['status'] = 'partial_sold'
        position['first_sell_price'] = current_price
        position['peak_price'] = current_price
        return

    # 止损: -50%
    if pnl_percent <= STOP_LOSS_PERCENT:
        await self._sell_all(token_address)
        return

    # 时间止损: 5分钟
    if time.time() - position['buy_time'] > MAX_HOLD_TIME_SECONDS:
        await self._sell_all(token_address)
        return
```

**第二阶段 - 底仓监控**:
```python
async def check_moonshot_position(self, token_address: str, current_price: float):
    position = self.positions[token_address]

    # 更新峰值价格
    if current_price > position['peak_price']:
        position['peak_price'] = current_price

    entry_pnl = (current_price - position['entry_price']) / position['entry_price'] * 100

    # 底仓止盈: 5倍
    if entry_pnl >= MOONSHOT_PROFIT_PERCENT:
        await self._sell_remaining(token_address)
        return

    # 峰值回撤止损: -30%
    drawdown = (current_price - position['peak_price']) / position['peak_price'] * 100
    if drawdown <= MOONSHOT_STOP_LOSS_PERCENT:
        await self._sell_remaining(token_address)
        return

    # 时间止损: 24小时
    if time.time() - position['buy_time'] > MOONSHOT_MAX_HOLD_HOURS * 3600:
        await self._sell_remaining(token_address)
        return
```

### 4. RiskManager (风控管理器)

**功能**: 全程监控,确保风险可控

**风控检查点**:
1. **买入前检查**:
   - 今日交易次数是否超限
   - 今日投入金额是否超限
   - 当前持仓数量是否超限
   - 账户BNB余额是否充足

2. **运行时监控**:
   - 统计总盈亏
   - 检测异常 (如连续多笔失败)
   - 紧急停止机制 (如亏损超过阈值)

```python
class RiskManager:
    def can_buy(self) -> tuple[bool, str]:
        # 检查今日交易次数
        if self.daily_trades >= MAX_DAILY_TRADES:
            return False, "Daily trade limit reached"

        # 检查今日投入
        if self.daily_investment >= MAX_DAILY_INVESTMENT_BNB:
            return False, "Daily investment limit reached"

        # 检查持仓数量
        if len(self.active_positions) >= MAX_CONCURRENT_POSITIONS:
            return False, "Max concurrent positions reached"

        return True, "OK"
```

### 5. BacktestEngine (回测引擎)

**功能**: 使用历史数据验证策略参数

**回测流程**:
1. 读取历史JSONL文件
2. 按时间顺序重放事件
3. 模拟Filter/Executor/Tracker逻辑
4. 计算每笔交易盈亏
5. 生成统计报告

**核心逻辑**:
```python
class BacktestEngine:
    async def run_backtest(self, data_file: str):
        events = self._load_events(data_file)

        for event in events:
            if event['event_type'] == 'launch':
                # 模拟过滤
                if self.filter.should_buy(event):
                    # 模拟买入
                    self._simulate_buy(event)

            elif event['event_type'] in ['buy', 'sell']:
                # 更新价格
                price = event['ether_amount'] / event['token_amount']
                # 检查止盈止损
                await self.tracker.check_all_positions(price)

        # 生成报告
        self._generate_report()
```

**统计指标**:
- 总收益率
- 胜率 (盈利交易 / 总交易)
- 平均盈利/亏损
- 最大回撤
- 夏普比率
- 每笔交易详情

## 配置参数

### .env 配置文件

```bash
# ========== 钱包配置 ==========
PRIVATE_KEY=your_private_key_here  # 请务必保密!

# ========== 交易开关 ==========
ENABLE_TRADING=false      # 实盘交易开关 (测试时false)
ENABLE_BACKTEST=true      # 回测模式

# ========== 买入策略 ==========
BUY_AMOUNT_BNB=0.05                # 每次买入金额
BUY_GAS_PRICE_GWEI=20              # Gas价格 (抢跑建议20+)
BUY_SLIPPAGE_PERCENT=15            # 滑点容忍度

# ========== 卖出策略 (第一阶段) ==========
TAKE_PROFIT_PERCENT=200            # 止盈: 200%
TAKE_PROFIT_SELL_PERCENT=90        # 止盈卖出90%, 留10%
STOP_LOSS_PERCENT=-50              # 止损: -50%
MAX_HOLD_TIME_SECONDS=300          # 最长持有5分钟

# ========== 卖出策略 (第二阶段 - 底仓) ==========
KEEP_POSITION_FOR_MOONSHOT=true    # 启用底仓策略
MOONSHOT_PROFIT_PERCENT=500        # 底仓止盈: 5倍
MOONSHOT_STOP_LOSS_PERCENT=-30     # 底仓止损: 峰值回撤30%
MOONSHOT_MAX_HOLD_HOURS=24         # 底仓最长持有24小时

# ========== 风控参数 ==========
MAX_DAILY_TRADES=10                # 每日最多交易10次
MAX_DAILY_INVESTMENT_BNB=0.5       # 每日最大投入0.5 BNB
MAX_CONCURRENT_POSITIONS=3         # 最多同时持仓3个

# ========== 过滤条件 (可选) ==========
FILTER_KEYWORDS_BLACKLIST=scam,rug,test  # 黑名单关键词
FILTER_MIN_INITIAL_LIQUIDITY=0.01        # 最低初始流动性BNB
```

## 文件结构

```
d:\Code\meme\
├── src/
│   ├── core/
│   │   ├── listener.py          # 现有: 事件监听器
│   │   ├── processor.py         # 现有: 数据处理器
│   │   ├── ws_manager.py        # 现有: WebSocket管理
│   │   ├── trader.py            # 新增: 交易执行器
│   │   ├── position.py          # 新增: 持仓追踪器
│   │   ├── filter.py            # 新增: 交易过滤器
│   │   └── risk.py              # 新增: 风控管理器
│   ├── backtest/
│   │   ├── engine.py            # 新增: 回测引擎
│   │   └── report.py            # 新增: 回测报告
│   └── utils/
│       ├── helpers.py           # 现有: 工具函数
│       └── wallet.py            # 新增: 钱包管理
├── config/
│   ├── config.py                # 现有: 基础配置
│   ├── trading_config.py        # 新增: 交易配置
│   └── TokenManager.lite.abi    # 现有: 合约ABI
├── data/
│   ├── events/                  # 现有: 事件记录
│   └── trades/                  # 新增: 交易记录
├── docs/
│   └── plans/
│       └── 2026-01-20-auto-trading-design.md  # 本文档
├── .env                         # 配置文件
├── .env.example                 # 配置示例
├── main.py                      # 主程序
└── backtest.py                  # 新增: 回测入口
```

## 安全性考虑

1. **私钥安全**:
   - 私钥存储在.env文件中
   - .env已在.gitignore中,不会提交到git
   - 建议使用专用钱包,避免大额资金

2. **交易安全**:
   - 默认ENABLE_TRADING=false,防止误操作
   - 实现紧急停止机制
   - 所有交易记录到文件,可审计

3. **风险控制**:
   - 单笔固定金额限制
   - 每日总投入限制
   - 最大持仓数量限制
   - 自动止损机制

## 实施计划

### 阶段1: 核心交易功能 (2-3天)
1. 实现TradeExecutor基础买卖功能
2. 实现PositionTracker持仓管理
3. 集成到现有监控系统
4. 使用测试网验证

### 阶段2: 策略优化 (1-2天)
5. 实现TradeFilter过滤逻辑
6. 实现RiskManager风控
7. 实现分批卖出 + 底仓策略
8. 参数调优

### 阶段3: 回测系统 (1-2天)
9. 实现BacktestEngine
10. 使用历史数据回测
11. 优化策略参数
12. 生成回测报告

### 阶段4: 上线准备 (1天)
13. 小额实盘测试
14. 监控和日志完善
15. 文档和使用说明

## 测试策略

1. **单元测试**: 各模块独立测试
2. **回测验证**: 使用历史数据验证策略
3. **测试网测试**: BSC测试网小额测试
4. **实盘小额测试**: 0.01 BNB单笔测试
5. **逐步放大**: 确认无误后调整到0.05 BNB

## 性能目标

- **买入延迟**: TokenCreate事件 → 交易上链 < 0.5秒
- **价格更新**: 每个buy/sell事件实时更新
- **止盈响应**: 触发条件 → 卖出交易 < 1秒
- **系统可用性**: 24/7运行,自动重连

## 风险提示

1. **市场风险**: Meme币波动极大,可能归零
2. **技术风险**: 智能合约漏洞、Gas war失败
3. **滑点风险**: 高波动可能导致实际成交价偏离
4. **流动性风险**: 卖出时可能因流动性不足失败

**建议**:
- 从小额开始测试
- 密切监控前期运行
- 根据回测结果调整参数
- 设置每日总亏损上限

---

**文档版本**: v1.0
**创建日期**: 2026-01-20
**作者**: Claude Sonnet 4.5 + 用户协作设计
