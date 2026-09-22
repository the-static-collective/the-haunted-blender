"""N3 optional local living-mesh cartridge; no changes to N0/N1/N2 command doors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import living_mesh


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="haunted-living-mesh",
        description="Artist-authored 5x5 triangle mesh from frozen N2 geometry",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("example-grid")
    init.add_argument("--out", type=Path, required=True,
                      help="Write a new local JSON 5x5 grid template, never overwrite")
    create = sub.add_parser("create")
    create.add_argument("root", type=Path)
    create.add_argument("correspondence_snapshot", type=Path)
    create.add_argument("vertices_json", type=Path,
                        help="Private JSON object with target 25 normalized vertices and optional source vertices")
    create.add_argument("--max-landmark-error-px", type=float, default=3.0)
    create.add_argument("--revises", help="Previous N3 recipe ID; creates a distinct revision")
    for name in ("freeze", "plan", "render"):
        action = sub.add_parser(name)
        action.add_argument("root", type=Path)
        action.add_argument("recipe_id" if name == "freeze" else "snapshot")
        if name == "render":
            action.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "example-grid":
        template = {"source": living_mesh.grid(), "target": living_mesh.grid()}
        out = args.out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as file:
            file.write(json.dumps(template, indent=2) + "\n")
        result = {"template": str(out), "note": "Move only interior target points to add local deformation"}
    elif args.command == "create":
        data = json.loads(args.vertices_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) not in ({"target"}, {"source", "target"}):
            raise ValueError("Vertex JSON must contain target and optional source, nothing else")
        result = living_mesh.create(
            args.root, args.correspondence_snapshot,
            target_vertices=data["target"], source_vertices=data.get("source"),
            max_landmark_error_px=args.max_landmark_error_px, revises=args.revises,
        )
    elif args.command == "freeze":
        result = {"snapshot": str(living_mesh.freeze(args.root, args.recipe_id))}
    elif args.command == "plan":
        result = living_mesh.plan(args.root, Path(args.snapshot))
    else:
        result = living_mesh.render(args.root, Path(args.snapshot), args.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
