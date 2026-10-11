#!/usr/bin/env python3
"""Download ENA FASTQ URLs with Aspera, preserving per-file failure status."""
import argparse
import concurrent.futures
import csv
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Parallel ENA FASTQ downloads with Aspera")
    parser.add_argument("--input", "-i", default=str(Path(__file__).with_name("filereport_read_run_PRJNA727602_tsv.txt")))
    parser.add_argument("--output", "-o", default="fastq_files")
    parser.add_argument("--workers", "-w", type=int, default=4)
    parser.add_argument("--ascp-key", default=os.environ.get("ASCP_KEY"), required=not os.environ.get("ASCP_KEY"))
    parser.add_argument("--ascp-binary", default=os.environ.get("ASCP_BINARY", "ascp"))
    parser.add_argument("--column", "-c", type=int, help="Zero-based column index; default: fastq_ftp header")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.column is not None and args.column < 0:
        parser.error("--column must be non-negative")
    return args


def download_with_ascp(url_pair, ascp_key, ascp_binary, output):
    failed = 0
    for url in filter(None, (value.strip() for value in url_pair.split(";"))):
        parsed = urlsplit(url if "://" in url else "ftp://" + url)
        if parsed.hostname != "ftp.sra.ebi.ac.uk" or not parsed.path.startswith("/vol1/"):
            print("Unsupported ENA FASTQ URL: " + url, file=sys.stderr)
            failed += 1
            continue
        remote = "era-fasp@fasp.sra.ebi.ac.uk:" + parsed.path
        command = [ascp_binary, "-QT", "-l", "300m", "-P33001", "-k1", "-i", ascp_key, remote, "."]
        try:
            subprocess.run(command, cwd=output, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"Download failed for {parsed.path}: {exc}", file=sys.stderr)
            failed += 1
    return failed


def main(argv=None):
    args = parse_args(argv)
    output = Path(args.output).expanduser().resolve()
    try:
        # Resolve input before creating the output directory; keep the caller's cwd.
        with Path(args.input).expanduser().open(encoding="utf-8-sig", newline="") as stream:
            rows = csv.reader(stream, delimiter="\t")
            header = next(rows)
            column = args.column if args.column is not None else header.index("fastq_ftp")
            urls = [row[column].strip() for row in rows if row and any(row)]
        urls = [url for url in urls if url]
        if not urls:
            raise ValueError("No FASTQ URLs found in the input table")
        output.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError, IndexError, StopIteration) as exc:
        print(f"Cannot read input or create output: {exc}", file=sys.stderr)
        return 1
    key = str(Path(args.ascp_key).expanduser().resolve())
    binary = str(Path(args.ascp_binary).expanduser().resolve()) if ("/" in args.ascp_binary or "\\" in args.ascp_binary) else args.ascp_binary
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        jobs = [executor.submit(download_with_ascp, url, key, binary, str(output)) for url in urls]
        failed = sum(job.result() for job in jobs)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
