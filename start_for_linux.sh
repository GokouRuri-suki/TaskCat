#!/bin/bash

# ========================================
#   TaskCat Linux one-click launcher
# ========================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  TaskCat Linux one-click launcher"
echo "========================================"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装。请先安装 Python3。"
    echo "在 Ubuntu/Debian 上: sudo apt install python3 python3-pip"
    echo "在 Fedora 上: sudo dnf install python3 python3-pip"
    echo "在 Arch 上: sudo pacman -S python python-pip"
    exit 1
fi

# Check if Java is installed (required for GUI)
if ! command -v java &> /dev/null; then
    echo "警告: Java 未安装。GUI 可能无法启动。"
    echo "提示: 需要 Java 17 或更高版本"
    read -p "是否继续？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to setup virtual environment
setup_venv() {
    echo "正在设置虚拟环境..."
    cd "$SCRIPT_DIR/fastapi"
    
    if [ -d ".venv" ]; then
        echo "虚拟环境已存在。"
        return 0
    fi
    
    echo "创建虚拟环境..."
    python3 -m venv .venv
    
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败。"
        echo "请确保已安装 python3-venv 包:"
        echo "  Ubuntu/Debian: sudo apt install python3-venv"
        echo "  Fedora: sudo dnf install python3-virtualenv"
        echo "  Arch: sudo pacman -S python-virtualenv"
        return 1
    fi
    
    echo "激活虚拟环境并安装依赖..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "错误: 安装依赖失败。"
        return 1
    fi
    
    echo "虚拟环境设置完成！"
    return 0
}

# Function to cleanup processes on exit
cleanup() {
    echo "正在停止所有进程..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "停止后端进程 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$GUI_PID" ]; then
        echo "停止 GUI 进程 (PID: $GUI_PID)..."
        kill $GUI_PID 2>/dev/null || true
    fi
    echo "清理完成。"
    exit 0
}

# Trap signals for cleanup
trap cleanup SIGINT SIGTERM EXIT

echo "[1/2] 启动后端服务..."
cd "$SCRIPT_DIR/fastapi"

# Check for virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "未检测到虚拟环境。"
    echo ""
    read -p "是否自动创建虚拟环境并安装依赖？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! setup_venv; then
            echo "虚拟环境设置失败。"
            exit 1
        fi
    else
        echo "请手动创建虚拟环境："
        echo "  cd fastapi"
        echo "  python3 -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
fi

# Activate virtual environment
echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# Verify that required packages are installed
echo "检查依赖包..."
if ! python3 -c "import uvicorn, fastapi" &> /dev/null; then
    echo "警告: 缺少必要的 Python 包。"
    echo "正在安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误: 安装依赖失败。"
        exit 1
    fi
fi

# Start backend in background
echo "启动后端服务..."
python3 -m uvicorn src:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "后端服务已启动 (PID: $BACKEND_PID)"
echo "等待后端服务初始化..."

# Wait for backend to be ready
sleep 3

# Check if backend is running
if ! curl -s http://127.0.0.1:8000 > /dev/null; then
    echo "错误: 后端服务启动失败。"
    exit 1
fi

echo "后端服务就绪！"
echo "[2/2] 启动 GUI..."

cd "$SCRIPT_DIR/java"

# Make mvnw executable if needed
if [ -f "mvnw" ]; then
    if [ ! -x "mvnw" ]; then
        echo "设置 mvnw 为可执行..."
        chmod +x mvnw
        if [ $? -ne 0 ]; then
            echo "警告: 无法设置 mvnw 为可执行，尝试使用 sudo..."
            echo "请手动运行: chmod +x java/mvnw"
        fi
    fi
    
    # Start GUI in background
    echo "启动 JavaFX GUI..."
    ./mvnw javafx:run &
    GUI_PID=$!
else
    echo "错误: 未找到 mvnw 文件。"
    echo "请确保 java/mvnw 文件存在。"
    exit 1
fi

echo "GUI 已启动 (PID: $GUI_PID)"
echo ""
echo "========================================"
echo "TaskCat 已成功启动！"
echo "- 后端: http://127.0.0.1:8000"
echo "- GUI: 已启动 (PID: $GUI_PID)"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "========================================"

# Wait for GUI to exit
wait $GUI_PID

echo ""
echo "GUI 已关闭。"
echo "正在停止后端服务..."