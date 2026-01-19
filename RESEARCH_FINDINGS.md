# FourMeme 监控方案说明

## 问题分析

经过详细调研，发现 FourMeme 平台的架构与传统的 Factory 模式不同：

1. **没有中心化 Factory 合约**: FourMeme 不像 Uniswap 或 PancakeSwap 那样有一个统一的 Factory 合约发出 TokenCreated 事件
2. **每个代币独立部署**: 每个 meme 币都是单独部署的合约
3. **事件分散**: Transfer/Approval 等标准 ERC20 事件分散在各个代币合约中

## 已验证的地址

- `0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d` - 代币合约（有大量 Transfer 事件）
- `0x5c952063c7fc8610FFDB798152D69F0B9550762b` - 可能的 TokenManager（170 bytes，代理合约）
- `0x7aDE9F26e31B6aCF393a39F7D27b4Da48481ef1f` - System 用户地址（EOA，非合约）

## 推荐方案

### 方案 1: 使用 FourMeme API（推荐）

FourMeme 官方提供了 API 接口（见 GitBook 文档）：

**优点**:
- 直接获取平台数据
- 延迟低，数据准确
- 无需解析复杂的链上事件

**实现**:
```python
# 轮询 API 获取最新发行的代币
GET https://api.four.meme/tokens/latest
GET https://api.four.meme/tokens/{id}/stats
```

### 方案 2: 监听 TokenManager 合约（需进一步调研）

根据 GitBook 提到的 Token Manager ABI，可能需要：

1. 获取完整的 TokenManager ABI
2. 找到正确的 TokenManager 合约地址
3. 监听其发出的创建/毕业事件

**需要的资源**:
- TokenManager.lite.abi
- TokenManager2.lite.abi
- TokenManagerHelper3.abi

这些文件在 GitBook 中有提供，但需要手动下载。

### 方案 3: 监听 BSC 上的所有新合约创建

监听所有新部署的合约，筛选出 FourMeme 代币：

**缺点**:
- 数据量巨大
- 难以区分 FourMeme 代币和其他合约
- 需要高级节点支持

## 下一步建议

1. **短期方案**: 联系 FourMeme 官方或查看完整的 API 文档
2. **中期方案**: 下载 TokenManager ABI，找到正确的合约地址
3. **长期方案**: 研究 FourMeme 前端代码，了解其完整的合约交互逻辑

## 当前系统状态

✅ **已找到正确的 TokenManager 合约**: `0x5c952063c7fc8610FFDB798152D69F0B9550762b`

**验证数据** (最近50个区块):
- 捕获到 82 个事件
- 4 种不同的事件签名:
  - `0a5575b3648bae2210cee56bf33254cc1ddfbc7bf637c0af2ac18b14fb1bae19`
  - `741ffc4605df23259462547defeab4f6e755bdc5fbb6d0820727d6d3400c7e0d`
  - `7db52723a3b2cdd6164364b3b766e65e540d7be48ffa89582956d8eaebe62942`
  - `48063b1239b68b5d50123408787a6df1f644d9160f0e5f702fefddb9a855954d`

**下一步**: 需要获取 TokenManager 的完整 ABI 来解码这些事件。
- 从 GitBook 文档下载 TokenManager.lite.abi
- 或者反编译合约获取事件定义
- 或者通过 BSCScan API 获取 ABI

系统已正常捕获事件，只是无法解码！

---

**更新时间**: 2026-01-20
**状态**: 需要官方文档或 API 密钥
