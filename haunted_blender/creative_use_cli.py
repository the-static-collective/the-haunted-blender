"""Record and compare independently accepted uses of the same material bytes."""
import argparse
import json
from pathlib import Path

from . import creative_use


def main():
    parser = argparse.ArgumentParser(prog="haunted-creative-use")
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record")
    record.add_argument("root", type=Path)
    record.add_argument("artifact_snapshot", type=Path)
    record.add_argument("take_acceptance", type=Path)
    record.add_argument("--role", required=True)
    record.add_argument("--intent", required=True)
    compare = commands.add_parser("compare")
    compare.add_argument("root", type=Path)
    compare.add_argument("first_use", type=Path)
    compare.add_argument("second_use", type=Path)
    args = parser.parse_args()
    if args.command == "record":
        result = creative_use.record(args.root, args.artifact_snapshot,
                                     args.take_acceptance, role=args.role, intent=args.intent)
    else:
        result = creative_use.compare(args.root, args.first_use, args.second_use)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
