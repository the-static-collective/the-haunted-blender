"""Content-address resolver for generic filmmaker-accepted motion-organ takes."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import catalog, motion_organ

ADDRESS = re.compile(r"^sha256:([a-f0-9]{64})$")
SCHEMA = "haunted-blender/accepted-motion-video-resolver/v1"


class MotionVideoResolverError(Exception):
    pass


def resolve_accepted_motion_video_for_serve(root, address: str):
    match = ADDRESS.fullmatch(address) if isinstance(address, str) else None
    if match is None:
        raise MotionVideoResolverError("Expected sha256:<64 lowercase hex>.")
    digest = match.group(1)
    root = Path(root).expanduser().resolve(strict=True)
    folder = root / "snapshots" / "motion-organ-acceptances"
    if not folder.is_dir():
        raise MotionVideoResolverError("No motion-organ acceptance vault exists.")

    resolved = []
    for acceptance_path in sorted(folder.glob("*.json")):
        try:
            witness = json.loads(acceptance_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if (
            witness.get("schema") != motion_organ.ACCEPTANCE_SCHEMA
            or witness.get("status") != "filmmaker_accepted_private_motion_organ"
            or witness.get("videoSha256") != digest
            or witness.get("distributionAuthorized") is not False
        ):
            continue
        if acceptance_path != motion_organ._acceptance_path(root, motion_organ._sha(witness)):
            continue
        request_path = motion_organ._request_path(root, witness["requestSha256"])
        try:
            request, request_sha = motion_organ.load_request(root, request_path)
        except Exception:
            continue
        if (
            request_sha != witness["requestSha256"]
            or request["sceneId"] != witness["sceneId"]
            or request["sceneSha256"] != witness["sceneSha256"]
            or request["windowId"] != witness["windowId"]
        ):
            continue

        candidates = motion_organ.candidate_board(root, request_path)["candidates"]
        candidate = next((c for c in candidates if c["videoSha256"] == digest), None)
        if candidate is None:
            continue
        receipt_path = Path(candidate["receipt"])
        if catalog.digest_file(receipt_path) != witness["candidateReceiptSha256"]:
            continue
        video = Path(candidate["video"])
        if catalog.digest_file(video) != digest:
            continue
        info = motion_organ._probe_video(video)
        resolved.append((acceptance_path, witness, request, video, info))

    if len(resolved) != 1:
        raise MotionVideoResolverError("Accepted motion video is missing, stale, or ambiguous.")

    acceptance_path, witness, request, video, info = resolved[0]
    descriptor = {
        "schema": SCHEMA,
        "status": "resolved-filmmaker-accepted-private-motion-organ",
        "address": address,
        "sha256": digest,
        "byteLength": video.stat().st_size,
        "mediaType": "video/mp4",
        "acceptanceSha256": catalog.digest_file(acceptance_path),
        "requestSha256": witness["requestSha256"],
        "sceneId": witness["sceneId"],
        "sceneSha256": witness["sceneSha256"],
        "windowId": witness["windowId"],
        "providerId": witness["providerId"],
        "offerId": witness["offerId"],
        "durationSeconds": info["durationSeconds"],
        "width": info["width"],
        "height": info["height"],
        "distributionAuthorized": False,
        "authority": "none",
        "boundary": [
            "ADDRESS != ACCEPTANCE",
            "CANDIDATE != FILMMAKER ACCEPTED TAKE",
            "PROVIDER != EDITOR",
            "ACCEPTANCE != PUBLICATION AUTHORIZATION",
            "RESOLUTION REQUIRES BYTE REVERIFICATION",
        ],
    }
    return descriptor, video
