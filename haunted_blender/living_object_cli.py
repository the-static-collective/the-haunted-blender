"""N5 local multi-part object CLI. Existing N0-N4 command doors stay unchanged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import living_object


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="haunted-living-object",
        description="Compose 2-4 independent frozen N4 foregrounds into a local cinematic object",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("create")
    c.add_argument("root", type=Path)
    c.add_argument("layers_json", type=Path,
                   help="Private JSON array of named N4 snapshot, z, delay_frames, and opacity")
    c.add_argument("--revises", help="Existing N5 recipe ID; writes a separate immutable revision")
    for name in ("freeze", "plan", "render"):
        item = sub.add_parser(name)
        item.add_argument("root", type=Path)
        item.add_argument("recipe_id" if name == "freeze" else "snapshot")
        if name == "render":
            item.add_argument("--out", required=True, type=Path)
            item.add_argument("--alpha-out", type=Path,
                              help="Optional lossless transparent RGBA midpoint PNG separate from opaque MP4")
    args = parser.parse_args()
    if args.command == "create":
        layers = json.loads(args.layers_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        result = living_object.create(args.root, layers, revises=args.revises)
    elif args.command == "freeze":
        result = {"snapshot": str(living_object.freeze(args.root, args.recipe_id))}
    elif args.command == "plan":
        result = living_object.plan(args.root, Path(args.snapshot))
    else:
        result = living_object.render(args.root, Path(args.snapshot), args.out,
                                      alpha_preview_out=args.alpha_out)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
