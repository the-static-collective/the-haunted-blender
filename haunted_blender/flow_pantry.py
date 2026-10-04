"""Local, path-light indexing for a folder of user-owned video material.

FLOW PANTRY indexes bytes and technical media facts. It does not infer meaning,
quality, authorship, rights, or selection authority from filenames or pixels.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

SCHEMA = "haunted-blender/flow-pantry/v1"
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_toaster_specimen_id(sha256: str, byte_length: int) -> str:
    digest = str(sha256).lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("A 64-character SHA-256 digest is required.")
    if not isinstance(byte_length, int) or byte_length < 0:
        raise ValueError("A non-negative byte length is required.")
    return f"sha256:{digest}:{byte_length}"


def _probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=index,codec_type,codec_name,width,height",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = json.loads(proc.stdout)
    streams = raw.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = (raw.get("format") or {}).get("duration")
    return {
        "durationSeconds": round(float(duration), 6) if duration is not None else None,
        "videoCodec": video.get("codec_name") if video else None,
        "width": int(video["width"]) if video and video.get("width") is not None else None,
        "height": int(video["height"]) if video and video.get("height") is not None else None,
        "audioCodec": audio.get("codec_name") if audio else None,
    }


def index_flow_folder(folder: str | Path, *, recursive: bool = True, probe: bool = True) -> dict:
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Flow source is not a directory: {root}")

    iterator = root.rglob("*") if recursive else root.iterdir()
    paths = sorted(
        (
            p for p in iterator
            if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
        ),
        key=lambda p: p.relative_to(root).as_posix().lower(),
    )
    if not paths:
        raise ValueError("No supported video files were found.")

    items = []
    seen = set()
    for path in paths:
        stat = path.stat()
        if stat.st_size < 1:
            raise ValueError(f"Refusing empty video file: {path.name}")
        sha = _sha256_file(path)
        specimen = canonical_toaster_specimen_id(sha, stat.st_size)
        relative = path.relative_to(root).as_posix()
        item = {
            "assetId": f"flow-video:{sha}:{stat.st_size}",
            "toasterSpecimenId": specimen,
            "relativePath": relative,
            "extension": path.suffix.lower(),
            "sha256": sha,
            "byteLength": stat.st_size,
            "technical": _probe(path) if probe else None,
        }
        items.append(item)
        seen.add(specimen)

    return {
        "schema": SCHEMA,
        "authority": "index-only",
        "recursive": bool(recursive),
        "itemCount": len(items),
        "uniqueSpecimenCount": len(seen),
        "filenameSemantics": "none",
        "items": items,
    }


def validate_flow_manifest(manifest: dict) -> dict:
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError("Unsupported Flow Pantry manifest.")
    if manifest.get("authority") != "index-only":
        raise ValueError("Flow Pantry authority must remain index-only.")
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Flow Pantry requires at least one indexed item.")
    for item in items:
        expected = canonical_toaster_specimen_id(item.get("sha256"), item.get("byteLength"))
        if item.get("toasterSpecimenId") != expected:
            raise ValueError("Flow Pantry specimen identity mismatch.")
    return manifest
