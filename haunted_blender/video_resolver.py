"""Read-only content-address resolver for filmmaker-accepted private video takes.

A SHA-256 address is not enough. Resolution requires a valid accepted-take
witness, its matching request/admission receipt, and unchanged local MP4 bytes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import catalog, creative_take, project, take_cut

ADDRESS = re.compile(r"^sha256:([a-f0-9]{64})$")
SCHEMA = "haunted-blender/accepted-video-resolver/v0"


class VideoResolverError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def parse_address(address: str) -> str:
    match = ADDRESS.fullmatch(address) if isinstance(address, str) else None
    if match is None:
        raise VideoResolverError(
            "INVALID_ADDRESS",
            "Expected sha256:<64 lowercase hex>.",
            400,
        )
    return match.group(1)


def _root(root) -> Path:
    return Path(root).expanduser().resolve(strict=True)


def _acceptance_candidates(root: Path, digest: str):
    folder = root / "snapshots" / "creative-take-acceptances"
    if not folder.is_dir():
        return []

    matches = []
    for path in sorted(folder.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            witness = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if (
            witness.get("schema") == "haunted-blender/accepted-creative-take/v0"
            and witness.get("status") == "filmmaker_accepted_private_preview"
            and witness.get("distribution_authorized") is False
            and witness.get("video_sha256") == digest
        ):
            matches.append((path.resolve(), witness))
    return matches


def _resolve_internal(root, address: str):
    digest = parse_address(address)
    root = _root(root)
    candidates = _acceptance_candidates(root, digest)

    if not candidates:
        raise VideoResolverError(
            "NOT_FOUND",
            "No filmmaker-accepted private take matches that video address.",
            404,
        )

    resolved = []
    failures = []
    for acceptance_path, witness in candidates:
        try:
            expected_acceptance = (
                root
                / "snapshots"
                / "creative-take-acceptances"
                / (creative_take._sha(witness) + ".json")
            )
            if acceptance_path != expected_acceptance:
                raise ValueError("Acceptance witness identity changed")

            request_path = (
                root
                / "snapshots"
                / "creative-takes"
                / (witness["request_sha256"] + ".json")
            )
            request, request_sha = creative_take.load_request(root, request_path)
            if (
                request_sha != witness["request_sha256"]
                or request["artifact_sha256"] != witness["artifact_sha256"]
                or request["beat"] != witness["beat"]
            ):
                raise ValueError("Accepted take request lineage changed")

            artifact_snapshot = request["artifact_snapshot"]
            artifact, artifact_sha, verified_witness, verified_request_sha, video = (
                take_cut._accepted_take(root, artifact_snapshot, acceptance_path)
            )
            if (
                artifact_sha != witness["artifact_sha256"]
                or verified_request_sha != request_sha
                or verified_witness["video_sha256"] != digest
                or catalog.digest_file(video) != digest
            ):
                raise ValueError("Accepted video lineage or bytes changed")

            info = take_cut._probe(video, max_seconds=600)
            resolved.append(
                {
                    "acceptance_path": acceptance_path,
                    "acceptance_sha256": catalog.digest_file(acceptance_path),
                    "request_sha256": request_sha,
                    "artifact_sha256": artifact_sha,
                    "artifact_id": artifact["id"],
                    "beat": witness["beat"],
                    "video": video,
                    "info": info,
                }
            )
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            failures.append(str(exc))

    if not resolved:
        raise VideoResolverError(
            "STALE_ACCEPTANCE",
            "Accepted-take witness exists but its lineage or local bytes no longer verify.",
            409,
        )

    unique = {(str(item["video"]), item["acceptance_sha256"]) for item in resolved}
    if len(unique) != 1:
        raise VideoResolverError(
            "AMBIGUOUS_ACCEPTANCE",
            "More than one distinct accepted-take witness resolves that video address.",
            409,
        )

    item = resolved[0]
    descriptor = {
        "schema": SCHEMA,
        "status": "resolved-filmmaker-accepted-private-take",
        "address": address,
        "sha256": digest,
        "byteLength": item["video"].stat().st_size,
        "mediaType": "video/mp4",
        "acceptanceSha256": item["acceptance_sha256"],
        "requestSha256": item["request_sha256"],
        "artifactSha256": item["artifact_sha256"],
        "artifactId": item["artifact_id"],
        "beat": item["beat"],
        "durationSeconds": item["info"]["duration_seconds"],
        "width": item["info"]["width"],
        "height": item["info"]["height"],
        "distributionAuthorized": False,
        "authority": "none",
        "boundary": [
            "ADDRESS != ACCEPTANCE",
            "CANDIDATE != FILMMAKER ACCEPTED TAKE",
            "ACCEPTANCE != PUBLICATION AUTHORIZATION",
            "RESOLUTION REQUIRES BYTE REVERIFICATION",
            "PLAYABLE != RELEASED",
        ],
    }
    return descriptor, item["video"]


def resolve_accepted_video(root, address: str) -> dict:
    descriptor, _ = _resolve_internal(root, address)
    return descriptor


def resolve_accepted_video_for_serve(root, address: str):
    return _resolve_internal(root, address)
