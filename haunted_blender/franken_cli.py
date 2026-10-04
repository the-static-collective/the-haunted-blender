from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cutout_stage import render_cutout
from .flow_pantry import index_flow_folder
from .playdeck_bridge import flow_to_playdeck
from .toaster_bridge import plan_toaster_vspantry


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(value: dict, path: str | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="haunted-blender-franken")
    sub = parser.add_subparsers(dest="command", required=True)

    flow = sub.add_parser("index-flow")
    flow.add_argument("folder")
    flow.add_argument("--out")
    flow.add_argument("--no-probe", action="store_true")

    deck = sub.add_parser("plan-playdeck")
    deck.add_argument("manifest")
    deck.add_argument("--deck-id", default="flow-pantry")
    deck.add_argument("--title", default="Flow Pantry")
    deck.add_argument("--out")

    toaster = sub.add_parser("plan-toaster")
    toaster.add_argument("manifest")
    toaster.add_argument("--out")

    cutout = sub.add_parser("render-cutout")
    cutout.add_argument("plan")
    cutout.add_argument("output")
    cutout.add_argument("--receipt")

    args = parser.parse_args(argv)
    if args.command == "index-flow":
        _write(index_flow_folder(args.folder, probe=not args.no_probe), args.out)
    elif args.command == "plan-playdeck":
        _write(
            flow_to_playdeck(_read_json(args.manifest), deck_id=args.deck_id, title=args.title),
            args.out,
        )
    elif args.command == "plan-toaster":
        _write(plan_toaster_vspantry(_read_json(args.manifest)), args.out)
    else:
        _write(render_cutout(_read_json(args.plan), args.output), args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
