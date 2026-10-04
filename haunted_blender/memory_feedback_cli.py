"""Render observer-local memory residue over one accepted moving take."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import memory_feedback


def _load(path):
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(prog="haunted-memory-feedback")
    parser.add_argument("root", type=Path)
    parser.add_argument("artifact_snapshot", type=Path)
    parser.add_argument("take_acceptance", type=Path)
    parser.add_argument("memory_plan", type=Path,
                        help="JSON object with timeline and regions")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    plan = _load(args.memory_plan)
    if set(plan) != {"timeline", "regions"}:
        parser.error("memory plan must contain timeline and regions only")
    result = memory_feedback.render(
        args.root, args.artifact_snapshot, args.take_acceptance,
        plan["timeline"], plan["regions"], args.out)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
