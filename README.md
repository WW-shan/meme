# FourMeme BSC 链上监控系统

实时监控 BSC 链上 FourMeme 平台的新币发行、发射进度、毕业等事件。

## 功能特性

- ✅ **实时监控**：基于 WebSocket 实现低延迟（< 1秒）事件监听
- ✅ **事件追踪**：监控 Token 发行、Bonding 进度、毕业到 DEX、交易等事件
- ✅ **彩色输出**：终端实时彩色输出，易于阅读
- ✅ **数据持久化**：自动保存到 JSONL 文件，每天滚动
- ✅ **自动重连**：网络断线自动重连，指数退避策略
- ✅ **事件去重**：防止重复处理同一事件

## 系统要求

- Python 3.8+
- 稳定的网络连接
- BSC WebSocket 节点访问（免费或付费）
- **Linux 用户注意**：需要安装 `libgomp1` 库（用于机器学习模型）
  ```bash
  sudo apt-get install libgomp1  # Ubuntu/Debian
  # 或
  sudo yum install libgomp       # CentOS/RHEL
  ```

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件（可选）
# 默认配置已可直接使用
```

### 3. 运行

```bash
python main.py
```

## 后台运行 (Linux)

推荐使用 `systemd` 托管服务（已提供配置文件）：

1. **修改路径**：编辑 `systemd/fourmeme-bot.service`，将 `/root/meme` 替换为你的实际项目路径。
2. **安装服务**：
   ```bash
   sudo cp systemd/fourmeme-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable fourmeme-bot
   sudo systemctl start fourmeme-bot
   ```
3. **查看日志**：
   ```bash
   sudo journalctl -u fourmeme-bot -f
   # 或查看文件日志
   tail -f logs/bot.log
   ```

或者使用 `nohup` 临时运行：
```bash
nohup tools/start_bot.sh > logs/bot.log 2>&1 &
```

## 快速管理脚本 (Linux)

我们提供了一个便捷的脚本 `tools/bot_manage.sh` 来管理后台进程：

```bash
# 首先赋予执行权限
chmod +x tools/bot_manage.sh

# 启动
./tools/bot_manage.sh start

# 查看状态（包含 PID、运行时间、内存占用、最新日志）
./tools/bot_manage.sh status

# 查看实时日志
./tools/bot_manage.sh log

# 停止
./tools/bot_manage.sh stop

# 重启
./tools/bot_manage.sh restart
```

## 配置说明

### 环境变量 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BSC_WSS_URL` | BSC WebSocket 节点地址 | `wss://bsc-ws-node.nariox.org` |
| `FOURMEME_CONTRACT` | FourMeme 系统合约地址 | `0x7aDE9F26e31B6aCF393a39F7D27b4Da48481ef1f` |
| `OUTPUT_DIR` | 事件数据保存目录 | `data/events` |
| `LOG_LEVEL` | 日志级别 (DEBUG/INFO/WARNING) | `INFO` |
| `MONITOR_EVENTS` | 监控的事件类型 | `all` |

### BSC 节点选择

**免费公共节点**（适合测试）：
- `wss://bsc-ws-node.nariox.org`
- `wss://bsc.publicnode.com`

**付费节点**（推荐生产使用）：
- [QuickNode](https://www.quicknode.com/) - ~$50/月
- [Ankr](https://www.ankr.com/) - ~$30/月
- [GetBlock](https://getblock.io/) - 按请求计费

## 输出示例

```
[2026-01-20 10:24:12] 🚀 LAUNCH | $PEPE2 (PEPE2.0) | 0x1a2b3c4d5e... | 2.5 BNB
[2026-01-20 10:25:30] 📈 BOOST  | 0x3c4d5e6f7a... | Progress: 67.3% | MCap: $45000.00
[2026-01-20 10:27:18] 🎓 GRADUATE | 0x5e6f7a8b9c... | Final MCap: $125,000 | DEX: 0xabc123...
```

## 数据格式

事件数据保存在 `data/events/fourmeme_events_YYYYMMDD.jsonl`，每行一个 JSON：

```json
{
  "event_type": "launch",
  "timestamp": 1737331200,
  "datetime": "2026-01-20T10:24:12",
  "block_number": 12345678,
  "tx_hash": "0x...",
  "token_address": "0x...",
  "token_name": "PEPE2.0",
  "token_symbol": "PEPE2",
  "creator": "0x...",
  "initial_liquidity": 2.5
}
```

## 项目结构

```
meme-monitor/
├── config/
│   ├── config.py          # 配置管理
│   └── contracts.json     # 合约地址和ABI
├── src/
│   ├── core/
│   │   ├── ws_manager.py  # WebSocket管理
│   │   ├── listener.py    # 事件监听
│   │   └── processor.py   # 数据处理
│   └── utils/
│       └── helpers.py     # 工具函数
├── data/
│   └── events/            # 事件数据文件
├── logs/                  # 日志文件
├── main.py                # 程序入口
├── requirements.txt       # Python依赖
└── .env                   # 配置文件
```

## 监控特定事件

编辑 `.env` 文件中的 `MONITOR_EVENTS`：

```bash
# 只监控发行事件
MONITOR_EVENTS=launch

# 监控发行和毕业
MONITOR_EVENTS=launch,graduate

# 监控所有事件（默认）
MONITOR_EVENTS=all
```

## 故障排查

### 连接失败

1. 检查网络连接
2. 尝试切换 BSC 节点（编辑 `.env` 中的 `BSC_WSS_URL`）
3. 查看日志文件 `logs/monitor.log`

### 无事件输出

1. 确认 FourMeme 平台当前是否有新活动
2. 检查合约地址是否正确
3. 尝试使用历史区块测试（需修改代码）

### 权限错误

```bash
# 确保目录权限正确
chmod +x main.py
mkdir -p data/events logs
```

## 高级功能

### 自定义合约 ABI

如果需要监听更多事件，编辑 `config/contracts.json`：

```json
{
  "contract_address": "0x7aDE9F26e31B6aCF393a39F7D27b4Da48481ef1f",
  "abi": [
    {
      "anonymous": false,
      "inputs": [...],
      "name": "CustomEvent",
      "type": "event"
    }
  ]
}
```

### 添加自定义处理逻辑

在 `main.py` 中注册自定义处理器：

```python
async def custom_handler(event_name, event_data):
    # 自定义处理逻辑
    print(f"Custom: {event_name}")

listener.register_handler('TokenLaunched', custom_handler)
```

## 后续开发计划

- [ ] Telegram 通知集成
- [ ] 自动交易功能（买入/卖出）
- [ ] 策略引擎（市值过滤、流动性判断）
- [ ] Web 仪表板
- [ ] 数据分析和可视化

## 注意事项

⚠️ **风险提示**：
- 本项目仅用于学习和研究
- 加密货币投资有风险，请谨慎决策
- 使用前请确保遵守当地法律法规

⚠️ **安全提示**：
- 不要在公共场合分享你的私钥或 API 密钥
- 如需添加交易功能，请使用专用钱包
- 定期检查代码和依赖的安全性

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。

---

**免责声明**：本软件按"原样"提供，不提供任何明示或暗示的保证。使用本软件产生的任何风险由用户自行承担。
