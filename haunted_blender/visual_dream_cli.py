"""Freeze, inspect and render the local visual dream experiment."""
import argparse
import json
from pathlib import Path

from . import visual_dream


def main():
    parser = argparse.ArgumentParser(prog="haunted-visual-dream")
    parser.add_argument("root", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    freezing = commands.add_parser("freeze")
    freezing.add_argument("score_json", type=Path)
    planning = commands.add_parser("plan")
    planning.add_argument("score_snapshot", type=Path)
    rendering = commands.add_parser("render")
    rendering.add_argument("score_snapshot", type=Path)
    rendering.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        score = json.loads(args.score_json.read_text(encoding="utf-8"))
        result = {"score_snapshot": str(visual_dream.freeze(args.root, score))}
    elif args.command == "plan":
        result = visual_dream.plan(args.root, args.score_snapshot)
    else:
        result = visual_dream.render(args.root, args.score_snapshot, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
