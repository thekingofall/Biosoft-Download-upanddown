# Synapse 递归下载

```bash
# 从合集根目录执行
python -m pip install -r synapse/requirements.txt
export SYNAPSE_AUTH_TOKEN='your_token_here'
python download.py synapse --synapse-id syn61592786 --output downloaded_data
```

环境变量优先，也支持此目录下的 `.env`，格式见 [env.example.txt](env.example.txt)。Windows PowerShell 使用 `$env:SYNAPSE_AUTH_TOKEN='your_token_here'`。令牌由使用者自行提供，数据权限由 Synapse 管理。

目录获取或文件下载失败会计入失败数，并以非零退出码结束。统计中的字节数取自 Synapse 返回的文件元数据。早期个人下载列表流程见 [legacy](legacy/)。
