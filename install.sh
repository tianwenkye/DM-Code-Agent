#!/bin/bash

echo "==================================="
echo "启动 DM-Code-Agent Web 服务"
echo "==================================="

echo ""
echo "步骤 1: 安装 Python 依赖..."
pip install -r requirements.txt

echo ""
echo "步骤 2: 安装前端依赖..."
cd frontend
npm install
cd ..

echo ""
echo "==================================="
echo "服务启动完成！"
echo "==================================="
echo ""
echo "请使用以下命令分别启动后端和前端："
echo ""
echo "后端："
echo "  uvicorn backend.main:app --reload --port 8000"
echo ""
echo "前端："
echo "  cd frontend && npm run dev"
echo ""
echo "或者使用以下命令同时启动（需要 tmux）："
echo "  ./start-all.sh"
echo ""
