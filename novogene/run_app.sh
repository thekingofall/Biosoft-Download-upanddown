#!/bin/bash

# Novogene下载管理系统一键运行脚本
ENV_NAME="novogene-download"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认配置
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="3683"

# 参数解析
CUSTOM_HOST=""
CUSTOM_PORT=""

# 帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -H, --host HOST    指定服务器地址 (默认: $DEFAULT_HOST)"
    echo "  -p, --port PORT    指定端口号 (默认: $DEFAULT_PORT)"
    echo "  -h, --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                           # 使用默认配置"
    echo "  $0 -p 5000                   # 使用端口5000"
    echo "  $0 -H 0.0.0.0 -p 8080       # 监听所有地址的8080端口"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -H|--host)
            CUSTOM_HOST="$2"
            shift 2
            ;;
        -p|--port)
            CUSTOM_PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "🚀 启动Novogene下载管理系统..."

# 检查环境是否存在
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "❌ 环境 '$ENV_NAME' 不存在，正在自动创建..."
    "$SCRIPT_DIR/scripts/setup_env.sh"
fi

# 激活环境并运行
echo "🔧 激活环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

# 设置环境变量
if [[ -n "$CUSTOM_HOST" ]]; then
    export FLASK_HOST="$CUSTOM_HOST"
    echo "📡 自定义服务器地址: $CUSTOM_HOST"
else
    echo "📡 使用默认服务器地址: $DEFAULT_HOST"
fi

if [[ -n "$CUSTOM_PORT" ]]; then
    export FLASK_PORT="$CUSTOM_PORT"
    echo "🔌 自定义端口: $CUSTOM_PORT"
else
    echo "🔌 使用默认端口: $DEFAULT_PORT"
fi

echo "🌐 启动Web服务器..."
cd "$SCRIPT_DIR"
python run.py
