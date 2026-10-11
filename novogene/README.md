# 诺禾云数据下载管理器

一个基于Web的诺禾云数据自动下载管理系统，支持邮件解析、可视化下载进度监控、文件完整性验证等功能。

## 功能特性

- 🔍 **智能邮件解析**: 自动解析诺禾云邮件，提取登录信息和下载参数
- 📊 **可视化管理**: 直观的Web界面，实时显示下载进度和状态
- ⚡ **多任务并发**: 支持多个下载任务同时进行
- 🛡️ **文件验证**: 自动MD5校验，确保文件完整性
- 📱 **响应式设计**: 支持桌面和移动设备访问
- 📝 **详细日志**: 完整的下载日志记录和错误追踪

## 系统要求

- Python 3.10–3.12
- Linux/Unix 系统
- 诺禾云 lnd 命令行工具
- Anaconda/Miniconda (推荐使用mamba)
- 网络连接

## 快速开始

### 方法1: 自动环境配置 (推荐)

使用mamba/conda自动创建和管理环境：

```bash
# 1. 克隆项目
cd Biosoft-Download-upanddown/novogene

# 2. 自动配置环境 (使用mamba创建，conda激活)
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh

# 3. 一键运行
./run_app.sh
```

### 方法2: 手动环境管理

```bash
# 1. 使用mamba创建环境 (速度更快)
mamba env create -f environment.yml

# 或使用conda创建环境
# conda env create -f environment.yml

# 2. 激活环境
conda activate novogene-download

# 3. 运行应用
python run.py
```

### 方法3: 便捷脚本

```bash
# 快速激活环境
source scripts/activate_env.sh

# 运行应用
python run.py
```

### 访问界面

打开浏览器访问: `http://127.0.0.1:3683`

## 环境管理

### 环境配置文件

系统提供完整的conda环境配置：

- `environment.yml` - conda/mamba环境定义文件
- `scripts/setup_env.sh` - 自动环境配置脚本
- `scripts/activate_env.sh` - 快速环境激活脚本
- `run_app.sh` - 一键运行脚本

### 环境命令

```bash
# 创建环境
mamba env create -f environment.yml

# 更新环境
mamba env update -f environment.yml

# 激活环境
conda activate novogene-download

# 退出环境
conda deactivate

# 删除环境
conda env remove -n novogene-download

# 查看环境列表
conda env list
```

## 使用说明

### 邮件解析

1. 将诺禾云发送的邮件内容完整复制
2. 粘贴到首页的文本框中
3. 点击"解析邮件并配置下载"
4. 确认解析的信息无误后开始下载

### 任务管理

- **任务列表**: 查看所有下载任务的状态和进度
- **任务详情**: 实时查看下载日志和详细进度
- **任务控制**: 支持取消、删除任务操作

### 文件验证

下载完成后可以进行文件验证：
- 自动MD5校验
- 文件统计信息
- 完整性验证报告

## 项目结构

```
Novogene_Download/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖
├── app.py                      # Flask主应用
├── run.py                      # 运行入口
├── config/
│   └── settings.py             # 配置文件
├── scripts/
│   ├── __init__.py
│   ├── email_parser.py         # 邮件解析模块
│   ├── download_manager.py     # 下载管理核心
│   └── file_validator.py       # 文件验证模块
├── templates/                  # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── download.html
│   ├── task_list.html
│   ├── task_status.html
│   ├── validation_result.html
│   └── error.html
├── static/                     # 静态资源
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
├── data/                       # 数据下载目录
└── logs/                       # 日志文件目录
```

## API接口

### 任务状态
- `GET /api/task/<task_id>/status` - 获取任务状态
- `POST /api/task/<task_id>/cancel` - 取消任务
- `POST /api/task/<task_id>/remove` - 删除任务
- `GET /api/task/<task_id>/logs` - 获取任务日志

## 配置选项

### 环境变量

```bash
# Flask配置
export FLASK_DEBUG=true
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000

# 下载配置
export LND_CMD_PATH=/path/to/lnd
export MAX_CONCURRENT_TASKS=3
export TASK_TIMEOUT=3600

# 日志配置
export LOG_RETENTION_DAYS=30
```

### 配置文件

在 `config/settings.py` 中可以修改：
- lnd命令路径
- 默认下载目录
- 最大并发任务数
- 任务超时时间
- 日志配置

## 常见问题

### Q: lnd命令无法执行
A: 确保lnd命令有执行权限，路径配置正确：
```bash
chmod +x /usr/local/bin/lnd
```

### Q: 下载失败
A: 检查：
- 网络连接是否正常
- 登录信息是否正确
- 数据是否在有效期内
- 磁盘空间是否充足

### Q: 邮件解析失败
A: 确保邮件内容包含必要字段：
- 登录账号
- 登录密码  
- 数据路径

### Q: 页面无法访问
A: 检查：
- Flask应用是否正常启动
- 端口5000是否被占用
- 防火墙设置

## 日志调试

日志文件位置：
- 应用日志: `logs/app.log`
- 任务日志: 在任务详情页面查看

设置调试模式：
```bash
export FLASK_DEBUG=true
python app.py
```

## 安全注意事项

- 不要在公网环境直接暴露服务
- 定期更改诺禾云密码
- 及时清理过期的下载数据
- 保护好登录信息

## 贡献指南

1. Fork 本仓库
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 基础邮件解析功能
- Web界面下载管理
- 文件验证功能

## 支持

如有问题或建议，请提交 Issue 或联系开发者。
