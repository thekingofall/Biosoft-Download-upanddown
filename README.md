# Biosoft-Download-upanddown

生物信息数据下载工具合集：ENA / Aspera FASTQ 下载、诺禾云下载管理，以及 Synapse 递归下载。

## 工具目录

| 模块 | 原项目 | 用途 |
|---|---|---|
| [aspera](aspera/) | ASCPdown | 根据 ENA 导出的 TSV 文件并行下载 FASTQ |
| [novogene](novogene/) | Novogene_DownloadWeb | 解析交付邮件、管理 LND 下载任务、查看日志和校验结果 |
| [synapse](synapse/) | synapse-downloader | 按 Synapse 项目或文件夹 ID 递归下载数据 |
| [synapse/legacy](synapse/legacy/) | synap | 从个人 Synapse 下载列表逐项下载的早期脚本 |

## 安装

Python 3.10–3.12；Aspera 和诺禾云 LND 命令行工具需另行安装。

```bash
git clone https://github.com/thekingofall/Biosoft-Download-upanddown.git
cd Biosoft-Download-upanddown
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

各模块也可以单独安装依赖。Aspera 脚本使用 Python 标准库。

## ENA / Aspera

从 ENA 导出包含 `fastq_ftp` 列的 TSV 文件，指定本机 Aspera 密钥路径：

```bash
python download.py aspera -i aspera/filereport_read_run_PRJNA727602_tsv.txt -o fastq_files --ascp-binary ascp --ascp-key /path/to/asperaweb_id_dsa.openssh -w 4
python download.py aspera --help
```

默认按表头识别 `fastq_ftp`；其他表格可通过 `--column` 指定从 0 开始的列号。`Ascpdown.py` 是兼容入口。

## 诺禾云

```bash
python -m pip install -r novogene/requirements.txt
python download.py novogene
```

打开 <http://127.0.0.1:3683>，在设置中填写 LND 可执行文件的完整路径和下载目录，再粘贴交付邮件。可通过 `LND_CMD_PATH`、`FLASK_HOST`、`FLASK_PORT`、`SECRET_KEY` 环境变量配置；默认监听本机。此 Web 工具适合可信的本机或受控服务器环境，对外部署需要额外配置身份认证和 HTTPS。LND 使用登录会话，建议同一实例按顺序运行不同账号的任务。

## Synapse

```bash
python -m pip install -r synapse/requirements.txt
export SYNAPSE_AUTH_TOKEN='your_token_here'
# Windows PowerShell: $env:SYNAPSE_AUTH_TOKEN='your_token_here'
python download.py synapse --synapse-id syn61592786 --output downloaded_data
python download.py synapse --help
```

也可将 [env.example.txt](synapse/env.example.txt) 复制为 `synapse/.env` 并填入令牌。使用账号已获授权的数据；受控数据可能还需要在 Synapse 网站完成相应访问审批。

早期下载列表脚本：

```bash
python download.py synapse-legacy --output downloaded_data
```

## 来源与验证

四个原仓库的代码按上述目录整合，来源版本与文件对应关系见 [SOURCES.json](SOURCES.json)。旧提交历史由仓库所有者在本地保存。公开版本采用环境变量读取令牌，并将服务器地址与个人路径改为可配置值。

```bash
python -m unittest discover -s tests -v
```

测试覆盖参数转发、相对路径、下载失败返回值、Synapse 递归及诺禾云页面与配置接口。真实数据传输需要相应服务的账号权限、网络和外部下载工具。
