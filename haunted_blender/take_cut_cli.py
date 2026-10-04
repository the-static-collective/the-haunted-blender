"""Render one accepted moving take into an otherwise static private cut."""
import argparse
import json
from pathlib import Path

from . import take_cut


def main():
    parser = argparse.ArgumentParser(prog="haunted-take-cut")
    parser.add_argument("root", type=Path)
    parser.add_argument("artifact_snapshot", type=Path)
    parser.add_argument("take_acceptance", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(take_cut.render(args.root, args.artifact_snapshot,
                                     args.take_acceptance, args.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
