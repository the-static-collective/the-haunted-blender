"""Explicit composition doors. No command mints performed-use admission."""
import argparse
from pathlib import Path

from . import mangalize as m, manga_performed_use as use


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-performed-use")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("role", "placement", "compose", "verify"):
        p = sub.add_parser(command)
        p.add_argument("source_root", type=Path)
        p.add_argument("ancestor_event", type=Path)
        p.add_argument("released_event", type=Path)
        p.add_argument("output", type=Path)
        if command == "role":
            p.add_argument("--asset", required=True)
            p.add_argument("--role", choices=use.ROLES, required=True)
        elif command == "placement":
            p.add_argument("--role-proposal", type=Path, required=True)
            p.add_argument("--geometry", type=Path, required=True)
        else:
            # Each directory must contain three separate canonical artifacts.
            p.add_argument("--use", type=Path, action="append", required=True)
        if command in ("role", "placement"):
            p.add_argument("--authority-ref", required=True)
            p.add_argument("--rationale", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("compose", "verify"):
            bundles = [{kind: m.read(path / (kind + ".json")) for kind in ("role", "placement", "admission")} for path in args.use]
            result = (use.verify if args.command == "verify" else use.execute)(
                args.source_root, args.ancestor_event, args.released_event, bundles, args.output)
            print(result if isinstance(result, str) else result["layoutHash"])
        else:
            drawer = use.verified_drawer(args.source_root, args.ancestor_event, args.released_event)
            if args.command == "role":
                result = use.role_proposal(drawer, asset_id=args.asset, role=args.role, rationale=args.rationale, authority_ref=args.authority_ref)
            else:
                result = use.placement_proposal(drawer, m.read(args.role_proposal), placement=m.read(args.geometry),
                    rationale=args.rationale, authority_ref=args.authority_ref)
            m.persist(args.output, result)
            print(result[use.HASH_KEYS[args.command]])
            print("PERFORMED USE READY — ADMISSION REQUIRED")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"MANGALIZE-003: REFUSE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
