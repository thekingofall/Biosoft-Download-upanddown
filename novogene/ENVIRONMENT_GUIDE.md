# 环境管理指南

本文档详细说明如何使用mamba创建和conda激活Novogene下载管理系统的运行环境。

## 概览

本系统提供了多种环境管理方式：
- 🚀 **一键自动化**: 完全自动的环境创建和应用启动
- 🛠️ **手动管理**: 手动控制每个步骤
- 🐍 **Python接口**: 编程方式管理环境
- 📝 **命令行工具**: 灵活的命令行操作

## 系统要求

- **操作系统**: Linux/Unix
- **Python版本**: 3.10–3.12
- **依赖软件**: Anaconda或Miniconda
- **推荐工具**: mamba (用于更快的包管理)

## 安装mamba (可选但推荐)

mamba是conda的高性能替代品，创建环境速度更快：

```bash
# 方法1: 通过conda安装
conda install mamba -n base -c conda-forge

# 方法2: 通过miniforge安装 (推荐新用户)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
```

## 使用方法

### 方法1: 一键自动化启动 (推荐)

适合新用户和快速部署：

```bash
# 进入项目目录
cd Biosoft-Download-upanddown/novogene

# 一键运行 (自动检查环境，创建环境，启动应用)
./run_app.sh
```

**功能特性**:
- 自动检测conda/mamba可用性
- 自动创建不存在的环境
- 智能选择mamba或conda
- 彩色输出和进度提示
- 错误处理和恢复

### 方法2: 自动环境配置

手动控制环境创建过程：

```bash
# 运行环境配置脚本
./scripts/setup_env.sh
```

**配置脚本功能**:
- 检测mamba/conda可用性
- 创建或更新环境
- 验证环境完整性
- 创建便捷脚本
- 彩色输出和用户交互

### 方法3: 手动环境管理

完全手动控制每个步骤：

```bash
# 使用mamba创建环境 (推荐，速度快)
mamba env create -f environment.yml

# 或使用conda创建环境
conda env create -f environment.yml

# 激活环境
conda activate novogene-download

# 验证环境
python -c "import flask, psutil; print('环境验证成功')"

# 运行应用
python run.py

# 退出环境
conda deactivate
```

### 方法4: 便捷脚本

使用预制的便捷脚本：

```bash
# 快速激活环境
source scripts/activate_env.sh

# 或直接运行
./scripts/activate_env.sh
```

### 方法5: Python编程接口

通过Python代码管理环境：

```python
from scripts.env_manager import EnvironmentManager

# 创建环境管理器
env_manager = EnvironmentManager("novogene-download")

# 检查环境状态
exists = env_manager.env_exists()
print(f"环境存在: {exists}")

# 创建环境
success, message = env_manager.create_environment()
print(f"创建结果: {message}")

# 获取环境信息
info = env_manager.get_environment_info()
for key, value in info.items():
    print(f"{key}: {value}")
```

### 方法6: 命令行工具

使用Python环境管理器的CLI接口：

```bash
# 创建环境
python scripts/env_manager.py create

# 强制重建环境
python scripts/env_manager.py create --force

# 更新环境
python scripts/env_manager.py update

# 查看环境信息
python scripts/env_manager.py info

# 验证环境
python scripts/env_manager.py validate

# 删除环境
python scripts/env_manager.py remove
```

## 环境文件说明

### environment.yml

定义conda环境的完整配置：

```yaml
name: novogene-download
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - pip=21.0.1
  - flask>=3.1
  - werkzeug>=3.1
  - jinja2=3.0.3
  - markupsafe=2.0.1
  - click=8.0.4
  - itsdangerous=2.0.1
  - psutil=5.8.0
```

**配置说明**:
- `name`: 环境名称
- `channels`: 包源通道
- `dependencies`: 依赖包列表
- 依赖配置见 requirements.txt 和 environment.yml

## 常用命令

### 环境操作

```bash
# 查看所有环境
conda env list

# 激活环境
conda activate novogene-download

# 退出环境
conda deactivate

# 删除环境
conda env remove -n novogene-download

# 导出环境
conda env export -n novogene-download > environment.yml

# 克隆环境
conda create --name new-env --clone novogene-download
```

### 包管理

```bash
# 在环境中安装包
conda activate novogene-download
conda install package-name

# 或使用mamba (更快)
mamba install package-name

# 更新包
conda update package-name

# 列出环境中的包
conda list

# 搜索包
conda search package-name
```

### 环境维护

```bash
# 清理缓存
conda clean --all

# 更新conda
conda update conda

# 验证环境
conda info --envs
```

## 故障排除

### 常见问题

1. **conda命令未找到**
   ```bash
   # 初始化conda
   ~/miniconda3/bin/conda init
   source ~/.bashrc
   ```

2. **环境创建失败**
   ```bash
   # 清理缓存重试
   conda clean --all
   mamba env create -f environment.yml
   ```

3. **包冲突**
   ```bash
   # 使用mamba解决依赖
   mamba env create -f environment.yml
   ```

4. **权限问题**
   ```bash
   # 添加执行权限
   chmod +x scripts/*.sh
   chmod +x run_app.sh
   ```

5. **Python版本不兼容**
   ```bash
   # 修改environment.yml中的Python版本
   # 重新创建环境
   conda env remove -n novogene-download
   mamba env create -f environment.yml
   ```

### 调试模式

启用详细输出进行调试：

```bash
# Bash调试
bash -x scripts/setup_env.sh

# Python调试
python -v scripts/env_manager.py info

# Conda调试
conda create -f environment.yml --debug
```

### 日志查看

```bash
# 查看conda日志
cat ~/.conda/environments.txt

# 查看应用日志
tail -f logs/app.log
```

## 最佳实践

### 环境管理

1. **使用mamba**: 创建环境时优先使用mamba
2. **定期更新**: 定期更新环境和包
3. **备份环境**: 定期导出environment.yml
4. **清理缓存**: 定期清理conda缓存

### 开发工作流

1. **开发前**: 激活环境
2. **安装包**: 使用conda/mamba安装
3. **测试**: 在干净环境中测试
4. **部署前**: 导出最新的environment.yml

### 性能优化

1. **使用mamba**: 比conda快3-5倍
2. **多通道**: 配置多个conda通道
3. **本地缓存**: 利用本地包缓存
4. **并行下载**: 启用并行下载

## 自动化建议

### CI/CD集成

```yaml
# GitHub Actions示例
- name: Setup Conda
  uses: conda-incubator/setup-miniconda@v2
  with:
    environment-file: environment.yml
    activate-environment: novogene-download
```

### 定时任务

```bash
# 添加到crontab，每天检查环境
0 2 * * * cd /path/to/project && ./scripts/setup_env.sh --update
```

### 监控脚本

```bash
#!/bin/bash
# 环境健康检查
conda activate novogene-download
python -c "
import flask, psutil
print('环境状态: 正常')
" || echo "环境状态: 异常"
```

## 总结

本系统提供了从完全自动化到精细控制的多种环境管理方式：

1. **新用户**: 使用 `./run_app.sh` 一键启动
2. **开发者**: 使用 `./scripts/setup_env.sh` 手动配置
3. **高级用户**: 使用 `scripts/env_manager.py` 编程接口
4. **运维人员**: 使用命令行工具进行批量管理

选择适合您需求的方式，享受高效的环境管理体验！
