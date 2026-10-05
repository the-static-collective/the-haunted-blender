from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scene_growth import awaken_kept_scene, grow_kept_scene, normalize_timing


def read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(value: object, path: str) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="haunted-blender-scene-growth")
    sub = p.add_subparsers(dest="command", required=True)

    timing = sub.add_parser("timing")
    timing.add_argument("track")
    timing.add_argument("--lyrics")
    timing.add_argument("--out", required=True)

    grow = sub.add_parser("grow")
    grow.add_argument("keep_result")
    grow.add_argument("timing")
    grow.add_argument("kit")
    grow.add_argument("output_dir")
    grow.add_argument("--fps", type=int, default=12)
    grow.add_argument("--donor-freeze")

    awaken = sub.add_parser("awaken")
    awaken.add_argument("root")
    awaken.add_argument("grown_scene")
    awaken.add_argument("window_id")
    awaken.add_argument("accepted_video_address")
    awaken.add_argument("output")

    args = p.parse_args(argv)
    if args.command == "timing":
        result = normalize_timing(read(args.track), read(args.lyrics) if args.lyrics else None)
        write(result, args.out)
        print(args.out)
    elif args.command == "grow":
        result = grow_kept_scene(
            read(args.keep_result), read(args.timing), read(args.kit), args.output_dir,
            fps=args.fps, donor_freeze=args.donor_freeze,
        )
        print(result["videoPath"])
    else:
        result = awaken_kept_scene(
            args.root, read(args.grown_scene), args.window_id,
            args.accepted_video_address, args.output,
        )
        print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
