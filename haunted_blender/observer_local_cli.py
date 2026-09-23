"""Run the observer-local door matrix or one memory-carrying camera projection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import observer_local


def _load(path):
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(prog="haunted-observer-local")
    parser.add_argument("scenario", type=Path,
                        help="JSON with world plus observers")
    parser.add_argument("--beat", type=int, required=True)
    parser.add_argument("--door", required=True, help="threshold id")
    parser.add_argument("--open", type=float, nargs="+", required=True,
                        dest="openness")
    parser.add_argument("--observer", help="run one observer instead of a matrix")
    parser.add_argument("--prior", type=Path, help="prior memory receipt JSON")
    args = parser.parse_args()

    scenario = _load(args.scenario)
    world = scenario["world"]
    observers = scenario["observers"]
    if args.observer:
        matches = [x for x in observers if x.get("id") == args.observer]
        if len(matches) != 1:
            parser.error("--observer must name exactly one scenario observer")
        if len(args.openness) != 1:
            parser.error("single-observer mode requires exactly one --open value")
        prior = _load(args.prior) if args.prior else None
        result = observer_local.project(
            world, args.beat, matches[0], {args.door: args.openness[0]}, prior)
    else:
        if args.prior:
            parser.error("--prior is only valid with --observer")
        result = observer_local.door_matrix(
            world, args.beat, observers, args.door, args.openness)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
