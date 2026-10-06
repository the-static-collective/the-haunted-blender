from __future__ import annotations

import argparse
import json

from . import cockpit_engine


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-cockpit-engine")
    sub = parser.add_subparsers(dest="command", required=True)

    configure = sub.add_parser("configure")
    configure.add_argument("root")
    configure.add_argument("--kit", required=True)
    configure.add_argument("--source-receipt", action="append", required=True)
    configure.add_argument("--offers")
    configure.add_argument("--lyrics")
    configure.add_argument("--audio")
    configure.add_argument("--checkpoint")
    configure.add_argument("--fps", type=int, default=12)
    configure.add_argument("--preview-seconds", type=float, default=2.0)
    configure.add_argument("--occurrence-budget-micros", type=int, default=100000)
    configure.add_argument("--per-job-budget-micros", type=int, default=50000)

    grow = sub.add_parser("grow")
    grow.add_argument("root")
    grow.add_argument("section_id")

    keep = sub.add_parser("keep")
    keep.add_argument("root")
    keep.add_argument("section_id")
    keep.add_argument("slot", type=int)

    awaken = sub.add_parser("awaken")
    awaken.add_argument("root")
    awaken.add_argument("section_id")

    play = sub.add_parser("play")
    play.add_argument("root")

    view = sub.add_parser("view")
    view.add_argument("root")
    view.add_argument("section_id")

    args = parser.parse_args(argv)
    if args.command == "configure":
        result = cockpit_engine.configure_project(
            args.root,
            source_receipt_ids=args.source_receipt,
            kit_path=args.kit,
            motion_offers_path=args.offers,
            lyrics_path=args.lyrics,
            audio_path=args.audio,
            common_checkpoint_id=args.checkpoint,
            fps=args.fps,
            preview_seconds=args.preview_seconds,
            occurrence_budget_usd_micros=args.occurrence_budget_micros,
            per_job_budget_usd_micros=args.per_job_budget_micros,
        )
    elif args.command == "grow":
        result = cockpit_engine.grow(args.root, args.section_id)
    elif args.command == "keep":
        result = cockpit_engine.keep(args.root, args.section_id, slot=args.slot)
    elif args.command == "awaken":
        result = cockpit_engine.awaken(args.root, args.section_id)
    elif args.command == "play":
        result = cockpit_engine.play(args.root)
    else:
        result = cockpit_engine.engine_view(args.root, args.section_id)

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
