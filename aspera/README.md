# ENA / Aspera FASTQ 下载

从 ENA 导出带 `fastq_ftp` 表头的 TSV 文件，使用 Aspera 并行下载。

```bash
# 从合集根目录执行
python download.py aspera -i aspera/filereport_read_run_PRJNA727602_tsv.txt --ascp-binary ascp --ascp-key /path/to/asperaweb_id_dsa.openssh -o fastq_files -w 4
python download.py aspera --help
```

Aspera 密钥路径也可通过 `ASCP_KEY` 配置，可执行程序通过 `ASCP_BINARY` 配置。使用 `--column` 选择从 0 开始的列号。输入路径相对于运行命令的目录；输出目录独立创建。任何文件下载失败时返回非零退出码。

`Ascpdown.py` 保留为兼容入口；[FetachENAname.md](FetachENAname.md) 保留原 ENA 文件列表获取截图。
