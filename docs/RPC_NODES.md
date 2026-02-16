# BSC RPC 节点推荐指南

## 🎯 数据收集专用推荐

数据收集需要频繁调用 `eth_getLogs`，对节点的稳定性和速率限制要求较高。

### ⭐ 首选节点

#### 1. 48.club FourMeme 专用节点（强烈推荐）
```
https://four.rpc.48.club
```
- **优点**：
  - 专为 FourMeme 优化
  - 速度快，延迟低
  - 社区维护，稳定可靠
- **缺点**：无
- **推荐场景**：数据收集、实时监控
- **配置**：
  ```bash
  BSC_WSS_URL=https://four.rpc.48.club
  ```

#### 2. Ankr（免费层，推荐）
```
https://rpc.ankr.com/bsc
```
- **优点**：
  - 商业级别稳定性
  - 免费层额度较高
  - 全球CDN加速
  - 响应速度快
- **缺点**：
  - 免费层有请求限制（但对多数场景足够）
- **免费限额**：~30 req/s
- **推荐场景**：生产环境数据收集

#### 3. dRPC
```
https://bsc.drpc.org
```
- **优点**：
  - 去中心化RPC网络
  - 免费层可用
  - 速度较快
- **缺点**：
  - 偶尔有限流
- **推荐场景**：备用节点

---

## 🆓 免费公共节点

### Binance 官方节点
```
https://bsc-dataseed.binance.org
https://bsc-dataseed1.binance.org
https://bsc-dataseed2.binance.org
https://bsc-dataseed3.binance.org
https://bsc-dataseed4.binance.org
```
- **优点**：
  - 官方维护，权威可靠
  - 多个端点可轮换
- **缺点**：
  - **严格的请求限流**（对数据收集不友好）
  - getLogs 调用易被限制
- **推荐场景**：轻量级查询，不适合密集数据收集

### PublicNode
```
https://bsc.publicnode.com
https://bsc-rpc.publicnode.com
```
- **优点**：
  - 社区驱动，免费
  - 较为稳定
- **缺点**：
  - 速度一般
  - 高峰期可能拥堵
- **推荐场景**：备用节点

### 其他免费节点
```
https://bsc-dataseed1.defibit.io
https://bsc-dataseed1.ninicoin.io
```
- **稳定性**：中等
- **推荐场景**：测试和备用

---

## 💰 付费节点（生产环境推荐）

### 1. NodeReal（推荐）
```
https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY
```
- **定价**：免费层 + 按需付费
- **免费额度**：15M CU/月（约300K请求）
- **优点**：
  - BSC 官方合作伙伴
  - 极低延迟
  - 专业级稳定性
  - 支持增强 API
- **获取**：[nodereal.io](https://nodereal.io)
- **推荐场景**：生产环境、高频交易

### 2. QuickNode（最快）
```
https://YOUR_ENDPOINT.bsc.quiknode.pro/YOUR_KEY/
```
- **定价**：$9/月起
- **优点**：
  - 业界最快的响应速度
  - 99.9% SLA保证
  - 全球分布式节点
  - 专业技术支持
- **获取**：[quicknode.com](https://www.quicknode.com)
- **推荐场景**：实时交易、MEV、对延迟极度敏感的应用

### 3. Alchemy
```
https://bsc-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```
- **定价**：免费层 + 按需付费
- **免费额度**：300M CU/月
- **优点**：
  - 强大的开发者工具
  - 增强型 API
  - 详细的监控面板
- **获取**：[alchemy.com](https://www.alchemy.com)
- **推荐场景**：需要开发者工具的场景

### 4. Infura
```
https://bsc-mainnet.infura.io/v3/YOUR_PROJECT_ID
```
- **定价**：免费层 + 付费
- **免费额度**：100K req/day
- **优点**：
  - 老牌服务商，稳定
  - 支持多链
- **获取**：[infura.io](https://www.infura.io)

### 5. GetBlock
```
https://bsc.getblock.io/YOUR_API_KEY/mainnet/
```
- **定价**：免费层 + 付费
- **免费额度**：40K req/day
- **优点**：
  - 支持众多区块链
  - 价格实惠
- **获取**：[getblock.io](https://getblock.io)

---

## 📊 性能对比

| 节点 | 平均延迟 | 稳定性 | getLogs限制 | 成本 | 推荐度 |
|------|---------|--------|-------------|------|--------|
| 48.club | ~80ms | ⭐⭐⭐⭐⭐ | 宽松 | 免费 | ⭐⭐⭐⭐⭐ |
| Ankr | ~100ms | ⭐⭐⭐⭐⭐ | 中等 | 免费 | ⭐⭐⭐⭐⭐ |
| dRPC | ~120ms | ⭐⭐⭐⭐ | 中等 | 免费 | ⭐⭐⭐⭐ |
| NodeReal | ~60ms | ⭐⭐⭐⭐⭐ | 宽松 | 付费 | ⭐⭐⭐⭐⭐ |
| QuickNode | ~50ms | ⭐⭐⭐⭐⭐ | 无限制 | 付费 | ⭐⭐⭐⭐⭐ |
| Binance | ~150ms | ⭐⭐⭐⭐ | **严格** | 免费 | ⭐⭐⭐ |
| PublicNode | ~200ms | ⭐⭐⭐ | 中等 | 免费 | ⭐⭐⭐ |

---

## 🛠️ 配置方法

### 方法1：环境变量（推荐）

在 `.env` 文件中配置：

```bash
# 数据收集节点（推荐48.club）
BSC_WSS_URL=https://four.rpc.48.club

# 交易执行节点（可配置多个，逗号分隔）
BSC_HTTP_RPC=https://bsc-dataseed.binance.org,https://rpc.ankr.com/bsc
```

### 方法2：代码中修改

编辑 `config/config.py`：

```python
BSC_WSS_URL = os.getenv(
    'BSC_WSS_URL',
    'https://four.rpc.48.club'  # 修改默认值
)
```

---

## 🔍 节点测试

测试节点速度和稳定性：

```bash
# 测试延迟
curl -X POST https://four.rpc.48.club \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  -w "\nTime: %{time_total}s\n"

# 测试 getLogs（数据收集关键）
curl -X POST https://four.rpc.48.club \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_getLogs",
    "params":[{
      "address":"0x5c952063c7fc8610FFDB798152D69F0B9550762b",
      "fromBlock":"latest",
      "toBlock":"latest"
    }],
    "id":1
  }' \
  -w "\nTime: %{time_total}s\n"
```

---

## 💡 使用建议

### 数据收集场景
1. **首选**：48.club FourMeme 专用节点
2. **备选**：Ankr 或 dRPC
3. **生产环境**：NodeReal 付费版

### 实盘交易场景
1. **首选**：QuickNode（低延迟）
2. **备选**：NodeReal 或 Ankr
3. **次选**：Binance 官方节点

### 节点轮换策略
```bash
# 配置多个节点，自动轮换
BSC_HTTP_RPC=https://four.rpc.48.club,https://rpc.ankr.com/bsc,https://bsc.drpc.org
```

### 故障转移
程序会自动尝试备用节点，无需手动干预。

---

## ⚠️ 常见问题

### Q: "eth_getLogs is limited to 5000 blocks"
**A**: 使用 48.club 或付费节点，它们对 getLogs 限制较宽松。

### Q: 节点频繁超时
**A**: 
1. 检查网络连接
2. 更换到延迟更低的节点（48.club 或 Ankr）
3. 考虑使用付费节点

### Q: 数据收集掉块
**A**:
1. 使用更稳定的节点（48.club 推荐）
2. 检查程序日志中的 `blocks_skipped` 统计
3. 考虑使用多个节点轮换

### Q: 如何选择节点？
**A**: 
- **免费场景**：48.club > Ankr > dRPC
- **付费场景**：NodeReal ≈ QuickNode > Alchemy
- **数据收集**：优先选择对 getLogs 限制宽松的节点

---

## 📚 相关资源

- [BSC 官方文档](https://docs.bnbchain.org/docs/rpc)
- [48.club 社区](https://48.club)
- [ChainList - BSC RPC 列表](https://chainlist.org/chain/56)
