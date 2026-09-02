# TaskCat Linux 启动指南

## 快速开始

### 1. 给启动脚本添加执行权限
```bash
chmod +x start_for_linux.sh
```

### 2. 运行启动脚本
```bash
./start_for_linux.sh
```

### 3. 如果提示缺少虚拟环境
脚本会询问是否自动创建虚拟环境：
- 输入 `y` 自动创建虚拟环境和安装依赖
- 输入 `n` 手动创建

## 手动设置（如果自动设置失败）

### 1. 进入 fastapi 目录
```bash
cd fastapi
```

### 2. 创建虚拟环境
```bash
python3 -m venv .venv
```

### 3. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 4. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 5. 返回项目根目录并运行
```bash
cd ..
./start_for_linux.sh
```

## 系统要求

### Python
- Python 3.8 或更高版本
- 需要 `python3-venv` 包（用于创建虚拟环境）

### Java（用于 GUI）
- Java 17 或更高版本
- 如果没有安装 Java，GUI 将无法启动，但后端服务仍可运行

## 安装系统依赖

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv openjdk-17-jdk
```

### Fedora
```bash
sudo dnf install python3 python3-pip python3-virtualenv java-17-openjdk
```

### Arch Linux
```bash
sudo pacman -S python python-pip python-virtualenv jdk17-openjdk
```

## 故障排除

### 1. 权限错误
```bash
chmod +x start_for_linux.sh
chmod +x java/mvnw
```

### 2. 虚拟环境创建失败
确保已安装 `python3-venv`：
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Fedora
sudo dnf install python3-virtualenv

# Arch
sudo pacman -S python-virtualenv
```

### 3. 依赖安装失败
检查网络连接，或使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. Maven 包装器权限
```bash
chmod +x java/mvnw
```

## 脚本功能

- 自动检测并激活虚拟环境
- 自动安装缺失的 Python 依赖
- 启动 FastAPI 后端服务（端口 8000）
- 启动 JavaFX GUI 应用程序
- 优雅地处理进程清理（按 Ctrl+C 停止所有服务）

## 停止应用程序

按 `Ctrl+C` 停止所有服务。

或者分别停止：
- 后端服务：找到对应的 PID 并执行 `kill [PID]`
- GUI：直接关闭窗口