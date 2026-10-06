from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import flow_pantry, zero_dollar_mill


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _read(path: str) -> dict:
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Will not overwrite: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-zero-dollar")
    sub = parser.add_subparsers(dest="command", required=True)

    index = sub.add_parser("index")
    index.add_argument("source_folder")
    index.add_argument("manifest_json")
    index.add_argument("--no-probe", action="store_true")
    index.add_argument("--nonrecursive", action="store_true")

    plan = sub.add_parser("plan")
    plan.add_argument("manifest_json")
    plan.add_argument("source_folder")
    plan.add_argument("plan_json")
    plan.add_argument("--target-seconds", type=float)
    plan.add_argument("--audio")
    plan.add_argument("--slug-seconds", type=float, default=4.0)
    plan.add_argument("--width", type=int, default=1280)
    plan.add_argument("--height", type=int, default=720)
    plan.add_argument("--fps", type=int, default=24)

    render = sub.add_parser("render")
    render.add_argument("plan_json")
    render.add_argument("source_folder")
    render.add_argument("output_dir")
    render.add_argument("--audio")

    smash = sub.add_parser("smash")
    smash.add_argument("source_folder")
    smash.add_argument("output_dir")
    smash.add_argument("--target-seconds", type=float)
    smash.add_argument("--audio")
    smash.add_argument("--slug-seconds", type=float, default=4.0)
    smash.add_argument("--width", type=int, default=1280)
    smash.add_argument("--height", type=int, default=720)
    smash.add_argument("--fps", type=int, default=24)

    args = parser.parse_args(argv)

    if args.command == "index":
        manifest = flow_pantry.index_flow_folder(
            args.source_folder,
            recursive=not args.nonrecursive,
            probe=not args.no_probe,
        )
        path = Path(args.manifest_json).expanduser().resolve()
        _write(path, manifest)
        result = {"manifest": str(path), "itemCount": manifest["itemCount"]}
    elif args.command == "plan":
        manifest = _read(args.manifest_json)
        target = zero_dollar_mill.target_duration(
            target_seconds=args.target_seconds,
            audio_path=args.audio,
        )
        body = zero_dollar_mill.build_plan(
            manifest,
            args.source_folder,
            target_seconds=target,
            slug_seconds=args.slug_seconds,
            width=args.width,
            height=args.height,
            fps=args.fps,
        )
        path = Path(args.plan_json).expanduser().resolve()
        _write(path, body)
        result = {
            "plan": str(path),
            "planId": body["id"],
            "targetSeconds": body["targetSeconds"],
            "slugCount": body["slugCount"],
            "coverageRatio": body["coverageRatio"],
        }
    elif args.command == "render":
        result = zero_dollar_mill.render_plan(
            _read(args.plan_json),
            args.source_folder,
            args.output_dir,
            audio_path=args.audio,
        )
    else:
        output = Path(args.output_dir).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        manifest_path = output / "flow-pantry.json"
        plan_path = output / "zero-dollar.plan.json"
        if manifest_path.exists() or plan_path.exists():
            raise FileExistsError("SMASH output directory already contains plan artifacts")

        manifest = flow_pantry.index_flow_folder(args.source_folder, recursive=True, probe=True)
        _write(manifest_path, manifest)
        target = zero_dollar_mill.target_duration(
            target_seconds=args.target_seconds,
            audio_path=args.audio,
        )
        body = zero_dollar_mill.build_plan(
            manifest,
            args.source_folder,
            target_seconds=target,
            slug_seconds=args.slug_seconds,
            width=args.width,
            height=args.height,
            fps=args.fps,
        )
        _write(plan_path, body)
        receipt = zero_dollar_mill.render_plan(
            body,
            args.source_folder,
            output,
            audio_path=args.audio,
        )
        result = {
            "manifest": str(manifest_path),
            "plan": str(plan_path),
            "receipt": str(output / "zero-dollar-current-cut.receipt.json"),
            "output": receipt["outputPath"],
            "outputSha256": receipt["outputSha256"],
            "targetSeconds": receipt["targetSeconds"],
            "observedOutputSeconds": receipt["observedOutputSeconds"],
            "coverageRatio": receipt["coverageRatio"],
            "slugCount": receipt["slugCount"],
            "uniqueSourceCount": receipt["uniqueSourceCount"],
            "recipeCountUsed": receipt["recipeCountUsed"],
            "derivativeYield": receipt["derivativeYield"],
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        }

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
