"""Separate CLI for experimental N1. Existing N0 command door and film schema remain unchanged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import alchemy


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="haunted-alchemy",
        description="Local alchemical compiler (artist-proposed relations, deterministic still transitions)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("root", type=Path)
    create.add_argument("source_asset_id")
    create.add_argument("target_asset_id")
    create.add_argument("--bridge", help="Required for a triadic-bridge relation")
    create.add_argument("--relation", choices=tuple(alchemy.RELATIONS), default="shape-echo")
    create.add_argument("--order", help="Comma-separated role order; each role exactly once")
    create.add_argument("--statement", default="Artist-proposed visual relationship")

    for name in ("freeze", "plan", "render"):
        action = sub.add_parser(name)
        action.add_argument("root", type=Path)
        action.add_argument("recipe_id" if name == "freeze" else "snapshot", type=str)
        if name == "render":
            action.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "create":
        result = alchemy.create(
            args.root, args.source_asset_id, args.target_asset_id,
            bridge=args.bridge, relation=args.relation,
            order=args.order.split(",") if args.order else None,
            statement=args.statement,
        )
    elif args.command == "freeze":
        result = {"snapshot": str(alchemy.freeze(args.root, args.recipe_id))}
    elif args.command == "plan":
        result = alchemy.plan(args.root, Path(args.snapshot))
    else:
        result = alchemy.render(args.root, Path(args.snapshot), args.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
