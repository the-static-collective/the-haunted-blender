from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dream_cutout_compiler import compile_proposal, render_sixup


def read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="haunted-blender-dream-cutout")
    sub = p.add_subparsers(dest="command", required=True)

    compile_one = sub.add_parser("compile")
    compile_one.add_argument("ecology")
    compile_one.add_argument("proposal")
    compile_one.add_argument("kit")
    compile_one.add_argument("--duration", type=float, default=2.0)
    compile_one.add_argument("--fps", type=int, default=12)
    compile_one.add_argument("--donor-freeze")
    compile_one.add_argument("--out", required=True)

    sixup = sub.add_parser("sixup")
    sixup.add_argument("ecology")
    sixup.add_argument("kit")
    sixup.add_argument("output_dir")
    sixup.add_argument("--duration", type=float, default=2.0)
    sixup.add_argument("--fps", type=int, default=12)
    sixup.add_argument(
        "--donor-map",
        help="JSON object mapping DREAMBREEDER donor ids to local video paths.",
    )

    args = p.parse_args(argv)
    if args.command == "compile":
        result = compile_proposal(
            read(args.ecology),
            args.proposal,
            read(args.kit),
            duration=args.duration,
            fps=args.fps,
            donor_freeze=args.donor_freeze,
        )
        Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(args.out)
    else:
        donors = read(args.donor_map) if args.donor_map else None
        result = render_sixup(
            read(args.ecology),
            read(args.kit),
            args.output_dir,
            duration=args.duration,
            fps=args.fps,
            donor_video_by_id=donors,
        )
        print(result["contactSheetVideo"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
