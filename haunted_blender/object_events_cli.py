"""N6 isolated event graph command door; N0-N5 commands are unchanged."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import object_events


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="haunted-object-events",
        description="Declare birth/death/split/join visibility over a frozen N5 multi-part object",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("root", type=Path)
    create.add_argument("living_object_snapshot", type=Path)
    create.add_argument("events_json", type=Path, help="Private JSON object with parts and events")
    create.add_argument("--revises", help="An earlier N6 recipe ID; creates a separate immutable revision")
    for name in ("freeze", "plan", "render"):
        item = sub.add_parser(name)
        item.add_argument("root", type=Path)
        item.add_argument("recipe_id" if name == "freeze" else "snapshot")
        if name == "render":
            item.add_argument("--out", required=True, type=Path)
            item.add_argument("--alpha-out", type=Path,
                              help="Optional independent transparent midpoint RGBA PNG")
    args = parser.parse_args()
    if args.command == "create":
        payload = json.loads(args.events_json.expanduser().resolve(strict=True).read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"parts", "events"}:
            raise ValueError("Events JSON must contain exactly parts and events")
        result = object_events.create(
            args.root, args.living_object_snapshot,
            payload["parts"], payload["events"], revises=args.revises,
        )
    elif args.command == "freeze":
        result = {"snapshot": str(object_events.freeze(args.root, args.recipe_id))}
    elif args.command == "plan":
        result = object_events.plan(args.root, Path(args.snapshot))
    else:
        result = object_events.render(
            args.root, Path(args.snapshot), args.out, alpha_preview_out=args.alpha_out,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
