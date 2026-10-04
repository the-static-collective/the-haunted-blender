"""N2 only: manually selected normalized image landmarks -> independent film preview."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import correspondence


def main() -> None:
    p = argparse.ArgumentParser(prog="haunted-correspondence",
                                description="Experimental local artist-controlled 2D correspondence renderer")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("create")
    c.add_argument("root", type=Path)
    c.add_argument("alchemy_snapshot", type=Path)
    c.add_argument("points_json", type=Path, help="Local JSON array of {id,from:[u,v],to:[u,v]}")
    c.add_argument("--from-role")
    c.add_argument("--to-role")
    c.add_argument("--max-error-px", type=float, default=2.0)
    c.add_argument("--revises", help="Previous correspondence recipe ID; a new recipe is created, never overwritten")
    for name in ("freeze", "plan", "render"):
        item = sub.add_parser(name)
        item.add_argument("root", type=Path)
        item.add_argument("recipe_id" if name == "freeze" else "snapshot")
        if name == "render":
            item.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.command == "create":
        points = json.loads(a.points_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        result = correspondence.create(a.root, a.alchemy_snapshot, points,
                                       from_role=a.from_role, to_role=a.to_role,
                                       max_error_px=a.max_error_px, revises=a.revises)
    elif a.command == "freeze":
        result = {"snapshot": str(correspondence.freeze(a.root, a.recipe_id))}
    elif a.command == "plan":
        result = correspondence.plan(a.root, Path(a.snapshot))
    else:
        result = correspondence.render(a.root, Path(a.snapshot), a.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
