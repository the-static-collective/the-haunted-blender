"""Local-only command door. No external service calls, no implicit uploads."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import catalog, project, render


def main() -> None:
    p = argparse.ArgumentParser(prog="haunted-blender", description="Haunted Blender experimental nuclear scaffold")
    sub = p.add_subparsers(dest="command", required=True)
    def action(name: str, *args: str) -> argparse.ArgumentParser:
        q = sub.add_parser(name)
        q.add_argument("root", type=Path)
        for a in args:
            q.add_argument(a)
        return q
    action("init")
    scan = action("scan", "folder")
    scan.add_argument("--note", help="Optional informational tag; no upload", default="")
    action("stats")
    search = action("find")
    search.add_argument("--query", default="")
    search.add_argument("--kind", choices=("raw", "image", "audio", "video"))
    search.add_argument("--limit", type=int, default=50)
    action("inspect", "asset_id")
    check = action("verify")
    check.add_argument("--limit", type=int, default=50)
    action("derivative", "raw_id", "image_path")
    action("new-film", "title")
    action("new-scene", "film_id", "title")
    shot = action("add-shot", "film_id", "scene_id", "asset_id")
    shot.add_argument("--seconds", type=float, default=4)
    shot.add_argument("--direction", default="")
    action("freeze", "film_id")
    action("plan", "snapshot")
    r = action("render", "snapshot")
    r.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    root = a.root.expanduser().resolve()
    if a.command == "init":
        result = {"initialized": str(catalog.init(root))}
    elif a.command == "scan":
        result = catalog.scan(root, Path(a.folder))
    elif a.command == "stats":
        result = catalog.stats(root)
    elif a.command == "find":
        result = catalog.find(root, a.query, a.kind, a.limit)
    elif a.command == "inspect":
        result = catalog.inspect(root, a.asset_id)
    elif a.command == "verify":
        result = catalog.verify(root, a.limit)
    elif a.command == "derivative":
        result = {"image_asset_id": catalog.derivative(root, a.raw_id, Path(a.image_path))}
    elif a.command == "new-film":
        result = project.new_film(root, a.title)
    elif a.command == "new-scene":
        result = project.add_scene(root, a.film_id, a.title)
    elif a.command == "add-shot":
        result = project.add_shot(root, a.film_id, a.scene_id, a.asset_id, round(a.seconds * 1000), a.direction)
    elif a.command == "freeze":
        result = {"snapshot": str(project.freeze(root, a.film_id))}
    elif a.command == "plan":
        result = render.plan(root, Path(a.snapshot))
    elif a.command == "render":
        result = render.render(root, Path(a.snapshot), a.out)
    else:
        p.error("Unsupported command")
        return
    print(json.dumps(result, indent=2, ensure_ascii=False))
