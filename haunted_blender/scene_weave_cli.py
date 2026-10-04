"""Separate optional command door for the experimental Cinematic Relationship Engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import scene_weave as weave


def read(path):
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(prog="haunted-scene-weave")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("seed", "freeze", "compose", "branch", "approve"):
        action = commands.add_parser(name)
        action.add_argument("root", type=Path)
        if name == "seed":
            action.add_argument("alchemy_snapshot", type=Path)
            action.add_argument("story_json", type=Path)
        elif name == "freeze":
            action.add_argument("world_id")
        else:
            action.add_argument("world_snapshot", type=Path)
            if name == "compose":
                action.add_argument("--beat", type=int, required=True)
            elif name == "branch":
                action.add_argument("--source-fact", required=True)
                action.add_argument("--new-fact-json", type=Path, required=True)
                action.add_argument("--out", type=Path, required=True)
            else:
                action.add_argument("proposal_json", type=Path)
                action.add_argument("--approve", action="store_true")
    args = parser.parse_args()
    if args.command == "seed":
        result = weave.from_alchemy(args.root, args.alchemy_snapshot, read(args.story_json))
    elif args.command == "freeze":
        result = {"world_snapshot": str(weave.freeze(args.root, args.world_id))}
    elif args.command == "compose":
        result = weave.compose(weave.load_snapshot(args.root, args.world_snapshot), args.beat)
    elif args.command == "branch":
        world = weave.load_snapshot(args.root, args.world_snapshot)
        result = weave.propose_branch(world, source_fact_id=args.source_fact,
                                      new_fact=read(args.new_fact_json))
        out = args.out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    else:
        world = weave.load_snapshot(args.root, args.world_snapshot)
        descendant = weave.approve_branch(world, read(args.proposal_json),
                                          filmmaker_approval=args.approve)
        path = weave.save_child(args.root, descendant)
        result = {"world_id": descendant["id"], "path": str(path),
                  "parent_sha256": descendant["parent_sha256"]}
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
