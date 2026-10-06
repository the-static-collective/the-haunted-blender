from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import weakest_window_doctor as doctor
from . import zero_dollar_mill


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
    parser = argparse.ArgumentParser(prog="haunted-blender-window-doctor")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("video")
    scan.add_argument("plan_json")
    scan.add_argument("report_json")
    scan.add_argument("--window-seconds", type=float, default=4.0)
    scan.add_argument("--sample-fps", type=int, default=4)

    prescribe = sub.add_parser("prescribe")
    prescribe.add_argument("report_json")
    prescribe.add_argument("plan_json")
    prescribe.add_argument("treatment_json")
    prescribe.add_argument("--fraction", type=float, default=0.10)
    prescribe.add_argument("--max-windows", type=int)

    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("plan_json")
    apply_cmd.add_argument("treatment_json")
    apply_cmd.add_argument("treated_plan_json")

    smash = sub.add_parser("smash")
    smash.add_argument("video")
    smash.add_argument("plan_json")
    smash.add_argument("source_folder")
    smash.add_argument("output_dir")
    smash.add_argument("--audio")
    smash.add_argument("--window-seconds", type=float, default=4.0)
    smash.add_argument("--sample-fps", type=int, default=4)
    smash.add_argument("--fraction", type=float, default=0.10)
    smash.add_argument("--max-windows", type=int)

    args = parser.parse_args(argv)

    if args.command == "scan":
        report = doctor.scan(
            args.video,
            _read(args.plan_json),
            window_seconds=args.window_seconds,
            sample_fps=args.sample_fps,
        )
        path = Path(args.report_json).expanduser().resolve()
        _write(path, report)
        result = {
            "report": str(path),
            "reportId": report["id"],
            "weakest": report["weakest"],
            "meanWeakness": report["meanWeakness"],
            "coverageRatio": report["coverageRatio"],
        }
    elif args.command == "prescribe":
        treatment = doctor.prescribe(
            _read(args.report_json),
            _read(args.plan_json),
            fraction=args.fraction,
            max_windows=args.max_windows,
        )
        path = Path(args.treatment_json).expanduser().resolve()
        _write(path, treatment)
        result = {
            "treatment": str(path),
            "treatmentId": treatment["id"],
            "mutationCount": len(treatment["mutations"]),
        }
    elif args.command == "apply":
        treated = doctor.apply_level_one(
            _read(args.plan_json), _read(args.treatment_json)
        )
        path = Path(args.treated_plan_json).expanduser().resolve()
        _write(path, treated)
        result = {
            "plan": str(path),
            "planId": treated["id"],
            "changedSlugCount": treated["doctor"]["changedSlugCount"],
        }
    else:
        video = Path(args.video).expanduser().resolve(strict=True)
        plan = _read(args.plan_json)
        source = Path(args.source_folder).expanduser().resolve(strict=True)
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)

        before = doctor.scan(
            video,
            plan,
            window_seconds=args.window_seconds,
            sample_fps=args.sample_fps,
        )
        before_path = output / "doctor.before.json"
        _write(before_path, before)

        treatment = doctor.prescribe(
            before,
            plan,
            fraction=args.fraction,
            max_windows=args.max_windows,
        )
        treatment_path = output / "doctor.treatment.json"
        _write(treatment_path, treatment)

        treated = doctor.apply_level_one(plan, treatment)
        treated_plan_path = output / "doctor.level1.plan.json"
        _write(treated_plan_path, treated)

        trial_dir = output / "level1-trial"
        receipt = zero_dollar_mill.render_plan(
            treated,
            source,
            trial_dir,
            audio_path=args.audio,
        )
        after = doctor.scan(
            receipt["outputPath"],
            treated,
            window_seconds=args.window_seconds,
            sample_fps=args.sample_fps,
        )
        after_path = output / "doctor.after.json"
        _write(after_path, after)

        comparison = doctor.compare(before, after)
        verdict = {
            "schema": "haunted-blender/weakest-window-verdict/v1",
            **comparison,
            "acceptedLevelOne": bool(comparison["improved"]),
            "trialOutput": receipt["outputPath"],
            "trialOutputSha256": receipt["outputSha256"],
            "providerCredits": 0,
            "usdMicros": 0,
            "nextLevel": 1 if comparison["improved"] else 2,
            "nextRecommendation": (
                "Keep the deterministic Level-1 trial and rescan its new weakest windows."
                if comparison["improved"]
                else "Do not spend credits. Escalate weak windows to Level 2 owned-clip compost."
            ),
            "laws": [
                "TRIAL OUTPUT != CURRENT CUT UNTIL VERDICT",
                "FAILED LEVEL 1 != PROVIDER SPEND",
                "COVERAGE MAY NOT DECREASE",
                "CHEAPEST EFFECTIVE LEVEL FIRST",
            ],
        }
        verdict_path = output / "doctor.verdict.json"
        _write(verdict_path, verdict)

        result = {
            "before": str(before_path),
            "treatment": str(treatment_path),
            "treatedPlan": str(treated_plan_path),
            "trialOutput": receipt["outputPath"],
            "after": str(after_path),
            "verdict": str(verdict_path),
            "acceptedLevelOne": verdict["acceptedLevelOne"],
            "nextLevel": verdict["nextLevel"],
            "beforeMeanWeakness": comparison["beforeMeanWeakness"],
            "afterMeanWeakness": comparison["afterMeanWeakness"],
            "coveragePreserved": comparison["coveragePreserved"],
            "providerCredits": 0,
            "usdMicros": 0,
        }

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
