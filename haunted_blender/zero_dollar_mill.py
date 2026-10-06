"""FRANKEN BLENDER 008e — Zero-Dollar Film Mill.

Optimization order:

1. quantity / complete coverage
2. duration / usable seconds
3. quality / polish

The mill deliberately proves that a whole-song video can exist before any
finite-credit or paid generator is required.

FLOW PANTRY video bytes are treated as reusable ingredients. Deterministic
FFmpeg transformations manufacture bounded "slugs" until target duration is
fully covered. AI/provider footage may be added later as mutation fuel.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .flow_pantry import validate_flow_manifest

PLAN_SCHEMA = "haunted-blender/zero-dollar-film-plan/v1"
RECEIPT_SCHEMA = "haunted-blender/zero-dollar-film-receipt/v1"

DEFAULT_RECIPES = (
    "fit",
    "mirror",
    "reverse",
    "slow",
    "fast",
    "push",
    "kinetic-push",
    "pull",
    "misregister",
    "mirror-reverse",
    "soft-loop",
)


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _probe_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    duration = float(proc.stdout.strip())
    if duration <= 0:
        raise ValueError(f"Media duration is invalid: {path.name}")
    return duration


def _project_local(root: Path, path: str | Path, *, must_exist: bool = True) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = root / value
    value = value.expanduser().resolve(strict=must_exist)
    try:
        value.relative_to(root)
    except ValueError as exc:
        raise ValueError("Zero-Dollar Film Mill paths must stay inside project root") from exc
    return value


def _stable_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _plan_id(body: dict) -> str:
    return "zero-dollar-plan:" + hashlib.sha256(_stable_bytes(body)).hexdigest()[:24]


def target_duration(*, target_seconds: float | None = None, audio_path: str | Path | None = None) -> float:
    if target_seconds is not None:
        value = float(target_seconds)
        if value <= 0:
            raise ValueError("target_seconds must be positive")
        return round(value, 6)
    if audio_path is None:
        raise ValueError("Provide target_seconds or audio_path")
    return round(_probe_duration(Path(audio_path).expanduser().resolve(strict=True)), 6)


def build_plan(
    manifest: dict,
    source_root: str | Path,
    *,
    target_seconds: float,
    slug_seconds: float = 4.0,
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    recipes: tuple[str, ...] | list[str] = DEFAULT_RECIPES,
) -> dict:
    validate_flow_manifest(manifest)
    source_root = Path(source_root).expanduser().resolve(strict=True)
    target = float(target_seconds)
    slug = float(slug_seconds)
    if target <= 0 or slug <= 0:
        raise ValueError("target and slug durations must be positive")
    if int(width) < 64 or int(height) < 64 or int(fps) < 1:
        raise ValueError("Invalid render geometry")
    recipes = tuple(str(v) for v in recipes)
    unknown = [v for v in recipes if v not in DEFAULT_RECIPES]
    if unknown:
        raise ValueError("Unknown deterministic recipe(s): " + ", ".join(unknown))
    if not recipes:
        raise ValueError("At least one deterministic recipe is required")

    sources = []
    for item in manifest["items"]:
        path = (source_root / item["relativePath"]).resolve(strict=True)
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise ValueError("Flow Pantry item escaped source root") from exc
        if _sha_file(path) != item["sha256"]:
            raise ValueError(f"Flow Pantry source bytes changed: {item['relativePath']}")
        duration = (
            float((item.get("technical") or {}).get("durationSeconds"))
            if (item.get("technical") or {}).get("durationSeconds") is not None
            else _probe_duration(path)
        )
        sources.append(
            {
                "assetId": item["assetId"],
                "sha256": item["sha256"],
                "relativePath": item["relativePath"],
                "path": str(path),
                "durationSeconds": duration,
            }
        )

    slug_count = int(math.ceil(target / slug))
    slugs = []
    remaining = target
    for index in range(slug_count):
        source = sources[index % len(sources)]
        recipe = recipes[(index // len(sources) + index) % len(recipes)]
        duration = min(slug, remaining)
        src_duration = max(0.001, float(source["durationSeconds"]))
        # Spread starting points deterministically across long clips. Short clips
        # loop; looping is an explicit derivative, not an implied new source.
        seed = int(source["sha256"][:8], 16)
        available_start = max(0.0, src_duration - min(src_duration, slug * 1.6))
        phase = ((seed + index * 7919) % 10000) / 10000.0
        start = round(available_start * phase, 6)
        slugs.append(
            {
                "index": index + 1,
                "id": f"slug-{index + 1:04d}",
                "sourceAssetId": source["assetId"],
                "sourceSha256": source["sha256"],
                "sourceRelativePath": source["relativePath"],
                "sourceDurationSeconds": round(src_duration, 6),
                "sourceStartSeconds": start,
                "durationSeconds": round(duration, 6),
                "recipe": recipe,
                "externalGenerationCost": 0,
                "authority": "deterministic-derivative",
            }
        )
        remaining -= duration

    unique_sources = len({row["sourceSha256"] for row in slugs})
    body = {
        "schema": PLAN_SCHEMA,
        "optimizationOrder": ["quantity", "duration", "quality"],
        "targetSeconds": round(target, 6),
        "slugSeconds": round(slug, 6),
        "slugCount": slug_count,
        "plannedCoverageSeconds": round(sum(row["durationSeconds"] for row in slugs), 6),
        "coverageRatio": 1.0,
        "canvas": {"width": int(width), "height": int(height), "fps": int(fps)},
        "sourceCountAvailable": len(sources),
        "uniqueSourceCountPlanned": unique_sources,
        "recipes": list(recipes),
        "slugs": slugs,
        "cost": {
            "externalGenerations": 0,
            "providerCredits": 0,
            "usdMicros": 0,
            "class": "repeatable-local-zero-dollar",
        },
        "laws": [
            "COVERAGE BEFORE POLISH",
            "QUANTITY BEFORE DURATION BEFORE QUALITY",
            "DERIVATIVE != NEW SOURCE",
            "LOOP != NEW EVIDENCE",
            "LOCAL RENDER != PROVIDER GENERATION",
            "FULL COVERAGE != FINAL CUT",
        ],
    }
    return {**body, "id": _plan_id(body)}


def _recipe_filter(name: str, *, width: int, height: int, fps: int, duration: float) -> str:
    base = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={width}:{height},setsar=1,fps={fps}"
    )
    if name == "fit":
        return base
    if name == "mirror":
        return base + ",hflip"
    if name == "reverse":
        return base + ",reverse"
    if name == "slow":
        return base + ",setpts=1.35*PTS"
    if name == "fast":
        return base + ",setpts=0.75*PTS"
    if name == "push":
        # Scale up, then crop center. Cheap static reframing.
        return (
            f"scale={math.ceil(width*1.10)}:{math.ceil(height*1.10)}:"
            "force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={width}:{height},setsar=1,fps={fps}"
        )
    if name == "kinetic-push":
        # Real temporal motion from otherwise static footage. zoompan's zoom
        # state advances on each output frame; no external generation required.
        return (
            f"scale={math.ceil(width*1.18)}:{math.ceil(height*1.18)}:"
            "force_original_aspect_ratio=increase:flags=lanczos,"
            f"zoompan=z='min(zoom+0.004,1.16)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={width}x{height}:fps={fps},"
            "setsar=1"
        )
    if name == "pull":
        return (
            f"scale={math.ceil(width*0.92)}:{math.ceil(height*0.92)}:"
            "force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps={fps}"
        )
    if name == "misregister":
        return base + ",crop=iw-8:ih-8:4:4,pad=iw+8:ih+8:4:4:color=black"
    if name == "mirror-reverse":
        return base + ",hflip,reverse"
    if name == "soft-loop":
        # The input itself is looped; make the repeated use visually distinct.
        return base + ",eq=contrast=1.04:saturation=0.90"
    raise ValueError(f"Unknown recipe: {name}")


def render_plan(
    plan: dict,
    source_root: str | Path,
    output_dir: str | Path,
    *,
    audio_path: str | Path | None = None,
) -> dict:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("Unsupported Zero-Dollar Film Mill plan")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")
    source_root = Path(source_root).expanduser().resolve(strict=True)
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    slug_dir = output_dir / "slugs"
    slug_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / "zero-dollar-current-cut.mp4"
    if final.exists():
        raise FileExistsError("Zero-Dollar Film Mill never overwrites current-cut output")

    width = int(plan["canvas"]["width"])
    height = int(plan["canvas"]["height"])
    fps = int(plan["canvas"]["fps"])
    rendered = []

    for row in plan["slugs"]:
        source = (source_root / row["sourceRelativePath"]).resolve(strict=True)
        try:
            source.relative_to(source_root)
        except ValueError as exc:
            raise ValueError("Slug source escaped source root") from exc
        if _sha_file(source) != row["sourceSha256"]:
            raise ValueError("Slug source bytes changed after planning")
        out = slug_dir / f"{row['id']}-{row['recipe']}.mp4"
        if out.exists():
            raise FileExistsError(f"Slug output already exists: {out.name}")
        duration = float(row["durationSeconds"])
        # Stream-loop makes even a tiny ingredient capable of feeding arbitrary
        # duration. The output is always bounded back to the planned slug.
        input_span = max(duration * 1.8, duration + 1.0)
        vf = _recipe_filter(
            row["recipe"], width=width, height=height, fps=fps, duration=duration
        )
        cmd = [
            "ffmpeg", "-nostdin", "-v", "error", "-y",
            "-stream_loop", "-1",
            "-ss", f"{float(row['sourceStartSeconds']):.6f}",
            "-i", str(source),
            "-t", f"{input_span:.6f}",
            "-vf", vf,
            "-t", f"{duration:.6f}",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(out),
        ]
        subprocess.run(cmd, check=True)
        rendered.append(
            {
                **row,
                "outputPath": str(out),
                "outputSha256": _sha_file(out),
                "observedDurationSeconds": round(_probe_duration(out), 6),
            }
        )

    with tempfile.TemporaryDirectory(prefix="zero-dollar-join-") as td:
        temp = Path(td)
        concat = temp / "playlist.txt"
        concat.write_text(
            "".join(f"file '{Path(item['outputPath']).as_posix()}'\n" for item in rendered),
            encoding="utf-8",
        )
        joined = temp / "joined.mp4"
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-v", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat),
                "-t", f"{float(plan['targetSeconds']):.6f}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", str(joined),
            ],
            check=True,
        )
        if audio_path is not None:
            audio = Path(audio_path).expanduser().resolve(strict=True)
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error", "-y",
                    "-i", str(joined), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-shortest",
                    "-movflags", "+faststart", str(final),
                ],
                check=True,
            )
        else:
            shutil.copy2(joined, final)

    observed = round(_probe_duration(final), 6)
    target = float(plan["targetSeconds"])
    source_seconds = sum(
        min(float(row["sourceDurationSeconds"]), float(row["durationSeconds"]))
        for row in plan["slugs"]
    )
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "planId": plan["id"],
        "status": "full-zero-dollar-coverage",
        "outputPath": str(final),
        "outputSha256": _sha_file(final),
        "targetSeconds": round(target, 6),
        "observedOutputSeconds": observed,
        "coverageRatio": round(min(1.0, observed / target), 6),
        "slugCount": len(rendered),
        "uniqueSourceCount": len({row["sourceSha256"] for row in rendered}),
        "recipeCountUsed": len({row["recipe"] for row in rendered}),
        "derivedOutputSeconds": round(sum(row["observedDurationSeconds"] for row in rendered), 6),
        "sourceSecondsNominallyConsumed": round(source_seconds, 6),
        "derivativeYield": round(
            sum(row["observedDurationSeconds"] for row in rendered) / max(0.001, source_seconds),
            6,
        ),
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "audio": str(Path(audio_path).expanduser().resolve()) if audio_path else None,
        "slugs": rendered,
        "laws": [
            "FULL ZERO-DOLLAR COVERAGE PROVEN",
            "COVERAGE != POLISH",
            "DERIVATIVE YIELD != NEW EVIDENCE",
            "AI MUTATION MAY REPLACE WINDOWS LATER",
        ],
    }
    receipt_path = output_dir / "zero-dollar-current-cut.receipt.json"
    if receipt_path.exists():
        final.unlink(missing_ok=True)
        raise FileExistsError("Zero-Dollar Film Mill never overwrites receipt")
    tmp = receipt_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, receipt_path)
    return receipt
