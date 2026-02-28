#!/bin/bash

echo "==================================="
echo "同时启动后端和前端服务"
echo "==================================="

if ! command -v tmux &> /dev/null
then
    echo "错误：需要安装 tmux"
    echo "请运行：sudo apt-get install tmux"
    exit 1
fi

SESSION_NAME="dm-code-agent"

tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    tmux new-session -d -s $SESSION_NAME -n "backend" "uvicorn backend.main:app --reload --port 8000"
    tmux new-window -t $SESSION_NAME -n "frontend" "cd frontend && npm run dev"
    echo "✓ 服务已在 tmux 会话中启动"
    echo ""
    echo "使用以下命令查看服务："
    echo "  tmux attach -t $SESSION_NAME"
    echo ""
    echo "切换窗口："
    echo "  Ctrl+b 然后 n (下一个窗口)"
    echo "  Ctrl+b 然后 p (上一个窗口)"
    echo ""
    echo "分离会话："
    echo "  Ctrl+b 然后 d"
    echo ""
    echo "访问地址："
    echo "  前端：http://localhost:3000"
    echo "  后端 API：http://localhost:8000"
    echo "  API 文档：http://localhost:8000/docs"
else
    echo "会话已存在，使用以下命令连接："
    echo "  tmux attach -t $SESSION_NAME"
fi
