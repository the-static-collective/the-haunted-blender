"""FRANKEN BLENDER 008p — Owned Pixel Manga Film.

008p proves that an explicitly admitted, hash-bound derivative of a user-declared
owned Drive image can materially participate in every frame of the 008n/008o
Page Five film while narrative custody remains separate.

The donor image is a shared visual staging surface. Crop windows are editorial
framing choices, not semantic segmentation or character identity claims.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import manga_film, narrative_performance

DONOR_SCHEMA = "haunted-blender/owned-pixel-donor/v1"
RECEIPT_SCHEMA = "haunted-blender/owned-pixel-manga-film-receipt/v1"


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _stable(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash(value: object) -> str:
    return hashlib.sha256(_stable(value)).hexdigest()


def _read_json(path: str | Path) -> tuple[Path, dict]:
    p = Path(path).expanduser().resolve(strict=True)
    return p, json.loads(p.read_text(encoding="utf-8"))


def load_donor(manifest_path: str | Path) -> dict:
    """Decode and verify the exact repo-local derivative donor bytes."""
    from PIL import Image

    path, manifest = _read_json(manifest_path)
    if manifest.get("schema") != DONOR_SCHEMA:
        raise ValueError("Expected owned-pixel donor manifest")

    derivative = manifest.get("derivative") or {}
    if derivative.get("encoding") != "base64-file":
        raise ValueError("008p donor must use base64-file encoding")

    # manifests live at <repo>/specimens/008p/*.donor.json
    repo_root = path.parents[2]
    encoded_path = repo_root / str(derivative.get("path") or "")
    encoded_path = encoded_path.resolve(strict=True)
    encoded = encoded_path.read_text(encoding="utf-8").strip()
    raw = base64.b64decode(encoded, validate=True)

    observed_sha = hashlib.sha256(raw).hexdigest()
    if observed_sha != derivative.get("sha256"):
        raise ValueError("Owned pixel derivative SHA mismatch")
    if len(raw) != int(derivative.get("byteLength") or -1):
        raise ValueError("Owned pixel derivative byte length mismatch")

    image = Image.open(io.BytesIO(raw)).convert("RGB")
    expected_size = (
        int(derivative.get("width") or 0),
        int(derivative.get("height") or 0),
    )
    if image.size != expected_size:
        raise ValueError("Owned pixel derivative dimensions mismatch")

    return {
        "manifestPath": str(path),
        "manifest": manifest,
        "image": image,
        "raw": raw,
        "derivativeSha256": observed_sha,
        "encodedPath": str(encoded_path),
    }


# These are manual staging windows into the *shared donor composition*.
# They deliberately do not claim semantic object/character segmentation.
_CROP_WINDOWS = (
    (0.54, 0.52, 0.96, 0.98),  # guitar-side activity
    (0.24, 0.59, 0.77, 1.00),  # table / cup field
    (0.31, 0.52, 0.63, 0.94),  # human-scale listening field
    (0.18, 0.36, 0.66, 0.87),  # bus body / interior field
    (0.31, 0.66, 0.79, 1.00),  # table / hands field
    (0.18, 0.34, 0.66, 0.73),  # bus window field
    (0.47, 0.33, 0.81, 0.84),  # bus door / front field
    (0.00, 0.00, 1.00, 1.00),  # whole composition return
)


def _crop_box(index: int, width: int, height: int, u: float) -> tuple[int, int, int, int]:
    x1f, y1f, x2f, y2f = _CROP_WINDOWS[min(index, len(_CROP_WINDOWS) - 1)]
    # tiny deterministic Ken Burns drift within the authored window
    drift_x = math.sin(u * math.pi) * 0.012
    drift_y = math.cos(u * math.pi) * 0.008
    span_x = x2f - x1f
    span_y = y2f - y1f
    x1f = min(max(0.0, x1f + drift_x), max(0.0, 1.0 - span_x))
    y1f = min(max(0.0, y1f + drift_y), max(0.0, 1.0 - span_y))
    x2f = x1f + span_x
    y2f = y1f + span_y
    x1 = max(0, min(width - 2, round(x1f * width)))
    y1 = max(0, min(height - 2, round(y1f * height)))
    x2 = max(x1 + 1, min(width, round(x2f * width)))
    y2 = max(y1 + 1, min(height, round(y2f * height)))
    return x1, y1, x2, y2


def _owned_frame(plan: dict, donor_image, frame_index: int, fps: int, width: int, height: int):
    from PIL import Image, ImageChops, ImageEnhance

    t = frame_index / fps
    beat_index, beat = manga_film._beat_for_time(plan, t)
    u = manga_film._local_progress(beat, t)

    box = _crop_box(beat_index, donor_image.width, donor_image.height, u)
    pixels = donor_image.crop(box).resize((width, height), Image.Resampling.LANCZOS)
    pixels = ImageEnhance.Contrast(pixels).enhance(1.08)
    pixels = ImageEnhance.Color(pixels).enhance(0.94)

    # 008o supplies the readable particular/staging grammar. Multiplication keeps
    # the donor pixels as the image substrate while darkening where 008o draws.
    grammar = manga_film._draw_frame(plan, frame_index, fps, width, height).convert("RGB")
    inked = ImageChops.multiply(pixels, grammar)
    frame = Image.blend(pixels, inked, 0.48)
    return frame, beat_index, beat, box


def render_owned_plan(
    plan: dict,
    donor_manifest_path: str | Path,
    output_path: str | Path,
    *,
    width: int = 640,
    height: int = 360,
    fps: int = 12,
) -> dict:
    narrative_performance._require_schema(plan, narrative_performance.PLAN_SCHEMA)
    if width < 160 or height < 120 or fps < 1:
        raise ValueError("invalid 008p render geometry")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg and FFprobe are required")

    donor = load_donor(donor_manifest_path)
    manifest = donor["manifest"]
    donor_image = donor["image"]

    out = Path(output_path).expanduser().resolve()
    if out.exists():
        raise FileExistsError("008p renderer never overwrites")
    out.parent.mkdir(parents=True, exist_ok=True)

    duration = float(plan["durationSeconds"])
    frame_count = max(1, int(math.ceil(duration * fps)))
    audio = manga_film.audio_plan(plan)

    frame_crops: dict[str, tuple[int, int, int, int]] = {}
    with tempfile.TemporaryDirectory(prefix="haunted-blender-008p-") as td:
        root = Path(td)
        for frame_index in range(frame_count):
            frame, _index, beat, box = _owned_frame(
                plan, donor_image, frame_index, fps, width, height
            )
            frame.save(root / f"frame-{frame_index:06d}.png")
            frame_crops.setdefault(beat["id"], box)

        audio_receipt = manga_film.render_audio(audio, root / "page-five.wav")
        subprocess.run(
            [
                "ffmpeg", "-nostdin", "-v", "error", "-y",
                "-framerate", str(fps),
                "-i", str(root / "frame-%06d.png"),
                "-i", str(root / "page-five.wav"),
                "-t", f"{duration:.6f}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                str(out),
            ],
            check=True,
        )

    probe = manga_film._probe(out)
    beats = []
    derivative_sha = donor["derivativeSha256"]
    for beat in plan["beats"]:
        start = float(beat["start"])
        end = float(beat["end"])
        box = frame_crops.get(beat["id"])
        beats.append({
            "beatId": beat["id"],
            "sourceParticularId": beat["sourceParticularId"],
            "sourceParticularHash": beat["sourceParticularHash"],
            "shotType": beat["type"],
            "start": start,
            "end": end,
            "firstFrame": int(math.floor(start * fps)),
            "lastFrame": max(0, min(frame_count - 1, int(math.ceil(end * fps)) - 1)),
            "pixelDonorDerivativeSha256": derivative_sha,
            "stagingCrop": {
                "x1": box[0], "y1": box[1], "x2": box[2], "y2": box[3],
            } if box else None,
            "cropAuthority": "manual-staging-window-only",
            "semanticSegmentationClaim": False,
        })

    body = {
        "schema": RECEIPT_SCHEMA,
        "planId": plan["id"],
        "sourceId": plan["sourceId"],
        "proposalId": plan["proposalId"],
        "admissionId": plan["admissionId"],
        "adapter": "008o-grammar+owned-pixel-donor+ffmpeg/v1",
        "collectionId": manifest["collectionId"],
        "donorId": manifest["id"],
        "donorExternalId": manifest["externalId"],
        "donorOriginalDriveSha256": manifest["sourceSha256"],
        "donorDerivativeSha256": derivative_sha,
        "donorTransform": manifest["derivative"]["transform"],
        "outputSha256": _file_sha(out),
        "outputByteLength": out.stat().st_size,
        "width": probe["width"],
        "height": probe["height"],
        "fps": fps,
        "frameCount": frame_count,
        "durationSeconds": probe["durationSeconds"],
        "hasAudio": probe["hasAudio"],
        "audioPlanId": audio["id"],
        "audioRenderSha256": audio_receipt["sha256"],
        "beatCount": len(beats),
        "beats": beats,
        "ownedPixelFrames": frame_count,
        "ownedPixelContribution": "shared-donor-surface-present-in-every-rendered-frame",
        "externalGenerations": 0,
        "providerCredits": 0,
        "usdMicros": 0,
        "receiptAuthority": "none",
        "laws": [
            "OWNED COLLECTION != AUTOMATIC FILM ADMISSION",
            "ORIGINAL DRIVE BYTES != REPO DERIVATIVE BYTES",
            "STAGING CROP != SEMANTIC SEGMENTATION",
            "OWNED PIXELS != CHARACTER IDENTITY",
            "PIXEL DONOR != NARRATIVE AUTHORITY",
            "EVERY RENDERED BEAT RETAINS SOURCE PARTICULAR HASH",
            "EVERY RENDERED FRAME CONTAINS ADMITTED DONOR PIXELS",
            "RENDER RECEIPT != SOURCE AUTHORITY",
        ],
    }
    return {**body, "id": "owned-pixel-manga-film:" + _hash(body)[:24]}


def render_spec(
    spec_path: str | Path,
    donor_manifest_path: str | Path,
    output_dir: str | Path,
    *,
    width: int = 640,
    height: int = 360,
    fps: int = 12,
) -> dict:
    spec = narrative_performance.read_spec(spec_path)
    bundle = narrative_performance.compile_spec(spec)
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    movie = out / "page-five-owned-pixel-manga-film.mp4"
    receipt = render_owned_plan(
        bundle["plan"], donor_manifest_path, movie,
        width=width, height=height, fps=fps,
    )
    receipt_path = out / "page-five-owned-pixel-manga-film.receipt.json"
    if receipt_path.exists():
        raise FileExistsError("008p receipt already exists")
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "bundle": bundle,
        "movie": str(movie),
        "receipt": receipt,
        "receiptPath": str(receipt_path),
    }
