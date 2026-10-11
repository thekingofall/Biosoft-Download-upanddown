#!/bin/bash

# 快速激活Novogene下载管理系统环境
ENV_NAME="novogene-download"

# 检查环境是否存在
if ! conda env list | grep -q "^$ENV_NAME "; then
    echo "错误：环境 '$ENV_NAME' 不存在，请先运行 ./scripts/setup_env.sh"
    exit 1
fi

# 激活环境
echo "激活环境 '$ENV_NAME'..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

echo "环境已激活！当前Python: $(which python)"
echo "要运行应用程序，请执行: python run.py"
