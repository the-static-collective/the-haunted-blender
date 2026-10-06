from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import paper_director


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
    parser = argparse.ArgumentParser(prog="haunted-blender-paper-director")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("timing_json")
    plan_cmd.add_argument("output_json")
    plan_cmd.add_argument("--performance")
    plan_cmd.add_argument("--doctor-report")
    plan_cmd.add_argument("--max-shot-seconds", type=float, default=3.2)
    plan_cmd.add_argument("--min-shot-seconds", type=float, default=0.45)

    render_cmd = sub.add_parser("render")
    render_cmd.add_argument("base_video")
    render_cmd.add_argument("plan_json")
    render_cmd.add_argument("output_mp4")
    render_cmd.add_argument("--performance")

    smash = sub.add_parser("smash")
    smash.add_argument("base_video")
    smash.add_argument("timing_json")
    smash.add_argument("output_dir")
    smash.add_argument("--performance")
    smash.add_argument("--doctor-report")
    smash.add_argument("--max-shot-seconds", type=float, default=3.2)
    smash.add_argument("--min-shot-seconds", type=float, default=0.45)

    args = parser.parse_args(argv)

    if args.command == "plan":
        timing = _read(args.timing_json)
        performance = _read(args.performance) if args.performance else None
        doctor = _read(args.doctor_report) if args.doctor_report else None
        plan = paper_director.plan(
            timing,
            performance=performance,
            doctor_report=doctor,
            max_shot_seconds=args.max_shot_seconds,
            min_shot_seconds=args.min_shot_seconds,
        )
        path = Path(args.output_json).expanduser().resolve()
        _write(path, plan)
        result = {
            "plan": str(path),
            "planId": plan["id"],
            "shotCount": plan["shotCount"],
            "shotTypeCounts": plan["shotTypeCounts"],
            "coverageRatio": plan["coverageRatio"],
        }
    elif args.command == "render":
        performance = _read(args.performance) if args.performance else None
        result = paper_director.render(
            args.base_video,
            _read(args.plan_json),
            args.output_mp4,
            performance=performance,
        )
    else:
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        timing = _read(args.timing_json)
        performance = _read(args.performance) if args.performance else None
        doctor = _read(args.doctor_report) if args.doctor_report else None
        plan = paper_director.plan(
            timing,
            performance=performance,
            doctor_report=doctor,
            max_shot_seconds=args.max_shot_seconds,
            min_shot_seconds=args.min_shot_seconds,
        )
        plan_path = output / "paper-director.plan.json"
        _write(plan_path, plan)
        receipt = paper_director.render(
            args.base_video,
            plan,
            output / "paper-directed.mp4",
            performance=performance,
        )
        result = {
            "plan": str(plan_path),
            "planId": plan["id"],
            "output": str(output / "paper-directed.mp4"),
            "outputSha256": receipt["outputSha256"],
            "shotCount": receipt["shotCount"],
            "shotTypeCounts": plan["shotTypeCounts"],
            "coverageRatio": receipt["coverageRatio"],
            "audioAuthority": receipt["audioAuthority"],
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        }

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
