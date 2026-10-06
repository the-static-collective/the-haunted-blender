from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import flow_pantry, parts_harvester


def _read(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Will not overwrite: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-parts")
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("harvest")
    one.add_argument("source_video")
    one.add_argument("output_dir")
    one.add_argument("--stills", type=int, default=6)
    one.add_argument("--loop-seconds", type=float, default=1.5)
    one.add_argument("--fragment-seconds", type=float, default=0.8)
    one.add_argument("--sample-fps", type=int, default=4)

    batch = sub.add_parser("batch")
    batch.add_argument("source_folder")
    batch.add_argument("output_dir")
    batch.add_argument("--manifest")
    batch.add_argument("--stills", type=int, default=6)
    batch.add_argument("--loop-seconds", type=float, default=1.5)
    batch.add_argument("--fragment-seconds", type=float, default=0.8)
    batch.add_argument("--sample-fps", type=int, default=4)

    drawer = sub.add_parser("drawer")
    drawer.add_argument("output_json")
    drawer.add_argument("harvest_json", nargs="+")

    select = sub.add_parser("select-stage")
    select.add_argument("drawer_json")
    select.add_argument("output_json")
    select.add_argument("--max-per-role", type=int, default=3)

    doctor = sub.add_parser("doctor-prescribe")
    doctor.add_argument("doctor_report_json")
    doctor.add_argument("drawer_json")
    doctor.add_argument("output_json")
    doctor.add_argument("--max-windows", type=int, default=6)

    transplant = sub.add_parser("transplant")
    transplant.add_argument("behavior_json")
    transplant.add_argument("target_sha256")
    transplant.add_argument("output_json")
    transplant.add_argument("--duration", type=float, required=True)
    transplant.add_argument("--x", type=float, default=0)
    transplant.add_argument("--y", type=float, default=0)
    transplant.add_argument("--scale", type=float, default=1)
    transplant.add_argument("--rotation", type=float, default=0)

    args = parser.parse_args(argv)

    if args.command == "harvest":
        result = parts_harvester.harvest(
            args.source_video,
            args.output_dir,
            still_count=args.stills,
            loop_seconds=args.loop_seconds,
            fragment_seconds=args.fragment_seconds,
            sample_fps=args.sample_fps,
        )
    elif args.command == "batch":
        source = Path(args.source_folder).expanduser().resolve(strict=True)
        manifest = (
            _read(args.manifest)
            if args.manifest
            else flow_pantry.index_flow_folder(source, recursive=True, probe=True)
        )
        result = parts_harvester.harvest_flow_manifest(
            manifest,
            source,
            args.output_dir,
            still_count=args.stills,
            loop_seconds=args.loop_seconds,
            fragment_seconds=args.fragment_seconds,
            sample_fps=args.sample_fps,
        )
    elif args.command == "drawer":
        harvests = [_read(path) for path in args.harvest_json]
        result = parts_harvester.build_drawer(harvests, args.output_json)
    elif args.command == "select-stage":
        result = parts_harvester.select_for_stage(
            _read(args.drawer_json),
            max_per_role=args.max_per_role,
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    elif args.command == "doctor-prescribe":
        result = parts_harvester.prescribe_for_weak_windows(
            _read(args.doctor_report_json),
            _read(args.drawer_json),
            max_windows=args.max_windows,
        )
        _write(Path(args.output_json).expanduser().resolve(), result)
    else:
        result = parts_harvester.behavior_transplant(
            _read(args.behavior_json),
            target_source_sha256=args.target_sha256,
            duration_seconds=args.duration,
            base_state={
                "x": args.x,
                "y": args.y,
                "scale": args.scale,
                "rotation": args.rotation,
            },
        )
        _write(Path(args.output_json).expanduser().resolve(), result)

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
