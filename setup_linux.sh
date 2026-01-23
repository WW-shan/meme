#!/bin/bash
# 一键部署数据收集系统 (Linux)

set -e

echo "======================================================================"
echo "FourMeme 数据收集系统 - 一键部署"
echo "======================================================================"
echo ""

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
echo "[1/6] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python: $(python3 --version)${NC}"

# 检查虚拟环境
echo ""
echo "[2/6] 检查虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# 安装依赖
echo ""
echo "[3/6] 安装依赖..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓ 依赖已安装${NC}"

# 创建必要目录
echo ""
echo "[4/6] 创建目录..."
mkdir -p data/events
mkdir -p data/training
mkdir -p data/datasets
mkdir -p data/logs
echo -e "${GREEN}✓ 目录已创建${NC}"

# 检查.env文件
echo ""
echo "[5/6] 检查配置..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo "请复制 .env.example 并配置:"
    echo "  cp .env.example .env"
    echo "  vi .env  # 编辑配置"
else
    echo -e "${GREEN}✓ .env 文件存在${NC}"
fi

# 设置权限
echo ""
echo "[6/6] 设置权限..."
chmod +x tools/collector.sh
echo -e "${GREEN}✓ 脚本权限已设置${NC}"

echo ""
echo "======================================================================"
echo -e "${GREEN}部署完成!${NC}"
echo "======================================================================"
echo ""
echo "快速开始:"
echo ""
echo "1. 启动数据收集:"
echo "   ${GREEN}./tools/collector.sh start${NC}"
echo ""
echo "2. 查看日志:"
echo "   ${GREEN}tail -f data/logs/collector_*.log${NC}"
echo ""
echo "3. 构建训练集:"
echo "   ${GREEN}python tools/collect_data.py build${NC}"
echo ""
echo "4. 查看数据摘要:"
echo "   ${GREEN}python tools/dataset_summary.py${NC}"
echo ""
echo "管理命令:"
echo "   ${GREEN}./tools/collector.sh status${NC}   # 查看状态"
echo "   ${GREEN}./tools/collector.sh stop${NC}     # 停止收集"
echo "   ${GREEN}./tools/collector.sh restart${NC}  # 重启收集"
echo ""
echo "======================================================================"
