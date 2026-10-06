"""FRANKEN BLENDER 008h — Parts Harvester / Compost Mill.

Explodes one owned video into many traceable deterministic ingredients.

The harvester intentionally avoids semantic claims. It can make stills, crops,
textures, threshold masks, loops, transition fragments, palettes, and low-res
motion signatures, but it does not claim that a crop is a character, a mask is
an object segmentation, or a motion centroid belongs to a specific object.

Every derivative binds the source SHA-256 and transform recipe.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from statistics import mean
from typing import Any

SCHEMA = "haunted-blender/parts-harvest/v1"
DRAWER_SCHEMA = "haunted-blender/parts-drawer/v1"
BEHAVIOR_SCHEMA = "haunted-blender/motion-behavior/v1"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


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
            "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate",
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
        raise ValueError("No video stream")
    duration = float((raw.get("format") or {}).get("duration") or 0)
    if duration <= 0:
        raise ValueError("Video duration is invalid")
    return {
        "durationSeconds": round(duration, 6),
        "codec": video.get("codec_name"),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "frameRate": str(video.get("r_frame_rate") or ""),
    }


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _frame_at(source: Path, out: Path, at: float, *, width: int | None = None) -> None:
    vf = []
    if width:
        vf.append(f"scale={int(width)}:-2:flags=lanczos")
    args = [
        "ffmpeg", "-nostdin", "-v", "error", "-y",
        "-ss", f"{max(0.0, at):.6f}", "-i", str(source),
        "-frames:v", "1",
    ]
    if vf:
        args += ["-vf", ",".join(vf)]
    args += [str(out)]
    _run(args)


def _clip(
    source: Path,
    out: Path,
    *,
    start: float,
    duration: float,
    width: int = 640,
    reverse: bool = False,
    pingpong: bool = False,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if pingpong:
        forward = out.with_name(out.stem + ".forward.mp4")
        reverse_path = out.with_name(out.stem + ".reverse.mp4")
        concat = out.with_name(out.stem + ".concat.txt")
        _clip(source, forward, start=start, duration=duration, width=width)
        _clip(source, reverse_path, start=start, duration=duration, width=width, reverse=True)
        concat.write_text(
            f"file '{forward.as_posix()}'\nfile '{reverse_path.as_posix()}'\n",
            encoding="utf-8",
        )
        try:
            _run([
                "ffmpeg", "-nostdin", "-v", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(out),
            ])
        finally:
            forward.unlink(missing_ok=True)
            reverse_path.unlink(missing_ok=True)
            concat.unlink(missing_ok=True)
        return

    vf = [f"scale={int(width)}:-2:flags=lanczos", "setsar=1"]
    if reverse:
        vf.append("reverse")
    _run([
        "ffmpeg", "-nostdin", "-v", "error", "-y",
        "-ss", f"{max(0.0, start):.6f}", "-i", str(source),
        "-t", f"{max(0.1, duration):.6f}",
        "-vf", ",".join(vf),
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out),
    ])


def _raw_frames(
    source: Path,
    *,
    sample_fps: int = 4,
    width: int = 64,
    height: int = 36,
) -> list[bytes]:
    proc = subprocess.run(
        [
            "ffmpeg", "-nostdin", "-v", "error",
            "-i", str(source),
            "-vf", f"fps={sample_fps},scale={width}:{height},format=gray",
            "-f", "rawvideo", "-pix_fmt", "gray", "-",
        ],
        check=True,
        capture_output=True,
    )
    size = width * height
    usable = len(proc.stdout) - (len(proc.stdout) % size)
    return [
        proc.stdout[i:i + size]
        for i in range(0, usable, size)
        if len(proc.stdout[i:i + size]) == size
    ]


def _motion_signature(
    source: Path,
    *,
    sample_fps: int = 4,
    width: int = 64,
    height: int = 36,
) -> dict:
    frames = _raw_frames(source, sample_fps=sample_fps, width=width, height=height)
    if len(frames) < 2:
        return {
            "schema": BEHAVIOR_SCHEMA,
            "sampleFps": sample_fps,
            "width": width,
            "height": height,
            "samples": [],
            "meanEnergy": 0.0,
            "peakEnergy": 0.0,
        }

    samples = []
    for index in range(1, len(frames)):
        a, b = frames[index - 1], frames[index]
        diffs = [abs(x - y) for x, y in zip(a, b)]
        total = sum(diffs)
        energy = total / (len(diffs) * 255.0)
        if total:
            sx = 0.0
            sy = 0.0
            for i, value in enumerate(diffs):
                x = i % width
                y = i // width
                sx += x * value
                sy += y * value
            cx = sx / total / max(1, width - 1)
            cy = sy / total / max(1, height - 1)
        else:
            cx, cy = 0.5, 0.5
        samples.append({
            "atSeconds": round(index / sample_fps, 6),
            "energy": round(energy, 8),
            "changeCentroidX": round(cx, 6),
            "changeCentroidY": round(cy, 6),
        })

    energies = [s["energy"] for s in samples]
    body = {
        "schema": BEHAVIOR_SCHEMA,
        "sampleFps": sample_fps,
        "width": width,
        "height": height,
        "samples": samples,
        "meanEnergy": round(mean(energies), 8),
        "peakEnergy": round(max(energies), 8),
        "laws": [
            "CHANGE CENTROID != OBJECT TRACK",
            "MOTION SIGNATURE != SEMANTIC MOTION",
            "BEHAVIOR MAY BE REUSED WITHOUT CLAIMING IDENTITY",
        ],
    }
    return {**body, "id": "motion-behavior:" + _sha(body)[:24]}


def _palette(frame_path: Path, *, count: int = 8) -> list[str]:
    from PIL import Image

    image = Image.open(frame_path).convert("RGB")
    image.thumbnail((160, 160))
    quant = image.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    palette = quant.getpalette()
    colors = quant.getcolors() or []
    colors.sort(reverse=True)
    result = []
    for _, index in colors[:count]:
        r, g, b = palette[index * 3:index * 3 + 3]
        result.append(f"#{r:02x}{g:02x}{b:02x}")
    return result


def _derive_still_bits(frame_path: Path, output_dir: Path, *, label: str) -> list[dict]:
    from PIL import Image, ImageEnhance, ImageFilter

    image = Image.open(frame_path).convert("RGBA")
    w, h = image.size
    bits = []

    def save(kind: str, name: str, img: Image.Image, recipe: dict):
        out = output_dir / f"{label}-{name}.png"
        img.save(out)
        bits.append({
            "kind": kind,
            "path": str(out),
            "sha256": _file_sha(out),
            "recipe": recipe,
        })

    # Center crop and four quadrant-ish crops.
    crop_w = max(32, round(w * 0.62))
    crop_h = max(32, round(h * 0.62))
    anchors = {
        "center": ((w - crop_w) // 2, (h - crop_h) // 2),
        "nw": (0, 0),
        "ne": (max(0, w - crop_w), 0),
        "sw": (0, max(0, h - crop_h)),
        "se": (max(0, w - crop_w), max(0, h - crop_h)),
    }
    for name, (x, y) in anchors.items():
        crop = image.crop((x, y, x + crop_w, y + crop_h))
        save(
            "crop",
            f"crop-{name}",
            crop,
            {"op": "crop", "anchor": name, "box": [x, y, x + crop_w, y + crop_h]},
        )

    # Texture: small repeated-looking patches, blurred and contrast variants.
    patch = image.crop(
        (
            max(0, (w - crop_w) // 2),
            max(0, (h - crop_h) // 2),
            min(w, (w + crop_w) // 2),
            min(h, (h + crop_h) // 2),
        )
    ).resize((256, 256))
    save("texture", "texture-clean", patch, {"op": "center-texture", "size": [256, 256]})
    save(
        "texture",
        "texture-soft",
        patch.filter(ImageFilter.GaussianBlur(radius=4)),
        {"op": "center-texture-blur", "radius": 4},
    )
    save(
        "texture",
        "texture-hard",
        ImageEnhance.Contrast(patch).enhance(1.8),
        {"op": "center-texture-contrast", "factor": 1.8},
    )

    # Threshold masks: deliberately not semantic segmentation.
    gray = image.convert("L")
    for threshold, name in ((64, "dark"), (128, "mid"), (192, "light")):
        alpha = gray.point(lambda p, t=threshold: 255 if p >= t else 0)
        mask = Image.new("RGBA", image.size, (255, 255, 255, 0))
        mask.putalpha(alpha)
        save(
            "mask",
            f"mask-{name}",
            mask,
            {"op": "luminance-threshold", "threshold": threshold, "semantic": False},
        )

    return bits


def harvest(
    source_path: str | Path,
    output_dir: str | Path,
    *,
    still_count: int = 6,
    loop_seconds: float = 1.5,
    fragment_seconds: float = 0.8,
    sample_fps: int = 4,
) -> dict:
    source = Path(source_path).expanduser().resolve(strict=True)
    if source.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValueError("Unsupported source video")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")
    if still_count < 3 or still_count > 24:
        raise ValueError("still_count must be 3–24")

    root = Path(output_dir).expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("Parts Harvester output directory must be empty")
    root.mkdir(parents=True, exist_ok=True)

    technical = _probe(source)
    duration = technical["durationSeconds"]
    source_sha = _file_sha(source)
    source_id = f"source-video:{source_sha}"

    still_dir = root / "stills"
    bit_dir = root / "bits"
    loop_dir = root / "loops"
    fragment_dir = root / "fragments"
    for folder in (still_dir, bit_dir, loop_dir, fragment_dir):
        folder.mkdir(parents=True, exist_ok=True)

    stills = []
    for index in range(still_count):
        fraction = (index + 0.5) / still_count
        at = min(max(0.0, duration * fraction), max(0.0, duration - 0.02))
        out = still_dir / f"still-{index + 1:03d}.png"
        _frame_at(source, out, at)
        stills.append({
            "kind": "still",
            "index": index + 1,
            "atSeconds": round(at, 6),
            "path": str(out),
            "sha256": _file_sha(out),
            "sourceSha256": source_sha,
            "recipe": {"op": "frame", "atSeconds": round(at, 6)},
        })

    bits = []
    for still in stills[: min(3, len(stills))]:
        label = f"still-{still['index']:03d}"
        derived = _derive_still_bits(Path(still["path"]), bit_dir, label=label)
        for item in derived:
            item["sourceSha256"] = source_sha
            item["parentStillSha256"] = still["sha256"]
            bits.append(item)

    mid = max(0.0, duration / 2 - loop_seconds / 2)
    loop_duration = min(loop_seconds, duration)
    loops = []
    for kind, reverse, pingpong in (
        ("forward-loop", False, False),
        ("reverse-loop", True, False),
        ("pingpong-loop", False, True),
    ):
        out = loop_dir / f"{kind}.mp4"
        _clip(
            source,
            out,
            start=mid,
            duration=loop_duration,
            reverse=reverse,
            pingpong=pingpong,
        )
        loops.append({
            "kind": "loop",
            "variant": kind,
            "path": str(out),
            "sha256": _file_sha(out),
            "sourceSha256": source_sha,
            "sourceStartSeconds": round(mid, 6),
            "sourceDurationSeconds": round(loop_duration, 6),
            "recipe": {
                "op": kind,
                "start": round(mid, 6),
                "duration": round(loop_duration, 6),
            },
        })

    frag = min(fragment_seconds, duration)
    fragments = []
    for name, start in (
        ("entrance", 0.0),
        ("middle", max(0.0, duration / 2 - frag / 2)),
        ("exit", max(0.0, duration - frag)),
    ):
        out = fragment_dir / f"{name}.mp4"
        _clip(source, out, start=start, duration=frag)
        fragments.append({
            "kind": "fragment",
            "variant": name,
            "path": str(out),
            "sha256": _file_sha(out),
            "sourceSha256": source_sha,
            "sourceStartSeconds": round(start, 6),
            "sourceDurationSeconds": round(frag, 6),
            "recipe": {
                "op": "bounded-fragment",
                "variant": name,
                "start": round(start, 6),
                "duration": round(frag, 6),
            },
        })

    behavior = _motion_signature(source, sample_fps=sample_fps)
    behavior_path = root / "motion-behavior.json"
    behavior_path.write_text(
        json.dumps(behavior, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    palette = _palette(Path(stills[len(stills) // 2]["path"]))
    palette_path = root / "palette.json"
    palette_body = {
        "schema": "haunted-blender/palette-sample/v1",
        "sourceSha256": source_sha,
        "colors": palette,
        "authority": "sampled-color-only",
    }
    palette_path.write_text(
        json.dumps(palette_body, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    all_artifacts = [
        *stills,
        *bits,
        *loops,
        *fragments,
        {
            "kind": "motion-behavior",
            "path": str(behavior_path),
            "sha256": _file_sha(behavior_path),
            "sourceSha256": source_sha,
            "recipe": {"op": "low-res-frame-difference-signature"},
        },
        {
            "kind": "palette",
            "path": str(palette_path),
            "sha256": _file_sha(palette_path),
            "sourceSha256": source_sha,
            "recipe": {"op": "median-cut-palette", "colors": len(palette)},
        },
    ]

    body = {
        "schema": SCHEMA,
        "source": {
            "id": source_id,
            "path": str(source),
            "sha256": source_sha,
            "technical": technical,
        },
        "counts": {
            "stills": len(stills),
            "crops": sum(1 for x in bits if x["kind"] == "crop"),
            "textures": sum(1 for x in bits if x["kind"] == "texture"),
            "masks": sum(1 for x in bits if x["kind"] == "mask"),
            "loops": len(loops),
            "fragments": len(fragments),
            "motionBehaviors": 1,
            "palettes": 1,
            "totalArtifacts": len(all_artifacts),
        },
        "artifacts": all_artifacts,
        "derivativeYieldCount": len(all_artifacts),
        "cost": {
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
        },
        "laws": [
            "PART != SOURCE",
            "DERIVATIVE != NEW EVIDENCE",
            "CROP != OBJECT IDENTITY",
            "MASK != SEMANTIC SEGMENTATION",
            "CHANGE CENTROID != OBJECT TRACK",
            "BEHAVIOR != APPEARANCE",
            "EVERY HARVESTED ARTIFACT BINDS SOURCE SHA256",
        ],
    }
    result = {**body, "id": "parts-harvest:" + _sha(body)[:24]}
    manifest_path = root / "harvest.json"
    manifest_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _artifact_key(row: dict) -> tuple:
    return (
        str(row.get("sourceSha256") or ""),
        str(row.get("kind") or ""),
        str(row.get("sha256") or ""),
    )


def build_drawer(harvests: list[dict], output_path: str | Path) -> dict:
    if not harvests:
        raise ValueError("Parts drawer needs at least one harvest")
    artifacts = []
    source_ids = []
    seen = set()
    for harvest in harvests:
        if harvest.get("schema") != SCHEMA:
            raise ValueError("Unsupported harvest")
        source_ids.append(harvest["source"]["id"])
        for row in harvest.get("artifacts") or []:
            key = _artifact_key(row)
            if key in seen:
                continue
            seen.add(key)
            artifacts.append({
                **row,
                "harvestId": harvest["id"],
            })

    by_kind: dict[str, int] = {}
    for row in artifacts:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1

    body = {
        "schema": DRAWER_SCHEMA,
        "sourceCount": len(set(source_ids)),
        "harvestIds": [h["id"] for h in harvests],
        "artifactCount": len(artifacts),
        "byKind": by_kind,
        "artifacts": artifacts,
        "laws": [
            "DRAWER INDEX != SELECTION",
            "MORE PARTS != MORE SOURCE AUTHORITY",
            "REUSE PRESERVES ORIGINAL PROVENANCE",
        ],
    }
    result = {**body, "id": "parts-drawer:" + _sha(body)[:24]}
    path = Path(output_path).expanduser().resolve()
    if path.exists():
        raise FileExistsError("Parts drawer never overwrites")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def select_for_stage(
    drawer: dict,
    *,
    roles: tuple[str, ...] = ("poster", "screen", "texture", "cutaway", "motion"),
    max_per_role: int = 3,
) -> dict:
    if drawer.get("schema") != DRAWER_SCHEMA:
        raise ValueError("Expected parts drawer")
    if max_per_role < 1 or max_per_role > 20:
        raise ValueError("max_per_role must be 1–20")

    preferred = {
        "poster": ("still", "crop", "palette"),
        "screen": ("loop", "fragment"),
        "texture": ("texture", "mask", "crop"),
        "cutaway": ("fragment", "still", "crop"),
        "motion": ("motion-behavior", "loop"),
    }
    artifacts = drawer.get("artifacts") or []
    selection = {}
    for role in roles:
        kinds = preferred.get(role, ())
        rows = []
        used_sources = set()
        for kind in kinds:
            for row in artifacts:
                if row.get("kind") != kind:
                    continue
                source = row.get("sourceSha256")
                if source in used_sources and len(rows) < max_per_role - 1:
                    continue
                rows.append({
                    "role": role,
                    "kind": row["kind"],
                    "path": row["path"],
                    "sha256": row["sha256"],
                    "sourceSha256": source,
                    "harvestId": row["harvestId"],
                })
                used_sources.add(source)
                if len(rows) >= max_per_role:
                    break
            if len(rows) >= max_per_role:
                break
        selection[role] = rows

    body = {
        "schema": "haunted-blender/parts-stage-selection/v1",
        "drawerId": drawer["id"],
        "selection": selection,
        "authority": "proposal-only",
        "laws": [
            "SELECTION != EDITORIAL KEEP",
            "ROLE != SEMANTIC IDENTITY",
            "SCREEN MATERIAL MAY REMAIN MOVING",
            "POSTER MAY BE A FREEZE FRAME",
        ],
    }
    return {**body, "id": "parts-stage-selection:" + _sha(body)[:24]}
