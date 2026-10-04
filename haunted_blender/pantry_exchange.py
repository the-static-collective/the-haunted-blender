"""Nuklear Pantry Exchange v1: export verified Blender alchemy evidence without source media."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import alchemy, catalog
from .project import stable_bytes

SCHEMA = "static-collective/pantry-exchange/v1"
MAX_RECEIPT_BYTES = 1024 * 1024


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_receipt(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    if not 0 < len(data) <= MAX_RECEIPT_BYTES:
        raise ValueError("Alchemy receipt is empty or exceeds 1 MiB")
    try:
        receipt = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Alchemy receipt is not valid JSON") from exc
    if not isinstance(receipt, dict):
        raise ValueError("Alchemy receipt must be an object")
    return receipt, data


def export_alchemy(root: Path, snapshot: Path, video: Path, manifest_path: Path) -> dict:
    """Export a verified, path-free content/lineage claim; not renderer authority or consent."""
    video = video.expanduser().resolve(strict=True)
    if video.suffix.lower() != ".mp4" or not video.is_file():
        raise ValueError("Pantry Exchange v1 requires a completed local MP4")
    manifest_path = manifest_path.expanduser().resolve()
    receipt_path = video.with_suffix(video.suffix + ".receipt.json")
    snapshot = snapshot.expanduser().resolve(strict=True)
    spec = alchemy.plan(root, snapshot)  # Rechecks original and rendered derivative hashes.
    bundle, snapshot_sha256 = alchemy._load_snapshot(root, snapshot)
    receipt, receipt_bytes = _read_receipt(receipt_path)
    if manifest_path in (video, receipt_path, snapshot):
        raise ValueError("Manifest must not overwrite source, receipt, or snapshot")
    expected = {
        "schema": "haunted-blender/alchemy-receipt/v1",
        "status": "scoped_complete",
        "snapshot_sha256": snapshot_sha256,
        "recipe_id": spec["recipe_id"],
        "relation": spec["relation"],
        "evidence_class": "artist_proposed",
        "adapter": "ffmpeg-alchemy-crossfade/v1",
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError("Alchemy receipt mismatch: " + key)
    if Path(receipt.get("output_path", "")).expanduser().resolve() != video:
        raise ValueError("Receipt output path does not identify the selected video")
    media_sha256 = catalog.digest_file(video)
    if receipt.get("output_sha256") != media_sha256:
        raise ValueError("Video bytes differ from the completed Blender receipt")
    ordered = []
    for segment in spec["segments"]:
        role = segment["role"]
        requested = bundle["sources"][role]["requested"]
        frame = bundle["sources"][role]["frame"]
        ordered.append({
            "role": role,
            "assetId": requested["id"],
            "sourceSha256": requested["sha256"],
            "renderedSha256": frame["sha256"],
        })
    expected_segments = [
        {"role": item["role"], "asset_id": item["assetId"],
         "rendered_sha256": item["renderedSha256"]}
        for item in ordered
    ]
    if receipt.get("segments") != expected_segments:
        raise ValueError("Alchemy receipt segment lineage differs from frozen sources")
    if manifest_path.exists():
        # Idempotent repeat of this exact exchange is safe; never overwrite another manifest.
        previous = manifest_path.read_bytes()
    else:
        previous = None
    manifest = {
        "schema": SCHEMA,
        "producer": {
            "app": "haunted-blender",
            "kind": "alchemy-crossfade",
            "recipeId": spec["recipe_id"],
            "snapshotSha256": snapshot_sha256,
            "receiptSha256": _sha256(receipt_bytes),
            "adapter": "ffmpeg-alchemy-crossfade/v1",
            "relation": spec["relation"],
            "evidenceClass": "artist_proposed",
            "orderedSources": ordered,
        },
        "media": {
            "sha256": media_sha256,
            "byteLength": video.stat().st_size,
            "container": "mp4",
            "audio": "none",
        },
        "authority": {
            "creativeRelation": "artist-proposed",
            "renderAuthority": "none",
            "consumerAudioAuthority": "none",
        },
    }
    payload = stable_bytes(manifest) + b"\n"
    if previous is not None:
        if previous != payload:
            raise FileExistsError("Existing exchange manifest differs; refusing overwrite")
    else:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("xb") as handle:
            handle.write(payload)
    return {
        "manifestPath": str(manifest_path),
        "manifestSha256": _sha256(payload),
        "mediaSha256": media_sha256,
        "receiptSha256": manifest["producer"]["receiptSha256"],
        "schema": SCHEMA,
        "status": "exported-not-imported",
    }
