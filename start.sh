#!/bin/bash

# FourMeme Monitor 快速启动脚本

echo "🚀 FourMeme Monitor - Quick Start"
echo "=================================="

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.dependencies_installed
else
    echo "✅ Dependencies already installed"
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created. You can edit it if needed."
fi

# 启动监控
echo ""
echo "=================================="
echo "🎯 Starting FourMeme Monitor..."
echo "=================================="
echo ""

python main.py
