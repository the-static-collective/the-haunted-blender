"""Local command door for experimental ART × I × FACT constructors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import construction


def main():
    parser = argparse.ArgumentParser(prog="haunted-construction")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("accept", "plan", "render"):
        command = commands.add_parser(name)
        command.add_argument("root", type=Path)
        if name == "accept":
            command.add_argument("source_artifact_snapshot", type=Path)
            command.add_argument("steps_json", type=Path)
            command.add_argument("--intent", required=True)
            command.add_argument("--approve", action="store_true")
        else:
            command.add_argument("recipe_snapshot", type=Path)
            if name == "render":
                command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "accept":
        steps = json.loads(args.steps_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        result = construction.accept(args.root, args.source_artifact_snapshot,
                                     args.intent, steps, filmmaker_approval=args.approve)
    elif args.command == "plan":
        result = construction.plan(args.root, args.recipe_snapshot)
    else:
        result = construction.render_recipe(args.root, args.recipe_snapshot, args.out)
    print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
