# FourMeme BSC 链上监控系统设计文档

**日期：** 2026-01-20
**项目：** FourMeme 实时监控系统
**技术栈：** Python + Web3.py + WebSocket

---

## 项目概述

开发一个基于 Python 的实时监控系统，用于监控 BSC 链上 FourMeme 平台的新币发行、发射进度、毕业等事件。系统采用 WebSocket 连接，实现 0.x 秒级的低延迟监控，并将数据输出到终端和本地文件。

### 核心需求

- 监控 FourMeme 平台的新币发行、发射、毕业事件
- 使用 WebSocket 实现实时监控（延迟 < 1秒）
- 终端打印输出 + 保存到本地 JSON 文件
- 仅监控功能，暂不实现自动交易

---

## 整体架构

系统采用事件驱动架构，核心组件：

### 1. WebSocket 连接管理器 (WSConnectionManager)
- 建立和维护与 BSC 节点的 WSS 连接
- 自动重连机制（断线后指数退避重连）
- 心跳检测确保连接活跃

### 2. 事件监听器 (FourMemeListener)
- 订阅 FourMeme 合约的特定事件（发行、发射、毕业）
- 实时接收事件并解析数据
- 基于交易哈希去重，防止重复处理

### 3. 数据处理器 (DataProcessor)
- 格式化事件数据（代币地址、名称、符号、市值等）
- 终端输出美化（带颜色、时间戳）
- 写入本地 JSON 文件（每个事件一行）

### 4. 配置管理 (Config)
- BSC WSS 节点地址
- FourMeme 合约地址和 ABI
- 输出文件路径、日志级别等

### 主流程

```
启动 → 建立 WSS 连接 → 订阅合约事件 → 接收事件 → 解析并输出 → 保存到文件 → 持续监听
```

---

## 数据结构设计

### 事件数据模型

```python
{
    "event_type": "launch" | "boost" | "graduate",
    "timestamp": 1737331200,  # Unix时间戳
    "block_number": 12345678,
    "tx_hash": "0x...",
    "token_address": "0x...",
    "token_name": "DogeKiller",
    "token_symbol": "DOGEK",
    "creator": "0x...",  # 创建者地址
    "initial_liquidity": 1.5,  # BNB数量
    "market_cap": 50000,  # 美元估值（如果合约提供）
    "bonding_progress": 45.2  # 百分比（仅boost/graduate事件）
}
```

### FourMeme 合约事件映射

需要监听的三个关键事件：
- `TokenLaunched` → "launch"（新币发行）
- `BondingCurveProgressed` → "boost"（发射进度更新）
- `TokenGraduated` → "graduate"（毕业到DEX）

### 文件存储格式

- 格式：JSONL（每行一个JSON）
- 文件名：`fourmeme_events_YYYYMMDD.jsonl`
- 每天自动滚动新文件
- 便于追加和后续分析

---

## 错误处理与重连机制

### WebSocket 重连策略

- 初次连接失败：立即重试 1 次
- 后续断线：指数退避重连（1s → 2s → 4s → 8s，最多 60s）
- 最大重试次数：无限次（除非主动停止）
- 每次重连前检查网络可达性

### 事件去重

- 维护最近 1000 个交易哈希的内存缓存（LRU）
- 防止重连时收到重复事件

### 异常场景处理

| 场景 | 处理方式 |
|------|----------|
| 节点返回错误数据 | 记录日志，跳过该事件，继续监听 |
| JSON 解析失败 | 保存原始数据到 error.log，继续运行 |
| 文件写入失败 | 终端警告，数据暂存内存队列，稍后重试 |
| 合约 ABI 不匹配 | 启动时检测并报错退出 |

### 监控指标

- 每分钟输出心跳日志（已接收事件数、连接状态）
- 超过 5 分钟无新区块 → 发出警告（可能节点问题）

---

## 技术栈

### 核心依赖

```
web3.py (v6.x)          - WebSocket 订阅、合约事件解码
websocket-client        - WebSocket 连接管理
python-dotenv           - 配置管理
colorama / rich         - 终端输出美化
```

### BSC 节点选择

**阶段一：免费公共节点**
- `wss://bsc-ws-node.nariox.org`
- `wss://bsc.publicnode.com`
- 限制：可能不稳定，有速率限制

**阶段二：付费节点（生产环境）**
- QuickNode: ~$50/月
- Ankr: ~$30/月
- 优势：低延迟、高可用

### 项目结构

```
meme-monitor/
├── config/
│   ├── config.py          # 配置管理
│   └── contracts.json     # 合约地址和ABI
├── src/
│   ├── ws_manager.py      # WebSocket管理
│   ├── listener.py        # 事件监听
│   ├── processor.py       # 数据处理
│   └── utils.py           # 工具函数
├── data/
│   └── events/            # 存储事件文件
├── logs/                  # 日志文件
├── main.py                # 程序入口
├── requirements.txt
└── .env.example           # 配置模板
```

---

## FourMeme 合约调研计划

### Step 1: GitHub 搜索
- 搜索 FourMeme 相关仓库
- 查找官方合约代码和文档

### Step 2: 链上调研
- 在 BscScan 上搜索 "FourMeme" 相关合约
- 查看合约的交易历史，识别常见事件
- 找到 Factory 合约（负责创建新币的主合约）

### Step 3: 合约分析
- 使用 BscScan 查看合约源码（如已验证）
- 如未验证，使用 Dedaub/Heimdall 反编译
- 提取关键事件签名

### Step 4: 测试验证
- 找一个最近发行的币，追溯其创建交易
- 解码事件日志，确认数据结构
- 编写测试脚本验证可行性

### 所需信息
- FourMeme Factory 合约地址
- TokenLaunched / TokenGraduated 等事件的 ABI
- 新币合约的标准模板

---

## 启动流程

### 安装配置

```bash
# 1. 创建项目环境
cd meme-monitor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置节点
cp .env.example .env
# 编辑 .env，填入 BSC_WSS_URL

# 4. 运行
python main.py
```

### 运行时输出示例

```
[2026-01-20 10:23:45] 🟢 Connected to BSC WebSocket
[2026-01-20 10:23:45] 🎯 Subscribing to FourMeme events...
[2026-01-20 10:24:12] 🚀 LAUNCH | $PEPE2 (PEPE2.0) | 0x1a2b... | 2.5 BNB
[2026-01-20 10:25:30] 📈 BOOST  | $DOGE | 0x3c4d... | Progress: 67.3%
[2026-01-20 10:27:18] 🎓 GRADUATE | $SHIB | 0x5e6f... | Market Cap: $125K
```

### 命令行参数（可选扩展）

```bash
python main.py --verbose              # 详细日志模式
python main.py --events launch        # 只监听发行事件
python main.py --output custom.jsonl  # 自定义输出文件
```

### 优雅退出

- Ctrl+C 触发退出
- 关闭 WebSocket 连接
- 刷新缓冲区，确保所有数据写入文件
- 输出运行统计（总监听时长、捕获事件数）

---

## 后续扩展计划

1. **交易功能**：在监控基础上增加自动买卖逻辑
2. **策略引擎**：支持自定义交易策略（市值过滤、流动性判断等）
3. **Telegram 通知**：重要事件推送到 Telegram
4. **数据分析**：历史数据统计和可视化
5. **多平台支持**：扩展到其他 meme 币平台

---

## 风险与注意事项

1. **免费节点限制**：可能不稳定，需准备备用节点
2. **合约变更**：FourMeme 可能升级合约，需定期检查
3. **Gas 费估算**：后续交易功能需考虑 BSC 的 Gas 机制
4. **安全性**：私钥管理、交易签名等需谨慎处理
5. **法律合规**：确保使用符合当地法规

---

## 总结

本设计文档定义了 FourMeme BSC 链上监控系统的完整架构。系统采用 WebSocket 实现低延迟实时监控，具备健壮的错误处理和重连机制。通过模块化设计，便于后续扩展交易功能和其他高级特性。
