"""Deterministic limited-animation compositor for layered still assets.

This is intentionally boring machinery: local image layers + authored transforms
become frames. Expensive/generated video is a separate awakening, not the default.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

SCHEMA = "haunted-blender/cutout-stage/v1"
RECEIPT_SCHEMA = "haunted-blender/cutout-render-receipt/v1"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _state(layer: dict, t: float) -> dict:
    base = {
        "x": float(layer.get("x", 0)),
        "y": float(layer.get("y", 0)),
        "scale": float(layer.get("scale", 1)),
        "rotation": float(layer.get("rotation", 0)),
        "opacity": float(layer.get("opacity", 1)),
    }
    raw = sorted(layer.get("keyframes") or [], key=lambda k: float(k["time"]))
    if not raw:
        return base

    states = []
    current = dict(base)
    for keyframe in raw:
        current = {**current, **{k: float(v) for k, v in keyframe.items() if k != "time"}}
        states.append((float(keyframe["time"]), dict(current)))

    if t <= states[0][0]:
        return states[0][1]
    if t >= states[-1][0]:
        return states[-1][1]

    for (ta, a), (tb, b) in zip(states, states[1:]):
        if ta <= t <= tb:
            u = 0.0 if tb == ta else (t - ta) / (tb - ta)
            return {key: a[key] + (b[key] - a[key]) * u for key in base}
    return states[-1][1]


def _validate(plan: dict) -> dict:
    if not isinstance(plan, dict) or plan.get("schema") != SCHEMA:
        raise ValueError("Unsupported cutout-stage plan.")
    canvas = plan.get("canvas") or {}
    width = int(canvas.get("width", 0))
    height = int(canvas.get("height", 0))
    fps = int(canvas.get("fps", 0))
    duration = float(canvas.get("duration", 0))
    if width < 16 or height < 16 or fps < 1 or duration <= 0:
        raise ValueError("Invalid cutout-stage canvas.")
    layers = plan.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValueError("Cutout-stage requires at least one layer.")
    ids = set()
    for layer in layers:
        lid = str(layer.get("id") or "")
        if not lid or lid in ids:
            raise ValueError("Cutout layer ids must be unique and nonempty.")
        ids.add(lid)
        source = Path(str(layer.get("source") or "")).expanduser()
        if not source.is_file():
            raise ValueError(f"Missing cutout source for {lid}.")
        if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Cutout v1 accepts still-image layers only.")
        for keyframe in layer.get("keyframes") or []:
            when = float(keyframe["time"])
            if when < 0 or when > duration:
                raise ValueError("Keyframe time is outside the composition.")
    return plan


def render_cutout(plan: dict, output_path: str | Path) -> dict:
    _validate(plan)
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for cutout rendering.") from exc
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for cutout rendering.")

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("Cutout renderer never overwrites an existing output.")
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = plan["canvas"]
    width, height = int(canvas["width"]), int(canvas["height"])
    fps, duration = int(canvas["fps"]), float(canvas["duration"])
    frame_count = int(math.ceil(duration * fps))

    prepared = []
    receipt_layers = []
    for layer in sorted(plan["layers"], key=lambda item: (int(item.get("z", 0)), str(item["id"]))):
        source = Path(layer["source"]).expanduser().resolve()
        digest = _sha256(source)
        image = Image.open(source).convert("RGBA")
        prepared.append((layer, image, source, digest))
        receipt_layers.append(
            {
                "id": layer["id"],
                "sourceSha256": digest,
                "sourceAuthoritySha256": layer.get("sourceAuthoritySha256"),
                "material": layer.get("material"),
                "materializedAssetId": layer.get("materializedAssetId"),
                "byteLength": source.stat().st_size,
                "z": int(layer.get("z", 0)),
            }
        )

    digest_plan = {
        "schema": SCHEMA,
        "canvas": {
            "width": width, "height": height, "fps": fps, "duration": duration,
        },
        "layers": [
            {
                "id": layer["id"],
                "sourceSha256": digest,
                "sourceAuthoritySha256": layer.get("sourceAuthoritySha256"),
                "material": layer.get("material"),
                "materializedAssetId": layer.get("materializedAssetId"),
                "z": int(layer.get("z", 0)),
                "x": float(layer.get("x", 0)),
                "y": float(layer.get("y", 0)),
                "scale": float(layer.get("scale", 1)),
                "rotation": float(layer.get("rotation", 0)),
                "opacity": float(layer.get("opacity", 1)),
                "keyframes": layer.get("keyframes") or [],
            }
            for layer, _image, _source, digest in prepared
        ],
    }
    plan_sha = hashlib.sha256(_canonical_bytes(digest_plan)).hexdigest()

    with tempfile.TemporaryDirectory(prefix="haunted-blender-cutout-") as temp:
        temp_dir = Path(temp)
        for frame_index in range(frame_count):
            t = frame_index / fps
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            for layer, original, _source, _digest in prepared:
                state = _state(layer, t)
                scale = max(0.001, state["scale"])
                target_w = max(1, round(original.width * scale))
                target_h = max(1, round(original.height * scale))
                img = original.resize((target_w, target_h), Image.Resampling.LANCZOS)
                if state["rotation"]:
                    img = img.rotate(
                        -state["rotation"],
                        resample=Image.Resampling.BICUBIC,
                        expand=True,
                    )
                opacity = min(1.0, max(0.0, state["opacity"]))
                if opacity < 1:
                    alpha = img.getchannel("A").point(lambda value: round(value * opacity))
                    img.putalpha(alpha)
                frame.alpha_composite(img, (round(state["x"]), round(state["y"])))
            frame.convert("RGB").save(temp_dir / f"frame-{frame_index:06d}.png")

        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-framerate", str(fps),
                "-i", str(temp_dir / "frame-%06d.png"),
                "-frames:v", str(frame_count),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(out),
            ],
            check=True,
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "scoped_complete",
        "adapter": "pillow-cutout+ffmpeg/v1",
        "planSha256": plan_sha,
        "outputSha256": _sha256(out),
        "outputByteLength": out.stat().st_size,
        "frameCount": frame_count,
        "fps": fps,
        "durationSeconds": duration,
        "audioAuthority": "none",
        "layers": receipt_layers,
    }
    return receipt
