# Synapse 下载列表脚本

来自原 `synap` 仓库，保留个人下载列表逐项下载流程。

```bash
python -m pip install -r synapse/requirements.txt
export SYNAPSE_AUTH_TOKEN='your_token_here'
python download.py synapse-legacy --output downloaded_data
```

命令从合集根目录执行。脚本重命名为 `download_synapse_legacy.py`，导入 SDK 时可正确找到安装的 `synapseclient` 包。原内嵌令牌改为环境变量；输出目录通过参数指定。

脚本读取下载列表清单，并按条目的文件 ID 和版本下载。已有本地同名文件按原流程覆盖。下载列表条目继续保留在 Synapse 中。
