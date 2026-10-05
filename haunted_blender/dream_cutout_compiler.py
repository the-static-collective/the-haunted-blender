"""FRANKEN BLENDER 004 — compile unborn DREAMBREEDER proposals into
cheap deterministic cutout previews.

PREVIEW != KEEP
PREVIEW != HISTORY
PREVIEW RENDER != RESOLVED EXECUTION
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from .cutout_stage import SCHEMA as CUTOUT_SCHEMA, render_cutout
from .dreambreeder import ECOLOGY_SCHEMA

KIT_SCHEMA = "haunted-blender/cutout-kit/v1"
COMPILED_SCHEMA = "haunted-blender/dream-cutout-plan/v1"
SIXUP_SCHEMA = "haunted-blender/dream-sixup-preview/v1"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_ecology(ecology: dict) -> dict:
    if not isinstance(ecology, dict) or ecology.get("schema") != ECOLOGY_SCHEMA:
        raise ValueError("Unsupported dream ecology.")
    proposals = ecology.get("proposals")
    if not isinstance(proposals, list) or len(proposals) != 6:
        raise ValueError("Dream cutout compiler requires an exact six-up ecology.")
    return ecology


def _validate_kit(kit: dict) -> dict:
    if not isinstance(kit, dict) or kit.get("schema") != KIT_SCHEMA:
        raise ValueError("Unsupported cutout kit.")
    canvas = kit.get("canvas") or {}
    if int(canvas.get("width", 0)) < 16 or int(canvas.get("height", 0)) < 16:
        raise ValueError("Cutout kit canvas is invalid.")
    layers = kit.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValueError("Cutout kit requires at least one layer.")
    ids = set()
    for layer in layers:
        lid = str(layer.get("id") or "")
        role = str(layer.get("role") or "")
        source = Path(str(layer.get("source") or "")).expanduser()
        if not lid or lid in ids:
            raise ValueError("Cutout kit layer ids must be unique and nonempty.")
        ids.add(lid)
        if not role:
            raise ValueError("Cutout kit layer role is required.")
        if not source.is_file():
            raise ValueError(f"Missing cutout kit source: {lid}.")
    return kit


def _seed_fraction(seed: str, offset: int) -> float:
    start = (offset * 4) % max(4, len(seed) - 4)
    return int(seed[start:start + 4], 16) / 65535.0


def _motion_for(role: str, grammar: list[str], *, seed: str, duration: float, base: dict) -> list[dict]:
    x = float(base.get("x", 0))
    y = float(base.get("y", 0))
    scale = float(base.get("scale", 1))
    rotation = float(base.get("rotation", 0))
    opacity = float(base.get("opacity", 1))
    end = {"time": duration, "x": x, "y": y, "scale": scale, "rotation": rotation, "opacity": opacity}

    f1 = _seed_fraction(seed, 1) - 0.5
    f2 = _seed_fraction(seed, 2) - 0.5
    magnitude = 10.0 + 18.0 * abs(f1)

    if "drift-up" in grammar or "raise-world" in grammar:
        if role in {"actor", "body", "head", "arm-left", "arm-right", "prop"}:
            end["y"] = y - magnitude
        else:
            end["y"] = y + magnitude * 0.3

    if "step" in grammar:
        if role in {"actor", "body", "head", "arm-left", "arm-right"}:
            end["x"] = x + 18.0 + 20.0 * abs(f2)
            end["y"] = end["y"] - 4.0

    if "parallax" in grammar:
        if role == "background":
            end["x"] = x - 6.0 - 8.0 * abs(f1)
        elif role == "foreground":
            end["x"] = x + 14.0 + 12.0 * abs(f2)

    if "hinge" in grammar and role in {"prop", "arm-left", "arm-right", "foreground"}:
        end["rotation"] = rotation + 18.0 + 28.0 * f1

    if "wind" in grammar and role in {"arm-left", "arm-right", "prop", "foreground"}:
        end["rotation"] = end["rotation"] + 12.0 * (1 if f2 >= 0 else -1)

    if "echo" in grammar and role in {"actor", "body", "head"}:
        end["x"] = end["x"] + 8.0 * f1
        end["opacity"] = max(0.55, opacity - 0.15)

    if "misregister" in grammar:
        end["x"] = end["x"] + 5.0 * f2
        end["rotation"] = end["rotation"] + 2.5 * f1

    if "open-late" in grammar and role in {"light", "portal", "background"}:
        end["opacity"] = min(1.0, opacity + 0.35)

    if "backlight" in grammar and role == "light":
        end["scale"] = scale * 1.12
        end["opacity"] = min(1.0, opacity + 0.25)

    if "assemble" in grammar:
        if role in {"actor", "body", "head", "arm-left", "arm-right", "prop"}:
            end["x"] = x + (-f1 * 8.0)
            end["y"] = end["y"] + (-f2 * 6.0)

    if "return" in grammar:
        mid = {
            "time": duration * 0.55,
            "x": end["x"],
            "y": end["y"],
            "scale": end["scale"],
            "rotation": end["rotation"],
            "opacity": end["opacity"],
        }
        return [
            {"time": 0.0, "x": x, "y": y, "scale": scale, "rotation": rotation, "opacity": opacity},
            mid,
            {"time": duration, "x": x, "y": y, "scale": scale, "rotation": rotation, "opacity": opacity},
        ]

    return [
        {"time": 0.0, "x": x, "y": y, "scale": scale, "rotation": rotation, "opacity": opacity},
        end,
    ]


def extract_donor_freeze(video_path: str | Path, output_path: str | Path, *, at_seconds: float | None = None) -> dict:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required for donor freeze extraction.")
    source = Path(video_path).expanduser().resolve()
    if not source.is_file():
        raise ValueError("Donor video does not exist.")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(source)],
        check=True, capture_output=True, text=True,
    )
    duration = float(probe.stdout.strip())
    if duration <= 0:
        raise ValueError("Donor video duration is invalid.")
    when = duration * 0.5 if at_seconds is None else float(at_seconds)
    when = min(max(0.0, when), max(0.0, duration - 0.001))

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Donor freeze extraction never overwrites existing output.")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-ss", f"{when:.6f}", "-i", str(source),
            "-frames:v", "1", "-vf", "format=rgba", str(out),
        ],
        check=True,
    )
    return {
        "sourceSha256": _file_sha(source),
        "freezeSha256": _file_sha(out),
        "atSeconds": round(when, 6),
        "sourceDurationSeconds": round(duration, 6),
        "freezePath": str(out),
    }


def compile_proposal(
    ecology: dict,
    proposal_id: str,
    kit: dict,
    *,
    duration: float = 2.0,
    fps: int = 12,
    donor_freeze: str | Path | None = None,
) -> dict:
    ecology = _validate_ecology(ecology)
    kit = _validate_kit(kit)
    proposal = next((p for p in ecology["proposals"] if p["id"] == proposal_id), None)
    if proposal is None:
        raise ValueError("Proposal does not belong to this ecology.")
    if duration <= 0 or fps < 1:
        raise ValueError("Preview duration and fps must be positive.")

    layers = []
    for source_layer in kit["layers"]:
        layer = copy.deepcopy(source_layer)
        layer.pop("role", None)
        layer["source"] = str(Path(layer["source"]).expanduser().resolve())
        layer["keyframes"] = _motion_for(
            source_layer["role"],
            list(proposal.get("motionGrammar") or []),
            seed=proposal["id"].split(":")[-1],
            duration=float(duration),
            base=source_layer,
        )
        layers.append(layer)

    if donor_freeze is not None:
        freeze = Path(donor_freeze).expanduser().resolve()
        if not freeze.is_file():
            raise ValueError("Donor freeze does not exist.")
        canvas = kit["canvas"]
        layers.append(
            {
                "id": "donor-window",
                "source": str(freeze),
                "z": 50,
                "x": round(int(canvas["width"]) * 0.67),
                "y": round(int(canvas["height"]) * 0.08),
                "scale": float(kit.get("donorScale", 0.28)),
                "rotation": -3.0,
                "opacity": 0.9,
                "keyframes": _motion_for(
                    "prop",
                    list(proposal.get("motionGrammar") or []),
                    seed=proposal["id"].split(":")[-1],
                    duration=float(duration),
                    base={
                        "x": round(int(canvas["width"]) * 0.67),
                        "y": round(int(canvas["height"]) * 0.08),
                        "scale": float(kit.get("donorScale", 0.28)),
                        "rotation": -3.0,
                        "opacity": 0.9,
                    },
                ),
            }
        )

    plan = {
        "schema": CUTOUT_SCHEMA,
        "canvas": {
            "width": int(kit["canvas"]["width"]),
            "height": int(kit["canvas"]["height"]),
            "fps": int(fps),
            "duration": float(duration),
        },
        "layers": layers,
    }
    wrapper = {
        "schema": COMPILED_SCHEMA,
        "authorityClass": "proposal-preview",
        "ecologyId": ecology["id"],
        "proposalId": proposal["id"],
        "proposalSlot": proposal["slot"],
        "proposalLabel": proposal["label"],
        "worldPatch": proposal["worldPatch"],
        "motionGrammar": proposal["motionGrammar"],
        "donorId": proposal.get("donorId"),
        "cutoutPlan": plan,
        "laws": [
            "PREVIEW != KEEP",
            "PREVIEW != HISTORY",
            "PREVIEW RENDER != RESOLVED EXECUTION",
        ],
    }
    return {**wrapper, "id": f"dream-cutout-plan:{_hash(wrapper)[:24]}"}


def render_sixup(
    ecology: dict,
    kit: dict,
    output_dir: str | Path,
    *,
    duration: float = 2.0,
    fps: int = 12,
    donor_video_by_id: dict[str, str] | None = None,
) -> dict:
    ecology = _validate_ecology(ecology)
    kit = _validate_kit(kit)
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    donors = donor_video_by_id or {}

    rendered = []
    for proposal in ecology["proposals"]:
        slot = int(proposal["slot"])
        donor_freeze = None
        donor_witness = None
        donor_id = proposal.get("donorId")
        if donor_id and donor_id in donors:
            donor_freeze_path = root / f"proposal-{slot:02d}-donor-freeze.png"
            donor_witness = extract_donor_freeze(donors[donor_id], donor_freeze_path)
            donor_freeze = donor_freeze_path

        compiled = compile_proposal(
            ecology,
            proposal["id"],
            kit,
            duration=duration,
            fps=fps,
            donor_freeze=donor_freeze,
        )
        plan_path = root / f"proposal-{slot:02d}.plan.json"
        plan_path.write_text(json.dumps(compiled, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        video_path = root / f"proposal-{slot:02d}.mp4"
        render_receipt = render_cutout(compiled["cutoutPlan"], video_path)
        rendered.append(
            {
                "slot": slot,
                "proposalId": proposal["id"],
                "label": proposal["label"],
                "compiledPlanId": compiled["id"],
                "planPath": str(plan_path),
                "videoPath": str(video_path),
                "videoSha256": render_receipt["outputSha256"],
                "donorWitness": donor_witness,
                "authorityClass": "proposal-preview",
            }
        )

    contact = root / "six-up.mp4"
    _render_grid([Path(item["videoPath"]) for item in rendered], contact)

    result = {
        "schema": SIXUP_SCHEMA,
        "ecologyId": ecology["id"],
        "authorityClass": "proposal-preview",
        "previews": rendered,
        "contactSheetVideo": str(contact),
        "contactSheetSha256": _file_sha(contact),
        "laws": [
            "SIX-UP PREVIEW != SIX HISTORIES",
            "WATCHING != KEEP",
            "PREVIEW RECEIPT != PERFORMANCE RECEIPT",
        ],
    }
    index = root / "six-up.json"
    index.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _render_grid(videos: list[Path], output: Path) -> None:
    if len(videos) != 6:
        raise ValueError("Six-up contact preview requires exactly six videos.")
    if output.exists():
        raise FileExistsError("Six-up renderer never overwrites existing output.")
    inputs = []
    for video in videos:
        inputs.extend(["-i", str(video)])
    filters = []
    for i in range(6):
        filters.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}]")
    filters.append(
        "[v0][v1][v2][v3][v4][v5]xstack=inputs=6:"
        "layout=0_0|w0_0|w0+w1_0|0_h0|w0_h0|w0+w1_h0[v]"
    )
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            *inputs,
            "-filter_complex", ";".join(filters),
            "-map", "[v]",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ],
        check=True,
    )
