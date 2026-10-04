"""Independent experimental door: SceneWorld -> approved artifact -> N0 silent MP4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import scene_artifact


def main():
    parser = argparse.ArgumentParser(prog="haunted-scene-artifact")
    commands = parser.add_subparsers(dest="command", required=True)
    accept = commands.add_parser("accept")
    accept.add_argument("root", type=Path)
    accept.add_argument("world_snapshot", type=Path)
    accept.add_argument("alchemy_snapshot", type=Path)
    accept.add_argument("selections_json", type=Path,
                        help="Array of {beat: int, role: str, candidate: 'wide'}")
    accept.add_argument("--approve", action="store_true",
                        help="Explicitly accept this private local-preview treatment")
    render = commands.add_parser("render")
    render.add_argument("root", type=Path)
    render.add_argument("artifact_snapshot", type=Path)
    render.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "accept":
        selections = json.loads(args.selections_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        result = scene_artifact.accept(args.root, args.world_snapshot,
                                       args.alchemy_snapshot, selections,
                                       filmmaker_approval=args.approve)
    else:
        result = scene_artifact.render_accepted(args.root, args.artifact_snapshot, args.out)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
