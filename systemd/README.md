# Systemd 服务安装指南

## 安装步骤

### 1. 编辑服务文件

```bash
cd /path/to/meme
vi systemd/fourmeme-collector.service
```

修改以下内容:
- `YOUR_USERNAME` -> 你的用户名
- `/path/to/meme` -> 项目实际路径

### 2. 复制到systemd目录

```bash
sudo cp systemd/fourmeme-collector.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/fourmeme-collector.service
```

### 3. 重载systemd

```bash
sudo systemctl daemon-reload
```

### 4. 启动服务

```bash
sudo systemctl start fourmeme-collector
```

### 5. 设置开机自启

```bash
sudo systemctl enable fourmeme-collector
```

## 管理命令

```bash
# 启动服务
sudo systemctl start fourmeme-collector

# 停止服务
sudo systemctl stop fourmeme-collector

# 重启服务
sudo systemctl restart fourmeme-collector

# 查看状态
sudo systemctl status fourmeme-collector

# 查看日志
sudo journalctl -u fourmeme-collector -f

# 或查看应用日志
tail -f /path/to/meme/data/logs/systemd.log

# 禁用开机自启
sudo systemctl disable fourmeme-collector
```

## 卸载服务

```bash
# 停止并禁用
sudo systemctl stop fourmeme-collector
sudo systemctl disable fourmeme-collector

# 删除服务文件
sudo rm /etc/systemd/system/fourmeme-collector.service

# 重载systemd
sudo systemctl daemon-reload
```

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u fourmeme-collector -n 50

# 检查服务配置
sudo systemctl cat fourmeme-collector

# 手动测试
cd /path/to/meme
source .venv/bin/activate
python tools/collect_continuous.py
```

### 权限问题

```bash
# 确保用户有权限访问目录
sudo chown -R YOUR_USERNAME:YOUR_USERNAME /path/to/meme
chmod -R 755 /path/to/meme
```

## 优势

- ✅ 开机自启
- ✅ 自动重启 (崩溃恢复)
- ✅ 系统日志集成
- ✅ 服务管理简单
- ✅ 适合生产环境
