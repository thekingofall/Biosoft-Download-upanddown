#!/usr/bin/env python3
"""Launch a download tool from the combined repository."""
import argparse
from pathlib import Path
import subprocess
import sys

TOOLS = {
    "aspera": "aspera/Ascp_down.py",
    "novogene": "novogene/run.py",
    "synapse": "synapse/download_synapse_safe.py",
    "synapse-legacy": "synapse/legacy/download_synapse_legacy.py",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="ENA / Aspera, Novogene and Synapse download tools")
    parser.add_argument("tool", choices=TOOLS)
    parser.add_argument("tool_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    script = Path(__file__).resolve().parent / TOOLS[args.tool]
    return subprocess.call([sys.executable, str(script), *args.tool_args])


if __name__ == "__main__":
    sys.exit(main())
