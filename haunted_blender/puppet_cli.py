from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import cutaway_machine, paper_director, puppet_factory, stage_compost


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
    parser = argparse.ArgumentParser(prog="haunted-blender-puppet")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build")
    build.add_argument("spec_json")
    build.add_argument("output_dir")

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("rig_json")
    compile_cmd.add_argument("timing_json")
    compile_cmd.add_argument("output_dir")
    compile_cmd.add_argument("--doctor-report")
    compile_cmd.add_argument("--parts-drawer")

    render = sub.add_parser("render")
    render.add_argument("performance_json")
    render.add_argument("output_mp4")

    smash = sub.add_parser("smash")
    smash.add_argument("spec_json")
    smash.add_argument("timing_json")
    smash.add_argument("output_dir")
    smash.add_argument("--doctor-report")
    smash.add_argument("--max-cutaways", type=int, default=6)
    smash.add_argument("--cutaway-seconds", type=float, default=1.25)
    smash.add_argument("--parts-drawer")
    smash.add_argument("--direct", action="store_true")
    smash.add_argument("--max-shot-seconds", type=float, default=3.2)

    args = parser.parse_args(argv)

    if args.command == "build":
        rig = puppet_factory.build_rig(_read(args.spec_json), args.output_dir)
        result = {
            "rigId": rig["id"],
            "rig": str(Path(args.output_dir).expanduser().resolve() / "puppet-rig.json"),
            "poseCount": len(rig["poseGrammar"]),
            "mouthShapeCount": len(rig["mouth"]["atlas"]),
        }
    elif args.command == "compile":
        rig = _read(args.rig_json)
        timing = _read(args.timing_json)
        cutaways = None
        if args.doctor_report:
            cutaways = cutaway_machine.plan_from_doctor(
                _read(args.doctor_report),
                timing,
            )
        performance = puppet_factory.compile_performance(
            rig,
            timing,
            args.output_dir,
            cutaway_plan=cutaways,
        )
        if args.parts_drawer:
            dressing = stage_compost.plan(
                _read(args.parts_drawer),
                width=int(rig["canvas"]["width"]),
                height=int(rig["canvas"]["height"]),
                duration_seconds=float(performance["duration"]),
            )
            performance = stage_compost.apply_to_performance(performance, dressing)
            _write(
                Path(args.output_dir).expanduser().resolve() / "stage-dressing.json",
                dressing,
            )
        path = Path(args.output_dir).expanduser().resolve() / "puppet-performance.json"
        _write(path, performance)
        if cutaways is not None:
            _write(
                Path(args.output_dir).expanduser().resolve() / "cutaway-plan.json",
                cutaways,
            )
        result = {
            "performanceId": performance["id"],
            "performance": str(path),
            "durationSeconds": performance["duration"],
            "poseEventCount": len(performance["poseEvents"]),
            "mouthEventCount": len(performance["mouthEvents"]),
            "lyricGeographyCount": len(performance["lyricGeography"]),
            "cutawayCount": len(performance["cutaways"]),
        }
    elif args.command == "render":
        result = puppet_factory.render_performance(
            _read(args.performance_json), args.output_mp4
        )
    else:
        spec = _read(args.spec_json)
        timing = _read(args.timing_json)
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)

        rig_dir = output / "rig"
        rig = puppet_factory.build_rig(spec, rig_dir)

        doctor_report = _read(args.doctor_report) if args.doctor_report else None
        cutaways = None
        if doctor_report:
            cutaways = cutaway_machine.plan_from_doctor(
                doctor_report,
                timing,
                max_cutaways=args.max_cutaways,
                duration_seconds=args.cutaway_seconds,
            )
            _write(output / "cutaway-plan.json", cutaways)

        performance_dir = output / "performance"
        performance = puppet_factory.compile_performance(
            rig,
            timing,
            performance_dir,
            cutaway_plan=cutaways,
        )
        if args.parts_drawer:
            dressing = stage_compost.plan(
                _read(args.parts_drawer),
                width=int(rig["canvas"]["width"]),
                height=int(rig["canvas"]["height"]),
                duration_seconds=float(performance["duration"]),
            )
            performance = stage_compost.apply_to_performance(performance, dressing)
            _write(output / "stage-dressing.json", dressing)
        performance_path = output / "puppet-performance.json"
        _write(performance_path, performance)

        receipt = puppet_factory.render_performance(
            performance, output / "puppet-movie.mp4"
        )
        final_output = receipt["output"]
        final_sha = receipt["outputSha256"]
        director_result = None
        if args.direct:
            director_plan = paper_director.plan(
                timing,
                performance=performance,
                doctor_report=doctor_report,
                max_shot_seconds=args.max_shot_seconds,
            )
            director_plan_path = output / "paper-director.plan.json"
            _write(director_plan_path, director_plan)
            director_receipt = paper_director.render(
                receipt["output"],
                director_plan,
                output / "puppet-directed.mp4",
                performance=performance,
            )
            final_output = str(output / "puppet-directed.mp4")
            final_sha = director_receipt["outputSha256"]
            director_result = {
                "plan": str(director_plan_path),
                "planId": director_plan["id"],
                "shotCount": director_plan["shotCount"],
                "shotTypeCounts": director_plan["shotTypeCounts"],
                "coverageRatio": director_receipt["coverageRatio"],
                "output": final_output,
                "outputSha256": final_sha,
            }

        result = {
            "rig": str(rig_dir / "puppet-rig.json"),
            "rigId": rig["id"],
            "performance": str(performance_path),
            "performanceId": performance["id"],
            "paperStageOutput": receipt["output"],
            "paperStageOutputSha256": receipt["outputSha256"],
            "output": final_output,
            "outputSha256": final_sha,
            "durationSeconds": receipt["durationSeconds"],
            "poseEventCount": receipt["poseEventCount"],
            "mouthEventCount": receipt["mouthEventCount"],
            "lyricGeographyCount": receipt["lyricGeographyCount"],
            "cutawayCount": receipt["cutawayCount"],
            "paperDirector": director_result,
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        }

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
