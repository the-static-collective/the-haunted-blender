"""FRANKEN BLENDER 008l — Material Surface Grammar.

Deterministic local material treatments for paper-stage still assets and motion
keyframes. Material is an aesthetic/compositional profile, not a physics claim.

Original source bytes remain authoritative. Materialized PNGs are explicit
derived assets with source SHA + profile witness.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "haunted-blender/material-profile/v1"
ASSET_SCHEMA = "haunted-blender/materialized-asset/v1"

PRESETS = {
    "paper": {
        "surface": {"posterize": 5, "grain": 0.035, "edge": 0.10, "gloss": 0.0},
        "motion": {"position": 1.0, "rotation": 1.0, "scale": 1.0, "lag": 0.0, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 0.90, "wideBias": 1.00, "insertBias": 0.90},
    },
    "cardboard": {
        "surface": {"posterize": 5, "grain": 0.075, "edge": 0.22, "corrugation": 0.16, "gloss": 0.0},
        "motion": {"position": 0.72, "rotation": 0.68, "scale": 0.35, "lag": 0.02, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 0.75, "wideBias": 1.20, "insertBias": 0.90},
    },
    "wood": {
        "surface": {"posterize": 6, "grain": 0.12, "edge": 0.20, "woodGrain": 0.22, "gloss": 0.04},
        "motion": {"position": 0.58, "rotation": 0.78, "scale": 0.22, "lag": 0.015, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 0.88, "wideBias": 1.25, "insertBias": 0.82},
    },
    "clay": {
        "surface": {"posterize": 7, "grain": 0.045, "edge": 0.04, "soften": 0.65, "gloss": 0.08},
        "motion": {"position": 1.03, "rotation": 0.92, "scale": 1.18, "lag": 0.035, "jitter": 0.012, "drift": 0.0},
        "directing": {"closeupBias": 1.35, "wideBias": 0.88, "insertBias": 0.85},
    },
    "felt": {
        "surface": {"posterize": 6, "grain": 0.11, "edge": 0.02, "fuzz": 0.26, "gloss": 0.0},
        "motion": {"position": 0.88, "rotation": 0.72, "scale": 0.90, "lag": 0.065, "jitter": 0.004, "drift": 0.0},
        "directing": {"closeupBias": 1.10, "wideBias": 1.00, "insertBias": 0.80},
    },
    "plastic": {
        "surface": {"posterize": 8, "grain": 0.015, "edge": 0.06, "gloss": 0.28},
        "motion": {"position": 1.05, "rotation": 1.05, "scale": 0.95, "lag": 0.0, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 1.10, "wideBias": 0.98, "insertBias": 1.12},
    },
    "foil": {
        "surface": {"posterize": 7, "grain": 0.15, "edge": 0.10, "gloss": 0.45, "foil": 0.34},
        "motion": {"position": 1.0, "rotation": 1.08, "scale": 1.0, "lag": 0.0, "jitter": 0.055, "drift": 0.0},
        "directing": {"closeupBias": 1.18, "wideBias": 0.75, "insertBias": 1.45},
    },
    "stone": {
        "surface": {"posterize": 5, "grain": 0.18, "edge": 0.24, "stone": 0.42, "gloss": 0.0},
        "motion": {"position": 0.28, "rotation": 0.28, "scale": 0.12, "lag": 0.11, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 0.95, "wideBias": 1.40, "insertBias": 0.75},
    },
    "wax": {
        "surface": {"posterize": 7, "grain": 0.028, "edge": 0.025, "soften": 0.42, "gloss": 0.18, "warm": 0.12},
        "motion": {"position": 0.84, "rotation": 0.74, "scale": 1.08, "lag": 0.055, "jitter": 0.006, "drift": 0.0},
        "directing": {"closeupBias": 1.28, "wideBias": 0.82, "insertBias": 0.90},
    },
    "inked": {
        "surface": {"posterize": 4, "grain": 0.02, "edge": 0.48, "ink": 0.55, "gloss": 0.0},
        "motion": {"position": 1.0, "rotation": 1.0, "scale": 1.0, "lag": 0.0, "jitter": 0.0, "drift": 0.0},
        "directing": {"closeupBias": 1.12, "wideBias": 1.05, "insertBias": 0.92},
    },
    "ghost": {
        "surface": {"posterize": 7, "grain": 0.015, "edge": 0.02, "ghost": 0.48, "gloss": 0.06},
        "motion": {"position": 0.88, "rotation": 0.58, "scale": 1.03, "lag": 0.04, "jitter": 0.012, "drift": 0.085},
        "directing": {"closeupBias": 1.05, "wideBias": 0.80, "insertBias": 1.18},
    },
    "junk-collage": {
        "surface": {"posterize": 5, "grain": 0.18, "edge": 0.30, "collage": 0.44, "gloss": 0.05},
        "motion": {"position": 1.0, "rotation": 1.12, "scale": 0.96, "lag": 0.0, "jitter": 0.07, "drift": 0.02},
        "directing": {"closeupBias": 1.05, "wideBias": 0.88, "insertBias": 1.36},
    },
}


def _stable(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def profile(value: str | dict | None, *, fallback: str = "paper") -> dict:
    if value is None:
        value = fallback
    if isinstance(value, str):
        kind = value.strip().lower()
        overrides = {}
    elif isinstance(value, dict):
        kind = str(value.get("type") or fallback).strip().lower()
        overrides = value
    else:
        raise ValueError("Material must be a preset name or object")
    if kind not in PRESETS:
        raise ValueError(f"Unknown material preset: {kind}")

    base = json.loads(json.dumps(PRESETS[kind]))
    for group in ("surface", "motion", "directing"):
        raw = overrides.get(group) if isinstance(overrides, dict) else None
        if isinstance(raw, dict):
            base[group].update({str(k): float(v) for k, v in raw.items()})
    body = {
        "schema": SCHEMA,
        "type": kind,
        "surface": base["surface"],
        "motion": base["motion"],
        "directing": base["directing"],
        "authority": "aesthetic-profile-only",
        "laws": [
            "MATERIAL != PHYSICS CLAIM",
            "SURFACE != SOURCE IDENTITY",
            "MOTION FEEL != MATERIAL MEASUREMENT",
        ],
    }
    return {**body, "id": "material:" + _hash(body)[:24]}


def _seed_bytes(source_sha: str, material_id: str) -> bytes:
    return hashlib.sha256(f"{source_sha}:{material_id}".encode("utf-8")).digest()


def _noise(seed: bytes, x: int, y: int, channel: int = 0) -> float:
    # Integer-only deterministic pseudo-noise. Stable across Python processes.
    n = (
        (x + 1) * 374761393
        + (y + 1) * 668265263
        + seed[channel % len(seed)] * 69069
    ) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 65535.0


def _surface_image(image, material: dict, *, source_sha: str):
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

    src = image.convert("RGBA")
    alpha = src.getchannel("A")
    rgb = src.convert("RGB")
    spec = material["surface"]
    seed = _seed_bytes(source_sha, material["id"])

    soften = float(spec.get("soften", 0))
    if soften > 0:
        rgb = rgb.filter(ImageFilter.GaussianBlur(radius=max(0.1, soften)))

    posterize = int(round(float(spec.get("posterize", 8))))
    posterize = max(2, min(8, posterize))
    if posterize < 8:
        rgb = ImageOps.posterize(rgb, posterize)

    if float(spec.get("ink", 0)) > 0:
        edge = rgb.convert("L").filter(ImageFilter.FIND_EDGES)
        edge = ImageOps.autocontrast(edge)
        edge = edge.point(lambda p: 255 if p > 36 else 0)
        dark = Image.new("RGB", rgb.size, (20, 20, 20))
        rgb = Image.composite(dark, rgb, edge)

    grain = float(spec.get("grain", 0))
    if grain > 0:
        px = rgb.load()
        for y in range(rgb.height):
            for x in range(rgb.width):
                r, g, b = px[x, y]
                delta = round((_noise(seed, x, y) - 0.5) * 255 * grain)
                px[x, y] = (
                    max(0, min(255, r + delta)),
                    max(0, min(255, g + delta)),
                    max(0, min(255, b + delta)),
                )

    wood = float(spec.get("woodGrain", 0))
    if wood > 0:
        draw = ImageDraw.Draw(rgb, "RGBA")
        stride = max(3, round(11 - wood * 18))
        for y in range(stride // 2, rgb.height, stride):
            wobble = round((_noise(seed, y, 7, 2) - 0.5) * 6)
            draw.line(
                [(0, y), (rgb.width // 3, y + wobble), (rgb.width, y - wobble)],
                fill=(70, 38, 18, round(90 * wood)),
                width=max(1, round(wood * 3)),
            )

    corr = float(spec.get("corrugation", 0))
    if corr > 0:
        draw = ImageDraw.Draw(rgb, "RGBA")
        stride = max(4, round(13 - corr * 18))
        for x in range(0, rgb.width, stride):
            draw.line((x, 0, x, rgb.height), fill=(55, 40, 28, round(100 * corr)), width=1)

    foil = float(spec.get("foil", 0))
    if foil > 0:
        draw = ImageDraw.Draw(rgb, "RGBA")
        for i in range(max(3, round(foil * 18))):
            x = round(_noise(seed, i, 3, 4) * max(1, rgb.width - 1))
            y = round(_noise(seed, i, 8, 5) * max(1, rgb.height - 1))
            length = max(8, round(rgb.width * (0.08 + 0.15 * _noise(seed, i, 12, 6))))
            draw.line((x, y, min(rgb.width, x + length), max(0, y - length // 3)), fill=(255, 255, 255, round(120 * foil)), width=2)

    stone = float(spec.get("stone", 0))
    if stone > 0:
        gray = ImageOps.grayscale(rgb)
        gray = ImageEnhance.Contrast(gray).enhance(1.15)
        tinted = ImageOps.colorize(gray, (45, 45, 44), (196, 193, 182))
        rgb = Image.blend(rgb, tinted, min(0.82, stone + 0.24))

    warm = float(spec.get("warm", 0))
    if warm > 0:
        warm_img = Image.new("RGB", rgb.size, (244, 170, 92))
        rgb = Image.blend(rgb, warm_img, min(0.28, warm))

    collage = float(spec.get("collage", 0))
    if collage > 0:
        draw = ImageDraw.Draw(rgb, "RGBA")
        for i in range(max(2, round(collage * 10))):
            x = round(_noise(seed, i, 17, 3) * max(1, rgb.width - 1))
            y = round(_noise(seed, i, 19, 7) * max(1, rgb.height - 1))
            w = max(3, round(rgb.width * (0.05 + 0.16 * _noise(seed, i, 23, 8))))
            h = max(2, round(rgb.height * (0.025 + 0.08 * _noise(seed, i, 29, 9))))
            tint = (238, 219, 171, round(115 * collage))
            draw.rectangle((x, y, min(rgb.width, x + w), min(rgb.height, y + h)), fill=tint)

    gloss = float(spec.get("gloss", 0))
    if gloss > 0:
        overlay = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        band = max(2, round(rgb.height * 0.15))
        draw.polygon(
            [(0, 0), (rgb.width, 0), (max(0, rgb.width - band * 2), band), (0, band * 2)],
            fill=(255, 255, 255, round(120 * gloss)),
        )
        base = rgb.convert("RGBA")
        base.alpha_composite(overlay)
        rgb = base.convert("RGB")

    fuzz = float(spec.get("fuzz", 0))
    if fuzz > 0:
        expanded = alpha.filter(ImageFilter.MaxFilter(size=3))
        halo = expanded.point(lambda p: round(p * min(0.55, fuzz)))
        fuzz_layer = Image.new("RGBA", src.size, (205, 198, 188, 0))
        fuzz_layer.putalpha(halo)
    else:
        fuzz_layer = None

    edge_amount = float(spec.get("edge", 0))
    if edge_amount > 0:
        edge = alpha.filter(ImageFilter.FIND_EDGES)
        edge = edge.point(lambda p: round(p * min(1.0, edge_amount * 2.2)))
        outline = Image.new("RGBA", src.size, (25, 23, 20, 0))
        outline.putalpha(edge)
    else:
        outline = None

    ghost = float(spec.get("ghost", 0))
    if ghost > 0:
        cool = Image.new("RGB", rgb.size, (205, 232, 238))
        rgb = Image.blend(rgb, cool, min(0.42, ghost))
        alpha = alpha.point(lambda p: round(p * (1.0 - min(0.58, ghost))))

    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    if fuzz_layer is not None:
        staged = Image.new("RGBA", result.size, (0, 0, 0, 0))
        staged.alpha_composite(fuzz_layer)
        staged.alpha_composite(result)
        result = staged
    if outline is not None:
        staged = Image.new("RGBA", result.size, (0, 0, 0, 0))
        staged.alpha_composite(outline)
        staged.alpha_composite(result)
        result = staged
    return result


def materialize_asset(
    source_path: str | Path,
    output_path: str | Path,
    material_value: str | dict | None,
) -> dict:
    from PIL import Image

    source = Path(source_path).expanduser().resolve(strict=True)
    output = Path(output_path).expanduser().resolve()
    if output.exists():
        raise FileExistsError("Materialized asset never overwrites")
    output.parent.mkdir(parents=True, exist_ok=True)

    source_sha = _file_sha(source)
    mat = profile(material_value)
    image = Image.open(source).convert("RGBA")
    treated = _surface_image(image, mat, source_sha=source_sha)
    treated.save(output)

    body = {
        "schema": ASSET_SCHEMA,
        "sourcePath": str(source),
        "sourceSha256": source_sha,
        "material": mat,
        "outputPath": str(output),
        "outputSha256": _file_sha(output),
        "cost": {"externalGenerations": 0, "providerCredits": 0, "usdMicros": 0},
        "laws": [
            "MATERIALIZED ASSET != ORIGINAL SOURCE",
            "SURFACE TREATMENT IS DETERMINISTIC",
            "ORIGINAL SOURCE SHA REMAINS AUTHORITY",
        ],
    }
    return {**body, "id": "materialized-asset:" + _hash(body)[:24]}


def _motion_value(material: dict, key: str, default: float) -> float:
    return float((material.get("motion") or {}).get(key, default))


def apply_motion(
    keyframes: list[dict],
    material_value: str | dict | None,
    *,
    fps: int,
    role: str = "",
) -> list[dict]:
    """Apply bounded motion feel around the first keyframe as rest state."""
    if not keyframes:
        return []
    mat = profile(material_value)
    pos = _motion_value(mat, "position", 1.0)
    rot = _motion_value(mat, "rotation", 1.0)
    scl = _motion_value(mat, "scale", 1.0)
    lag = max(0.0, _motion_value(mat, "lag", 0.0))
    jitter = max(0.0, _motion_value(mat, "jitter", 0.0))
    drift = _motion_value(mat, "drift", 0.0)

    ordered = [dict(row) for row in sorted(keyframes, key=lambda r: float(r["time"]))]
    rest = ordered[0]
    base_x = float(rest.get("x", 0))
    base_y = float(rest.get("y", 0))
    base_scale = float(rest.get("scale", 1))
    base_rot = float(rest.get("rotation", 0))

    transformed = []
    duration = max(float(row["time"]) for row in ordered)
    for index, row in enumerate(ordered):
        item = dict(row)
        t = float(item["time"])
        if index and lag:
            t = min(duration, t + lag)
        item["time"] = round(t, 6)

        if "x" in item:
            item["x"] = round(base_x + (float(item["x"]) - base_x) * pos, 6)
        if "y" in item:
            dy = (float(item["y"]) - base_y) * pos
            if drift and duration > 0:
                dy += math.sin((t / duration) * math.pi * 2) * 8.0 * drift
            item["y"] = round(base_y + dy, 6)
        if "rotation" in item:
            item["rotation"] = round(base_rot + (float(item["rotation"]) - base_rot) * rot, 6)
        if "scale" in item:
            delta = (float(item["scale"]) - base_scale) * scl
            # Clay/wax-like materials get a tiny deterministic breathing squash.
            if scl > 1.05 and duration > 0 and role in {"head", "body"}:
                delta += base_scale * 0.014 * math.sin((t / duration) * math.pi * 4)
            item["scale"] = round(max(0.001, base_scale + delta), 6)

        transformed.append(item)

        if jitter and 0 < t < duration:
            seed = hashlib.sha256(f"{mat['id']}:{role}:{index}".encode()).digest()
            amp = min(4.0, 32.0 * jitter)
            jt = min(duration, t + max(1.0 / max(1, fps), 0.03))
            j = dict(item)
            j["time"] = round(jt, 6)
            if "x" in j:
                j["x"] = round(float(j["x"]) + (seed[0] / 255.0 - 0.5) * amp, 6)
            if "y" in j:
                j["y"] = round(float(j["y"]) + (seed[1] / 255.0 - 0.5) * amp, 6)
            if "rotation" in j:
                j["rotation"] = round(float(j["rotation"]) + (seed[2] / 255.0 - 0.5) * amp * 1.5, 6)
            transformed.append(j)

    unique = {}
    for row in transformed:
        unique[round(float(row["time"]), 6)] = row
    return [unique[key] for key in sorted(unique)]


def directing_bias(material_value: str | dict | None) -> dict:
    mat = profile(material_value)
    return dict(mat["directing"])
