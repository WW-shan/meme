# 🎉 训练集最终版本 - 完整总结

## 📊 数据规模

```
样本总数:   235,117
├─ 训练集:  188,093 (80%)
├─ 验证集:   23,511 (10%)
└─ 测试集:   23,513 (10%)

文件大小:   ~300MB
特征数:     56个 ⭐
标签数:     7个
```

## 🔥 特征总览 (56个)

### 基础特征 (1-6)
```
1.  total_supply         - 总供应量
2.  launch_fee           - 初始流动性
3.  liquidity_ratio      - 流动性比率
4.  name_length          - 名称长度
5.  symbol_length        - 符号长度
6.  time_since_launch    - 发布时长
```

### 交易数据 (7-17)
```
7.  total_buys           - 总买入次数
8.  total_sells          - 总卖出次数
9.  unique_buyers        - 独立买家数
10. unique_sellers       - 独立卖家数
11. total_buy_volume     - 总买入量(BNB)
12. total_sell_volume    - 总卖出量(BNB)
13. volume_10s           - 10秒成交量
14. volume_30s           - 30秒成交量
15. volume_1min          - 1分钟成交量
16. volume_2min          - 2分钟成交量
17. volume_5min          - 5分钟成交量
```

### 价格特征 (18-23)
```
18. current_price        - 当前价格
19. first_price          - 首次价格
20. price_change_pct     - 价格涨幅%
21. max_price            - 历史最高价
22. min_price            - 历史最低价
23. price_momentum       - 价格动量
```

### 技术指标 (24-30)
```
24. buy_pressure         - 买入压力
25. avg_buy_size         - 平均买入规模
26. avg_sell_size        - 平均卖出规模
27. trade_frequency      - 交易频率
28. buyer_concentration  - 买家集中度
29. seller_concentration - 卖家集中度
30. volume_acceleration  - 成交量加速度
```

### 持币地址分析 (31-34) 🆕
```
31. holder_count              - 持币地址数
32. holder_concentration_top5 - 前5大地址占比
33. max_holder_ratio          - 最大持币者占比
34. avg_holding               - 平均持币量
```

### 创建者分析 (35-39) 🆕
```
35. creator_is_buyer      - 创建者是否买入(0/1)
36. creator_is_seller     - 创建者是否卖出(0/1)
37. creator_buy_volume    - 创建者买入量
38. creator_sell_volume   - 创建者卖出量
39. creator_holding_ratio - 创建者持币占比
```

### 大户分析 (40-41) 🆕
```
40. whale_count          - 大户数量
41. whale_volume_ratio   - 大户成交占比
```

### 交易行为 (42-43) 🆕
```
42. repeat_buyer_ratio     - 重复买家比例
43. address_overlap_ratio  - 买卖地址重叠率
```

### 早期活动分析 (44-48) 🔥 NEW!
```
44. early_buy_count       - 前30秒买入次数
45. early_buy_volume      - 前30秒买入量
46. early_unique_buyers   - 前30秒独立买家数
47. early_activity_ratio  - 早期活跃度占比
48. early_volume_ratio    - 早期成交量占比
```

### 突发检测 (49-51) 🔥 NEW!
```
49. burst_detected        - 是否检测到突发买入(0/1)
50. burst_intensity       - 突发强度(最大10秒窗口成交量占比)
51. max_burst_volume      - 最大突发成交量
```

### 交易规律性 (52-55) 🔥 NEW!
```
52. interval_regularity   - 交易间隔规律性(判断机器人)
53. price_volatility      - 价格波动率
54. small_buy_ratio       - 小额买单比例
55. large_buy_ratio       - 大额买单比例
```

### 预测窗口 (56)
```
56. future_window         - 预测时间窗口(60/120/300/600秒)
```

---

## 🎯 关键特征解读

### 1. 早期活动特征 (44-48)

**作用**: 判断代币开盘活跃度

```python
# 优质代币特征
early_buy_count = 15        # 前30秒有15笔买入
early_unique_buyers = 12    # 12个不同的人买
early_activity_ratio = 0.8  # 80%的交易在前30秒
early_volume_ratio = 0.7    # 70%的成交量在前30秒
→ 开盘火爆!值得关注 ✅

# 冷清代币特征
early_buy_count = 2         # 前30秒只有2笔
early_unique_buyers = 2     # 只有2个人
early_activity_ratio = 0.1  # 早期活跃度低
→ 无人问津,跳过 ❌
```

### 2. 突发买入检测 (49-51)

**作用**: 检测是否有大资金突然涌入

```python
# 检测到突发
burst_detected = 1          # 检测到突发
burst_intensity = 0.6       # 某10秒窗口占总成交量的60%
max_burst_volume = 1.5      # 最大突发1.5 BNB
→ 有大资金进场!可能要拉盘 🚀

# 无突发
burst_detected = 0          # 未检测到
burst_intensity = 0.2       # 最大也只占20%
→ 成交量均匀分布,自然增长
```

**突发判断标准**:
- 任意10秒窗口成交量 > 总成交量的30%

### 3. 交易规律性 (52)

**作用**: 判断是机器人交易还是真人

```python
# 机器人交易
interval_regularity = 0.1   # 交易间隔非常规律
→ 可能是机器人刷量 ⚠️

# 真人交易
interval_regularity = 2.5   # 交易间隔很随机
→ 真实散户在交易 ✅
```

**计算方法**: 交易间隔的标准差 / 平均间隔

### 4. 价格波动率 (53)

**作用**: 判断价格稳定性

```python
price_volatility = 0.05     # 价格很稳定
→ 价格平稳上涨,健康 ✅

price_volatility = 0.5      # 价格剧烈波动
→ 暴涨暴跌,风险高 ⚠️
```

### 5. 买单规模分布 (54-55)

**作用**: 判断散户vs大户

```python
# 散户主导
small_buy_ratio = 0.8       # 80%是小单
large_buy_ratio = 0.05      # 5%是大单
→ 散户为主,FOMO情绪

# 大户主导
small_buy_ratio = 0.2       # 20%是小单
large_buy_ratio = 0.4       # 40%是大单
→ 大户在吸筹 💰
```

---

## 🚀 实战案例分析

### 案例1: 优质爆发币

```json
{
  // 早期活跃
  "early_buy_count": 20,
  "early_unique_buyers": 18,
  "early_activity_ratio": 0.9,
  "early_volume_ratio": 0.8,

  // 突发买入
  "burst_detected": 1,
  "burst_intensity": 0.7,
  "max_burst_volume": 2.5,

  // 真实交易
  "interval_regularity": 2.0,

  // 价格稳定上涨
  "price_volatility": 0.08,
  "price_change_pct": 60,

  // 大户参与
  "whale_count": 3,
  "whale_volume_ratio": 0.4,

  // 持币分散
  "holder_concentration_top5": 0.35,

  // 创建者未跑
  "creator_is_seller": 0,
  "creator_holding_ratio": 0.15
}

→ 评分: 95/100
→ 预测: 大涨! 强烈建议买入 🚀🚀🚀
```

### 案例2: 刷量跑路币

```json
{
  // 早期冷清
  "early_buy_count": 3,
  "early_unique_buyers": 2,
  "early_activity_ratio": 0.3,

  // 机器人刷量
  "interval_regularity": 0.05,

  // 高度集中
  "holder_concentration_top5": 0.95,
  "max_holder_ratio": 0.85,

  // 创建者跑路
  "creator_is_seller": 1,
  "creator_holding_ratio": 0.0,

  // 无大户
  "whale_count": 0,

  // 价格暴跌
  "price_change_pct": -30,

  // 大量人卖出
  "address_overlap_ratio": 0.7
}

→ 评分: 5/100
→ 预测: 跑路币! 绝对不要买 🚨🚨🚨
```

---

## 💡 特征重要性排名 (Top 20)

基于实战经验和业务理解:

```
1.  ⭐⭐⭐⭐⭐ creator_is_seller         - 创建者跑路最致命
2.  ⭐⭐⭐⭐⭐ holder_concentration_top5 - 集中度=操控风险
3.  ⭐⭐⭐⭐⭐ burst_detected            - 大资金进场信号
4.  ⭐⭐⭐⭐  early_activity_ratio      - 早期热度
5.  ⭐⭐⭐⭐  total_buy_volume          - 资金量
6.  ⭐⭐⭐⭐  volume_10s                - 爆发力
7.  ⭐⭐⭐⭐  buy_pressure              - 买卖力量
8.  ⭐⭐⭐   whale_volume_ratio        - 机构参与
9.  ⭐⭐⭐   burst_intensity           - 突发强度
10. ⭐⭐⭐   address_overlap_ratio     - 换手率
11. ⭐⭐⭐   interval_regularity       - 真实性
12. ⭐⭐⭐   price_change_pct          - 趋势
13. ⭐⭐⭐   early_unique_buyers       - 早期参与度
14. ⭐⭐⭐   trade_frequency           - 活跃度
15. ⭐⭐⭐   volume_acceleration       - 加速度
16. ⭐⭐    price_volatility          - 稳定性
17. ⭐⭐    large_buy_ratio           - 大户占比
18. ⭐⭐    max_holder_ratio          - 最大持币者
19. ⭐⭐    repeat_buyer_ratio        - 信心
20. ⭐⭐    creator_holding_ratio     - 创建者持币
```

---

## 📈 下一步行动

### 1. 立即可用
- 数据集已就绪: 235,117个样本
- 特征完整: 56个高质量特征
- 可直接开始训练模型

### 2. 模型建议
- **XGBoost**: 处理非线性关系,特征重要性分析
- **LightGBM**: 速度快,适合大数据集
- **神经网络**: 捕捉复杂模式
- **集成模型**: 结合多个模型,提升准确率

### 3. 训练任务
1. **二分类**: 预测是否盈利 (`is_profitable`)
2. **回归**: 预测收益率 (`max_return_pct`)
3. **多分类**: 预测收益等级 (`return_class`)

### 4. 评估指标
- **准确率**: 预测对错
- **Precision/Recall**: 盈利币识别率
- **AUC**: 整体分类能力
- **MSE/MAE**: 收益率预测误差

---

## 🎯 期望效果

如果模型训练良好,应该能达到:

- **识别优质币**: Precision > 60% (10个预测买的,6个真的涨)
- **避开亏损币**: Recall > 80% (10个好币,能识别出8个)
- **收益率预测**: MAE < 20% (预测误差在20%以内)

**关键**: 这56个特征覆盖了代币的所有重要维度,理论上足以训练出高质量的预测模型!

---

**文件位置**:
- 训练集: `data/datasets/train_20260123_145250.jsonl`
- 验证集: `data/datasets/val_20260123_145250.jsonl`
- 测试集: `data/datasets/test_20260123_145250.jsonl`

**开始训练吧!** 🚀
