"""Download the entries in a personal Synapse download list."""
import argparse
import csv
import os
from pathlib import Path
import sys


def main(argv=None, client=None):
    parser = argparse.ArgumentParser(description="Download your personal Synapse download list")
    parser.add_argument("--output", default="./downloaded_data")
    args = parser.parse_args(argv)
    auth_token = os.environ.get("SYNAPSE_AUTH_TOKEN")
    if not auth_token:
        parser.error("Set SYNAPSE_AUTH_TOKEN before running this script")
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    if client is None:
        import synapseclient
        client = synapseclient.Synapse(cache_root_dir=str(output))
    client.login(authToken=auth_token)
    manifest = client.get_download_list_manifest()
    failed = 0
    with open(manifest, newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            try:
                version = int(row["versionNumber"]) if row.get("versionNumber") else None
                downloaded = client.get(row["ID"], version=version, downloadLocation=str(output), ifcollision="overwrite.local")
                print(f"Downloaded: {downloaded.path}")
            except Exception as exc:
                print(f"Download failed for {row.get('ID', 'unknown')}: {exc}", file=sys.stderr)
                failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
