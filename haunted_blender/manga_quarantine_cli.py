"""Quarantine release doors. No command creates or infers an asset grant."""
import argparse
from pathlib import Path

from . import mangalize as m, manga_quarantine as q


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-quarantine")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("quarantine")
    p.add_argument("source_root", type=Path)
    p.add_argument("ancestor_event", type=Path)
    p.add_argument("output", type=Path)
    p = sub.add_parser("select")
    p.add_argument("quarantine", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--candidate", action="append", required=True)
    p.add_argument("--authority-ref", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--ancestor-event", type=Path, required=True)
    p.add_argument("--trace", type=Path)
    for command in ("promote", "verify"):
        p = sub.add_parser(command)
        p.add_argument("quarantine", type=Path)
        p.add_argument("selection", type=Path)
        p.add_argument("grant", type=Path)
        p.add_argument("source_root", type=Path)
        p.add_argument("ancestor_event", type=Path)
        p.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "quarantine":
            record = q.quarantine_set(args.source_root, args.ancestor_event)
            m.persist(args.output, record)
            print(record["quarantineSetHash"])
        elif args.command == "select":
            record = m.read(args.quarantine)
            q.verify_quarantine(args.source_root, args.ancestor_event, record)
            selection = q.select(record, asset_ids=args.candidate, authority_ref=args.authority_ref, reason=args.reason)
            m.persist(args.output, selection)
            if args.trace:
                m.persist(args.trace, q.trace(record, selection).encode())
            print(selection["selectionHash"])
            print("SELECTION READY — GRANT REQUIRED; no creative admission")
        else:
            record, selection, grant = (m.read(p) for p in (args.quarantine, args.selection, args.grant))
            result = (q.verify if args.command == "verify" else q.execute)(
                args.source_root, args.ancestor_event, record, selection, grant, args.output)
            print(result if isinstance(result, str) else result["promotionHash"])
        print(f"MANGALIZE-002: PASS ({args.command})")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"MANGALIZE-002: REFUSE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
