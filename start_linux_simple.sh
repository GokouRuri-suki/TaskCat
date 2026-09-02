#!/bin/bash

# ========================================
#   TaskCat Linux 简单启动脚本
#   要求：必须已有虚拟环境
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  TaskCat Linux 启动脚本"
echo "========================================"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装。"
    exit 1
fi

# 检查虚拟环境
cd fastapi
if [ ! -d ".venv" ]; then
    echo "错误: 未找到虚拟环境 (.venv)"
    echo ""
    echo "请先创建虚拟环境："
    echo "  cd fastapi"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "检查依赖..."
if ! python3 -c "import uvicorn, fastapi" &> /dev/null; then
    echo "错误: 缺少必要的 Python 包。"
    echo "请安装依赖: pip install -r requirements.txt"
    exit 1
fi

# 清理函数
cleanup() {
    echo "正在停止所有进程..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$GUI_PID" ]; then
        kill $GUI_PID 2>/dev/null || true
    fi
    echo "清理完成。"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 启动后端
echo "[1/2] 启动后端服务..."
python3 -m uvicorn src:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"
sleep 3

# 检查后端是否运行
if ! curl -s http://127.0.0.1:8000 > /dev/null; then
    echo "错误: 后端服务启动失败。"
    exit 1
fi

# 启动 GUI
echo "[2/2] 启动 GUI..."
cd "$SCRIPT_DIR/java"

if [ -f "mvnw" ] && [ ! -x "mvnw" ]; then
    chmod +x mvnw
fi

./mvnw javafx:run &
GUI_PID=$!
echo "GUI 已启动 (PID: $GUI_PID)"

echo ""
echo "========================================"
echo "TaskCat 已启动！"
echo "- 后端: http://127.0.0.1:8000"
echo "- GUI: 已启动"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================================"

wait $GUI_PID