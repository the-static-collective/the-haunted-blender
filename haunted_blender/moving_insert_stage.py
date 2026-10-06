"""FRANKEN BLENDER 008i — Moving Insert Stage.

Composites harvested moving loops/fragments into a completed puppet-stage MP4.
The still-image Cutout Stage remains unchanged.

Moving inserts are explicit bounded surfaces such as televisions, windows,
portals, dream panels, and advertisements. The source video remains independently
hashed and never becomes scene authority merely because it appears inside a set.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

SCHEMA = "haunted-blender/moving-insert-plan/v1"
RECEIPT_SCHEMA = "haunted-blender/moving-insert-render-receipt/v1"

ROLE_LAYOUTS = {
    "television": {"x": 0.08, "y": 0.13, "w": 0.25, "h": 0.27, "border": 6},
    "window": {"x": 0.72, "y": 0.16, "w": 0.20, "h": 0.32, "border": 5},
    "portal": {"x": 0.38, "y": 0.18, "w": 0.28, "h": 0.34, "border": 7},
    "dream": {"x": 0.16, "y": 0.08, "w": 0.68, "h": 0.46, "border": 4},
    "advertisement": {"x": 0.56, "y": 0.53, "w": 0.33, "h": 0.24, "border": 5},
    "background-screen": {"x": 0.04, "y": 0.05, "w": 0.92, "h": 0.55, "border": 3},
}


def _stable(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = json.loads(proc.stdout)
    video = next(
        (s for s in (raw.get("streams") or []) if s.get("codec_type") == "video"),
        None,
    )
    if not video:
        raise ValueError(f"No video stream: {path}")
    return {
        "durationSeconds": round(float((raw.get("format") or {}).get("duration") or 0), 6),
        "codec": video.get("codec_name"),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frameRate": str(video.get("r_frame_rate") or ""),
    }


def plan_from_dressing(
    dressing: dict,
    *,
    width: int,
    height: int,
    fps: int,
    duration_seconds: float,
    max_inserts: int = 4,
) -> dict:
    if dressing.get("schema") != "haunted-blender/parts-stage-dressing/v1":
        raise ValueError("Expected 008h stage dressing")
    if width < 64 or height < 64 or fps < 1 or duration_seconds <= 0:
        raise ValueError("Invalid moving-insert stage geometry")
    if max_inserts < 1 or max_inserts > 12:
        raise ValueError("max_inserts must be 1–12")

    rows = list(dressing.get("movingInserts") or [])[:max_inserts]
    role_cycle = ("television", "window", "portal", "advertisement")
    inserts = []

    for index, row in enumerate(rows):
        source = Path(str(row["path"])).expanduser().resolve(strict=True)
        if source.suffix.lower() not in {".mp4", ".mov", ".m4v", ".webm", ".mkv"}:
            raise ValueError("Moving Insert Stage accepts video ingredients only")
        observed_sha = _file_sha(source)
        if observed_sha != row["sha256"]:
            raise ValueError("Moving insert source bytes changed after harvest")

        role = role_cycle[index % len(role_cycle)]
        layout = ROLE_LAYOUTS[role]
        # Stagger the inserts so the stage has motion throughout without turning
        # into a wall of screens. The first television remains present longest.
        if index == 0:
            start = 0.0
            end = duration_seconds
        else:
            span = min(duration_seconds, max(1.2, duration_seconds * 0.46))
            centers = (index + 0.5) / max(2, len(rows) + 0.5)
            center = duration_seconds * centers
            start = max(0.0, center - span / 2)
            end = min(duration_seconds, start + span)
            start = max(0.0, end - span)

        inserts.append({
            "id": f"moving-insert-{index + 1:03d}",
            "role": role,
            "source": str(source),
            "sourceSha256": observed_sha,
            "harvestId": row.get("harvestId"),
            "kind": row.get("kind"),
            "sourceProvenanceSha256": row.get("sourceSha256"),
            "start": round(start, 6),
            "end": round(end, 6),
            "loop": True,
            "mute": True,
            "box": {
                "x": round(width * layout["x"]),
                "y": round(height * layout["y"]),
                "width": max(16, round(width * layout["w"])),
                "height": max(16, round(height * layout["h"])),
                "border": int(layout["border"]),
            },
        })

    body = {
        "schema": SCHEMA,
        "dressingId": dressing["id"],
        "canvas": {
            "width": int(width),
            "height": int(height),
            "fps": int(fps),
            "durationSeconds": float(duration_seconds),
        },
        "inserts": inserts,
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "MOVING INSERT != SCENE AUTHORITY",
            "INSERT AUDIO != PERFORMANCE AUDIO",
            "HARVESTED LOOP MAY REPEAT WITHOUT BECOMING NEW SOURCE",
            "MOVING SURFACE IS BOUNDED",
            "SOURCE SHA MUST MATCH HARVEST WITNESS",
        ],
    }
    return {**body, "id": "moving-insert-plan:" + _sha(body)[:24]}


def _filter_for_insert(index: int, insert: dict) -> str:
    box = insert["box"]
    w, h = int(box["width"]), int(box["height"])
    # Scale-and-crop to fill the cardboard surface. setpts resets each looped
    # ingredient to the composition clock before enable bounds are applied.
    return (
        f"[{index + 1}:v]"
        f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={w}:{h},setsar=1,setpts=PTS-STARTPTS"
        f"[ins{index}]"
    )


def render(
    base_video: str | Path,
    plan: dict,
    output_path: str | Path,
) -> dict:
    if plan.get("schema") != SCHEMA:
        raise ValueError("Expected moving-insert plan")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")

    base = Path(base_video).expanduser().resolve(strict=True)
    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Moving Insert Stage never overwrites")
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = plan["canvas"]
    duration = float(canvas["durationSeconds"])
    base_probe = _probe(base)
    if base_probe["durationSeconds"] + 0.06 < duration:
        raise ValueError("Base puppet movie does not cover insert plan duration")

    inserts = list(plan.get("inserts") or [])
    if not inserts:
        shutil.copy2(base, out)
        return {
            "schema": RECEIPT_SCHEMA,
            "status": "no-inserts-copy",
            "planId": plan["id"],
            "baseSha256": _file_sha(base),
            "outputSha256": _file_sha(out),
            "durationSeconds": _probe(out)["durationSeconds"],
            "insertCount": 0,
            "inserts": [],
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        }

    cmd = [
        "ffmpeg", "-nostdin", "-v", "error", "-y",
        "-i", str(base),
    ]
    for insert in inserts:
        # Explicit infinite input loop; the overlay remains bounded by enable.
        cmd += ["-stream_loop", "-1", "-i", str(Path(insert["source"]).resolve())]

    filters = []
    for i, insert in enumerate(inserts):
        filters.append(_filter_for_insert(i, insert))

    current = "[0:v]"
    for i, insert in enumerate(inserts):
        box = insert["box"]
        next_label = f"[stage{i}]"
        start = float(insert["start"])
        end = float(insert["end"])
        filters.append(
            f"{current}[ins{i}]overlay="
            f"x={int(box['x'])}:y={int(box['y'])}:"
            f"enable='between(t,{start:.6f},{end:.6f})'"
            f"{next_label}"
        )
        # Draw the construction-paper bezel *after* the moving pixels are placed.
        bezel = f"[bezel{i}]"
        border = max(2, int(box.get("border", 4)))
        filters.append(
            f"{next_label}drawbox="
            f"x={int(box['x'])-border}:y={int(box['y'])-border}:"
            f"w={int(box['width'])+border*2}:h={int(box['height'])+border*2}:"
            f"color=black@1:t={border}:"
            f"enable='between(t,{start:.6f},{end:.6f})'"
            f"{bezel}"
        )
        current = bezel

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", current,
        "-map", "0:a?",
        "-t", f"{duration:.6f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)

    observed = _probe(out)
    if observed["durationSeconds"] + 0.06 < duration:
        out.unlink(missing_ok=True)
        raise ValueError("Moving Insert Stage lost performance duration")

    receipt_inserts = []
    for insert in inserts:
        source = Path(insert["source"]).resolve()
        receipt_inserts.append({
            "id": insert["id"],
            "role": insert["role"],
            "sourceSha256": _file_sha(source),
            "sourceProvenanceSha256": insert.get("sourceProvenanceSha256"),
            "harvestId": insert.get("harvestId"),
            "start": insert["start"],
            "end": insert["end"],
            "box": insert["box"],
        })

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "scoped_complete",
        "adapter": "ffmpeg-moving-insert-stage/v1",
        "planId": plan["id"],
        "baseSha256": _file_sha(base),
        "outputSha256": _file_sha(out),
        "durationSeconds": observed["durationSeconds"],
        "insertCount": len(receipt_inserts),
        "inserts": receipt_inserts,
        "audioAuthority": "base-performance-only",
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "laws": [
            "INSERT AUDIO IS MUTED",
            "BASE PERFORMANCE RETAINS AUDIO AUTHORITY",
            "MOVING INSERT DOES NOT REPLACE BASE PERFORMANCE",
        ],
    }
    receipt_path = out.with_suffix(out.suffix + ".moving-inserts.json")
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt
