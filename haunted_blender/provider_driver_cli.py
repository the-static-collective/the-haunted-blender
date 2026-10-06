from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import provider_driver


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-provider-driver")
    sub = parser.add_subparsers(dest="command", required=True)

    configure = sub.add_parser("configure")
    configure.add_argument("root")
    configure.add_argument("config_json")

    view = sub.add_parser("view")
    view.add_argument("root")
    view.add_argument("section_id")

    drive = sub.add_parser("drive")
    drive.add_argument("root")
    drive.add_argument("section_id")
    drive.add_argument("--max-steps", type=int, default=12)

    approve = sub.add_parser("approve")
    approve.add_argument("root")
    approve.add_argument("section_id")
    approve.add_argument("--usd-micros", type=int, required=True)
    approve.add_argument("--approved-at")

    decline = sub.add_parser("decline")
    decline.add_argument("root")
    decline.add_argument("section_id")
    decline.add_argument("--reason", default="")

    accept = sub.add_parser("accept")
    accept.add_argument("root")
    accept.add_argument("section_id")
    accept.add_argument("candidate_path")

    args = parser.parse_args(argv)
    if args.command == "configure":
        root = Path(args.root).expanduser().resolve()
        path = Path(args.config_json)
        if not path.is_absolute():
            path = root / path
        path = path.expanduser().resolve(strict=True)
        body = json.loads(path.read_text(encoding="utf-8"))
        adapters = body.get("adapters") if isinstance(body, dict) else body
        result = provider_driver.configure_adapters(root, adapters)
    elif args.command == "view":
        result = provider_driver.provider_view(args.root, args.section_id)
    elif args.command == "drive":
        result = provider_driver.drive(args.root, args.section_id, max_steps=args.max_steps)
    elif args.command == "approve":
        result = provider_driver.approve_spend(
            args.root,
            args.section_id,
            expected_usd_micros=args.usd_micros,
            approved_at=args.approved_at or datetime.now(timezone.utc).isoformat(),
        )
    elif args.command == "decline":
        result = provider_driver.decline_current_candidate(
            args.root, args.section_id, reason=args.reason
        )
    else:
        result = provider_driver.accept_candidate(
            args.root, args.section_id, args.candidate_path
        )

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
