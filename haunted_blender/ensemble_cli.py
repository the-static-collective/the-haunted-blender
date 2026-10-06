from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import ensemble_stage, paper_director, puppet_factory, stage_compost


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
    parser = argparse.ArgumentParser(prog="haunted-blender-ensemble")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("ensemble_spec_json")
    compile_cmd.add_argument("timing_json")
    compile_cmd.add_argument("output_dir")

    render = sub.add_parser("render")
    render.add_argument("performance_json")
    render.add_argument("output_mp4")

    smash = sub.add_parser("smash")
    smash.add_argument("ensemble_spec_json")
    smash.add_argument("timing_json")
    smash.add_argument("output_dir")
    smash.add_argument("--parts-drawer")
    smash.add_argument("--doctor-report")
    smash.add_argument("--direct", action="store_true")
    smash.add_argument("--max-shot-seconds", type=float, default=3.2)

    args = parser.parse_args(argv)

    if args.command == "compile":
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        performance = ensemble_stage.compile_ensemble(
            _read(args.ensemble_spec_json),
            _read(args.timing_json),
            output / "performance",
        )
        path = output / "ensemble-performance.json"
        _write(path, performance)
        result = {
            "performance": str(path),
            "performanceId": performance["id"],
            "ensembleId": performance["ensemble"]["id"],
            "castCount": performance["ensemble"]["castCount"],
            "dialogueTurnCount": performance["ensemble"]["dialogueTurnCount"],
        }
    elif args.command == "render":
        result = puppet_factory.render_performance(
            _read(args.performance_json),
            args.output_mp4,
        )
    else:
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        spec = _read(args.ensemble_spec_json)
        timing = _read(args.timing_json)
        doctor = _read(args.doctor_report) if args.doctor_report else None

        performance = ensemble_stage.compile_ensemble(
            spec,
            timing,
            output / "performance",
        )

        if args.parts_drawer:
            canvas = performance["cutoutPlan"]["canvas"]
            dressing = stage_compost.plan(
                _read(args.parts_drawer),
                width=int(canvas["width"]),
                height=int(canvas["height"]),
                duration_seconds=float(performance["duration"]),
            )
            performance = stage_compost.apply_to_performance(performance, dressing)
            _write(output / "stage-dressing.json", dressing)

        performance_path = output / "ensemble-performance.json"
        _write(performance_path, performance)

        base_path = output / "ensemble-movie.mp4"
        base_receipt = puppet_factory.render_performance(performance, base_path)

        final_output = str(base_path)
        final_sha = base_receipt["outputSha256"]
        director_result = None

        if args.direct:
            director_plan = paper_director.plan(
                timing,
                performance=performance,
                doctor_report=doctor,
                max_shot_seconds=args.max_shot_seconds,
            )
            director_plan_path = output / "paper-director.plan.json"
            _write(director_plan_path, director_plan)
            directed_path = output / "ensemble-directed.mp4"
            director_receipt = paper_director.render(
                base_path,
                director_plan,
                directed_path,
                performance=performance,
            )
            final_output = str(directed_path)
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
            "performance": str(performance_path),
            "performanceId": performance["id"],
            "ensembleId": performance["ensemble"]["id"],
            "castCount": performance["ensemble"]["castCount"],
            "dialogueTurnCount": performance["ensemble"]["dialogueTurnCount"],
            "baseOutput": str(base_path),
            "baseOutputSha256": base_receipt["outputSha256"],
            "output": final_output,
            "outputSha256": final_sha,
            "paperDirector": director_result,
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        }

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
