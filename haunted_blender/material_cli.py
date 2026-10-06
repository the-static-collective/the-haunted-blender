from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import material_surface


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-material")
    sub = parser.add_subparsers(dest="command", required=True)

    presets = sub.add_parser("presets")
    presets.add_argument("--full", action="store_true")

    profile_cmd = sub.add_parser("profile")
    profile_cmd.add_argument("material_type")

    materialize = sub.add_parser("materialize")
    materialize.add_argument("source_image")
    materialize.add_argument("output_image")
    materialize.add_argument("--type", required=True)

    args = parser.parse_args(argv)

    if args.command == "presets":
        if args.full:
            result = {
                name: material_surface.profile(name)
                for name in sorted(material_surface.PRESETS)
            }
        else:
            result = {"materials": sorted(material_surface.PRESETS)}
    elif args.command == "profile":
        result = material_surface.profile(args.material_type)
    else:
        result = material_surface.materialize_asset(
            args.source_image,
            args.output_image,
            args.type,
        )

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
