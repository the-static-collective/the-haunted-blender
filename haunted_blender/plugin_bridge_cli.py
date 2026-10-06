from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import plugin_bridge


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-plugin-bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    pending = sub.add_parser("pending")
    pending.add_argument("root")

    show = sub.add_parser("show")
    show.add_argument("root")
    show.add_argument("call_sha256")

    claim = sub.add_parser("claim")
    claim.add_argument("root")
    claim.add_argument("call_sha256")
    claim.add_argument("--claimed-at")
    claim.add_argument("--actor", default="external-plugin-orchestrator")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("root")
    resolve.add_argument("call_sha256")
    resolve.add_argument("result_json")
    resolve.add_argument("--resolved-at")
    resolve.add_argument("--raw-reference")

    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()

    if args.command == "pending":
        result = plugin_bridge.pending(root)
    elif args.command == "show":
        path = root / "cockpit-plugin-bridge" / "outbox" / f"{args.call_sha256}.json"
        result = json.loads(path.read_text(encoding="utf-8"))
    elif args.command == "claim":
        result = plugin_bridge.claim(
            root,
            args.call_sha256,
            claimed_at=args.claimed_at or datetime.now(timezone.utc).isoformat(),
            actor=args.actor,
        )
    else:
        normalized = json.loads(
            Path(args.result_json).expanduser().resolve(strict=True).read_text(encoding="utf-8")
        )
        result = plugin_bridge.resolve(
            root,
            args.call_sha256,
            result=normalized,
            resolved_at=args.resolved_at or datetime.now(timezone.utc).isoformat(),
            raw_reference=args.raw_reference,
        )

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
