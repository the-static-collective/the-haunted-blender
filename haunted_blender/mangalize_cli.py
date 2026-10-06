"""First-class MANGALIZE command door. Convenience preserves event custody."""
import argparse
from pathlib import Path

from . import mangalize as m


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-mangalize")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("request", "smash"):
        p = sub.add_parser(name)
        p.add_argument("handoff", type=Path)
        p.add_argument("output", type=Path)
        p.add_argument("--page", required=True)
        p.add_argument("--page-manifest", required=True, type=Path)
        p.add_argument("--evidence-root", required=True, type=Path)
        p.add_argument("--target", choices=sorted(m.TARGETS), default="page-quarry")
        p.add_argument("--operation", choices=sorted(m.OPERATIONS), action="append")
        p.add_argument("--requesting-authority", required=True)
        p.add_argument("--source-repository", default="the-static-collective/lemonPRESS")
        p.add_argument("--source-commit")
        p.add_argument("--source-grant", type=Path, action="append", default=[])
        if name == "smash":
            p.add_argument("--allow", choices=sorted(m.OPERATIONS), action="append", required=True)
            p.add_argument("--admitting-authority", required=True)
    p = sub.add_parser("admit")
    p.add_argument("request", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--evidence-root", required=True, type=Path)
    p.add_argument("--allow", choices=sorted(m.OPERATIONS), action="append", required=True)
    p.add_argument("--authority-ref", required=True)
    for name in ("execute", "verify"):
        p = sub.add_parser(name)
        p.add_argument("request", type=Path)
        p.add_argument("admission", type=Path)
        p.add_argument("source_pages", type=Path)
        p.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in ("request", "smash"):
            request = m.make_request(args.evidence_root, args.handoff, args.page_manifest, page_id=args.page, target=args.target,
                operations=args.operation or ("harvest", "reuse", "derive"), authority_ref=args.requesting_authority,
                source_repository=args.source_repository, source_commit=args.source_commit, grant_paths=args.source_grant)
            m.verify_request(args.evidence_root, request)
            if args.command == "request":
                m.persist(args.output, request)
            else:
                admission = m.decide(request, allow=args.allow, authority_ref=args.admitting_authority)
                if admission["decision"] == "refused":
                    m.persist(args.output / "mangalize.request.json", request)
                    m.persist(args.output / "mangalize.admission.json", admission)
                    raise ValueError(admission["reason"])
                returned = m.execute(args.evidence_root, request, admission, args.output)
                print(returned["returnHash"])
        elif args.command == "admit":
            request = m.read(args.request)
            m.verify_request(args.evidence_root, request)
            admission = m.decide(request, allow=args.allow, authority_ref=args.authority_ref)
            m.persist(args.output, admission)
            if admission["decision"] == "refused":
                raise ValueError(admission["reason"])
        else:
            request, admission = m.read(args.request), m.read(args.admission)
            result = (m.verify if args.command == "verify" else m.execute)(args.source_pages, request, admission, args.output)
            print(result if isinstance(result, str) else result["returnHash"])
        print(f"MANGALIZE: PASS ({args.command})")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"MANGALIZE: REFUSE: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
