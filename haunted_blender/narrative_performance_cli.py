from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import narrative_performance


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Will not overwrite: {path}")
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-particular-performance")
    sub = parser.add_subparsers(dest="command", required=True)

    smash = sub.add_parser("smash")
    smash.add_argument("spec_json")
    smash.add_argument("output_dir")

    args = parser.parse_args(argv)
    bundle = narrative_performance.compile_spec(
        narrative_performance.read_spec(args.spec_json)
    )
    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    names = {
        "source": "narrative-source.json",
        "proposal": "staging-proposal.json",
        "admission": "editorial-admission.json",
        "plan": "particular-performance.plan.json",
        "receipt": "particular-performance.return.json",
    }
    paths = {}
    for key, filename in names.items():
        path = out / filename
        _write(path, bundle[key])
        paths[key] = str(path)

    print(json.dumps({
        "sourceId": bundle["source"]["id"],
        "proposalId": bundle["proposal"]["id"],
        "admissionId": bundle["admission"]["id"],
        "planId": bundle["plan"]["id"],
        "returnId": bundle["receipt"]["id"],
        "beatCount": bundle["plan"]["beatCount"],
        "durationSeconds": bundle["plan"]["durationSeconds"],
        "paths": paths,
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
