"""Local-only command door for verified Blender -> Toaster Pantry Exchange."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pantry_exchange import export_alchemy


def main() -> None:
    parser = argparse.ArgumentParser(prog="haunted-blender-exchange")
    parser.add_argument("root", type=Path, help="Existing local Blender library")
    parser.add_argument("snapshot", type=Path, help="Frozen alchemy snapshot")
    parser.add_argument("video", type=Path, help="Actual completed alchemy MP4")
    parser.add_argument("--out", required=True, type=Path, help="Local exchange JSON destination")
    args = parser.parse_args()
    print(json.dumps(export_alchemy(args.root, args.snapshot, args.video, args.out), indent=2))


if __name__ == "__main__":
    main()
