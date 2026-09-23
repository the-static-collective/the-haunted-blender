"""Local experimental time-slice renderer."""
import argparse
import json
from pathlib import Path

from . import time_slice


def main():
    parser = argparse.ArgumentParser(prog="haunted-time-slice")
    parser.add_argument("root", type=Path)
    parser.add_argument("artifact_snapshot", type=Path)
    parser.add_argument("take_acceptance", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(time_slice.render(args.root, args.artifact_snapshot,
                                       args.take_acceptance, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
