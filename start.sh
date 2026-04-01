#!/bin/bash
# 虚拟主播启动脚本

echo "🎭 虚拟主播系统启动中..."
echo "="50

# 进入项目目录
cd "$(dirname "$0")"

# 激活虚拟环境
source venv/bin/activate

# 启动服务
echo "🚀 启动后端服务..."
python backend/main.py
