from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dreambreeder import (
    admit_ghost,
    create_ecology,
    keep_proposal,
    recombine,
    resolve_descendant,
    scrape_ecology,
)


def read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(value: object, path: str | None) -> None:
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(data, encoding="utf-8")
    else:
        print(data, end="")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="haunted-blender-dream")
    sub = p.add_subparsers(dest="command", required=True)

    grow = sub.add_parser("grow")
    grow.add_argument("--relation", required=True)
    grow.add_argument("--checkpoint", required=True)
    grow.add_argument("--receipt", action="append", required=True)
    grow.add_argument("--donor", action="append", default=[])
    grow.add_argument("--generation", type=int, default=1)
    grow.add_argument("--out")

    keep = sub.add_parser("keep")
    keep.add_argument("ecology")
    keep.add_argument("proposal")
    keep.add_argument("--out")

    scrape = sub.add_parser("scrape")
    scrape.add_argument("ecology")
    scrape.add_argument("--out")

    ghost = sub.add_parser("haunt")
    ghost.add_argument("ecology")
    ghost.add_argument("proposal")
    ghost.add_argument("--note", default="")
    ghost.add_argument("--out")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("descendant")
    resolve.add_argument("--receipt", required=True)
    resolve.add_argument("--performance", required=True)
    resolve.add_argument("--out")

    child = sub.add_parser("recombine")
    child.add_argument("left")
    child.add_argument("right")
    child.add_argument("--label", required=True)
    child.add_argument("--ghost", action="append", default=[])
    child.add_argument("--out")

    args = p.parse_args(argv)
    if args.command == "grow":
        result = create_ecology(
            relation_id=args.relation,
            common_checkpoint_id=args.checkpoint,
            source_receipt_ids=args.receipt,
            generation=args.generation,
            donor_ids=args.donor,
        )
    elif args.command == "keep":
        result = keep_proposal(read(args.ecology), args.proposal)
    elif args.command == "scrape":
        result = scrape_ecology(read(args.ecology))
    elif args.command == "haunt":
        result = admit_ghost(read(args.ecology), args.proposal, local_note=args.note)
    elif args.command == "resolve":
        result = resolve_descendant(
            read(args.descendant), receipt_id=args.receipt, performance_id=args.performance
        )
    else:
        ghosts = [read(path) for path in args.ghost]
        result = recombine(read(args.left), read(args.right), local_label=args.label, ghost_influences=ghosts)
    write(result, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
