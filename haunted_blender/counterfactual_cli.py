"""Experimental door for comparing and rendering two accepted audience cuts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import counterfactual


def main():
    parser = argparse.ArgumentParser(prog="haunted-counterfactual")
    commands = parser.add_subparsers(dest="command", required=True)
    accept = commands.add_parser("accept")
    accept.add_argument("root", type=Path)
    accept.add_argument("cut_a", type=Path, help="First accepted Scene Artifact snapshot")
    accept.add_argument("cut_b", type=Path, help="Second accepted Scene Artifact snapshot")
    accept.add_argument("--approve", action="store_true", help="Approve this private preview pairing")
    render = commands.add_parser("render")
    render.add_argument("root", type=Path)
    render.add_argument("pair_snapshot", type=Path)
    render.add_argument("--out-a", type=Path, required=True)
    render.add_argument("--out-b", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "accept":
        result = counterfactual.accept(args.root, args.cut_a, args.cut_b,
                                       filmmaker_approval=args.approve)
    else:
        result = counterfactual.render_pair(args.root, args.pair_snapshot,
                                            args.out_a, args.out_b)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
