# 🚀 快速使用指南

## 一键启动

```bash
./start.sh
```

就这么简单！脚本会自动完成：
1. ✅ 检查 Python 环境
2. ✅ 创建虚拟环境（如果不存在）
3. ✅ 安装依赖包
4. ✅ 创建配置文件
5. ✅ 启动监控程序

## 预期输出

启动后你会看到：

```
🚀 FourMeme Monitor Started
Contract: 0x7aDE9F26e31B6aCF393a39F7D27b4Da48481ef1f
Output: data/events
WebSocket: wss://bsc-ws-node.nariox.org...
============================================================

⏳ Waiting for events... (Press Ctrl+C to stop)
```

## 当有新币发行时

```
[2026-01-20 10:24:12] 🚀 LAUNCH | $PEPE2 (PEPE2.0) | 0x1a2b... | 2.5 BNB
```

## 停止监控

按 `Ctrl+C` 即可安全退出。

## 查看数据

事件数据保存在：`data/events/fourmeme_events_YYYYMMDD.jsonl`

```bash
# 查看今天的事件
cat data/events/fourmeme_events_$(date +%Y%m%d).jsonl

# 统计事件数量
wc -l data/events/*.jsonl
```

## 自定义配置（可选）

编辑 `.env` 文件：

```bash
# 使用不同的节点
BSC_WSS_URL=wss://your-node-url

# 只监控发行事件
MONITOR_EVENTS=launch

# 修改日志级别
LOG_LEVEL=DEBUG
```

## 常见问题

**Q: 长时间无事件输出？**
A: FourMeme 平台可能暂无新活动，这是正常的。

**Q: 连接失败？**
A: 尝试更换节点，编辑 `.env` 中的 `BSC_WSS_URL`。

**Q: 如何后台运行？**
A: 使用 `nohup ./start.sh &` 或 `screen`/`tmux`。

## 技术支持

查看详细文档：
- [README.md](README.md) - 完整使用文档
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总结
- [设计文档](docs/plans/2026-01-20-fourmeme-monitor-design.md) - 技术设计

---

**祝你使用愉快！** 🎉
